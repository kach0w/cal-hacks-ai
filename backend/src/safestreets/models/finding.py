"""Stage 2 (corroboration) output: an observed condition matched — independently —
against community evidence, then routed to a candidate fix."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from safestreets.models.condition import ObservedCondition
from safestreets.models.intervention import Intervention


class FindingStatus(str, Enum):
    CONFIRMED = "CONFIRMED"   # seen AND independently corroborated
    CANDIDATE = "CANDIDATE"   # seen, no corroboration found
    REPORTED = "REPORTED"     # in community data, not visually confirmable


class Corroboration(BaseModel):
    source: str            # "311" | "news" | "council" | "crash"
    reference: str         # e.g. "complaint #2847221" or "SF Chronicle 2023-03-14"
    excerpt: str | None = None
    date: str | None = None


class Finding(BaseModel):
    condition: ObservedCondition
    status: FindingStatus
    corroboration: list[Corroboration] = Field(default_factory=list)
    intervention: Intervention | None = None

    # precision discipline: only set when the source record supports corner-level detail
    crash_count_intersection: int | None = None
    crash_count_zone: int | None = None
