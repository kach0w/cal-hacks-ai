"""News agent: local-news crash coverage near an intersection.

Witness accounts and physical scene descriptions that official databases miss — these
feed Stage 2 corroboration (an independent 'reported' signal next to 'seen').

Source strategy (cost-aware): The Berkeley Scanner is a Ghost site whose sitemap lists
every post with the date AND a category in the URL path, and whose article pages are
static server-rendered HTML. So discovery + content are both plain HTTP — NO Browserbase
needed here. Browserbase is reserved for JS-rendered / bot-walled outlets (e.g.
berkeleyside) as a fallback.
"""
from __future__ import annotations

import asyncio
import re
from typing import Any

import httpx

_SCANNER = "https://www.berkeleyscanner.com"
_SITEMAP = f"{_SCANNER}/sitemap-posts.xml"
_TRAFFIC_CATEGORIES = {"traffic-safety", "traffic"}
_UA = {"User-Agent": "Mozilla/5.0 (SafeStreets news agent)"}

# /YYYY/MM/DD/<category>/<slug>/
_POST_RE = re.compile(
    r"<loc>(" + re.escape(_SCANNER) + r"/(\d{4})/(\d{2})/(\d{2})/([^/]+)/([^/<]+)/?)</loc>"
)


async def _list_traffic_posts(client: httpx.AsyncClient, since_year: int) -> list[dict[str, Any]]:
    """Read the sitemap and return traffic posts (URL carries date + location slug)."""
    resp = await client.get(_SITEMAP, headers=_UA, timeout=20)
    resp.raise_for_status()
    posts: list[dict[str, Any]] = []
    for url, yyyy, mm, dd, category, slug in _POST_RE.findall(resp.text):
        if category not in _TRAFFIC_CATEGORIES or int(yyyy) < since_year:
            continue
        posts.append(
            {
                "url": url,
                "date": f"{yyyy}-{mm}-{dd}",
                "category": category,
                "slug": slug,  # e.g. 'berkeley-crash-pedestrian-injured-hearst-grant'
            }
        )
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


def _score(slug: str, street_terms: list[str]) -> int:
    """How many of the intersection's street names appear in the article slug."""
    return sum(1 for t in street_terms if t and t in slug)


async def _fetch_article(client: httpx.AsyncClient, post: dict[str, Any]) -> dict[str, Any]:
    """Pull the headline + published date + excerpt from a static article page."""
    resp = await client.get(post["url"], headers=_UA, timeout=20, follow_redirects=True)
    resp.raise_for_status()
    html = resp.text

    def meta(pattern: str) -> str | None:
        m = re.search(pattern, html)
        return m.group(1).strip() if m else None

    title = meta(r'<meta property="og:title" content="([^"]+)"') or post["slug"]
    published = meta(r'<meta property="article:published_time" content="([^"]+)"')
    excerpt = meta(r'<meta name="description" content="([^"]+)"') or ""
    return {
        "title": title,
        "date": (published[:10] if published else post["date"]),
        "url": post["url"],
        "excerpt": excerpt,
        "source": "berkeleyscanner.com",
    }


async def fetch_berkeleyside(
    query: str = "crash",
    limit: int = 8,
) -> list[dict[str, Any]]:
    """Scrape Berkeleyside search results via Browserbase.

    Berkeleyside renders its search results with JavaScript — the static HTML has the
    CSS for article cards but not the cards themselves — so plain HTTP returns an empty
    shell. This is the genuine Browserbase case: a real cloud browser runs the JS, then
    we read the rendered DOM. Returns [{title, date, url, excerpt, source}].
    """
    from safestreets.clients.browserbase_client import browser_page

    url = f"https://www.berkeleyside.org/?s={query}"
    async with browser_page() as page:
        await page.goto(url, wait_until="domcontentloaded")
        # wait for the JS-rendered result cards
        await page.wait_for_selector("article .entry-title a", timeout=20000)
        rows = await page.eval_on_selector_all(
            "article",
            """els => els.slice(0, 40).map(el => {
                const a = el.querySelector('.entry-title a, h2 a, h3 a');
                const t = el.querySelector('time');
                const ex = el.querySelector('.entry-excerpt, .excerpt, p');
                return {
                    title: a ? a.textContent.trim() : '',
                    url: a ? a.href : '',
                    date: t ? (t.getAttribute('datetime') || t.textContent.trim()) : '',
                    excerpt: ex ? ex.textContent.trim() : '',
                };
            })""",
        )
    out = [
        {**r, "date": (r["date"][:10] if r["date"] else ""), "source": "berkeleyside.org"}
        for r in rows
        if r.get("title") and r.get("url")
    ]
    return out[:limit]


async def fetch_news(
    lat: float,
    lng: float,
    city: str | None,
    street_terms: list[str] | None = None,
    since_year: int = 2023,
    limit: int | None = None,
    concurrency: int = 10,
) -> list[dict[str, Any]]:
    """Return local-news crash coverage near the intersection.

    `street_terms` (e.g. ['hearst', 'grant']) keeps only articles whose slug mentions
    the cross streets; without it we return every traffic-safety post since `since_year`.
    `limit=None` means no cap (fetch them all). Returns [{title, date, url, excerpt, source}].
    """
    street_terms = [t.lower() for t in (street_terms or [])]
    async with httpx.AsyncClient() as client:
        posts = await _list_traffic_posts(client, since_year)
        if street_terms:
            matched = [p for p in posts if _score(p["slug"], street_terms) > 0]
            matched.sort(key=lambda p: (_score(p["slug"], street_terms), p["date"]), reverse=True)
            posts = matched or posts  # fall back to all-recent if no street match
        if limit is not None:
            posts = posts[:limit]

        sem = asyncio.Semaphore(concurrency)

        async def _bounded(p: dict[str, Any]) -> dict[str, Any]:
            async with sem:
                return await _fetch_article(client, p)

        articles = await asyncio.gather(
            *(_bounded(p) for p in posts), return_exceptions=True
        )
    return [a for a in articles if isinstance(a, dict)]
