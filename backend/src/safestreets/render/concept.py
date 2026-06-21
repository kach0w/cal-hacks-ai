"""Stage 5: per-finding Gemini before/after concept renders (parallel)."""
from __future__ import annotations

import asyncio
import base64
from pathlib import Path

from safestreets.clients.gemini_image import fetch_image_bytes, generate_image, _VIEW_TO_MIME
from safestreets.models.finding import Finding
from safestreets.models.intersection import Intersection, ViewDirection

CONCEPT_LABEL = "Illustrative concept — not a photo of this site"

_VIEW_TO_DIRECTION = {
    "satellite":        ViewDirection.SATELLITE,
    "streetview_north": ViewDirection.NORTH,
    "streetview_south": ViewDirection.SOUTH,
    "streetview_east":  ViewDirection.EAST,
    "streetview_west":  ViewDirection.WEST,
}


def _fix_prompt(finding: Finding) -> str:
    fix = finding.intervention.name if finding.intervention else "general pedestrian safety improvements"
    zone = finding.condition.zone.value
    return (
        f"Photorealistic aerial satellite view of an urban intersection in Berkeley, California. "
        f"The {zone} zone shows: {finding.condition.observation}. "
        f"Show the intersection AFTER the safety fix has been applied: {fix}. "
        f"Bright daylight, top-down view, high resolution, realistic street markings and infrastructure."
    )


async def _render_one(finding: Finding, source_url: str | None, source_view: str) -> dict:
    after_bytes = await generate_image(_fix_prompt(finding))
    after_url = None
    if after_bytes:
        after_url = "data:image/png;base64," + base64.b64encode(after_bytes).decode()

    return {
        "zone": finding.condition.zone.value,
        "observation": finding.condition.observation,
        "fix": finding.intervention.name if finding.intervention else None,
        "before_url": source_url,
        "after_url": after_url,
        "label": CONCEPT_LABEL,
    }


async def generate(
    intersection: Intersection,
    findings: list[Finding],
    out_dir: Path = Path("."),
) -> list[dict]:
    url_map: dict[str, str] = {
        view_key: img.url
        for img in intersection.images
        for view_key, direction in _VIEW_TO_DIRECTION.items()
        if img.direction == direction
    }

    tasks = [
        _render_one(f, url_map.get(f.condition.source_view), f.condition.source_view)
        for f in findings
    ]
    return list(await asyncio.gather(*tasks))
