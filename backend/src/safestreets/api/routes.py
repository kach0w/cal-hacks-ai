"""HTTP surface.

- POST /analyze            run full pipeline for an intersection, returns AnalysisResult
- GET  /analyze/stream     SSE live agent feed (the 'wow moment')
- GET  /intersection       cached result for a lat/lng (instant on repeat)
- POST /submit             resident submission (photo + description)
- GET  /corridor/{id}      coalition view
"""
from __future__ import annotations

import base64
import json

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from safestreets.api.schemas import AnalyzeRequest, CouncilEmailRequest, SubmitRequest
from safestreets.clients.google_maps import satellite_url, streetview_capture_date, streetview_url
from safestreets.lastmile import coalition, council_lookup, email_agent, pdf
from safestreets.models.analysis import AnalysisResult
from safestreets.models.intersection import ImageRef, Intersection, ViewDirection
from safestreets.orchestrator import coordinator
from safestreets.orchestrator.dispatch import gather_data, run_pipeline
from safestreets.store import cache, keys

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
    """Gather data (cached), run the two-stage vision pipeline, cache + return the result.

    Repeat calls for the same intersection return the cached AnalysisResult instantly.
    """
    cached = await cache.get_json(keys.vision_key(req.lat, req.lng))
    if cached is not None:
        return cached

    data = await gather_data(req.lat, req.lng, req.city)
    intersection = Intersection(
        id=f"{round(req.lat, 5)},{round(req.lng, 5)}",
        address=req.address or " & ".join(data.get("streets", [])) or f"{req.lat},{req.lng}",
        lat=req.lat,
        lng=req.lng,
        city=req.city,
        images=[ImageRef(**img) for img in data.get("images", [])],
    )
    vkey = keys.vision_key(req.lat, req.lng)
    result = await coordinator.analyze(intersection, data, vision_key=vkey)
    payload = result.model_dump(mode="json")
    await cache.set_json(vkey, payload, ttl=keys.VISION_TTL)
    return payload


@router.post("/council-email")
async def council_email(req: CouncilEmailRequest):
    """Draft a constituent email to the council member(s) for this intersection and return
    it with a ready-to-send `.eml` (the council letter PDF attached).

    Requires a prior /analyze for the same point (it reuses the cached findings + letter).
    The agent writes the subject + human-sounding body; recipients are resolved by
    jurisdiction via Socrata. The frontend downloads the `.eml` to open in the user's mail
    client. Cached so re-opening the dialog is instant and doesn't re-bill the LLM.
    """
    cached_email = await cache.get_json(keys.council_email_key(req.lat, req.lng))
    if cached_email is not None:
        return cached_email

    cached = await cache.get_json(keys.vision_key(req.lat, req.lng))
    if cached is None:
        return {"status": "not_analyzed"}

    result = AnalysisResult.model_validate(cached)
    community = await cache.get_json(keys.scrape_key(req.lat, req.lng)) or {}
    contacts = await council_lookup.find_council_contacts(req.lat, req.lng, result.intersection.city)
    draft = await email_agent.build_council_email(result.findings, result.intersection, community, contacts)

    letter_text = result.council_report or draft.body
    pdf_bytes = pdf.council_letter_pdf(f"Pedestrian Safety — {result.intersection.address}", letter_text)
    pdf_name = email_agent.pdf_filename(result.intersection)
    eml = email_agent.build_eml(draft, pdf_bytes, pdf_name)

    payload = {
        "subject": draft.subject,
        "body": draft.body,
        "recipients": [c.model_dump() for c in draft.recipients],
        "eml_base64": base64.b64encode(eml.encode("utf-8")).decode(),
        "filename": pdf_name.replace(".pdf", ".eml"),
    }
    await cache.set_json(keys.council_email_key(req.lat, req.lng), payload, ttl=keys.VISION_TTL)
    return payload


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
