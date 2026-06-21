"""Offline tests for the Browserbase session wrapper.

Browserbase bills by open-browser time, so the one behaviour that must never
regress is: every session is closed, including when the caller raises. We fake
Playwright and the session factory entirely — no cloud browser is opened — and
assert the teardown contract on the real ``browser_page`` / ``fetch_via_browser``
code paths.
"""
from __future__ import annotations

import types

import pytest

from safestreets.clients import browserbase_client as bc
from safestreets.config import get_settings


# --------------------------------------------------------------------------- #
# Playwright fakes
# --------------------------------------------------------------------------- #
class _FakeResponse:
    def __init__(self, ok: bool, body: bytes = b"") -> None:
        self.ok = ok
        self._body = body

    async def body(self) -> bytes:
        return self._body


class _FakeRequest:
    """ctx.request — maps a URL to (ok, body) or an Exception to raise."""

    def __init__(self, table: dict) -> None:
        self.table = table

    async def get(self, url: str, timeout: int | None = None):
        outcome = self.table.get(url)
        if isinstance(outcome, Exception):
            raise outcome
        ok, body = outcome
        return _FakeResponse(ok, body)


class _FakePage:
    async def goto(self, *a, **k):
        return None

    async def content(self):
        return "<html></html>"


class _FakeContext:
    def __init__(self, request=None, pages=None) -> None:
        self.request = request
        self.pages = pages if pages is not None else []

    async def new_page(self):
        page = _FakePage()
        self.pages.append(page)
        return page


class _FakeBrowser:
    def __init__(self, ctx, closed: list) -> None:
        self.contexts = [ctx]
        self._closed = closed

    async def close(self):
        self._closed.append(True)


class _FakeChromium:
    def __init__(self, browser) -> None:
        self._browser = browser

    async def connect_over_cdp(self, url):
        return self._browser


class _FakePlaywright:
    def __init__(self, browser) -> None:
        self.chromium = _FakeChromium(browser)


class _FakePWManager:
    def __init__(self, browser) -> None:
        self._pw = _FakePlaywright(browser)

    async def __aenter__(self):
        return self._pw

    async def __aexit__(self, *a):
        return False


def _patch(monkeypatch, browser) -> None:
    async def fake_new_session():
        return types.SimpleNamespace(connect_url="ws://fake-cdp")

    monkeypatch.setattr(bc, "new_session", fake_new_session)
    monkeypatch.setattr(
        "playwright.async_api.async_playwright", lambda: _FakePWManager(browser)
    )


# --------------------------------------------------------------------------- #
# new_session
# --------------------------------------------------------------------------- #
async def test_new_session_creates_with_configured_project(monkeypatch):
    created = {}
    fake_session = object()

    class _Sessions:
        def create(self, project_id):
            created["project_id"] = project_id
            return fake_session

    monkeypatch.setattr(bc, "get_browserbase", lambda: types.SimpleNamespace(sessions=_Sessions()))

    result = await bc.new_session()

    assert result is fake_session
    assert created["project_id"] == get_settings().browserbase_project_id


# --------------------------------------------------------------------------- #
# browser_page — closes the browser on success AND on exception
# --------------------------------------------------------------------------- #
async def test_browser_page_yields_existing_page_and_closes(monkeypatch):
    closed: list = []
    existing = _FakePage()
    ctx = _FakeContext(pages=[existing])
    _patch(monkeypatch, _FakeBrowser(ctx, closed))

    async with bc.browser_page() as page:
        assert page is existing

    assert closed == [True]  # session ended -> billing stops


async def test_browser_page_closes_even_when_caller_raises(monkeypatch):
    closed: list = []
    ctx = _FakeContext(pages=[_FakePage()])
    _patch(monkeypatch, _FakeBrowser(ctx, closed))

    with pytest.raises(ValueError):
        async with bc.browser_page():
            raise ValueError("boom")

    assert closed == [True]  # the leak guard: teardown ran despite the error


# --------------------------------------------------------------------------- #
# fetch_via_browser — per-URL bytes/None, and the session is closed
# --------------------------------------------------------------------------- #
async def test_fetch_via_browser_returns_bytes_or_none_per_url(monkeypatch):
    closed: list = []
    table = {
        "https://x/ok.pdf": (True, b"PDFBYTES"),
        "https://x/notfound.pdf": (False, b""),
        "https://x/raises.pdf": RuntimeError("network blip"),
    }
    ctx = _FakeContext(request=_FakeRequest(table))
    _patch(monkeypatch, _FakeBrowser(ctx, closed))

    out = await bc.fetch_via_browser(list(table))

    assert out["https://x/ok.pdf"] == b"PDFBYTES"
    assert out["https://x/notfound.pdf"] is None   # non-ok response
    assert out["https://x/raises.pdf"] is None      # exception swallowed per-URL
    assert closed == [True]
