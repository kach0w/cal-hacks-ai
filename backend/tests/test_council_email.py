"""Tests for the council-email feature: the PDF writer, the email agent's parsing +
.eml assembly, the Socrata jurisdiction lookup, and the /council-email route.

All offline: the LLM call and Socrata are stubbed; the PDF/.eml builders are pure.
"""
from __future__ import annotations

import base64
import email as email_lib
import io
import types

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader

from safestreets.api import routes
from safestreets.lastmile import council_lookup, email_agent, pdf
from safestreets.lastmile.email_agent import EmailDraft, _parse_email
from safestreets.main import app
from safestreets.models.council import CouncilContact

client = TestClient(app)


# --------------------------------------------------------------------------- #
# pdf.council_letter_pdf
# --------------------------------------------------------------------------- #
def test_pdf_is_valid_and_text_extractable():
    data = pdf.council_letter_pdf("Pedestrian Safety — Main & 1st", "Dear Council,\n\nPlease act.")
    assert data.startswith(b"%PDF-1.4")
    reader = PdfReader(io.BytesIO(data))
    text = reader.pages[0].extract_text()
    assert "Pedestrian Safety" in text
    assert "Please act" in text


def test_pdf_paginates_long_bodies():
    body = "\n\n".join("Paragraph %d about a dangerous crossing. " % i * 20 for i in range(60))
    reader = PdfReader(io.BytesIO(pdf.council_letter_pdf("Title", body)))
    assert len(reader.pages) > 1


# --------------------------------------------------------------------------- #
# email_agent._parse_email
# --------------------------------------------------------------------------- #
def test_parse_email_extracts_json_even_with_surrounding_prose():
    subject, body = _parse_email('Here you go: {"subject": "S", "body": "B"} done', "fallback")
    assert subject == "S"
    assert body == "B"


def test_parse_email_falls_back_to_body_when_no_json():
    subject, body = _parse_email("just a plain email body", "Default Subject")
    assert subject == "Default Subject"
    assert body == "just a plain email body"


# --------------------------------------------------------------------------- #
# email_agent.build_eml / pdf_filename
# --------------------------------------------------------------------------- #
def test_build_eml_attaches_pdf_and_lists_all_recipients():
    draft = EmailDraft(
        subject="Urgent: Main & 1st",
        body="Dear Councilmembers,\n\nPlease help.",
        recipients=[
            CouncilContact(name="District 4", email="d4@city.gov", district="4"),
            CouncilContact(name="City Council", email="council@city.gov"),
        ],
    )
    eml = email_agent.build_eml(draft, pdf.council_letter_pdf("t", "body"), "report.pdf")
    msg = email_lib.message_from_string(eml)

    assert msg["Subject"] == "Urgent: Main & 1st"
    assert msg["To"] == "d4@city.gov, council@city.gov"
    attachments = [p.get_filename() for p in msg.walk() if p.get_filename()]
    assert attachments == ["report.pdf"]
    pdf_part = next(p for p in msg.walk() if p.get_filename() == "report.pdf")
    assert pdf_part.get_payload(decode=True).startswith(b"%PDF")


def test_pdf_filename_is_slugged_from_address():
    name = email_agent.pdf_filename(
        types.SimpleNamespace(address="Bancroft Ave & Fulton St")  # type: ignore[arg-type]
    )
    assert name == "SafeStreets-bancroft-ave-fulton-st.pdf"


# --------------------------------------------------------------------------- #
# council_lookup.find_council_contacts
# --------------------------------------------------------------------------- #
def _fake_settings(**overrides):
    base = dict(
        council_districts_domain="data.example.gov",
        council_districts_dataset="",
        council_geom_column="the_geom",
        council_general_email="council@city.gov",
        council_district_emails="",
    )
    base.update(overrides)
    return types.SimpleNamespace(**base)


async def test_lookup_returns_general_inbox_when_no_dataset_configured(monkeypatch):
    monkeypatch.setattr(council_lookup, "get_settings", lambda: _fake_settings())
    contacts = await council_lookup.find_council_contacts(37.87, -122.27, "Berkeley")
    assert len(contacts) == 1
    assert contacts[0].email == "council@city.gov"
    assert contacts[0].source == "general_inbox"


