"""Black-box tests for the adaptive dispatch pipeline.

We exercise the two public entry points the rest of the system relies on:

    * ``run_pipeline(lat, lng, city)`` — an async stream of progress events.
    * ``gather_data(lat, lng, city)``  — the non-streaming, cache-first gather.

The cache (Redis) and the data-collection agents are the module's external
boundaries, so the tests swap those for in-memory / scripted stand-ins and then
assert *only* on observable behaviour: what gets yielded, what gets returned,
and what ends up persisted. Nothing here looks at the private ``_gather`` /
``_with_retry`` helpers.
"""
from __future__ import annotations

import pytest

from safestreets.orchestrator import dispatch
from safestreets.store import keys


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
class _FakeImage:
    """An ImageRef-shaped stand-in. Dispatch only relies on the object exposing
    ``.model_dump(mode="json")`` when it serialises gathered imagery."""

    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def model_dump(self, mode: str = "json") -> dict:
        return self._payload


def _async_raise(exc: Exception):
    async def _fn(*args, **kwargs):
        raise exc

    return _fn


async def _collect(aiter) -> list[dict]:
    return [event async for event in aiter]


# --------------------------------------------------------------------------- #
# fixtures (the external boundaries)
# --------------------------------------------------------------------------- #
@pytest.fixture
def fake_store(monkeypatch):
    """In-memory replacement for the Redis-backed cache boundary. The returned
    dict *is* the store, so a test can pre-seed a cache hit or inspect what the
    pipeline persisted."""
    store: dict = {}

    async def get_json(key):
        return store.get(key)

    async def set_json(key, value, ttl=None):
        store[key] = value

    monkeypatch.setattr(dispatch.cache, "get_json", get_json)
    monkeypatch.setattr(dispatch.cache, "set_json", set_json)
    return store


@pytest.fixture
def stub_agents(monkeypatch):
    """Replace every data-collection boundary with controllable stubs. Returns
    the canned outputs so a test can assert they flow through unchanged."""
    canned = {
        "streets": ["A St", "B Ave"],
        "images": [_FakeImage({"direction": "satellite", "url": "u"})],
        "crash": [{"id": 1}],
        "complaints": [{"id": 2}],
    }

    async def nearby_streets(lat, lng):
        return canned["streets"]

    async def fetch_images(lat, lng):
        return canned["images"]

    async def fetch_crash_data(lat, lng, city):
        return canned["crash"]

    async def fetch_311(lat, lng):
        return canned["complaints"]

    monkeypatch.setattr("safestreets.clients.google_maps.nearby_streets", nearby_streets)
    monkeypatch.setattr("safestreets.agents.image_fetcher.fetch_images", fetch_images)
    monkeypatch.setattr("safestreets.agents.structured_data.fetch_crash_data", fetch_crash_data)
    monkeypatch.setattr("safestreets.agents.council_311_agent.fetch_311", fetch_311)
    return canned


# --------------------------------------------------------------------------- #
# run_pipeline — the streaming surface
# --------------------------------------------------------------------------- #
async def test_run_pipeline_short_circuits_on_cache_hit(fake_store):
    """A cached scrape is the 'instant on repeat' moment: exactly one event,
    flagged cached, and no agent work attempted (un-stubbed agents would fail)."""
    fake_store[keys.scrape_key(1.0, 2.0)] = {"images": []}

    events = await _collect(dispatch.run_pipeline(1.0, 2.0, "Berkeley"))

    assert len(events) == 1
    assert events[0].get("cached") is True
    assert "cache hit" in events[0]["msg"].lower()


async def test_run_pipeline_streams_per_agent_progress(fake_store, stub_agents):
    events = await _collect(dispatch.run_pipeline(3.0, 4.0, "Berkeley"))

    agents_seen = {e.get("agent") for e in events}
    assert {"orchestrator", "images", "structured", "complaints_311"} <= agents_seen
    # first event announces dispatch; last confirms completion
    assert "dispatch" in events[0]["msg"].lower()
    assert events[-1]["msg"] == "data gathered"


