"""Gemini Imagen 4 image generation client.

Uses imagen-4.0-generate-001 via generate_images (predict endpoint).
Falls back gracefully if the key is missing or generation fails.
"""
from __future__ import annotations

import asyncio
import logging
from functools import partial

import httpx
from google import genai
from google.genai import types

from safestreets.config import get_settings

log = logging.getLogger(__name__)

_VIEW_TO_MIME = {
    "satellite": "image/png",
    "streetview_north": "image/jpeg",
    "streetview_south": "image/jpeg",
    "streetview_east": "image/jpeg",
    "streetview_west": "image/jpeg",
}


async def fetch_image_bytes(url: str) -> bytes:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url)
        r.raise_for_status()
        return r.content


async def generate_image(
    prompt: str,
    source_image_bytes: bytes | None = None,
    source_mime: str = "image/jpeg",
) -> bytes | None:
    key = get_settings().google_ai_api_key
    if not key:
        log.warning("GOOGLE_AI_API_KEY not set — skipping concept render")
        return None

    client = genai.Client(api_key=key)

    try:
        fn = partial(
            client.models.generate_images,
            model="imagen-4.0-generate-001",
            prompt=prompt,
            config=types.GenerateImagesConfig(number_of_images=1),
        )
        result = await asyncio.get_event_loop().run_in_executor(None, fn)
        return result.generated_images[0].image.image_bytes
    except Exception:
        log.exception("Gemini image generation failed")
        return None
