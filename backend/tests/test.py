"""
Standalone test script for the Browserbase API.

This script verifies that your Browserbase credentials work by:
  1. Creating a new browser session via the Browserbase REST API.
  2. Connecting to that session over the Playwright CDP endpoint.
  3. Navigating to a page and reading back the title.
  4. Releasing the session.

Usage:
    # Set credentials in your shell (do NOT commit these):
    #   export BROWSERBASE_API_KEY=bb_live_xxx        (PowerShell: $env:BROWSERBASE_API_KEY="bb_live_xxx")
    #   export BROWSERBASE_PROJECT_ID=xxxxxxxx        (PowerShell: $env:BROWSERBASE_PROJECT_ID="xxxx")
    #
    # Install deps:
    #   pip install requests playwright
    #   playwright install chromium
    #
    # Run:
    #   python test.py
    #   python test.py --url https://example.com
"""

import argparse
import os
import sys
import requests

BROWSERBASE_API_BASE = "https://api.browserbase.com/v1"


def get_credentials():
    """Read credentials from environment variables."""
    api_key = os.environ.get("BROWSERBASE_API_KEY")
    project_id = os.environ.get("BROWSERBASE_PROJECT_ID")

    missing = []
    if not api_key:
        missing.append("BROWSERBASE_API_KEY")
    if not project_id:
        missing.append("BROWSERBASE_PROJECT_ID")

    if missing:
        print(f"ERROR: missing environment variable(s): {', '.join(missing)}")
        print("Set them before running this script.")
        sys.exit(1)

    return api_key, project_id


def create_session(api_key, project_id):
    """Create a new Browserbase session and return its (session_id, connect_url)."""
    print("==> Creating Browserbase session...")
    resp = requests.post(
        f"{BROWSERBASE_API_BASE}/sessions",
        headers={
            "X-BB-API-Key": api_key,
            "Content-Type": "application/json",
        },
        json={"projectId": project_id},
        timeout=30,
    )

    if resp.status_code not in (200, 201):
        print(f"ERROR: session creation failed [{resp.status_code}]: {resp.text}")
        sys.exit(1)

    data = resp.json()
    session_id = data.get("id")
    connect_url = data.get("connectUrl")
    print(f"    session id   : {session_id}")
    print(f"    connect url  : {connect_url}")
    return session_id, connect_url


def get_session(api_key, session_id):
    """Fetch session metadata to confirm the REST API is reachable."""
    print("==> Fetching session details...")
    resp = requests.get(
        f"{BROWSERBASE_API_BASE}/sessions/{session_id}",
        headers={"X-BB-API-Key": api_key},
        timeout=30,
    )
    if resp.status_code != 200:
        print(f"WARN: could not fetch session details [{resp.status_code}]: {resp.text}")
        return
    data = resp.json()
    print(f"    status       : {data.get('status')}")
    print(f"    region       : {data.get('region')}")


def drive_browser(connect_url, url):
    """Connect to the session over CDP with Playwright and load a page."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("WARN: playwright not installed; skipping browser drive test.")
        print("      Install with: pip install playwright && playwright install chromium")
        return

    print(f"==> Connecting over CDP and navigating to {url} ...")
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(connect_url)
        try:
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            title = page.title()
            print(f"    page title   : {title!r}")
            print("    PASS: browser navigation succeeded.")
        finally:
            browser.close()


def main():
    parser = argparse.ArgumentParser(description="Test the Browserbase API.")
    parser.add_argument(
        "--url",
        default="https://example.com",
        help="URL to navigate to in the test session (default: https://example.com)",
    )
    args = parser.parse_args()

    api_key, project_id = get_credentials()

    session_id, connect_url = create_session(api_key, project_id)
    get_session(api_key, session_id)

    if connect_url:
        drive_browser(connect_url, args.url)
    else:
        print("WARN: no connectUrl returned; skipping browser drive test.")

    print("\nDone.")


if __name__ == "__main__":
    main()
