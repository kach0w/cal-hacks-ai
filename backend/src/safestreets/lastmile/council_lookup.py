"""Resolve the city council member(s) for an intersection — by jurisdiction, via Socrata.

The "which member" question is really "which district does this corner fall in". That is
a point-in-polygon query against the city's published council-districts boundary dataset
(Socrata/SODA `intersects(<geom>, 'POINT(lng lat)')`). When that dataset also carries
contact columns (member name + email) we use them directly; otherwise we resolve the
district number against the configured district->email map, and as a last resort address
the city's general council inbox so the draft always has a valid recipient.

Everything here is best-effort and non-fatal: a portal hiccup degrades to the general
inbox rather than breaking the email flow.
"""
from __future__ import annotations

import json
from typing import Any

import httpx

from safestreets.clients import socrata
from safestreets.config import get_settings
from safestreets.models.council import CouncilContact

# Column-name candidates vary by portal; match case-insensitively against these.
_DISTRICT_FIELDS = ("district", "coun_dist", "council_district", "councildistrict", "dist", "name")
_NAME_FIELDS = ("councilmember", "member", "representative", "official", "full_name", "name")
_EMAIL_FIELDS = ("email", "contact_email", "member_email", "e_mail")


def _first_field(row: dict[str, Any], candidates: tuple[str, ...]) -> str | None:
    lower = {k.lower(): v for k, v in row.items() if not isinstance(v, (dict, list))}
    for c in candidates:
        v = lower.get(c)
        if v not in (None, ""):
            return str(v)
    return None


def _district_map() -> dict[str, dict[str, str]]:
    raw = get_settings().council_district_emails.strip()
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
        return {str(k): v for k, v in parsed.items()} if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


async def _district_row(lat: float, lng: float) -> dict[str, Any] | None:
    """The boundary-dataset row whose polygon contains the point, or None."""
    s = get_settings()
    if not s.council_districts_dataset:
        return None
    point = f"POINT({lng} {lat})"  # SODA WKT is lng-first
    where = f"intersects({s.council_geom_column}, '{point}')"
    try:
        rows = await socrata.query(s.council_districts_domain, s.council_districts_dataset, where, limit=1)
    except httpx.HTTPError:
        return None
    return rows[0] if rows else None


async def find_council_contacts(lat: float, lng: float, city: str | None = None) -> list[CouncilContact]:
    """Council member(s) whose district contains (lat, lng). Always returns >= 1 contact.

    Priority for the email address: contact columns on the matched Socrata row ->
    configured district map -> the city's general council inbox.
    """
    s = get_settings()
    general = CouncilContact(
        name="City Council",
        email=s.council_general_email,
        role="City Council",
        source="general_inbox",
    )

    row = await _district_row(lat, lng)
    if row is None:
        return [general]

    district = _first_field(row, _DISTRICT_FIELDS)
    name = _first_field(row, _NAME_FIELDS)
    email = _first_field(row, _EMAIL_FIELDS)

    # Configured map can supply / override the email (and name) for a district.
    mapped = _district_map().get(district or "", {})
    email = mapped.get("email") or email
    name = mapped.get("name") or name

    if not email:
        # Knew the district but not the address — keep the jurisdiction context, send to
        # the general inbox so it still reaches the council.
        return [
            CouncilContact(
                name=name or (f"Councilmember, District {district}" if district else "City Council"),
                email=s.council_general_email,
                district=district,
                source="general_inbox",
            )
        ]

    return [
        CouncilContact(
            name=name or (f"Councilmember, District {district}" if district else "Councilmember"),
            email=email,
            district=district,
            source="config" if mapped.get("email") else "socrata",
        )
    ]
