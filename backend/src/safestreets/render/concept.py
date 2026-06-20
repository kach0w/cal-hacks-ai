"""Generates an OPTIONAL Midjourney concept illustration of a proposed fix.

Hard rule: the returned image is ALWAYS surfaced with a 'Illustrative concept - not a
photo of this site' label. The honest primary 'after' is an overlay on the real photo,
not this. This exists so the demo's emotional beat doesn't become the AI-slop failure
the project is built to avoid.
"""
from __future__ import annotations

from safestreets.clients import midjourney
from safestreets.models.finding import Finding

CONCEPT_LABEL = "Illustrative concept - not a photo of this site"


async def generate(findings: list[Finding]) -> tuple[str | None, str]:
    """Returns (image_url_or_none, label). Stretch goal."""
    top = ", ".join(f.intervention.name for f in findings if f.intervention)[:200]
    prompt = f"photorealistic street intersection with these safety fixes applied: {top}"
    url = await midjourney.generate_concept(prompt)
    return url, CONCEPT_LABEL
