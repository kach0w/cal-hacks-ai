"""HTTP surface.

- POST /analyze            kick off analysis for an intersection
- GET  /analyze/stream     SSE live agent feed (the 'wow moment')
- GET  /intersection       cached result for a lat/lng (instant on repeat)
- POST /submit             resident submission (photo + description)
- GET  /corridor/{id}      coalition view
"""
from __future__ import annotations

import json

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from safestreets.api.schemas import AnalyzeRequest, SubmitRequest
from safestreets.lastmile import coalition
from safestreets.orchestrator.dispatch import run_pipeline
from safestreets.store import cache, keys

router = APIRouter()


@router.get("/analyze/stream")
async def analyze_stream(lat: float, lng: float, city: str | None = None):
    """Streams progress events to the frontend agent feed as the pipeline runs."""

    async def event_gen():
        async for event in run_pipeline(lat, lng, city):
            yield {"event": "progress", "data": json.dumps(event)}
        yield {"event": "done", "data": "{}"}

    return EventSourceResponse(event_gen())


@router.post("/analyze")
async def analyze(req: AnalyzeRequest):
    """TODO: assemble Intersection (images + community data from Redis) and call
    coordinator.analyze; cache the AnalysisResult under the vision key."""
    return {"status": "todo", "lat": req.lat, "lng": req.lng}


@router.get("/intersection")
async def get_intersection(lat: float, lng: float):
    cached = await cache.get_json(keys.vision_key(lat, lng))
    return cached or {"status": "not_analyzed"}


@router.post("/submit")
async def submit(req: SubmitRequest):
    """Resident submission: counts toward the corridor coalition and can supersede
    stale Street View. TODO: persist the photo + description for re-analysis."""
    corridor_id = f"{round(req.lat, 4)}:{round(req.lng, 4)}"
    count = await coalition.add_report(corridor_id, resident_token="anon")  # TODO: real token
    return {"status": "received", "coalition_count": count}


@router.get("/corridor/{corridor_id}")
async def corridor(corridor_id: str):
    return {"corridor_id": corridor_id, "coalition_count": await coalition.count(corridor_id)}
