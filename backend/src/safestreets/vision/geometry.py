"""Named-zone -> pixel placement.

This is the fix for the single most likely demo failure: vision-language models are
unreliable at returning raw pixel coordinates, so a marker can land on the wrong
corner. Instead, Stage 1 assigns each condition to a NAMED ZONE, and this module maps
that zone to a deterministic position on the satellite image from known geometry.

Coordinates are fractions of width/height with (0,0) at the top-left, assuming the
satellite image is north-up (Google Static Maps default).
"""
from __future__ import annotations

from safestreets.models.condition import NamedZone

# fractional (x, y) anchor for each zone on a north-up top-down image
_ZONE_FRACTIONS: dict[NamedZone, tuple[float, float]] = {
    NamedZone.NW: (0.30, 0.30),
    NamedZone.NE: (0.70, 0.30),
    NamedZone.SW: (0.30, 0.70),
    NamedZone.SE: (0.70, 0.70),
    NamedZone.N_LEG: (0.50, 0.15),
    NamedZone.S_LEG: (0.50, 0.85),
    NamedZone.E_LEG: (0.85, 0.50),
    NamedZone.W_LEG: (0.15, 0.50),
    NamedZone.CENTER: (0.50, 0.50),
}


def zone_to_fraction(zone: NamedZone) -> tuple[float, float]:
    return _ZONE_FRACTIONS[zone]


def zone_to_pixel(zone: NamedZone, width: int, height: int) -> tuple[int, int]:
    fx, fy = _ZONE_FRACTIONS[zone]
    return round(fx * width), round(fy * height)


def spread_overlapping(zones: list[NamedZone], width: int, height: int) -> list[tuple[int, int]]:
    """If two markers share a zone, nudge them apart so labels don't stack."""
    seen: dict[NamedZone, int] = {}
    out: list[tuple[int, int]] = []
    for z in zones:
        n = seen.get(z, 0)
        x, y = zone_to_pixel(z, width, height)
        x += n * 18  # small horizontal offset per repeat
        out.append((x, y))
        seen[z] = n + 1
    return out
