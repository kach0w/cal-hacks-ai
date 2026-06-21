"""Stage 5: per-finding Gemini before/after concept renders.

For each finding, fetches the source image Claude used (satellite or street view),
sends it to Gemini with a fix instruction, and saves the result to disk.
"""
from __future__ import annotations

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
    if finding.intervention:
        fix = finding.intervention.name
    else:
        fix = "general pedestrian safety improvements"
    obs = finding.condition.observation
    return (
        f"This is a photo of an urban intersection. "
        f"The observed safety issue is: {obs}. "
        f"Edit the image to show the fix applied: {fix}. "
        f"Keep the scene photorealistic. Label nothing."
    )


async def generate(
    intersection: Intersection,
    findings: list[Finding],
    out_dir: Path = Path("."),
) -> list[dict]:
    """Returns a list of dicts with keys: zone, before_url, after_url, label.

    after_url is a base64 data URI usable directly in <img src="...">.
    """
    url_map: dict[str, str] = {}
    for img in intersection.images:
        for view_key, direction in _VIEW_TO_DIRECTION.items():
            if img.direction == direction:
                url_map[view_key] = img.url

    results = []
    for i, finding in enumerate(findings):
        source_view = finding.condition.source_view
        source_url = url_map.get(source_view)

        source_bytes = None
        source_mime = "image/jpeg"
        if source_url:
            try:
                source_bytes = await fetch_image_bytes(source_url)
                source_mime = _VIEW_TO_MIME.get(source_view, "image/jpeg")
            except Exception:
                pass

        prompt = _fix_prompt(finding)
        after_bytes = await generate_image(prompt, source_bytes, source_mime)

        after_url = None
        if after_bytes:
            b64 = base64.b64encode(after_bytes).decode()
            after_url = f"data:image/png;base64,{b64}"

        results.append({
            "zone": finding.condition.zone.value,
            "observation": finding.condition.observation,
            "fix": finding.intervention.name if finding.intervention else None,
            "before_url": source_url,
            "after_url": after_url,
            "label": CONCEPT_LABEL,
        })

    return results
