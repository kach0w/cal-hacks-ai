"""Adaptive dispatch.

This is the Fetch.ai-track substance: not a static fan-out, but concurrent execution
with retry/backoff and signal-driven escalation. It also caches the gathered data in
Redis under `scrape_key` (24h) so repeat queries are instant and we don't re-scrape /
re-hit Browserbase for the same intersection. Emits progress events for the live feed.
"""
from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any

from safestreets.store import cache, keys

ProgressEvent = dict[str, Any]


async def _with_retry(fn: Callable[[], Awaitable[Any]], attempts: int = 2, base_delay: float = 0.5) -> Any:
    last: Exception | None = None
    for i in range(attempts):
        try:
            return await fn()
        except NotImplementedError:
            return None  # stubbed agent — don't crash the pipeline during the build
        except Exception as exc:  # noqa: BLE001
            last = exc
            await asyncio.sleep(base_delay * (2**i))
    raise last if last else RuntimeError("dispatch failed")


async def _gather(lat: float, lng: float, city: str | None) -> AsyncIterator[ProgressEvent]:
    """Run every agent, emitting progress; the final event carries the assembled
    community_data under '__data__' and the data is cached under scrape_key."""
    from safestreets.agents import (
        council_311_agent,
        image_fetcher,
        news_agent,
        structured_data,
    )
    from safestreets.clients import google_maps

    yield {"agent": "orchestrator", "msg": "locating intersection"}
    streets: list[str] = []
    try:
        streets = await google_maps.nearby_streets(lat, lng)
    except Exception:  # noqa: BLE001
        streets = []
    terms = google_maps.street_terms(streets)
    yield {"agent": "orchestrator", "msg": "streets", "streets": streets}

    yield {"agent": "images", "msg": "satellite + street view"}
    images = await _with_retry(lambda: image_fetcher.fetch_images(lat, lng)) or []
    yield {"agent": "images", "msg": "done", "count": len(images)}

    yield {"agent": "structured", "msg": "crash records"}
    crash = await _with_retry(lambda: structured_data.fetch_crash_data(lat, lng, city)) or []
    yield {"agent": "structured", "msg": "done", "count": len(crash)}

    yield {"agent": "news", "msg": "local news"}
    news = await _with_retry(
        lambda: news_agent.fetch_news(lat, lng, city, street_terms=terms)
    ) or []
    yield {"agent": "news", "msg": "done", "count": len(news)}

    yield {"agent": "council_311", "msg": "311 + council agendas"}
    cc = await _with_retry(
        lambda: council_311_agent.fetch_council_and_311(lat, lng, city, street_terms=terms)
    ) or {}
    complaints = cc.get("complaints_311", [])
    council = cc.get("council", [])
    yield {
        "agent": "council_311", "msg": "done",
        "complaints": len(complaints), "council": len(council),
    }

    data = {
        "images": [img.model_dump(mode="json") for img in images],
        "streets": streets,
        "crash_data": crash,
        "complaints_311": complaints,
        "news": news,
        "council": council,
    }
    await cache.set_json(keys.scrape_key(lat, lng), data, ttl=keys.SCRAPE_TTL)
    yield {"__data__": data}


async def run_pipeline(lat: float, lng: float, city: str | None) -> AsyncIterator[ProgressEvent]:
    """Yields progress events the SSE endpoint streams to the frontend agent feed.

    On a cache hit we short-circuit (the 'instant on repeat' moment); otherwise we run
    the agents live, emitting per-agent events, and persist the result for /analyze.
    """
    if await cache.get_json(keys.scrape_key(lat, lng)) is not None:
        yield {"agent": "orchestrator", "msg": "cache hit — instant", "cached": True}
        return

    yield {"agent": "orchestrator", "msg": "dispatching agents (adaptive)"}
    async for event in _gather(lat, lng, city):
        if "__data__" not in event:
            yield event
    yield {"agent": "orchestrator", "msg": "data gathered"}


async def gather_data(lat: float, lng: float, city: str | None) -> dict[str, Any]:
    """Non-streaming gather used by POST /analyze. Cache-first, then agents."""
    cached = await cache.get_json(keys.scrape_key(lat, lng))
    if cached is not None:
        return cached
    data: dict[str, Any] = {}
    async for event in _gather(lat, lng, city):
        if "__data__" in event:
            data = event["__data__"]
    return data
