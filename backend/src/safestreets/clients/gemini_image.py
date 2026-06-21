"""Gemini image editing client — cost-optimized."""
from __future__ import annotations

import asyncio
import logging
from functools import partial
from io import BytesIO

import httpx
from google import genai
from google.genai import types

from safestreets.config import get_settings

log = logging.getLogger(__name__)

_MODEL = "gemini-3.1-flash-image-preview"

_VIEW_TO_MIME = {
    "satellite": "image/png",
    "streetview_north": "image/jpeg",
    "streetview_south": "image/jpeg",
    "streetview_east": "image/jpeg",
    "streetview_west": "image/jpeg",
}

_MAX_PX = 512  # resize source image before sending to reduce input tokens


def _resize(data: bytes, max_px: int = _MAX_PX) -> bytes:
    from PIL import Image as PILImage
    img = PILImage.open(BytesIO(data)).convert("RGB")
    w, h = img.size
    if max(w, h) > max_px:
        scale = max_px / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), PILImage.LANCZOS)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=80)
    return buf.getvalue()


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
            resized = _resize(source_image_bytes)
            contents = [
                types.Part.from_bytes(data=resized, mime_type="image/jpeg"),
                types.Part.from_text(text=prompt),
            ]
        else:
            contents = prompt

        fn = partial(
            client.models.generate_content,
            model=_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
                thinking_config=types.ThinkingConfig(thinking_budget=0),
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
