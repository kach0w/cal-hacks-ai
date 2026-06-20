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


def _agent_calls(lat: float, lng: float, city: str | None) -> dict[str, Callable[[], Awaitable[Any]]]:
    """The agents to run, keyed by name. Single source of truth so the SSE feed
    (`run_pipeline`) and the uAgent path (`gather_community_data`) can't drift."""
    from safestreets.agents import (
        council_311_agent,
        image_fetcher,
        news_agent,
        structured_data,
    )

    return {
        "structured": lambda: structured_data.fetch_crash_data(lat, lng, city),
        "news": lambda: news_agent.fetch_news(lat, lng, city),
        "council_311": lambda: council_311_agent.fetch_council_and_311(lat, lng, city),
        "images": lambda: image_fetcher.fetch_images(lat, lng),
    }


async def gather_community_data(lat: float, lng: float, city: str | None) -> dict[str, Any]:
    """Run the agents and return their raw results keyed by agent name.

    This is the substance behind `run_pipeline` without the progress-event wrapping:
    non-SSE callers (the Fetch.ai uAgent orchestrator) use it to feed
    `coordinator.analyze`. Keys: structured, news, council_311, images.
    """
    results: dict[str, Any] = {}
    for name, call in _agent_calls(lat, lng, city).items():
        results[name] = await _with_retry(call)
    return results


# Friendly labels so the live feed reads like reporting, not like function names.
_LABELS = {
    "structured": "crash records (FARS + city open data)",
    "news": "local news",
    "council_311": "council minutes + 311 portal",
    "images": "satellite + street view imagery",
}


def _summarize(name: str, value: Any) -> str:
    """Honest one-liner for the feed — counts what actually came back, invents nothing."""
    label = _LABELS.get(name, name)
    if value is None:
        return f"{label}: no data"
    if isinstance(value, dict):  # council_311 -> {complaints_311, council}
        return (
            f"{label}: {len(value.get('complaints_311', []))} 311 reports, "
            f"{len(value.get('council', []))} council mentions"
        )
    if isinstance(value, list):
        unit = {"images": "views", "structured": "crash records", "news": "articles"}.get(name, "items")
        return f"{label}: {len(value)} {unit}"
    return f"{label}: ok"


def _event(name: str, value: Any, err: str | None) -> ProgressEvent:
    """Build the per-agent feed event (the {agent, msg, ...} shape AgentFeed.tsx renders)."""
    if err:
        return {"agent": name, "msg": f"{_LABELS.get(name, name)}: failed ({err})", "error": True}
    return {"agent": name, "msg": _summarize(name, value)}


def _escalation_reason(results: dict[str, Any]) -> str | None:
    """Signal-driven escalation gate: do the first-wave danger signals (crash records,
    news) warrant paying for the deep council-minutes + 311 scrape? Returns a human reason
    when they do, else None. Stubbed agents return nothing, so this stays quiet until the
    real crash/news feeds are live."""
    crashes = results.get("structured") or []
    news = results.get("news") or []
    triggers: list[str] = []
    if crashes:
        triggers.append(f"{len(crashes)} crash records")
    if news:
        triggers.append(f"{len(news)} news reports")
    return ", ".join(triggers) or None


async def _dispatch_concurrently(
    calls: dict[str, Callable[[], Awaitable[Any]]], names: list[str]
) -> AsyncIterator[tuple[str, Any, str | None]]:
    """Run the named agents concurrently (each with retry/backoff) and yield
    `(name, value, error)` as each one lands — completion order, so the feed updates live.
    A single agent failing surfaces as an error tuple; it never kills the stream."""

    async def _run(name: str) -> tuple[str, Any, str | None]:
        try:
            return name, await _with_retry(calls[name]), None
        except Exception as exc:  # noqa: BLE001 — surface to the feed, don't crash the pipeline
            return name, None, str(exc)

    for completed in asyncio.as_completed([asyncio.create_task(_run(n)) for n in names]):
        yield await completed


async def run_pipeline(lat: float, lng: float, city: str | None) -> AsyncIterator[ProgressEvent]:
    """Yields progress events the SSE endpoint streams to the frontend agent feed.

    Adaptive, not a static fan-out: a fast first wave (crash data, news, imagery) fans out
    concurrently, then strong danger signals escalate to the expensive deep council/311
    scrape. The event shape ({agent, msg, ...}) is what AgentFeed.tsx renders.
    """
    calls = _agent_calls(lat, lng, city)
    results: dict[str, Any] = {}

    # Wave 1: the primary danger signals + imagery, fanned out concurrently.
    yield {"agent": "orchestrator", "msg": "dispatching first-wave agents (concurrent)"}
    async for name, value, err in _dispatch_concurrently(calls, ["structured", "news", "images"]):
        results[name] = value
        yield _event(name, value, err)

    # ESCALATION HOOK: the deep council-minutes + 311 scrape (the slowest, most expensive
    # Browserbase pass) only runs when wave 1 shows this is a real corridor worth an
    # accountability case — that's the adaptive part the Fetch.ai track is about.
    reason = _escalation_reason(results)
    if reason:
        yield {
            "agent": "orchestrator",
            "msg": f"strong signals ({reason}) — escalating to deep council + 311 scrape",
            "escalated": True,
        }
        async for name, value, err in _dispatch_concurrently(calls, ["council_311"]):
            results[name] = value
            yield _event(name, value, err)
    else:
        results["council_311"] = None
        yield {"agent": "orchestrator", "msg": "no danger signal — skipping the deep council/311 scrape"}

    yield {"agent": "orchestrator", "msg": "data gathered", "results_keys": list(results)}
    # The non-SSE path (`gather_community_data`) feeds the gathered data to coordinator.analyze.
