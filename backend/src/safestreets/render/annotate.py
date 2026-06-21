"""Satellite annotation — no-op. Frontend renders all markers client-side."""
from __future__ import annotations

from safestreets.models.finding import Finding


async def annotate_satellite(satellite_url: str, findings: list[Finding]) -> bytes:
    return b""
