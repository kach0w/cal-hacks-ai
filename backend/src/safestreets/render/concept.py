"""Stage 5: per-finding Gemini before/after concept renders (parallel)."""
from __future__ import annotations

import asyncio
import base64
import logging
from pathlib import Path

from safestreets.clients.gemini_image import fetch_image_bytes, generate_image, _VIEW_TO_MIME
from safestreets.models.finding import Finding
from safestreets.models.intersection import Intersection, ViewDirection

log = logging.getLogger(__name__)

CONCEPT_LABEL = "AI-edited concept — same POV, hazard removed"

_VIEW_TO_DIRECTION = {
    "satellite":        ViewDirection.SATELLITE,
    "streetview_north": ViewDirection.NORTH,
    "streetview_south": ViewDirection.SOUTH,
    "streetview_east":  ViewDirection.EAST,
    "streetview_west":  ViewDirection.WEST,
}


def _edit_prompt(finding: Finding) -> str:
    fix = finding.intervention.name if finding.intervention else "general pedestrian safety improvements"
    return (
        f"This is a real photo of a street intersection. "
        f"Edit this image to show it AFTER this safety improvement has been applied: {fix}. "
        f"Keep the exact same camera angle, perspective, lighting, time of day, and all surroundings identical. "
        f"Only modify the specific infrastructure element that needs fixing: {finding.condition.observation}. "
        f"Do not change anything else. Do not move the camera. Do not add text or labels."
    )


async def _render_one(finding: Finding, source_url: str | None, source_view: str) -> dict:
    source_bytes: bytes | None = None
    mime = _VIEW_TO_MIME.get(source_view, "image/jpeg")

    if source_url and not source_url.startswith("data:"):
        try:
            source_bytes = await fetch_image_bytes(source_url)
        except Exception:
            log.warning("Could not fetch source image for %s", source_view)

    after_bytes = await generate_image(
        _edit_prompt(finding),
        source_image_bytes=source_bytes,
        source_mime=mime,
    )

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
