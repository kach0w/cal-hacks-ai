"""Google Static Maps + Street View URL builders and capture-date lookup.

The Street View metadata endpoint returns the image's capture date for free — this is
how we badge stale imagery and let resident photos supersede it.
"""
from __future__ import annotations

import httpx

from safestreets.config import get_settings

_STATIC = "https://maps.googleapis.com/maps/api/staticmap"
_SV = "https://maps.googleapis.com/maps/api/streetview"
_SV_META = "https://maps.googleapis.com/maps/api/streetview/metadata"

_HEADINGS = {"north": 0, "east": 90, "south": 180, "west": 270}


def satellite_url(lat: float, lng: float, zoom: int = 19, size: int = 640) -> str:
    key = get_settings().google_maps_api_key
    return f"{_STATIC}?center={lat},{lng}&zoom={zoom}&size={size}x{size}&maptype=satellite&key={key}"


def streetview_url(lat: float, lng: float, direction: str, size: int = 640) -> str:
    key = get_settings().google_maps_api_key
    heading = _HEADINGS[direction]
    return f"{_SV}?location={lat},{lng}&size={size}x{size}&heading={heading}&fov=90&key={key}"


async def streetview_capture_date(lat: float, lng: float) -> str | None:
    """Returns the 'date' field (YYYY-MM) from Street View metadata, or None."""
    key = get_settings().google_maps_api_key
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(_SV_META, params={"location": f"{lat},{lng}", "key": key})
        data = resp.json()
    raw = data.get("date") if data.get("status") == "OK" else None
    if raw and len(raw) == 7:
        raw = f"{raw}-01"
    return raw
