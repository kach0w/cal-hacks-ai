"""Stage 1: BLIND vision pass.

Claude sees ONLY imagery — no crash data, no complaints, no news. This is what makes
'seen' an independent signal from 'reported'. The output feeds Stage 2 for corroboration.
"""
from __future__ import annotations

import base64
import json
from pathlib import Path

import httpx

from safestreets.clients.anthropic_client import get_anthropic
from safestreets.config import get_settings
from safestreets.models.condition import Confidence, NamedZone, ObservedCondition
from safestreets.models.intersection import Intersection

_PROMPT = (Path(__file__).parent / "prompts" / "stage1_blind.txt").read_text()


async def _encode_image(url: str) -> dict:
    """Fetch an image URL and return an Anthropic image content block."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        media_type = resp.headers.get("content-type", "image/jpeg").split(";")[0]
        data = base64.standard_b64encode(resp.content).decode()
    return {
        "type": "image",
        "source": {"type": "base64", "media_type": media_type, "data": data},
    }


def _parse(text: str) -> list[ObservedCondition]:
    """Parse the model's JSON array into ObservedCondition objects, defensively."""
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    raw = json.loads(text)
    out: list[ObservedCondition] = []
    for item in raw:
        try:
            out.append(
                ObservedCondition(
                    zone=NamedZone(item["zone"]),
                    observation=item["observation"],
                    source_view=item.get("source_view", "satellite"),
                    source_capture_date=item.get("source_capture_date") or None,
                    confidence=Confidence(item.get("confidence", "medium")),
                    not_visually_confirmable=bool(item.get("not_visually_confirmable", False)),
                )
            )
        except (KeyError, ValueError):
            continue  # skip malformed rows rather than fail the whole pass
    return out


async def run_blind_pass(intersection: Intersection) -> list[ObservedCondition]:
    """Run the blind vision pass over the intersection's imagery."""
    settings = get_settings()
    client = get_anthropic()

    # IMPORTANT: only imagery goes in. No community text.
    content: list[dict] = [{"type": "text", "text": _PROMPT}]
    for img in intersection.images:
        date_note = f" (captured {img.capture_date})" if img.capture_date else ""
        content.append({"type": "text", "text": f"[{img.direction.value}{date_note}]"})
        content.append(await _encode_image(img.url))

    resp = await client.messages.create(
        model=settings.claude_vision_model,
        max_tokens=1024,
        messages=[{"role": "user", "content": content}],
    )
    text = "".join(b.text for b in resp.content if b.type == "text")
    return _parse(text)
