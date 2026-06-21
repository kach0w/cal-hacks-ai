"""HTTP surface.

- POST /analyze            run full pipeline for an intersection, returns AnalysisResult
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
from safestreets.clients.google_maps import satellite_url, streetview_capture_date, streetview_url
from safestreets.lastmile import coalition
from safestreets.models.intersection import ImageRef, Intersection, ViewDirection
from safestreets.orchestrator import coordinator
from safestreets.orchestrator.dispatch import run_pipeline

router = APIRouter()

# Hardcoded community data until Browserbase agents are wired up
_DEMO_COMMUNITY_DATA: dict = {
    "crash_data": [],
    "complaints_311": [],
    "news": [],
    "council": [],
}


async def _build_intersection(lat: float, lng: float, address: str, city: str) -> Intersection:
    raw_date = await streetview_capture_date(lat, lng)
    capture_date = raw_date if raw_date else None
    slug = address.lower().replace(" ", "-").replace(",", "").replace("&", "and")[:40]
    images = [
        ImageRef(direction=ViewDirection.SATELLITE, url=satellite_url(lat, lng)),
        ImageRef(direction=ViewDirection.NORTH, url=streetview_url(lat, lng, "north"), capture_date=capture_date),
        ImageRef(direction=ViewDirection.SOUTH, url=streetview_url(lat, lng, "south"), capture_date=capture_date),
        ImageRef(direction=ViewDirection.EAST,  url=streetview_url(lat, lng, "east"),  capture_date=capture_date),
        ImageRef(direction=ViewDirection.WEST,  url=streetview_url(lat, lng, "west"),  capture_date=capture_date),
    ]
    return Intersection(id=slug, address=address, lat=lat, lng=lng, city=city or "Berkeley", images=images)


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
    """Run the full pipeline (stages 1-5) and return the analysis result."""
    intersection = await _build_intersection(
        req.lat, req.lng,
        req.address or f"{req.lat:.5f},{req.lng:.5f}",
        req.city or "Berkeley",
    )

    result = await coordinator.analyze(intersection, _DEMO_COMMUNITY_DATA)
    return result.model_dump(mode="json")


@router.get("/intersection")
async def get_intersection(lat: float, lng: float):
    return {"status": "not_analyzed"}


@router.post("/submit")
async def submit(req: SubmitRequest):
    corridor_id = f"{round(req.lat, 4)}:{round(req.lng, 4)}"
    count = await coalition.add_report(corridor_id, resident_token="anon")
    return {"status": "received", "coalition_count": count}


@router.get("/corridor/{corridor_id}")
async def corridor(corridor_id: str):
    return {"corridor_id": corridor_id, "coalition_count": await coalition.count(corridor_id)}
