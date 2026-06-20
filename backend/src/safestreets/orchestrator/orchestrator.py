"""Fetch.ai uAgent wrapper.

For the demo, the HTTP API drives the pipeline directly via `dispatch.run_pipeline`.
This uAgent is the Fetch.ai-track surface: it receives AnalyzeRequest messages and
coordinates the same pipeline through the agent protocol. Keep both paths thin so they
share `dispatch` and `coordinator` logic.
"""
from __future__ import annotations

import asyncio
import re
from typing import Any

from uagents import Agent, Context

from safestreets.config import get_settings
from safestreets.models.analysis import AnalysisResult
from safestreets.models.intersection import Intersection
from safestreets.orchestrator import coordinator, dispatch
from safestreets.orchestrator.messages import AnalyzeAck, AnalyzeRequest
from safestreets.store import cache, keys

settings = get_settings()

orchestrator = Agent(name="safestreets-orchestrator", seed=settings.orchestrator_seed)

# Hold references to in-flight pipeline tasks so the event loop doesn't garbage-collect
# them mid-run (asyncio only keeps a weak reference to the task).
_jobs: set[asyncio.Task[None]] = set()


def _intersection_id(msg: AnalyzeRequest) -> str:
    """A stable, human-ish id (e.g. 'oakland-international-blvd-35th'), falling back
    to the coordinate pair when there's no address text to slugify."""
    parts = [p for p in (msg.city, msg.address) if p]
    slug = re.sub(r"[^a-z0-9]+", "-", "-".join(parts).lower()).strip("-")
    return slug or f"{msg.lat},{msg.lng}"


def _to_community_data(results: dict[str, Any]) -> dict[str, Any]:
    """Map dispatch's raw agent results onto the keys the coordinator's corroboration
    and accountability steps expect (crash_data / complaints_311 / news / council)."""
    council_311 = results.get("council_311") or {}
    return {
        "crash_data": results.get("structured") or [],
        "news": results.get("news") or [],
        "complaints_311": council_311.get("complaints_311", []),
        "council": council_311.get("council", []),
    }


async def _run_pipeline(ctx: Context, msg: AnalyzeRequest, job_id: str) -> None:
    """Reuse the same dispatch + coordinator logic the HTTP path uses, then cache the
    result under the vision key so it's retrievable via GET /intersection."""
    try:
        # 1. Gather community data through the shared adaptive dispatch.
        results = await dispatch.gather_community_data(msg.lat, msg.lng, msg.city)

        # 2. Assemble the intersection (imagery is one of the gathered agents).
        intersection = Intersection(
            id=_intersection_id(msg),
            address=msg.address,
            lat=msg.lat,
            lng=msg.lng,
            city=msg.city,
            images=results.get("images") or [],
        )

        # 3. Run the two-stage vision pipeline + intervention/last-mile.
        result: AnalysisResult = await coordinator.analyze(
            intersection, _to_community_data(results)
        )

        # 4. Cache so repeat queries (and the requester polling for `job_id`) are instant.
        await cache.set_json(
            keys.vision_key(msg.lat, msg.lng), result.model_dump(), ttl=keys.VISION_TTL
        )
        ctx.logger.info(f"analysis complete job={job_id} findings={len(result.findings)}")
    except Exception as exc:  # noqa: BLE001 — never let one job take the agent down
        ctx.logger.error(f"analysis failed job={job_id}: {exc}")


@orchestrator.on_message(model=AnalyzeRequest, replies=AnalyzeAck)
async def handle_analyze(ctx: Context, sender: str, msg: AnalyzeRequest) -> None:
    ctx.logger.info(f"analyze request for {msg.address}")

    # The pipeline (two Claude calls + scrapes) takes a while, so don't block the reply
    # on it: kick it off in the background and hand the sender a job id to poll. The
    # job id is the vision cache key, so GET /intersection?lat&lng returns the result.
    job_id = keys.vision_key(msg.lat, msg.lng)
    task = asyncio.create_task(_run_pipeline(ctx, msg, job_id))
    _jobs.add(task)
    task.add_done_callback(_jobs.discard)

    await ctx.send(sender, AnalyzeAck(job_id=job_id))


if __name__ == "__main__":
    orchestrator.run()
