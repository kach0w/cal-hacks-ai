"""Midjourney concept illustration client (OPTIONAL, SECONDARY).

Whatever this returns is rendered with a 'Illustrative concept - not a photo of this
site' label. Never present a Midjourney image as the real intersection.
"""
from __future__ import annotations


async def generate_concept(prompt: str) -> str | None:
    """TODO: call the Midjourney provider; return an image URL or None."""
    raise NotImplementedError("Midjourney concept generation is a stretch goal.")
