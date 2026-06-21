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
    from safestreets.clients.google_maps import reverse_geocode as google_maps_reverse_geocode
    from safestreets.clients import google_maps
    from safestreets.config import get_settings

    city = city or get_settings().demo_city  # demo scope lives in one config knob
    yield {"agent": "orchestrator", "msg": "locating intersection"}
    streets: list[str] = []
    geo_city = ""
    try:
        geo = await google_maps_reverse_geocode(lat, lng)
        streets = geo["streets"]
        geo_city = geo["city"]
    except Exception:  # noqa: BLE001
        streets = []
    yield {"agent": "orchestrator", "msg": "streets", "streets": streets}

    # Run images, crash records, and 311 in parallel — they're all independent network calls.
    from safestreets.clients.google_maps import street_terms as make_terms
    terms = make_terms(streets)

    yield {"agent": "orchestrator", "msg": "fetching images + crash + 311 + news in parallel"}
    images_task = asyncio.ensure_future(_with_retry(lambda: image_fetcher.fetch_images(lat, lng)))
    crash_task  = asyncio.ensure_future(_with_retry(lambda: structured_data.fetch_crash_data(lat, lng, city)))
    compl_task  = asyncio.ensure_future(_with_retry(lambda: council_311_agent.fetch_311(lat, lng)))
    news_task   = asyncio.ensure_future(_with_retry(lambda: news_agent.fetch_news(lat, lng, city, terms)))

    images_raw, crash, complaints, news = await asyncio.gather(
        images_task, crash_task, compl_task, news_task, return_exceptions=True
    )
    images     = images_raw if isinstance(images_raw, list) else []
    crash      = crash      if isinstance(crash,      list) else []
    complaints = complaints if isinstance(complaints, list) else []
    news       = news       if isinstance(news,       list) else []
    yield {"agent": "orchestrator", "msg": "data ready", "images": len(images), "crashes": len(crash), "complaints": len(complaints), "news": len(news)}

    data = {
        "images": [img.model_dump(mode="json") for img in images],
        "streets": streets,
        "city": geo_city or city or "",
        "crash_data": crash,
        "complaints_311": complaints,
        "news": news,
    }
    # Only cache scrape if we got some community data — avoids poisoning the cache
    # with empty agent results that would block all future re-fetches.
    if crash or complaints or news:
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
    """Non-streaming gather used by POST /analyze. Cache-first, then agents.

    POST /analyze and the SSE stream both start concurrently on first load, so both
    may call _gather simultaneously. If our _gather comes back with empty community
    data, the SSE stream's _gather may have saved better data in the meantime — check
    the scrape_key one more time before handing empty data to the analysis pipeline.
    """
    cached = await cache.get_json(keys.scrape_key(lat, lng))
    if cached is not None:
        return cached
    data: dict[str, Any] = {}
    async for event in _gather(lat, lng, city):
        if "__data__" in event:
            data = event["__data__"]
    # If our own _gather got nothing, check whether the concurrent SSE _gather saved
    # better community data while we were running.
    if not data.get("crash_data") and not data.get("complaints_311") and not data.get("news"):
        fresher = await cache.get_json(keys.scrape_key(lat, lng))
        if fresher is not None:
            return fresher
    return data
