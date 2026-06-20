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
_GEOCODE = "https://maps.googleapis.com/maps/api/geocode/json"

_HEADINGS = {"north": 0, "east": 90, "south": 180, "west": 270}

# words to drop so 'University Avenue' -> 'university' (the part that appears in slugs/PDFs)
_STREET_SUFFIXES = {
    "ave", "avenue", "st", "street", "blvd", "boulevard", "rd", "road", "way",
    "dr", "drive", "ln", "lane", "ct", "court", "pl", "place", "ter", "terrace",
    "hwy", "highway", "pkwy", "parkway", "n", "s", "e", "w", "north", "south", "east", "west",
}


async def nearby_streets(lat: float, lng: float) -> list[str]:
    """Reverse-geocode to the street names at this point (for news/council matching).

    Returns the distinct 'route' names Google reports nearby, e.g.
    ['University Avenue', 'Martin Luther King Jr Way'].
    """
    key = get_settings().google_maps_api_key
    if not key:
        return []
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(_GEOCODE, params={"latlng": f"{lat},{lng}", "key": key})
        data = resp.json()
    routes: list[str] = []
    for result in data.get("results", []):
        for comp in result.get("address_components", []):
            if "route" in comp.get("types", []):
                name = comp.get("long_name")
                if name and name not in routes:
                    routes.append(name)
    return routes


def street_terms(streets: list[str]) -> list[str]:
    """Tokenize street names into lowercase keywords usable for slug/PDF matching.

    'Martin Luther King Jr Way' -> ['martin', 'luther', 'king', 'jr'] (drops 'way').
    """
    terms: list[str] = []
    for s in streets:
        for tok in s.lower().replace(".", "").split():
            if tok not in _STREET_SUFFIXES and len(tok) > 2 and tok not in terms:
                terms.append(tok)
    return terms


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
    return data.get("date") if data.get("status") == "OK" else None
