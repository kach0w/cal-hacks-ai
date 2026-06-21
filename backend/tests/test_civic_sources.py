"""Offline tests for the city-wide civic street-safety scraper.

This is the most orchestration-heavy agent: it discovers safety URLs from three
sitemaps, fetches the matched pages + council PDFs through Browserbase, parses
them, and geocodes the news items. We fake HTTP (``http_router``), the cloud
browser (``fake_browser``), and geocoding, then assert the pipeline routes
content into the right per-site buckets with correct counts.
"""
from __future__ import annotations

import httpx
import pytest

from safestreets.agents import civic_sources as civic


def _article(title: str, description: str = "") -> bytes:
    html = (
        "<!doctype html><html><head>"
        f'<meta property="og:title" content="{title}" />'
        f'<meta name="description" content="{description}" />'
        "</head><body></body></html>"
    )
    return html.encode("utf-8")


# --------------------------------------------------------------------------- #
# _path / _is_safety
# --------------------------------------------------------------------------- #
def test_path_strips_domain_so_domain_keywords_dont_match():
    # 'bike' is in the *domain* walkBIKEberkeley.org but the path has no keyword
    assert civic._path("https://walkBIKEberkeley.org/2025/01/01/board-minutes") == (
        "/2025/01/01/board-minutes"
    )


def test_is_safety_requires_a_safety_keyword_in_the_path():
    assert civic._is_safety("https://x.org/2025/01/01/pedestrian-crash-shattuck") is True
    assert civic._is_safety("https://x.org/2025/01/01/city-budget-hearing") is False


def test_is_safety_drops_excluded_crime_topics():
    # has a keyword ('pedestrian') but also an excluded one ('shooting')
    assert civic._is_safety("https://x.org/2025/01/01/pedestrian-shooting-downtown") is False


def test_is_safety_require_berkeley_filters_other_cities():
    url = "https://www.berkeleyside.org/2025/01/01/oakland-traffic-crash"
    assert civic._is_safety(url, require_berkeley=True) is False
    berkeley = "https://www.berkeleyside.org/2025/01/01/berkeley-traffic-crash"
    assert civic._is_safety(berkeley, require_berkeley=True) is True


# --------------------------------------------------------------------------- #
# _parse_article / _extract_streets
# --------------------------------------------------------------------------- #
def test_parse_article_reads_meta_and_falls_back_to_url_date():
    html = _article("Crash at Shattuck and University", "A pedestrian was injured.").decode()
    out = civic._parse_article(
        "https://www.berkeleyscanner.com/2025/03/01/traffic-safety/x", html, "berkeleyscanner.com"
    )
    assert out["title"] == "Crash at Shattuck and University"
    assert out["date"] == "2025-03-01"        # from the /YYYY/MM/DD/ path
    assert out["excerpt"] == "A pedestrian was injured."
    assert out["source"] == "berkeleyscanner.com"


def test_extract_streets_is_whole_word_and_longest_first():
    found = civic._extract_streets("Crash at Martin Luther King Jr Way and Shattuck Ave")
    assert "martin luther king" in found   # multi-word name wins over a bare 'king'
    assert "shattuck" in found


def test_extract_streets_returns_empty_when_no_known_street():
    assert civic._extract_streets("A generic article about nothing in particular") == []


# --------------------------------------------------------------------------- #
# _scrape_sitemap_site — discovery -> filter -> fetch -> parse
# --------------------------------------------------------------------------- #
async def test_scrape_sitemap_site_keeps_only_safety_pages(http_router, fake_browser):
    sitemap = (
        "<urlset>"
        "<url><loc>https://www.berkeleyscanner.com/2025/03/01/traffic-safety/pedestrian-crash-shattuck</loc></url>"
        "<url><loc>https://www.berkeleyscanner.com/2025/02/01/crime/downtown-robbery</loc></url>"
        "</urlset>"
    )
    http_router.text("sitemap-posts.xml", sitemap)
    safety_url = "https://www.berkeleyscanner.com/2025/03/01/traffic-safety/pedestrian-crash-shattuck"
    fake_browser.pages[safety_url] = _article("Pedestrian crash on Shattuck")

    async with httpx.AsyncClient() as client:
        items = await civic._scrape_sitemap_site(
            client, "berkeleyscanner.com", "https://www.berkeleyscanner.com/sitemap-posts.xml"
        )

    assert len(items) == 1                       # the crime/robbery URL was filtered out
    assert items[0]["title"] == "Pedestrian crash on Shattuck"
    assert items[0]["source"] == "berkeleyscanner.com"
    # exactly one Browserbase fetch, carrying only the safety URL
    assert fake_browser.calls == [[safety_url]]


