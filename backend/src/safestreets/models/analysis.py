"""The full bundle returned for an intersection, plus the resident-submission input."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from safestreets.models.accountability import AccountabilityEvent
from safestreets.models.finding import Finding
from safestreets.models.intersection import Intersection


class RedditPost(BaseModel):
    subreddit: str          # bare name, e.g. 'berkeley' (UI renders 'r/berkeley')
    title: str
    body: str


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
    renders: list[dict] = Field(default_factory=list)   # per-finding before/after data URIs
    social_post: str | None = None
    reddit_post: RedditPost | None = None
    council_report: str | None = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)
