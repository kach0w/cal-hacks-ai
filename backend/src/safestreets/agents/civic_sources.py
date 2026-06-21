"""Civic street-safety scraper — the four Berkeley community sites, via Browserbase.

Collects Berkeley street-safety coverage/discussion from:
  - berkeleyscanner.com   (local crime/safety news)
  - berkeleyside.org      (local news)
  - walkbikeberkeley.org  (walk/bike advocacy org; Squarespace, bot-walled)
  - berkeleyca.gov        (city council agendas, via Granicus)

Discovery is cheap (each site's sitemap / Granicus list over plain HTTP); the matched
PAGES are then fetched through a Browserbase session — robust to bot-walls and the
single explicit ask here ("use Browserbase for these sites"). News/advocacy items are
parsed from OpenGraph/meta tags; council items reuse the agenda pipeline.

Results are returned per-site and persisted to Redis under `ss:civic:<city>:street-safety`.
"""
from __future__ import annotations

import asyncio
import re
from typing import Any

import httpx

_UA = {"User-Agent": "Mozilla/5.0 (SafeStreets civic agent)"}

# road/street-safety terms — deliberately excludes generic crime words (shooting, fire)
# so we don't pull in non-traffic articles that merely contain 'safety'.
_SAFETY_KEYWORDS = (
    "crash", "collision", "pedestrian", "cyclist", "bicycle", "bike", "traffic",
    "vision-zero", "vision_zero", "crosswalk", "hit-run", "hit-and-run", "scooter",
    "sidewalk", "road-diet", "bike-lane", "e-bike", "daylighting", "speed", "struck",
)

# road-safety keyword present but the story isn't a street-safety one — drop these.
_EXCLUDE = ("gunfire", "shooting", "shot", "robbery", "burglary", "arson", "fire-",
            "-fire", "homicide", "stabbing", "baker", "tax", "budget", "election")

_PER_SITE_CAP = None  # None = no cap (fetch every match); set an int to bound Browserbase cost


def _path(url: str) -> str:
    """Lowercased URL path only — so the *domain* (e.g. walkBIKEberkeley.org) never
    triggers a keyword match; only the article slug counts."""
    return re.sub(r"^https?://[^/]+", "", url).lower()


def _is_safety(url: str, require_berkeley: bool = False) -> bool:
    p = _path(url)
    if not any(k in p for k in _SAFETY_KEYWORDS):
        return False
    if any(x in p for x in _EXCLUDE):
        return False
    if require_berkeley and "berkeley" not in p:
        return False
    return True


async def _sitemap_urls(client: httpx.AsyncClient, sitemap: str) -> list[str]:
    try:
        resp = await client.get(sitemap, headers=_UA, timeout=25, follow_redirects=True)
        resp.raise_for_status()
    except httpx.HTTPError:
        return []
    return re.findall(r"<loc>([^<]+)</loc>", resp.text)


def _meta(html: str, pattern: str) -> str | None:
    m = re.search(pattern, html)
    return m.group(1).strip() if m else None


def _parse_article(url: str, html: str, source: str) -> dict[str, Any]:
    title = _meta(html, r'<meta property="og:title" content="([^"]+)"') or url.rsplit("/", 2)[-2]
    published = _meta(html, r'<meta property="article:published_time" content="([^"]+)"')
    excerpt = (
        _meta(html, r'<meta name="description" content="([^"]+)"')
        or _meta(html, r'<meta property="og:description" content="([^"]+)"')
        or ""
    )
    # most of these URLs embed the date as /YYYY/MM/DD/ — fall back to that
    m = re.search(r"/(\d{4})/(\d{1,2})/(\d{1,2})/", url)
    url_date = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}" if m else None
    return {
        "title": title,
        "date": (published[:10] if published else url_date),
        "url": url,
        "excerpt": excerpt,
        "source": source,
    }