# --------------------------------------------------------------------------- #
# enrich_locations — drops un-locatable items, geocodes intersections
# --------------------------------------------------------------------------- #
async def test_enrich_locations_drops_no_street_and_geocodes_intersections(monkeypatch):
    async def fake_geocode(address):
        return {"lat": 37.87, "lng": -122.27, "formatted": "Shattuck Ave & University Ave"}

    monkeypatch.setattr("safestreets.clients.google_maps.geocode_address", fake_geocode)

    items = [
        {"title": "Crash at Shattuck and University", "excerpt": ""},  # 2 streets -> intersection
        {"title": "Telegraph Avenue repaving", "excerpt": ""},        # 1 street -> street
        {"title": "Generic council news", "excerpt": ""},             # 0 streets -> dropped
    ]

    located = await civic.enrich_locations(items)

    assert len(located) == 2
    intersection = next(i for i in located if i["title"].startswith("Crash"))
    assert intersection["location_type"] == "intersection"
    assert intersection["lat"] == 37.87 and intersection["lng"] == -122.27
    street = next(i for i in located if i["title"].startswith("Telegraph"))
    assert street["location_type"] == "street"


# --------------------------------------------------------------------------- #
# fetch_street_safety — full faked pipeline across all four sources
# --------------------------------------------------------------------------- #
async def test_fetch_street_safety_buckets_all_sources_with_counts(
    monkeypatch, http_router, fake_browser, fixture, pdf_bytes
):
    async def fake_geocode(address):
        return {"lat": 37.87, "lng": -122.27, "formatted": "Shattuck Ave & University Ave"}

    monkeypatch.setattr("safestreets.clients.google_maps.geocode_address", fake_geocode)

    # --- sitemaps (one safety URL each) ---
    scanner_url = "https://www.berkeleyscanner.com/2025/03/01/traffic-safety/pedestrian-crash-shattuck-university"
    bside_url = "https://www.berkeleyside.org/2025/04/05/berkeley-cyclist-injured-telegraph"
    walkbike_url = "https://walkbikeberkeley.org/2025/01/01/vision-zero-plan-update"

    http_router.text("berkeleyscanner.com/sitemap-posts.xml",
                     f"<urlset><url><loc>{scanner_url}</loc></url></urlset>")
    http_router.text("berkeleyside.org/post-sitemap.xml",
                     f"<urlset><url><loc>{bside_url}</loc></url></urlset>")
    http_router.text("walkbikeberkeley.org/sitemap.xml",
                     f"<urlset><url><loc>{walkbike_url}</loc></url></urlset>")

    fake_browser.pages[scanner_url] = _article("Pedestrian crash at Shattuck and University")
    fake_browser.pages[bside_url] = _article("Cyclist injured on Telegraph Avenue")
    fake_browser.pages[walkbike_url] = _article("Vision Zero plan update")

    # --- council (Granicus discovery -> matched PDFs) ---
    http_router.text("ViewPublisher", fixture("granicus_viewpublisher.html"))
    http_router.text("clip_id=124", fixture("granicus_agenda_124.html"))
    http_router.text("clip_id=123", fixture("granicus_agenda_123.html"))
    from safestreets.agents import council_311_agent as council

    bike_pdf = council._abs_pdf("/sites/default/files/2026-06-16 Item 02 Bancroft Avenue Bike Lane.pdf")
    ped_pdf = council._abs_pdf("/sites/default/files/2026-06-09 Item 14 Pedestrian Crossing Improvements.pdf")
    fake_browser.pages[bike_pdf] = pdf_bytes("Bancroft Avenue bike lane")
    fake_browser.pages[ped_pdf] = pdf_bytes("Pedestrian crossing improvements")

    result = await civic.fetch_street_safety()

    # scanner item names two streets -> located as an intersection
    assert result["counts"]["berkeleyscanner"] == 1
    assert result["berkeleyscanner"][0]["location_type"] == "intersection"
    # berkeleyside item names one street -> located as a street
    assert result["counts"]["berkeleyside"] == 1
    assert result["berkeleyside"][0]["location_type"] == "street"
    # walkbike is not geocoded, just parsed
    assert result["counts"]["walkbikeberkeley"] == 1
    # both safety-topic agenda items came through council
    assert result["counts"]["council"] == 2
    assert {i["source"] for i in result["council"]} == {"berkeleyca.gov"}
