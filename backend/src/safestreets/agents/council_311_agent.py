"""Council/311 agent.

Two independent civic signals for an intersection:

- **311 complaints** — Berkeley publishes these as open data (Socrata, with lat/lng), so
  this side is a plain API query filtered by proximity. No scraping.
- **Council agenda items** — published as PDFs linked from Granicus. Discovery is static
  HTML (meeting list + agenda PDF links whose *filenames* carry the date + item title),
  so we search filenames for the cross streets cheaply, then pull only the matched PDFs
  through a Browserbase session and extract their text. Council items carry dates so the
  accountability log can compute 'raised in 2022, still no action'.
"""
from __future__ import annotations

import io
import re
from typing import Any
from urllib.parse import unquote

import httpx

from safestreets.clients import socrata

_GRANICUS = "https://berkeley.granicus.com"
_VIEW_PUBLISHER = f"{_GRANICUS}/ViewPublisher.php?view_id=5"
_PDF_HOST = "https://berkeleyca.gov"  # /sites/default/files/... lives on the Drupal site
_UA = {"User-Agent": "Mozilla/5.0 (SafeStreets council agent)"}

# Berkeley 311 Cases (Socrata). bscu-qpbu is private (403); p88g-6gs2 is the public set.
_SOCRATA_DOMAIN = "data.cityofberkeley.info"
_BERKELEY_311_DATASET = "p88g-6gs2"

_AGENDAVIEWER_RE = re.compile(r"AgendaViewer\.php\?view_id=5&(?:amp;)?clip_id=(\d+)")
_PDF_HREF_RE = re.compile(r"""href=["']([^"']*?\.pdf[^"']*)["']""", re.I)

# Berkeley agenda filenames stamp the date in several formats; try them in order.
_DATE_PATTERNS = (
    re.compile(r"(20\d{2})-(\d{2})-(\d{2})"),         # 2026-06-16
    re.compile(r"(20\d{2})-(\d{2})(\d{2})"),          # 2026-0519
    re.compile(r"\b(\d{1,2})[_/](\d{1,2})[_/](20\d{2})"),  # 6_9_2026 or 6/9/2026
)


def _parse_date(name: str) -> str | None:
    """Normalize whatever date the filename carries to ISO YYYY-MM-DD."""
    for i, pat in enumerate(_DATE_PATTERNS):
        m = pat.search(name)
        if not m:
            continue
        if i < 2:  # year first
            y, mo, da = m.group(1), m.group(2), m.group(3)
        else:      # month/day first
            mo, da, y = m.group(1), m.group(2), m.group(3)
        return f"{y}-{int(mo):02d}-{int(da):02d}"
    return None


def _abs_pdf(path: str) -> str:
    if path.startswith("http"):
        return path
    if path.startswith("//"):
        return "https:" + path
    return _PDF_HOST + path


def _pdf_meta(pdf_url: str) -> tuple[str | None, str]:
    """Derive (date, title) from a Berkeley agenda PDF filename.

    e.g. '2026-06-16 Item 02 Temporary Appropriations FY 2027.pdf'
         -> ('2026-06-16', 'Item 02 Temporary Appropriations FY 2027')
    """
    name = unquote(pdf_url.rsplit("/", 1)[-1]).removesuffix(".pdf").strip()
    date = _parse_date(name)
    # strip a leading ISO date prefix for a cleaner title; leave embedded dates alone
    title = re.sub(r"^20\d{2}-\d{2}-\d{2}\s*", "", name).strip(" -")
    return date, title


async def _recent_meeting_clip_ids(client: httpx.AsyncClient, max_meetings: int) -> list[str]:
    resp = await client.get(_VIEW_PUBLISHER, headers=_UA, timeout=30, follow_redirects=True)
    resp.raise_for_status()
    seen: list[str] = []
    for cid in _AGENDAVIEWER_RE.findall(resp.text):  # listing is newest-first
        if cid not in seen:
            seen.append(cid)
        if len(seen) >= max_meetings:
            break
    return seen