async def _scrape_sitemap_site(
    client: httpx.AsyncClient, source: str, sitemap: str, require_berkeley: bool = False
) -> list[dict[str, Any]]:
    """Discover safety URLs from a sitemap, fetch the pages via Browserbase, parse them.

    `require_berkeley` is set for multi-city outlets (berkeleyside covers the whole East
    Bay) so we keep only Berkeley stories; the other three are Berkeley-only by nature.
    """
    from safestreets.clients.browserbase_client import browser_page, fetch_via_browser

    urls = [u for u in await _sitemap_urls(client, sitemap) if _is_safety(u, require_berkeley)]
    urls.sort(reverse=True)  # most-recent-ish (dates lead the path)
    urls = urls[:_PER_SITE_CAP]
    if not urls:
        return []

    # Primary path: one Browserbase session fetches every matched page's bytes.
    blobs = await fetch_via_browser(urls)
    items: list[dict[str, Any]] = []
    missing: list[str] = []
    for u in urls:
        data = blobs.get(u)
        if data:
            items.append(_parse_article(u, data.decode("utf-8", "ignore"), source))
        else:
            missing.append(u)

    # Fallback for sites that block the request context (e.g. Squarespace): full nav.
    for u in missing:
        try:
            async with browser_page() as page:
                await page.goto(u, wait_until="domcontentloaded", timeout=40000)
                html = await page.content()
            items.append(_parse_article(u, html, source))
        except Exception:  # noqa: BLE001
            continue
    return items


async def _scrape_council_safety() -> list[dict[str, Any]]:
    """Berkeley council agenda items about street safety (bike/ped/traffic/vision zero).

    Reuses the council agent's Granicus discovery + Browserbase PDF fetch, but matches on
    safety topics in the agenda filename instead of a specific intersection's streets.
    """
    from safestreets.agents import council_311_agent as ca

    topics = ["bicycle", "bike", "pedestrian", "traffic", "vision", "crosswalk", "safe", "speed"]
    async with httpx.AsyncClient() as client:
        clip_ids = await ca._recent_meeting_clip_ids(client, 12)
        candidates: list[tuple[str, str | None, str]] = []
        for cid in clip_ids:
            for pdf in await ca._agenda_pdfs(client, cid):
                date, title = ca._pdf_meta(pdf)
                if any(t in title.lower() for t in topics):
                    candidates.append((pdf, date, title))
    candidates = candidates[:_PER_SITE_CAP]
    if not candidates:
        return []
    from safestreets.clients.browserbase_client import fetch_via_browser

    blobs = await fetch_via_browser([c[0] for c in candidates])
    out: list[dict[str, Any]] = []
    for pdf_url, date, title in candidates:
        data = blobs.get(pdf_url)
        out.append(
            {
                "title": title,
                "date": date,
                "url": pdf_url,
                "excerpt": ca._pdf_text_snippet(data, topics) if data else None,
                "source": "berkeleyca.gov",
            }
        )
    return out


async def fetch_street_safety() -> dict[str, Any]:
    """Scrape all four Berkeley civic sites for street-safety content via Browserbase.

    Returns {"berkeleyscanner": [...], "berkeleyside": [...], "walkbikeberkeley": [...],
             "council": [...], "counts": {...}}.
    """
    async with httpx.AsyncClient() as client:
        scanner, bside, walkbike = await asyncio.gather(
            _scrape_sitemap_site(client, "berkeleyscanner.com", "https://www.berkeleyscanner.com/sitemap-posts.xml"),
            _scrape_sitemap_site(client, "berkeleyside.org", "https://www.berkeleyside.org/post-sitemap.xml", require_berkeley=True),
            _scrape_sitemap_site(client, "walkbikeberkeley.org", "https://walkbikeberkeley.org/sitemap.xml"),
        )
    council = await _scrape_council_safety()
    result = {
        "berkeleyscanner": scanner,
        "berkeleyside": bside,
        "walkbikeberkeley": walkbike,
        "council": council,
    }
    result["counts"] = {k: len(v) for k, v in result.items()}
    return result
