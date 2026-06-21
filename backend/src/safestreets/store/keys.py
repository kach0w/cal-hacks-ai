"""Redis key schema. Intersections are keyed by rounded lat/lng so repeat queries
hit the cache; corridors and accountability persist beyond the TTL."""
from __future__ import annotations

# rounding ~5 decimals ≈ 1m; good enough to collapse the same intersection
_PRECISION = 5

VISION_TTL = 60 * 60 * 24       # 24h — imagery analysis can go stale
SCRAPE_TTL = 60 * 60 * 24       # 24h — news/311/council
INTERVENTION_TTL = 60 * 60 * 24


def _ll(lat: float, lng: float) -> str:
    return f"{round(lat, _PRECISION)}:{round(lng, _PRECISION)}"


def intersection_key(lat: float, lng: float) -> str:
    return f"ss:intersection:{_ll(lat, lng)}"


def scrape_key(lat: float, lng: float) -> str:
    return f"ss:scrape:{_ll(lat, lng)}"


def vision_key(lat: float, lng: float) -> str:
    return f"ss:vision:{_ll(lat, lng)}"


def council_email_key(lat: float, lng: float) -> str:
    return f"ss:council-email:{_ll(lat, lng)}"


def intervention_key(lat: float, lng: float) -> str:
    return f"ss:intervention:{_ll(lat, lng)}"


def civic_key(city: str) -> str:
    # city-wide street-safety scrape of the four civic sites (not per-intersection)
    return f"ss:civic:{city.lower()}:street-safety"


def coalition_key(corridor_id: str) -> str:
    # persistent (no TTL): the count of residents flagging a corridor
    return f"ss:coalition:{corridor_id}"


def accountability_key(intersection_id: str) -> str:
    # persistent (no TTL): the durable record
    return f"ss:accountability:{intersection_id}"
