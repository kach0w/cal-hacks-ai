"""Identifies who actually decides this and drafts a message + names the next meeting.

The responsible body is usually the city traffic engineer / DOT and the relevant council
office. This is data-dependent (per-city); start with a config map for the demo city.
"""
from __future__ import annotations

from typing import Any

from safestreets.models.analysis import AnalysisResult


async def build_messenger_packet(result: AnalysisResult, city_contacts: dict[str, Any]) -> dict[str, Any]:
    """TODO: resolve council district from lat/lng; pull the next public meeting date;
    draft a ready-to-send message that cites the top findings and the accountability log.
    Returns {responsible_body, official, next_meeting, draft_message}."""
    raise NotImplementedError("Map district -> official + next meeting for the demo city.")
