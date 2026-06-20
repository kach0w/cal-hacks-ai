"""The full bundle returned for an intersection, plus the resident-submission input."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from safestreets.models.accountability import AccountabilityEvent
from safestreets.models.finding import Finding
from safestreets.models.intersection import Intersection


class ResidentSubmission(BaseModel):
    lat: float
    lng: float
    zone_hint: str | None = None
    description: str
    photo_url: str | None = None
    submitted_at: datetime = Field(default_factory=datetime.utcnow)


class AnalysisResult(BaseModel):
    intersection: Intersection
    findings: list[Finding] = Field(default_factory=list)
    accountability: list[AccountabilityEvent] = Field(default_factory=list)
    coalition_count: int = 0          # how many residents flagged this corridor
    annotated_image_url: str | None = None
    concept_image_url: str | None = None   # ALWAYS rendered with a "concept, not a photo" label
    generated_at: datetime = Field(default_factory=datetime.utcnow)
