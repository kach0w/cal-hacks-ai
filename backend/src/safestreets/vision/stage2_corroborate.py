"""Stage 2: independent corroboration.

Takes the conditions Stage 1 SAW (without ever seeing community data) and matches them,
in a separate call, against crash/311/news/council records. Output labels each finding
CONFIRMED / CANDIDATE / REPORTED. This is what keeps 'seen + corroborated' honest.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from safestreets.clients.anthropic_client import get_anthropic
from safestreets.config import get_settings
from safestreets.models.condition import ObservedCondition
from safestreets.models.finding import Corroboration, Finding, FindingStatus

_PROMPT = (Path(__file__).parent / "prompts" / "stage2_corroborate.txt").read_text()


def _parse(text: str, conditions: list[ObservedCondition]) -> list[Finding]:
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    rows = json.loads(text)
    findings: list[Finding] = []
    for row in rows:
        idx = row.get("index")
        if idx is None or idx >= len(conditions):
            continue
        corro = [
            Corroboration(
                source=c.get("source", "unknown"),
                reference=c.get("reference", ""),
                excerpt=c.get("excerpt"),
                date=c.get("date"),
            )
            for c in row.get("corroboration", [])
        ]
        findings.append(
            Finding(
                condition=conditions[idx],
                status=FindingStatus(row.get("status", "CANDIDATE")),
                corroboration=corro,
                crash_count_intersection=row.get("crash_count_intersection"),
                crash_count_zone=row.get("crash_count_zone"),
            )
        )
    return findings


async def corroborate(
    conditions: list[ObservedCondition],
    community_data: dict[str, Any],
) -> list[Finding]:
    """community_data keys: crash_data, complaints_311, news, council."""
    settings = get_settings()
    client = get_anthropic()

    payload = {
        "observed_conditions": [c.model_dump() for c in conditions],
        "crash_data": community_data.get("crash_data", []),
        "complaints_311": community_data.get("complaints_311", []),
        "news": community_data.get("news", []),
        "council": community_data.get("council", []),
    }

    resp = await client.messages.create(
        model=settings.claude_text_model,
        max_tokens=2500,
        messages=[
            {
                "role": "user",
                "content": f"{_PROMPT}\n\nDATA:\n{json.dumps(payload, default=str)}",
            }
        ],
    )
    text = "".join(b.text for b in resp.content if b.type == "text")
    return _parse(text, conditions)
