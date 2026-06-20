"""Stage 1 (blind vision) output: what the model can actually SEE."""
from __future__ import annotations

from datetime import date
from enum import Enum

from pydantic import BaseModel


class NamedZone(str, Enum):
    """Canonical intersection frame. We localize to named zones, never raw pixels,
    so a marker can't render on the wrong corner."""
    NW = "NW"          # corners
    NE = "NE"
    SW = "SW"
    SE = "SE"
    N_LEG = "N_LEG"    # approaches
    S_LEG = "S_LEG"
    E_LEG = "E_LEG"
    W_LEG = "W_LEG"
    CENTER = "CENTER"


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ObservedCondition(BaseModel):
    zone: NamedZone
    observation: str                       # what in the image indicates it
    source_view: str                       # "satellite" | "streetview_north" | ...
    source_capture_date: date | None = None
    confidence: Confidence = Confidence.MEDIUM
    not_visually_confirmable: bool = False  # e.g. signal phasing, night lighting
