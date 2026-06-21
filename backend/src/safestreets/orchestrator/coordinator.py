"""End-to-end coordination: dispatch -> two-stage vision -> intervention/funding ->
last-mile -> render. This is the function both the HTTP API and the uAgent call.
"""
from __future__ import annotations

import asyncio
import base64
import logging
from typing import Any

from safestreets.intervention import funding_match, matcher
from safestreets.lastmile import accountability, coalition
from safestreets.lastmile.ask import build_lastmile, build_reddit_post
from safestreets.models.analysis import AnalysisResult
from safestreets.models.intersection import Intersection
from safestreets.vision import stage1_blind, stage2_corroborate

log = logging.getLogger(__name__)


async def _render_and_persist(
    intersection: Intersection,
    findings: list,
    vision_key: str,
    cached_payload: dict,
) -> None:
    """Background task: generate Gemini before/after renders and patch the cached result."""
    try:
        from safestreets.render.concept import generate as render_concept
        from safestreets.store import cache

        renders = await render_concept(intersection, findings)
        cached_payload["renders"] = renders
        has_corroboration = any(f.get("corroboration") for f in cached_payload.get("findings", []))
        if has_corroboration:
            await cache.set_json(vision_key, cached_payload, ttl=86400)
        log.info("Concept renders complete for %s", intersection.id)
    except Exception:
        log.exception("Background render failed for %s", intersection.id)


async def analyze(
    intersection: Intersection,
    community_data: dict[str, Any],
    vision_key: str | None = None,
) -> AnalysisResult:
    # Stage 1: blind vision pass (street view only, images resized to 512px)
    conditions = await stage1_blind.run_blind_pass(intersection)

    # Stage 2: independent corroboration against crash/311/news/council data
    findings = await stage2_corroborate.corroborate(conditions, community_data)

    # Stage 3: attach interventions
    for f in findings:
        f.intervention = matcher.match(f.condition)
        if f.intervention:
            _ = funding_match.programs_for(f.intervention)

    result = AnalysisResult(
        intersection=intersection,
        findings=findings,
        accountability=await accountability.build_log(intersection.id, community_data),
        coalition_count=await coalition.count(intersection.id),
    )

    # Stage 4: social post + council letter in one Claude call (non-fatal)
    try:
        result.social_post, result.council_report = await build_lastmile(findings, intersection, community_data)
    except Exception:
        log.exception("Last-mile generation failed")

    # Reddit post (separate call, independently non-fatal)
    try:
        result.reddit_post = await build_reddit_post(findings, intersection, community_data)
    except Exception:
        pass

    # Annotated satellite overlay (non-fatal)
    sat = intersection.satellite()
    if sat:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=15) as http:
                r = await http.get(sat.url)
                r.raise_for_status()
            result.annotated_image_url = "data:image/jpeg;base64," + base64.b64encode(r.content).decode()
        except Exception:
            log.warning("Could not fetch satellite image")

    # Stage 5: Gemini concept renders — fire and forget, patch cache when done
    if vision_key:
        payload = result.model_dump(mode="json")
        asyncio.create_task(_render_and_persist(intersection, findings, vision_key, payload))

    return result
