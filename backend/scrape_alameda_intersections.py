"""
Scrape the most dangerous intersections in Alameda County from CCRS (data.ca.gov).

Queries the California Crash Reporting System, groups by PrimaryRoad+SecondaryRoad,
scores by severity (kills weighted 5x, injuries 1x), and writes the top results to
intersections.json at the repo root.

Run:
    cd backend && python scrape_alameda_intersections.py
"""
from __future__ import annotations

import asyncio
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import httpx

_CCRS_SQL = "https://data.ca.gov/api/3/action/datastore_search_sql"
_CCRS_RESOURCE = "9f4fc839-122d-4595-a146-43bc4ed16f46"

# Rough bounding box for Alameda County as fallback
_COUNTY_LAT = (37.45, 37.92)
_COUNTY_LNG = (-122.38, -121.47)

OUTPUT = Path(__file__).parent.parent / "intersections.json"


def _norm(s: str | None) -> str:
    if not s:
        return ""
    return re.sub(r"\s+", " ", s.strip().upper())


def _to_float(v: Any) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _to_int(v: Any) -> int:
    try:
        return int(v) if v is not None else 0
    except (TypeError, ValueError):
        return 0


async def fetch_ccrs_alameda() -> list[dict]:
    """Fetch all Alameda County crashes from CCRS using a bounding-box filter."""
    lat_min, lat_max = _COUNTY_LAT
    lng_min, lng_max = _COUNTY_LNG

    sql = (
        f'SELECT "Collision Id","Crash Date Time","Collision Type Description",'
        f'"NumberInjured","NumberKilled","HitRun","PrimaryRoad","SecondaryRoad",'
        f'"Latitude","Longitude","City Name" '
        f'FROM "{_CCRS_RESOURCE}" '
        f'WHERE CAST("Latitude" AS FLOAT) BETWEEN {lat_min} AND {lat_max} '
        f'AND CAST("Longitude" AS FLOAT) BETWEEN {lng_min} AND {lng_max} '
        f'AND "PrimaryRoad" IS NOT NULL '
        f'AND "SecondaryRoad" IS NOT NULL '
        f'LIMIT 50000'
    )

    print("Querying CCRS for Alameda County crashes…")
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.get(_CCRS_SQL, params={"sql": sql})
        resp.raise_for_status()
        payload = resp.json()

    if not payload.get("success"):
        raise RuntimeError(f"CCRS query failed: {payload}")

    records = payload["result"]["records"]
    print(f"  → {len(records)} raw crash records returned")
    return records


_FREEWAY_RE = re.compile(
    r"^(I-|SR-|US-|HWY|HIGHWAY|FREEWAY|EXPRESSWAY|CAL-|CA-|STATE ROUTE|INTERSTATE|ON RAMP|OFF RAMP|SB |NB |EB |WB |S/B|N/B|E/B|W/B)",
    re.IGNORECASE,
)

def _is_freeway(road: str) -> bool:
    return bool(_FREEWAY_RE.match(road))


def aggregate_intersections(records: list[dict]) -> list[dict]:
    """Group crashes by intersection, score by severity, return sorted list."""
    groups: dict[tuple[str, str], dict] = defaultdict(lambda: {
        "crash_count": 0,
        "total_killed": 0,
        "total_injured": 0,
        "hit_run_count": 0,
        "lats": [],
        "lngs": [],
        "cities": set(),
        "years": set(),
        "crash_types": defaultdict(int),
    })

    for r in records:
        p = _norm(r.get("PrimaryRoad"))
        s = _norm(r.get("SecondaryRoad"))
        if not p or not s:
            continue
        if _is_freeway(p) or _is_freeway(s):
            continue

        # Canonical key: alphabetically sorted so A/B == B/A
        key = tuple(sorted([p, s]))
        g = groups[key]

        g["crash_count"] += 1
        g["total_killed"] += _to_int(r.get("NumberKilled"))
        g["total_injured"] += _to_int(r.get("NumberInjured"))
        if r.get("HitRun") in ("Y", "1", 1, True):
            g["hit_run_count"] += 1

        lat = _to_float(r.get("Latitude"))
        lng = _to_float(r.get("Longitude"))
        if lat and lng:
            g["lats"].append(lat)
            g["lngs"].append(lng)

        city = _norm(r.get("City Name"))
        if city:
            g["cities"].add(city)

        date = (r.get("Crash Date Time") or "")[:4]
        if date.isdigit():
            g["years"].add(int(date))

        ctype = _norm(r.get("Collision Type Description") or "UNKNOWN")
        g["crash_types"][ctype] += 1

    results = []
    for (road_a, road_b), g in groups.items():
        if not g["lats"]:
            continue

        lat = sum(g["lats"]) / len(g["lats"])
        lng = sum(g["lngs"]) / len(g["lngs"])
        danger_score = g["total_killed"] * 5 + g["total_injured"] + g["crash_count"] * 0.5
        years = sorted(g["years"])
        top_types = sorted(g["crash_types"].items(), key=lambda x: -x[1])[:3]

        results.append({
            "address": f"{road_a.title()} & {road_b.title()}, Alameda County, CA",
            "primary_road": road_a.title(),
            "secondary_road": road_b.title(),
            "lat": round(lat, 6),
            "lng": round(lng, 6),
            "danger_score": round(danger_score, 1),
            "crash_count": g["crash_count"],
            "total_killed": g["total_killed"],
            "total_injured": g["total_injured"],
            "hit_run_count": g["hit_run_count"],
            "cities": sorted(g["cities"]),
            "year_range": f"{years[0]}–{years[-1]}" if len(years) > 1 else str(years[0]) if years else "unknown",
            "top_crash_types": [{"type": t, "count": c} for t, c in top_types],
        })

    results.sort(key=lambda x: -x["danger_score"])
    return results


async def main():
    records = await fetch_ccrs_alameda()
    intersections = aggregate_intersections(records)

    print(f"\nTop 20 dangerous intersections in Alameda County:")
    for i, x in enumerate(intersections[:20], 1):
        print(f"  {i:2}. {x['address']} — score={x['danger_score']} "
              f"({x['crash_count']} crashes, {x['total_killed']} killed, {x['total_injured']} injured)")

    output = {
        "source": "California Crash Reporting System (CCRS) via data.ca.gov",
        "county": "Alameda County, CA",
        "total_intersections_found": len(intersections),
        "intersections": intersections,
    }

    OUTPUT.write_text(json.dumps(output, indent=2))
    print(f"\nSaved {len(intersections)} intersections to {OUTPUT}")


if __name__ == "__main__":
    asyncio.run(main())
