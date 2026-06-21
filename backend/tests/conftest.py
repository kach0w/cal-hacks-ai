"""Shared test scaffolding.

The tests in this package are deterministic and fully offline: no live network,
no real browser sessions, no real Redis. Every external boundary the scraping
subsystem touches — HTTP (httpx), Browserbase/Playwright, the Socrata client,
Google Maps — is replaced with a controllable fake here, so a test asserts on
*behaviour* (what was parsed, what degraded gracefully) rather than on the live
internet.

Two helpers do most of the work:

* ``http_router``  — swaps ``httpx.AsyncClient`` for one backed by
  ``httpx.MockTransport``; a test registers URL-substring -> response routes.
* ``fake_browser`` — monkeypatches ``browserbase_client.fetch_via_browser`` and
  ``browser_page`` so no cloud browser session is ever opened.

The routes module also imports the optional ``google.genai`` dependency
transitively; it isn't installed in every environment, so we register a stub for
it before any application module is imported.
"""
from __future__ import annotations

import io
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest

FIXTURES = Path(__file__).parent / "fixtures"


# --------------------------------------------------------------------------- #
# optional-dependency stub (kept from the original conftest)
# --------------------------------------------------------------------------- #
def _install_genai_stub() -> None:
    if "google.genai" in sys.modules:
        return

    genai = types.ModuleType("google.genai")
    genai.Client = MagicMock(name="genai.Client")

    genai_types = types.ModuleType("google.genai.types")

    def _any_attr(name: str) -> MagicMock:  # PEP 562 module __getattr__
        return MagicMock(name=f"google.genai.types.{name}")

    genai_types.__getattr__ = _any_attr  # type: ignore[attr-defined]
    genai.types = genai_types

    sys.modules["google.genai"] = genai
    sys.modules["google.genai.types"] = genai_types


_install_genai_stub()


# --------------------------------------------------------------------------- #
# fixture file loading
# --------------------------------------------------------------------------- #
def load_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


@pytest.fixture
def fixture():
    """Return the text of a committed fixture by filename."""
    return load_fixture


# --------------------------------------------------------------------------- #
# deterministic PDF builder (avoids committing a binary fixture)
# --------------------------------------------------------------------------- #
def make_pdf(text: str) -> bytes:
    """A minimal single-page PDF carrying one text-showing operator. pypdf can
    extract ``text`` back out of it, so it stands in for a council-agenda PDF."""
    content = f"BT /F1 24 Tf 72 700 Td ({text}) Tj ET".encode("latin-1")
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objs, start=1):
        offsets.append(out.tell())
        out.write(b"%d 0 obj\n" % i + body + b"\nendobj\n")
    xref_pos = out.tell()
    out.write(b"xref\n0 %d\n" % (len(objs) + 1))
    out.write(b"0000000000 65535 f \n")
    for off in offsets:
        out.write(b"%010d 00000 n \n" % off)
    out.write(b"trailer\n<< /Size %d /Root 1 0 R >>\n" % (len(objs) + 1))
    out.write(b"startxref\n%d\n%%%%EOF" % xref_pos)
    return out.getvalue()


@pytest.fixture
def pdf_bytes():
    """Factory: ``pdf_bytes("Bancroft Avenue ...")`` -> extractable PDF bytes."""
    return make_pdf


# --------------------------------------------------------------------------- #
# httpx mock transport
# --------------------------------------------------------------------------- #
class _Router:
    """Routes a request to a response by first matching URL substring."""

    def __init__(self) -> None:
        self.routes: list[tuple[str, object]] = []
        self.requested: list[str] = []

    def add(self, needle: str, response) -> "_Router":
        """Register a route. ``response`` is an ``httpx.Response`` or a callable
        ``request -> httpx.Response``."""
        self.routes.append((needle, response))
        return self

    def text(self, needle: str, body: str, status: int = 200) -> "_Router":
        return self.add(needle, httpx.Response(status, text=body))

    def handler(self, request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        self.requested.append(url)
        for needle, resp in self.routes:
            if needle in url:
                return resp(request) if callable(resp) else resp
        return httpx.Response(404, text=f"unmocked: {url}")


@pytest.fixture
def http_router(monkeypatch):
    """Swap ``httpx.AsyncClient`` for one whose transport is the router. Any code
    that does ``httpx.AsyncClient(...)`` now talks to our registered routes."""
    router = _Router()
    real_client = httpx.AsyncClient

    def factory(*args, **kwargs):
        kwargs.pop("transport", None)
        return real_client(*args, transport=httpx.MockTransport(router.handler), **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", factory)
    return router


# --------------------------------------------------------------------------- #
# Browserbase / Playwright fakes
# --------------------------------------------------------------------------- #
class _BrowserStore:
    def __init__(self) -> None:
        self.pages: dict[str, bytes | None] = {}   # url -> bytes returned by fetch_via_browser
        self.calls: list[list[str]] = []           # each fetch_via_browser invocation


@pytest.fixture
def fake_browser(monkeypatch):
    """Replace the cloud-browser boundary. ``store.pages`` maps a URL to the bytes
    a fetch should return (missing/None simulates a failed fetch). ``store.calls``
    records each invocation so a test can assert the browser was / was not used."""
    store = _BrowserStore()

    async def fake_fetch_via_browser(urls, timeout_ms: int = 40000):
        store.calls.append(list(urls))
        return {u: store.pages.get(u) for u in urls}

    class _FakePageCtx:
        async def __aenter__(self):
            class _Page:
                async def goto(self, *a, **k):
                    return None

                async def content(self):
                    return ""

            return _Page()

        async def __aexit__(self, *a):
            return False

    def fake_browser_page():
        return _FakePageCtx()

    monkeypatch.setattr(
        "safestreets.clients.browserbase_client.fetch_via_browser", fake_fetch_via_browser
    )
    monkeypatch.setattr(
        "safestreets.clients.browserbase_client.browser_page", fake_browser_page
    )
    return store
