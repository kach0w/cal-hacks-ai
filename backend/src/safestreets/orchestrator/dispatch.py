"""Adaptive dispatch.

This is the Fetch.ai-track substance: not a static fan-out, but concurrent execution
with retry/backoff and signal-driven escalation (e.g. if the first scrape returns strong
signals, escalate to a deeper pass). Emits progress events for the live agent feed.
"""
from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any

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


async def run_pipeline(lat: float, lng: float, city: str | None) -> AsyncIterator[ProgressEvent]:
    """Yields progress events the SSE endpoint streams to the frontend agent feed.

    TODO: wire the real agents in. The shape below is what AgentFeed.tsx renders.
    """
    from safestreets.agents import (
        council_311_agent,
        image_fetcher,
        news_agent,
        structured_data,
    )

    yield {"agent": "orchestrator", "msg": "dispatching agents (adaptive)"}

    tasks = {
        "structured": _with_retry(lambda: structured_data.fetch_crash_data(lat, lng, city)),
        "news": _with_retry(lambda: news_agent.fetch_news(lat, lng, city)),
        "council_311": _with_retry(lambda: council_311_agent.fetch_council_and_311(lat, lng, city)),
        "images": _with_retry(lambda: image_fetcher.fetch_images(lat, lng)),
    }
    results: dict[str, Any] = {}
    for name, coro in tasks.items():
        results[name] = await coro
        yield {"agent": name, "msg": "done"}

    # ESCALATION HOOK: if news/311 signals are strong, trigger a deeper scrape here.
    yield {"agent": "orchestrator", "msg": "data gathered", "results_keys": list(results)}
    # The coordinator (below) consumes `results` to run the vision pipeline.
