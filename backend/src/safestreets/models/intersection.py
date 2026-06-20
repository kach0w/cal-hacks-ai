"""An intersection and the imagery fetched for it."""
from __future__ import annotations

from datetime import date
from enum import Enum

from pydantic import BaseModel, Field


class ViewDirection(str, Enum):
    SATELLITE = "satellite"
    NORTH = "streetview_north"
    SOUTH = "streetview_south"
    EAST = "streetview_east"
    WEST = "streetview_west"


class ImageRef(BaseModel):
    """A single fetched image. capture_date is what stops us from claiming a
    cleared bush is 'still there' based on a 2019 photo."""
    direction: ViewDirection
    url: str
    width: int = 640
    height: int = 640
    capture_date: date | None = None
    resident_submitted: bool = False  # supersedes stale Street View when True


class Intersection(BaseModel):
    id: str = Field(..., description="stable id, e.g. 'oakland-international-35th'")
    address: str
    lat: float
    lng: float
    city: str | None = None
    images: list[ImageRef] = Field(default_factory=list)

    def satellite(self) -> ImageRef | None:
        return next((i for i in self.images if i.direction == ViewDirection.SATELLITE), None)
