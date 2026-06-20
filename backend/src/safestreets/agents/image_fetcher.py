"""Fetches satellite + 4 Street View images with capture dates. Resident-submitted
photos supersede stale Street View for the relevant view."""
from __future__ import annotations

from safestreets.clients import google_maps
from safestreets.models.intersection import ImageRef, Intersection, ViewDirection

_SV_DIRS = {
    "north": ViewDirection.NORTH,
    "south": ViewDirection.SOUTH,
    "east": ViewDirection.EAST,
    "west": ViewDirection.WEST,
}


async def fetch_images(lat: float, lng: float) -> list[ImageRef]:
    images: list[ImageRef] = [
        ImageRef(direction=ViewDirection.SATELLITE, url=google_maps.satellite_url(lat, lng))
    ]
    capture = await google_maps.streetview_capture_date(lat, lng)
    for name, direction in _SV_DIRS.items():
        images.append(
            ImageRef(
                direction=direction,
                url=google_maps.streetview_url(lat, lng, name),
                capture_date=capture,
            )
        )
    return images


def apply_resident_photo(intersection: Intersection, photo_url: str, direction: ViewDirection) -> None:
    """Override a stale Street View image with a current resident photo."""
    intersection.images = [i for i in intersection.images if i.direction != direction]
    intersection.images.append(
        ImageRef(direction=direction, url=photo_url, resident_submitted=True)
    )