async def test_run_pipeline_never_leaks_data_sentinel(fake_store, stub_agents):
    """The assembled payload travels on an internal ``__data__`` event that the
    streaming surface must strip before handing events to the SSE endpoint."""
    events = await _collect(dispatch.run_pipeline(3.0, 4.0, "Berkeley"))

    assert all("__data__" not in e for e in events)


async def test_run_pipeline_persists_assembled_data(fake_store, stub_agents):
    await _collect(dispatch.run_pipeline(3.0, 4.0, "Berkeley"))

    cached = fake_store[keys.scrape_key(3.0, 4.0)]
    assert set(cached) == {"images", "streets", "crash_data", "complaints_311"}
    assert cached["streets"] == stub_agents["streets"]
    assert cached["crash_data"] == stub_agents["crash"]
    assert cached["complaints_311"] == stub_agents["complaints"]
    # imagery is serialised via model_dump on the way into the cache
    assert cached["images"] == [{"direction": "satellite", "url": "u"}]


# --------------------------------------------------------------------------- #
# gather_data — the non-streaming surface used by POST /analyze
# --------------------------------------------------------------------------- #
async def test_gather_data_returns_cached_verbatim(fake_store):
    payload = {"images": [], "streets": ["X"], "crash_data": [], "complaints_311": []}
    fake_store[keys.scrape_key(5.0, 6.0)] = payload

    result = await dispatch.gather_data(5.0, 6.0, "Berkeley")

    assert result == payload


async def test_gather_data_assembles_from_agents_on_miss(fake_store, stub_agents):
    result = await dispatch.gather_data(7.0, 8.0, "Berkeley")

    assert result["streets"] == stub_agents["streets"]
    assert result["crash_data"] == stub_agents["crash"]
    assert result["complaints_311"] == stub_agents["complaints"]
    assert result["images"] == [{"direction": "satellite", "url": "u"}]


# --------------------------------------------------------------------------- #
# resilience contracts
# --------------------------------------------------------------------------- #
async def test_stubbed_agent_does_not_crash_pipeline(fake_store, stub_agents, monkeypatch):
    """A not-yet-implemented agent raises NotImplementedError; the pipeline must
    treat that section as empty rather than failing the whole run."""
    monkeypatch.setattr(
        "safestreets.agents.image_fetcher.fetch_images",
        _async_raise(NotImplementedError()),
    )

    result = await dispatch.gather_data(9.0, 10.0, "Berkeley")

    assert result["images"] == []
    assert result["crash_data"] == stub_agents["crash"]  # others still contribute


async def test_street_lookup_failure_is_isolated(fake_store, stub_agents, monkeypatch):
    """A failing street lookup degrades to an empty street list without taking
    the rest of the gather down with it."""
    monkeypatch.setattr(
        "safestreets.clients.google_maps.nearby_streets",
        _async_raise(RuntimeError("maps down")),
    )

    result = await dispatch.gather_data(11.0, 12.0, "Berkeley")

    assert result["streets"] == []
    assert result["crash_data"] == stub_agents["crash"]


async def test_city_defaults_to_configured_demo_city(fake_store, monkeypatch):
    """When the caller omits a city, the pipeline resolves the demo-scope city
    from config and passes it to the crash-data agent (never None)."""
    seen: dict = {}

    async def empty(*args, **kwargs):
        return []

    async def fetch_crash_data(lat, lng, city):
        seen["city"] = city
        return []

    monkeypatch.setattr("safestreets.clients.google_maps.nearby_streets", empty)
    monkeypatch.setattr("safestreets.agents.image_fetcher.fetch_images", empty)
    monkeypatch.setattr("safestreets.agents.structured_data.fetch_crash_data", fetch_crash_data)
    monkeypatch.setattr("safestreets.agents.council_311_agent.fetch_311", empty)

    await dispatch.gather_data(1.5, 2.5, None)

    assert seen["city"]  # resolved to a real city, not None
