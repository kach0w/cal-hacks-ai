"""Gemini 2.5 Flash image generation client.

Uses gemini-2.5-flash-preview-05-20 via generateContent with IMAGE modality.
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

_MODEL = "gemini-2.5-flash-image"

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
            client.models.generate_content,
            model=_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )
        result = await asyncio.get_event_loop().run_in_executor(None, fn)
        for part in result.candidates[0].content.parts:
            if getattr(part, "inline_data", None) and part.inline_data.data:
                return part.inline_data.data
        log.warning("Gemini returned no image part")
        return None
    except Exception:
        log.exception("Gemini image generation failed")
        return None