async def _agenda_pdfs(client: httpx.AsyncClient, clip_id: str) -> list[str]:
    url = f"{_GRANICUS}/AgendaViewer.php?view_id=5&clip_id={clip_id}"
    try:
        resp = await client.get(url, headers=_UA, timeout=30, follow_redirects=True)
        resp.raise_for_status()
    except httpx.HTTPError:
        return []
    return [_abs_pdf(p) for p in _PDF_HREF_RE.findall(resp.text)]


def _title_has_street(title: str, street_terms: list[str]) -> bool:
    """True only if a street term appears as a WHOLE WORD in the title.

    Substring matching falsely flags 'parking'/'talking' for the 'king' in MLK Way, so
    we tokenize the title on non-alphanumerics and match whole tokens.
    """
    tokens = set(re.split(r"[^a-z0-9]+", title.lower()))
    return any(t in tokens for t in street_terms)


def _pdf_text_snippet(data: bytes, terms: list[str], width: int = 240) -> str | None:
    """Return a text snippet around the first street-term hit, or None if absent."""
    try:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        text = " ".join((page.extract_text() or "") for page in reader.pages)
    except Exception:  # noqa: BLE001
        return None
    for t in terms:
        m = re.search(rf"\b{re.escape(t)}\b", text, re.IGNORECASE)
        if m:
            start = max(0, m.start() - width // 2)
            return re.sub(r"\s+", " ", text[start : start + width]).strip()
    return None


async def _scrape_council(
    street_terms: list[str], max_meetings: int, max_pdfs: int
) -> list[dict[str, Any]]:
    if not street_terms:
        return []
    async with httpx.AsyncClient() as client:
        clip_ids = await _recent_meeting_clip_ids(client, max_meetings)
        candidates: list[tuple[str, str | None, str]] = []  # (pdf_url, date, title)
        for cid in clip_ids:
            for pdf in await _agenda_pdfs(client, cid):
                date, title = _pdf_meta(pdf)
                if _title_has_street(title, street_terms):
                    candidates.append((pdf, date, title))

    candidates = candidates[:max_pdfs]
    if not candidates:
        return []

    # Pull the matched PDFs through a Browserbase session and confirm via body text.
    from safestreets.clients.browserbase_client import fetch_via_browser

    blobs = await fetch_via_browser([c[0] for c in candidates])
    out: list[dict[str, Any]] = []
    for pdf_url, date, title in candidates:
        data = blobs.get(pdf_url)
        snippet = _pdf_text_snippet(data, street_terms) if data else None
        out.append(
            {
                "title": title,
                "date": date,
                "url": pdf_url,
                "snippet": snippet,
                "source": "berkeley.granicus.com",
            }
        )
    return out


async def _fetch_311(lat: float, lng: float, radius_deg: float = 0.0015) -> list[dict[str, Any]]:
    """Every Berkeley 311 case within the intersection bounding box (no cap)."""
    where = (
        f"latitude between {lat - radius_deg} and {lat + radius_deg} "
        f"and longitude between {lng - radius_deg} and {lng + radius_deg}"
    )
    try:
        rows = await socrata.query_all(_SOCRATA_DOMAIN, _BERKELEY_311_DATASET, where)
    except httpx.HTTPError:
        return []
    return [
        {
            "case_id": r.get("case_id"),
            "request": r.get("case_request") or r.get("case_summary"),
            "date_opened": (r.get("date_opened") or "")[:10],
            "status": r.get("case_status"),
            "address": r.get("street_address"),
            "lat": r.get("latitude"),
            "lng": r.get("longitude"),
        }
        for r in rows
    ]


async def fetch_council_and_311(
    lat: float,
    lng: float,
    city: str | None,
    street_terms: list[str] | None = None,
    max_meetings: int = 12,
    max_pdfs: int = 6,
) -> dict[str, Any]:
    """Returns {"complaints_311": [...], "council": [...]}.

    `street_terms` (e.g. ['bancroft', 'fulton']) drives council-agenda matching; 311 is
    geofiltered by lat/lng. Council items carry dates for the accountability log.
    """
    street_terms = [t.lower() for t in (street_terms or [])]
    complaints = await _fetch_311(lat, lng)
    council = await _scrape_council(street_terms, max_meetings, max_pdfs)
    return {"complaints_311": complaints, "council": council}
