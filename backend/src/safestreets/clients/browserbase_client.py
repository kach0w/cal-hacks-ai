"""Browserbase session helper for the scraping agents.

Note: Stagehand is TypeScript-first. This wrapper uses the Browserbase Python SDK; if
you want Stagehand's extract()/act() specifically, run a small Node sidecar and call it
from the agents (the agent interfaces don't change either way).
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from functools import lru_cache

from safestreets.config import get_settings


@lru_cache
def get_browserbase():
    from browserbase import Browserbase  # imported lazily so the app boots without it

    s = get_settings()
    return Browserbase(api_key=s.browserbase_api_key)


async def new_session():
    """Create a Browserbase session and return it.

    The caller drives it with Playwright via ``session.connect_url`` (CDP over WebSocket).
    Always ``browser.close()`` when done — sessions bill by open browser time.
    """
    s = get_settings()
    bb = get_browserbase()
    return bb.sessions.create(project_id=s.browserbase_project_id)


@asynccontextmanager
async def browser_page():
    """Open a Browserbase session + Playwright page, and guarantee teardown.

    Usage:
        async with browser_page() as page:
            await page.goto(...)
    Closing the browser ends the session so we stop paying for browser time.
    """
    from playwright.async_api import async_playwright

    session = await new_session()
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(session.connect_url)
        try:
            ctx = browser.contexts[0]
            page = ctx.pages[0] if ctx.pages else await ctx.new_page()
            yield page
        finally:
            await browser.close()


async def fetch_via_browser(urls: list[str], timeout_ms: int = 40000) -> dict[str, bytes | None]:
    """Fetch each URL's bytes through ONE Browserbase session's network stack.

    Used for council-agenda PDFs: routing the download through the cloud browser is
    robust to bot-walling, and one session covers many files (sessions bill by time).
    Returns {url: bytes or None}.
    """
    from playwright.async_api import async_playwright

    out: dict[str, bytes | None] = {}
    session = await new_session()
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(session.connect_url)
        try:
            ctx = browser.contexts[0]
            for u in urls:
                try:
                    resp = await ctx.request.get(u, timeout=timeout_ms)
                    out[u] = await resp.body() if resp.ok else None
                except Exception:  # noqa: BLE001
                    out[u] = None
        finally:
            await browser.close()
    return out
