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

# Approach headings: camera is ON the named leg, looking TOWARD the intersection center.
# e.g. "north" = camera north of center, facing south (180°).
_HEADINGS = {"north": 180, "east": 270, "south": 0, "west": 90}

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


async def reverse_city(lat: float, lng: float) -> str | None:
    """Reverse-geocode to the city/locality name at this point (e.g. 'Berkeley').

    Used to pick the right local subreddit. Falls through several component types because
    not every place publishes a plain 'locality' (unincorporated areas, big metros).
    """
    key = get_settings().google_maps_api_key
    if not key:
        return None
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(_GEOCODE, params={"latlng": f"{lat},{lng}", "key": key})
        data = resp.json()
    results = data.get("results", [])
    for ctype in ("locality", "postal_town", "administrative_area_level_3", "sublocality"):
        for result in results:
            for comp in result.get("address_components", []):
                if ctype in comp.get("types", []):
                    return comp.get("long_name")
    return None


async def geocode_address(address: str) -> dict | None:
    """Forward-geocode a free-text address/intersection to a point.

    For an intersection ('Cedar and San Pablo, Berkeley, CA') this returns the actual
    corner; for a single street it returns the street's geometric center (imprecise).
    Returns {lat, lng, formatted, location_type} or None.
    """
    key = get_settings().google_maps_api_key
    if not key:
        return None
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(_GEOCODE, params={"address": address, "key": key})
        data = resp.json()
    if data.get("status") != "OK" or not data.get("results"):
        return None
    top = data["results"][0]
    loc = top["geometry"]["location"]
    return {
        "lat": loc["lat"],
        "lng": loc["lng"],
        "formatted": top.get("formatted_address"),
        "location_type": top["geometry"].get("location_type"),
    }


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
    return (
        f"{_SV}?location={lat},{lng}&size={size}x{size}"
        f"&heading={heading}&fov=90&pitch=0"
        f"&radius=50&source=outdoor&key={key}"
    )


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