async def test_lookup_resolves_member_from_socrata_row(monkeypatch, http_router):
    monkeypatch.setattr(
        council_lookup, "get_settings", lambda: _fake_settings(council_districts_dataset="abcd-1234")
    )
    http_router.text(
        "/resource/abcd-1234.json",
        '[{"district": "4", "councilmember": "Jane Doe", "email": "jane@city.gov"}]',
    )
    contacts = await council_lookup.find_council_contacts(37.87, -122.27, "Berkeley")
    assert contacts[0].email == "jane@city.gov"
    assert contacts[0].district == "4"
    assert contacts[0].name == "Jane Doe"
    assert contacts[0].source == "socrata"


async def test_lookup_config_map_overrides_dataset_email(monkeypatch, http_router):
    monkeypatch.setattr(
        council_lookup,
        "get_settings",
        lambda: _fake_settings(
            council_districts_dataset="abcd-1234",
            council_district_emails='{"4": {"name": "Real Member", "email": "real@city.gov"}}',
        ),
    )
    http_router.text("/resource/abcd-1234.json", '[{"district": "4", "email": "stale@city.gov"}]')
    contacts = await council_lookup.find_council_contacts(37.87, -122.27, "Berkeley")
    assert contacts[0].email == "real@city.gov"
    assert contacts[0].name == "Real Member"
    assert contacts[0].source == "config"


async def test_lookup_degrades_to_inbox_when_socrata_errors(monkeypatch, http_router):
    monkeypatch.setattr(
        council_lookup, "get_settings", lambda: _fake_settings(council_districts_dataset="abcd-1234")
    )
    http_router.text("/resource/abcd-1234.json", "boom", status=500)
    contacts = await council_lookup.find_council_contacts(37.87, -122.27, "Berkeley")
    assert contacts[0].email == "council@city.gov"


# --------------------------------------------------------------------------- #
# POST /council-email
# --------------------------------------------------------------------------- #
_VISION = {
    "intersection": {"id": "x", "address": "Main & 1st", "lat": 1.0, "lng": 2.0, "city": "Berkeley"},
    "findings": [],
    "council_report": "Dear Council,\n\nMain & 1st is dangerous. Please act.",
}


def test_council_email_requires_prior_analysis(monkeypatch):
    async def get_json(key):
        return None  # nothing cached: no email draft AND no vision result

    monkeypatch.setattr(routes.cache, "get_json", get_json)
    r = client.post("/council-email", json={"lat": 1.0, "lng": 2.0})
    assert r.status_code == 200
    assert r.json() == {"status": "not_analyzed"}


def test_council_email_builds_eml_with_pdf_attachment(monkeypatch):
    async def get_json(key):
        if key.startswith("ss:council-email:"):
            return None
        if key.startswith("ss:vision:"):
            return _VISION
        return {}  # scrape/community data

    async def set_json(key, value, ttl=None):
        pass

    async def find_council_contacts(lat, lng, city):
        return [CouncilContact(name="District 4", email="d4@city.gov", district="4")]

    async def build_council_email(findings, intersection, community, contacts):
        return EmailDraft(subject="Safety at Main & 1st", body="Dear Councilmember,\n\nPlease act.", recipients=contacts)

    monkeypatch.setattr(routes.cache, "get_json", get_json)
    monkeypatch.setattr(routes.cache, "set_json", set_json)
    monkeypatch.setattr(routes.council_lookup, "find_council_contacts", find_council_contacts)
    monkeypatch.setattr(routes.email_agent, "build_council_email", build_council_email)

    r = client.post("/council-email", json={"lat": 1.0, "lng": 2.0})
    assert r.status_code == 200
    body = r.json()
    assert body["subject"] == "Safety at Main & 1st"
    assert body["recipients"][0]["email"] == "d4@city.gov"
    assert body["filename"].endswith(".eml")

    eml = base64.b64decode(body["eml_base64"]).decode("utf-8")
    msg = email_lib.message_from_string(eml)
    assert msg["To"] == "d4@city.gov"
    pdf_part = next((p for p in msg.walk() if p.get_filename()), None)
    assert pdf_part is not None and pdf_part.get_payload(decode=True).startswith(b"%PDF")


def test_council_email_returns_cached_draft_without_recomputing(monkeypatch):
    cached = {"subject": "cached", "body": "b", "recipients": [], "eml_base64": "AA==", "filename": "x.eml"}

    async def get_json(key):
        return cached if key.startswith("ss:council-email:") else None

    def fail(*a, **k):  # ensure the agent is never invoked on a cache hit
        raise AssertionError("should not rebuild on cache hit")

    monkeypatch.setattr(routes.cache, "get_json", get_json)
    monkeypatch.setattr(routes.email_agent, "build_council_email", fail)

    r = client.post("/council-email", json={"lat": 1.0, "lng": 2.0})
    assert r.status_code == 200
    assert r.json() == cached
