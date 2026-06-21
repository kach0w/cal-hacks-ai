"""Black-box integration tests for the Browserbase agents / session API.

These exercise the Browserbase service contract directly rather than any
internal code: session lifecycle (create -> inspect -> connect -> release)
and the failure modes an agent must handle (missing creds, bad project,
unreachable session).

Credentials are read ONLY from the process environment and the suite
auto-skips when they're absent, so it is safe to run in CI without secrets:

    BROWSERBASE_API_KEY      e.g. bb_live_xxx
    BROWSERBASE_PROJECT_ID   e.g. 0000-0000

Run:
    .venv\\Scripts\\python.exe -m pytest tests/test_browserbase.py -v
"""

import os
import uuid

import pytest

requests = pytest.importorskip("requests")

# Load credentials from a .env file if present. find_dotenv() walks up from the
# current working directory, so the repo-root .env is found even though pytest
# runs from backend/. Real environment variables still take precedence.
try:
    from dotenv import find_dotenv, load_dotenv

    load_dotenv(find_dotenv(usecwd=True))
except ImportError:
    pass

BROWSERBASE_API_BASE = "https://api.browserbase.com/v1"

API_KEY = os.environ.get("BROWSERBASE_API_KEY")
PROJECT_ID = os.environ.get("BROWSERBASE_PROJECT_ID")

# Whole module skips cleanly when creds are not provided.
live = pytest.mark.skipif(
    not (API_KEY and PROJECT_ID),
    reason="BROWSERBASE_API_KEY and BROWSERBASE_PROJECT_ID must be set for live tests",
)


def _auth_headers(api_key=API_KEY):
    return {"X-BB-API-Key": api_key, "Content-Type": "application/json"}


def _create_session(project_id=PROJECT_ID):
    return requests.post(
        f"{BROWSERBASE_API_BASE}/sessions",
        headers=_auth_headers(),
        json={"projectId": project_id},
        timeout=30,
    )


def _release_session(session_id):
    """Best-effort release so live tests don't leak running browsers."""
    try:
        requests.post(
            f"{BROWSERBASE_API_BASE}/sessions/{session_id}",
            headers=_auth_headers(),
            json={"projectId": PROJECT_ID, "status": "REQUEST_RELEASE"},
            timeout=30,
        )
    except requests.RequestException:
        pass


@pytest.fixture
def session():
    """Yield a freshly created session dict and guarantee its release."""
    resp = _create_session()
    assert resp.status_code in (200, 201), f"create failed: {resp.status_code} {resp.text}"
    data = resp.json()
    yield data
    _release_session(data["id"])


# --------------------------------------------------------------------------- #
# Credential / input validation (no live call needed)
# --------------------------------------------------------------------------- #

def _post_sessions_or_skip(headers):
    """POST to /sessions, skipping the test if the API can't be reached.

    These auth tests assert on the *response status*, so a connectivity or
    TLS failure is not a meaningful result -- skip rather than fail.
    """
    try:
        return requests.post(
            f"{BROWSERBASE_API_BASE}/sessions",
            headers=headers,
            json={"projectId": PROJECT_ID or "00000000-0000-0000-0000-000000000000"},
            timeout=30,
        )
    except requests.RequestException as exc:
        pytest.skip(f"Browserbase API unreachable: {exc}")


def test_missing_api_key_is_rejected():
    """A request with no API key must not be allowed to create a session."""
    resp = _post_sessions_or_skip({"Content-Type": "application/json"})
    assert resp.status_code in (401, 403), f"expected auth error, got {resp.status_code}"


def test_invalid_api_key_is_rejected():
    """A syntactically plausible but bogus key must be rejected."""
    resp = _post_sessions_or_skip(_auth_headers(api_key="bb_live_definitely_not_a_real_key"))
    assert resp.status_code in (401, 403), f"expected auth error, got {resp.status_code}"


# --------------------------------------------------------------------------- #
# Session lifecycle (live)
# --------------------------------------------------------------------------- #

@live
def test_create_session_returns_id_and_connect_url(session):
    """A created session must expose the fields an agent needs to attach."""
    assert session.get("id"), "session is missing an id"
    assert session.get("connectUrl"), "session is missing a connectUrl"
    assert str(session["connectUrl"]).startswith("ws"), "connectUrl should be a websocket URL"


@live
def test_get_session_roundtrips_the_same_id(session):
    """Fetching the session by id should return that same session."""
    resp = requests.get(
        f"{BROWSERBASE_API_BASE}/sessions/{session['id']}",
        headers=_auth_headers(),
        timeout=30,
    )
    assert resp.status_code == 200, f"{resp.status_code} {resp.text}"
    assert resp.json().get("id") == session["id"]


@live
def test_get_unknown_session_is_not_found():
    """A random (well-formed) session id must not resolve to a real session."""
    bogus = str(uuid.uuid4())
    resp = requests.get(
        f"{BROWSERBASE_API_BASE}/sessions/{bogus}",
        headers=_auth_headers(),
        timeout=30,
    )
    assert resp.status_code in (404, 400), f"expected not-found, got {resp.status_code}"


@live
def test_create_with_bad_project_is_rejected():
    """Creating against a project that isn't yours must fail."""
    resp = _create_session(project_id=str(uuid.uuid4()))
    assert resp.status_code >= 400, f"expected client error, got {resp.status_code}"


# --------------------------------------------------------------------------- #
# Driving the browser over CDP (live + playwright)
# --------------------------------------------------------------------------- #

@live
def test_agent_can_navigate_and_read_title(session):
    """The core agent capability: attach over CDP, load a page, read the DOM."""
    sync_playwright = pytest.importorskip("playwright.sync_api").sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(session["connectUrl"])
        try:
            ctx = browser.contexts[0] if browser.contexts else browser.new_context()
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            page.goto("https://example.com", wait_until="domcontentloaded", timeout=30000)
            assert "Example Domain" in page.title()
            assert "example" in page.url
        finally:
            browser.close()


@live
def test_agent_can_extract_text_content(session):
    """Agents typically scrape text; verify body text is reachable post-load."""
    sync_playwright = pytest.importorskip("playwright.sync_api").sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(session["connectUrl"])
        try:
            ctx = browser.contexts[0] if browser.contexts else browser.new_context()
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            page.goto("https://example.com", wait_until="domcontentloaded", timeout=30000)
            body = page.inner_text("body")
            assert body and len(body.strip()) > 0
            assert "illustrative examples" in body.lower()
        finally:
            browser.close()


@live
def test_released_session_cannot_be_reconnected():
    """After release, the connectUrl must no longer accept a CDP attach."""
    sync_playwright = pytest.importorskip("playwright.sync_api").sync_playwright

    resp = _create_session()
    assert resp.status_code in (200, 201)
    data = resp.json()
    _release_session(data["id"])

    with sync_playwright() as p:
        with pytest.raises(Exception):
            browser = p.chromium.connect_over_cdp(data["connectUrl"])
            browser.close()
