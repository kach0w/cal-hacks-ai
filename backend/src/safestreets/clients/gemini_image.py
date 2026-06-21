"""Gemini image generation/editing client.

If source_image_bytes is provided, sends it alongside the prompt for image editing.
Otherwise generates from text only. Returns raw PNG bytes or None on failure.
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
        if source_image_bytes:
            # Image editing: send source photo + fix instruction
            contents = [
                types.Part.from_bytes(data=source_image_bytes, mime_type=source_mime),
                types.Part.from_text(text=prompt),
            ]
            fn = partial(
                client.models.generate_content,
                model="gemini-2.5-flash-image",
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                ),
            )
            result = await asyncio.get_event_loop().run_in_executor(None, fn)
            for part in result.candidates[0].content.parts:
                if part.inline_data:
                    return part.inline_data.data
            log.error("Gemini returned no image parts")
            return None
        else:
            # Text-to-image via Imagen 4
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
