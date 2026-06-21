"""Offline tests for the council-agenda / 311 agent.

311 comes from a Socrata API (mocked at the client); council agendas come from
Granicus HTML discovery (``http_router``) plus PDFs fetched through Browserbase
(``fake_browser``) and parsed with pypdf. The date/title parsing is regex-heavy
and the place small format changes silently break, so it gets direct unit tests.
"""
from __future__ import annotations

import httpx
import pytest

from safestreets.agents import council_311_agent as council


# --------------------------------------------------------------------------- #
# _parse_date — three filename formats + the no-date case
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "name, expected",
    [
        ("2026-06-16 Item 02 Budget", "2026-06-16"),   # ISO with dashes
        ("agenda-2026-0519-packet", "2026-05-19"),     # year-MMDD
        ("minutes 6_9_2026 draft", "2026-06-09"),      # M_D_YYYY
        ("6/9/2026 council", "2026-06-09"),            # M/D/YYYY
        ("no date in this name", None),
    ],
)
def test_parse_date_normalizes_each_supported_format(name, expected):
    assert council._parse_date(name) == expected


# --------------------------------------------------------------------------- #
# _abs_pdf / _pdf_meta / _title_has_street
# --------------------------------------------------------------------------- #
def test_abs_pdf_resolves_relative_protocol_and_absolute():
    assert council._abs_pdf("/sites/x.pdf") == "https://berkeleyca.gov/sites/x.pdf"
    assert council._abs_pdf("//cdn.example/x.pdf") == "https://cdn.example/x.pdf"
    assert council._abs_pdf("http://host/x.pdf") == "http://host/x.pdf"


def test_pdf_meta_splits_date_and_title():
    url = "https://berkeleyca.gov/sites/default/files/2026-06-16 Item 02 Bancroft Avenue Bike Lane.pdf"
    date, title = council._pdf_meta(url)
    assert date == "2026-06-16"
    assert title == "Item 02 Bancroft Avenue Bike Lane"  # leading ISO date stripped


def test_title_has_street_is_whole_word():
    assert council._title_has_street("Item 02 Bancroft Avenue Bike Lane", ["bancroft"]) is True
    assert council._title_has_street("Item 02 Bancroft Avenue", ["shattuck"]) is False
    # 'king' must not match inside 'Parking'
    assert council._title_has_street("Parking Structure Study", ["king"]) is False


# --------------------------------------------------------------------------- #
# _pdf_text_snippet — valid + corrupt bytes
# --------------------------------------------------------------------------- #
def test_pdf_text_snippet_extracts_around_a_street_hit(pdf_bytes):
    data = pdf_bytes("Council item: Bancroft Avenue protected bike lane installation")
    snippet = council._pdf_text_snippet(data, ["bancroft"])
    assert snippet is not None
    assert "Bancroft" in snippet


def test_pdf_text_snippet_returns_none_for_absent_term(pdf_bytes):
    data = pdf_bytes("Temporary Appropriations FY 2027")
    assert council._pdf_text_snippet(data, ["bancroft"]) is None


def test_pdf_text_snippet_handles_corrupt_pdf_without_raising():
    assert council._pdf_text_snippet(b"%PDF-1.4 not really a pdf", ["bancroft"]) is None


# --------------------------------------------------------------------------- #
# fetch_311 — Socrata mapping + graceful HTTP failure
# --------------------------------------------------------------------------- #
async def test_fetch_311_maps_socrata_rows_to_contract(monkeypatch):
    rows = [
        {
            "case_id": "C1",
            "case_request": "Pothole on Bancroft",
            "date_opened": "2024-01-02T00:00:00",
            "case_status": "Open",
            "street_address": "123 Bancroft Ave",
            "latitude": "37.87",
            "longitude": "-122.27",
        },
        {
            "case_id": "C2",
            "case_summary": "Broken streetlight",  # request falls back to summary
            "date_opened": "2023-11-15",
            "case_status": "Closed",
        },
    ]

    async def fake_query_all(domain, dataset, where, **kw):
        return rows

    monkeypatch.setattr(council.socrata, "query_all", fake_query_all)

    out = await council.fetch_311(37.87, -122.27)

    assert [r["case_id"] for r in out] == ["C1", "C2"]
    assert out[0]["request"] == "Pothole on Bancroft"
    assert out[0]["date_opened"] == "2024-01-02"      # truncated to the date
    assert out[1]["request"] == "Broken streetlight"  # summary fallback


async def test_fetch_311_returns_empty_on_http_error(monkeypatch):
    async def boom(*a, **k):
        raise httpx.HTTPError("socrata down")

    monkeypatch.setattr(council.socrata, "query_all", boom)

    assert await council.fetch_311(37.87, -122.27) == []


# --------------------------------------------------------------------------- #
# fetch_council_and_311 — full council discovery -> match -> PDF snippet
# --------------------------------------------------------------------------- #
async def _no_311(monkeypatch):
    async def empty(*a, **k):
        return []

    monkeypatch.setattr(council.socrata, "query_all", empty)


async def test_fetch_council_matches_street_and_confirms_in_pdf(
    monkeypatch, http_router, fake_browser, fixture, pdf_bytes
):
    await _no_311(monkeypatch)
    http_router.text("ViewPublisher", fixture("granicus_viewpublisher.html"))
    http_router.text("clip_id=124", fixture("granicus_agenda_124.html"))
    http_router.text("clip_id=123", fixture("granicus_agenda_123.html"))

    bancroft_pdf = council._abs_pdf(
        "/sites/default/files/2026-06-16 Item 02 Bancroft Avenue Bike Lane.pdf"
    )
    fake_browser.pages[bancroft_pdf] = pdf_bytes("Item 02 Bancroft Avenue bike lane project")

    result = await council.fetch_council_and_311(
        37.87, -122.27, "Berkeley", street_terms=["bancroft"]
    )

    assert result["complaints_311"] == []
    council_items = result["council"]
    assert len(council_items) == 1  # only the Bancroft item matched the street term
    item = council_items[0]
    assert item["title"] == "Item 02 Bancroft Avenue Bike Lane"
    assert item["date"] == "2026-06-16"
    assert item["url"] == bancroft_pdf
    assert item["source"] == "berkeley.granicus.com"
    assert item["snippet"] is not None and "Bancroft" in item["snippet"]


async def test_fetch_council_snippet_is_none_when_pdf_unreadable(
    monkeypatch, http_router, fake_browser, fixture
):
    await _no_311(monkeypatch)
    http_router.text("ViewPublisher", fixture("granicus_viewpublisher.html"))
    http_router.text("clip_id=124", fixture("granicus_agenda_124.html"))
    http_router.text("clip_id=123", fixture("granicus_agenda_123.html"))

    bancroft_pdf = council._abs_pdf(
        "/sites/default/files/2026-06-16 Item 02 Bancroft Avenue Bike Lane.pdf"
    )
    fake_browser.pages[bancroft_pdf] = b"%PDF-1.4 corrupted bytes"

    result = await council.fetch_council_and_311(
        37.87, -122.27, "Berkeley", street_terms=["bancroft"]
    )

    assert len(result["council"]) == 1
    assert result["council"][0]["snippet"] is None  # degraded, but item still returned


async def test_fetch_council_without_streets_skips_browser(monkeypatch, fake_browser):
    await _no_311(monkeypatch)

    result = await council.fetch_council_and_311(37.87, -122.27, "Berkeley", street_terms=None)

    assert result["council"] == []
    assert fake_browser.calls == []  # no cloud-browser session opened
