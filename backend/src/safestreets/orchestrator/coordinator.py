"""End-to-end coordination: dispatch -> two-stage vision -> intervention/funding ->
last-mile -> render. This is the function both the HTTP API and the uAgent call.
"""
from __future__ import annotations

import base64
from typing import Any

from safestreets.intervention import funding_match, matcher
from safestreets.lastmile import accountability, coalition
from safestreets.lastmile.ask import build_lastmile
from safestreets.models.analysis import AnalysisResult
from safestreets.models.intersection import Intersection
from safestreets.render import annotate
from safestreets.render.concept import generate as render_concept
from safestreets.vision import stage1_blind, stage2_corroborate


async def analyze(intersection: Intersection, community_data: dict[str, Any]) -> AnalysisResult:
    # Stage 1: blind (imagery only)
    conditions = await stage1_blind.run_blind_pass(intersection)

    # Stage 2: independent corroboration
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

    # Stage 4: last-mile packet — single call for both outputs (non-fatal)
    try:
        result.social_post, result.council_report = await build_lastmile(findings, intersection, community_data)
    except Exception:
        pass

    # Annotated satellite overlay (non-fatal)
    sat = intersection.satellite()
    if sat:
        try:
            png = await annotate.annotate_satellite(sat.url, findings)
            result.annotated_image_url = "data:image/png;base64," + base64.b64encode(png).decode()
        except Exception:
            pass

    # Stage 5: per-finding Gemini before/after renders (non-fatal)
    try:
        result.renders = await render_concept(intersection, findings)
    except Exception:
        pass

    return result
