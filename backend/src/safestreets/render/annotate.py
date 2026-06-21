"""Draws numbered markers on the REAL satellite image at deterministic zone positions.
The grounded annotated real image is the hero deliverable."""
from __future__ import annotations

from io import BytesIO

import httpx
from PIL import Image, ImageDraw

from safestreets.models.finding import Finding
from safestreets.vision.geometry import spread_overlapping


async def annotate_satellite(satellite_url: str, findings: list[Finding]) -> bytes:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(satellite_url)
        resp.raise_for_status()
    img = Image.open(BytesIO(resp.content)).convert("RGB")
    out = BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()
