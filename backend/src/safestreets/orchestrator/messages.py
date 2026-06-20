"""uAgent message models (Fetch.ai). Kept minimal for the hackathon."""
from __future__ import annotations

from uagents import Model


class AnalyzeRequest(Model):
    lat: float
    lng: float
    address: str
    city: str | None = None


class AnalyzeAck(Model):
    job_id: str
