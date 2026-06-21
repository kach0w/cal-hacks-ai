"""Black-box tests for the HTTP surface.

NOTE: the orchestrator's "route" layer is the FastAPI router in
``safestreets.api.routes`` (it lives under ``api/``, not ``orchestrator/``).
These tests drive it the way a real client would — through HTTP requests against
``TestClient`` — and assert on status codes and JSON bodies only.

The router's downstream collaborators (Redis cache, the dispatch gather, the
vision coordinator, the coalition store) are the external boundaries, so each
test scripts them via monkeypatch. No private route helpers are touched.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from safestreets.api import routes
from safestreets.main import app

client = TestClient(app)


# --------------------------------------------------------------------------- #
# /health
# --------------------------------------------------------------------------- #
def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


# --------------------------------------------------------------------------- #
# POST /analyze
# --------------------------------------------------------------------------- #
def test_analyze_requires_coordinates():
    # lat/lng are required by the request schema
    r = client.post("/analyze", json={"address": "Main & 1st"})
    assert r.status_code == 422


def test_analyze_returns_cached_result_without_recomputing(monkeypatch):
    cached = {"findings": [], "source": "cache"}

    async def get_json(key):
        return cached

    # If the pipeline ran we'd hit un-stubbed gather/coordinator and fail.
    monkeypatch.setattr(routes.cache, "get_json", get_json)

    r = client.post("/analyze", json={"lat": 1.0, "lng": 2.0})

    assert r.status_code == 200
    assert r.json() == cached


def test_analyze_runs_pipeline_on_cache_miss(monkeypatch):
    async def get_json(key):
        return None

    async def set_json(key, value, ttl=None):
        pass

    async def gather_data(lat, lng, city):
        return {"streets": ["Main St"], "images": []}

    class _FakeResult:
        def model_dump(self, mode="json"):
            return {"findings": ["f1"], "computed": True}

    async def analyze(intersection, data):
        return _FakeResult()

    monkeypatch.setattr(routes.cache, "get_json", get_json)
    monkeypatch.setattr(routes.cache, "set_json", set_json)
    monkeypatch.setattr(routes, "gather_data", gather_data)
    monkeypatch.setattr(routes.coordinator, "analyze", analyze)

    r = client.post("/analyze", json={"lat": 1.5, "lng": 2.5, "address": "Main & 1st"})

    assert r.status_code == 200
    assert r.json() == {"findings": ["f1"], "computed": True}


def test_analyze_falls_back_to_gathered_streets_for_address(monkeypatch):
    """With no address supplied, the route synthesises one from the gathered
    streets. We observe it via what gets handed to the (mocked) coordinator."""
    captured: dict = {}

    async def get_json(key):
        return None

    async def set_json(key, value, ttl=None):
        pass

    async def gather_data(lat, lng, city):
        return {"streets": ["Main St", "1st Ave"], "images": []}

    class _FakeResult:
        def model_dump(self, mode="json"):
            return {"ok": True}

    async def analyze(intersection, data):
        captured["address"] = intersection.address
        return _FakeResult()

    monkeypatch.setattr(routes.cache, "get_json", get_json)
    monkeypatch.setattr(routes.cache, "set_json", set_json)
    monkeypatch.setattr(routes, "gather_data", gather_data)
    monkeypatch.setattr(routes.coordinator, "analyze", analyze)

    r = client.post("/analyze", json={"lat": 1.5, "lng": 2.5})

    assert r.status_code == 200
    assert captured["address"] == "Main St & 1st Ave"


# --------------------------------------------------------------------------- #
# GET /analyze/stream  (Server-Sent Events)
# --------------------------------------------------------------------------- #
def test_analyze_stream_emits_progress_then_done(monkeypatch):
    async def run_pipeline(lat, lng, city):
        yield {"agent": "orchestrator", "msg": "cache hit", "cached": True}

    monkeypatch.setattr(routes, "run_pipeline", run_pipeline)

    with client.stream("GET", "/analyze/stream", params={"lat": 1, "lng": 2}) as r:
        assert r.status_code == 200
        body = "".join(r.iter_text())

    assert "event: progress" in body
    assert "event: done" in body
    assert "cache hit" in body  # the scripted event made it through


# --------------------------------------------------------------------------- #
# GET /intersection  (currently a stub that always reports not_analyzed)
# --------------------------------------------------------------------------- #
def test_intersection_reports_not_analyzed():
    r = client.get("/intersection", params={"lat": 1, "lng": 2})
    assert r.status_code == 200
    assert r.json() == {"status": "not_analyzed"}


def test_intersection_requires_lat_lng():
    r = client.get("/intersection")
    assert r.status_code == 422


# --------------------------------------------------------------------------- #
# POST /submit
# --------------------------------------------------------------------------- #
def test_submit_records_report_and_returns_count(monkeypatch):
    async def add_report(corridor_id, resident_token="anon"):
        return 3

    monkeypatch.setattr(routes.coalition, "add_report", add_report)

    r = client.post("/submit", json={"lat": 1.0, "lng": 2.0, "description": "broken light"})

    assert r.status_code == 200
    assert r.json() == {"status": "received", "coalition_count": 3}


def test_submit_requires_description():
    r = client.post("/submit", json={"lat": 1.0, "lng": 2.0})
    assert r.status_code == 422


# --------------------------------------------------------------------------- #
# GET /corridor/{id}
# --------------------------------------------------------------------------- #
def test_corridor_returns_coalition_count(monkeypatch):
    async def count(corridor_id):
        return 7

    monkeypatch.setattr(routes.coalition, "count", count)

    r = client.get("/corridor/abc-123")

    assert r.status_code == 200
    assert r.json() == {"corridor_id": "abc-123", "coalition_count": 7}
