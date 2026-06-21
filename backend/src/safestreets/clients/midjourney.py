"""Midjourney concept illustration via piapi.ai (unofficial REST wrapper).

Submit an /imagine job, poll until done, return the first upscaled image URL.
Returns None on any error so callers degrade gracefully.
"""
from __future__ import annotations

import asyncio
import logging

import httpx

from safestreets.config import get_settings

log = logging.getLogger(__name__)

_BASE = "https://api.piapi.ai/mj/v2"
_POLL_INTERVAL = 5   # seconds between status checks
_MAX_WAIT = 300      # give up after 5 minutes


async def generate_concept(prompt: str) -> str | None:
    key = get_settings().midjourney_api_key
    if not key:
        log.warning("MIDJOURNEY_API_KEY not set — skipping concept render")
        return None

    headers = {"X-API-Key": key, "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=30) as client:
        # 1. Submit imagine job
        r = await client.post(
            f"{_BASE}/imagine",
            headers=headers,
            json={"prompt": prompt, "aspect_ratio": "1:1", "process_mode": "fast"},
        )
        r.raise_for_status()
        task_id = r.json().get("task_id")
        if not task_id:
            log.error("piapi /imagine returned no task_id: %s", r.text)
            return None

        log.info("Midjourney task submitted: %s", task_id)

        # 2. Poll until done
        elapsed = 0
        while elapsed < _MAX_WAIT:
            await asyncio.sleep(_POLL_INTERVAL)
            elapsed += _POLL_INTERVAL

            s = await client.get(f"{_BASE}/fetch", headers=headers, params={"task_id": task_id})
            s.raise_for_status()
            data = s.json()
            status = data.get("status", "")

            if status == "finished":
                # piapi returns a list of image URLs under output.image_urls
                urls = (data.get("output") or {}).get("image_urls") or []
                return urls[0] if urls else None

            if status in ("failed", "error"):
                log.error("Midjourney task %s failed: %s", task_id, data)
                return None

            log.debug("Midjourney task %s status=%s elapsed=%ds", task_id, status, elapsed)

    log.warning("Midjourney task %s timed out after %ds", task_id, _MAX_WAIT)
    return None
