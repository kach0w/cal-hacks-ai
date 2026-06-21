"""Structured data agent: crash records near an intersection.

Source: California Crash Reporting System (CCRS), published as a queryable API on
data.ca.gov. Unlike NHTSA FARS (fatal-only and currently WAF-blocked), CCRS is a direct
SQL-over-HTTP API covering ALL reported collisions (injury + fatal) with lat/lng and the
two cross streets — so it filters cleanly to a single intersection. No Browserbase needed.
"""
from __future__ import annotations

from typing import Any

import httpx

_CCRS_SQL = "https://data.ca.gov/api/3/action/datastore_search_sql"
_CCRS_RESOURCE = "9f4fc839-122d-4595-a146-43bc4ed16f46"  # California Crash Reporting System


def _to_int(v: Any) -> int | None:
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


async def fetch_crash_data(
    lat: float,
    lng: float,
    city: str | None,
    radius_deg: float = 0.003,
) -> list[dict[str, Any]]:
    """Every CCRS collision within the intersection bounding box (no cap).

    The bounding box does the geospatial selection; when the caller supplies `city` we
    also constrain by it so edge-of-box points in a neighbouring jurisdiction don't leak
    in. Nothing here is pinned to a specific city. Returns normalized crash dicts.
    """
    d = radius_deg
    conditions = [
        f'CAST("Latitude" AS FLOAT) BETWEEN {lat - d} AND {lat + d}',
        f'CAST("Longitude" AS FLOAT) BETWEEN {lng - d} AND {lng + d}',
    ]
    if city:
        conditions.insert(0, f"\"City Name\"='{city.replace(chr(39), chr(39) * 2)}'")
    sql = (
        'SELECT "Collision Id","Crash Date Time","Collision Type Description",'
        '"NumberInjured","NumberKilled","HitRun","PrimaryRoad","SecondaryRoad",'
        f'"Latitude","Longitude" FROM "{_CCRS_RESOURCE}" WHERE '
        + " AND ".join(conditions)
    )
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(_CCRS_SQL, params={"sql": sql})
        resp.raise_for_status()
        payload = resp.json()
    if not payload.get("success"):
        return []

    out: list[dict[str, Any]] = []
    for r in payload["result"]["records"]:
        out.append(
            {
                "collision_id": r.get("Collision Id"),
                "date": (r.get("Crash Date Time") or "")[:10],
                "type": r.get("Collision Type Description"),
                "injured": _to_int(r.get("NumberInjured")),
                "killed": _to_int(r.get("NumberKilled")),
                "hit_run": r.get("HitRun"),
                "primary_road": r.get("PrimaryRoad"),
                "secondary_road": r.get("SecondaryRoad"),
                "lat": r.get("Latitude"),
                "lng": r.get("Longitude"),
                "source": "CCRS (data.ca.gov)",
            }
        )
    return out
