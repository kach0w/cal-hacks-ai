"""HTTP request/response models."""
from __future__ import annotations

from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    address: str | None = None
    lat: float
    lng: float
    city: str | None = None


class SubmitRequest(BaseModel):
    lat: float
    lng: float
    description: str
    zone_hint: str | None = None
    photo_url: str | None = None
