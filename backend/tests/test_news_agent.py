"""Offline tests for the local-news crash-coverage agent.

The agent's job: read the Berkeley Scanner sitemap, keep only in-scope traffic
posts, and pull each article's title/date/excerpt from its meta tags. All HTTP
is served by the ``http_router`` mock, so these run with no network.
"""
from __future__ import annotations

import httpx
import pytest

from safestreets.agents import news_agent

_SITEMAP = "sitemap-posts.xml"


# --------------------------------------------------------------------------- #
# pure logic
# --------------------------------------------------------------------------- #
def test_score_counts_whole_word_street_matches():
    assert news_agent._score("berkeley-crash-hearst-grant", ["hearst", "grant"]) == 2
    assert news_agent._score("berkeley-crash-hearst-grant", ["hearst"]) == 1


def test_score_is_whole_word_not_substring():
    # 'king' (from MLK Way) must not match 'walking' / 'parking'
    assert news_agent._score("man-walking-near-parking-lot", ["king"]) == 0


# --------------------------------------------------------------------------- #
# fetch_news — discovery + extraction
# --------------------------------------------------------------------------- #
async def test_fetch_news_keeps_only_articles_naming_the_cross_streets(http_router, fixture):
    http_router.text(_SITEMAP, fixture("scanner_sitemap.xml"))
    http_router.text("hearst-grant", fixture("scanner_article.html"))

    results = await news_agent.fetch_news(37.87, -122.27, "Berkeley", street_terms=["hearst", "grant"])

    assert len(results) == 1
    article = results[0]
    assert article["title"] == "Pedestrian injured in Hearst and Grant crash"
    assert article["date"] == "2024-05-10"            # normalized from the ISO timestamp
    assert article["source"] == "berkeleyscanner.com"
    assert "hearst-grant" in article["url"]


async def test_fetch_news_ignores_non_traffic_and_out_of_range_posts(http_router, fixture):
    http_router.text(_SITEMAP, fixture("scanner_sitemap.xml"))
    http_router.text("hearst-grant", fixture("scanner_article.html"))
    http_router.text("university-injured", fixture("scanner_article.html"))
    http_router.text("shattuck-broken", fixture("scanner_article.html"))

    await news_agent.fetch_news(37.87, -122.27, "Berkeley")  # no streets -> recent fallback

    fetched = [u for u in http_router.requested if _SITEMAP not in u]
    # the crime post and the pre-2023 post are filtered before any article fetch
    assert not any("/crime/" in u for u in fetched)
    assert not any("/2022/" in u for u in fetched)


async def test_fetch_news_survives_a_single_failed_article(http_router, fixture):
    http_router.text(_SITEMAP, fixture("scanner_sitemap.xml"))
    http_router.text("hearst-grant", fixture("scanner_article.html"))
    http_router.text("university-injured", fixture("scanner_article.html"))
    http_router.text("shattuck-broken", "boom", status=500)  # one article 500s

    results = await news_agent.fetch_news(37.87, -122.27, "Berkeley")

    # the failing article is dropped, the rest still come back — no exception
    assert len(results) == 2
    assert all("shattuck-broken" not in a["url"] for a in results)


async def test_fetch_article_falls_back_to_slug_when_meta_missing(http_router, fixture):
    http_router.text("some-slug", fixture("article_malformed.html"))
    post = {
        "url": "https://www.berkeleyscanner.com/2024/05/10/traffic-safety/some-slug/",
        "date": "2024-05-10",
        "slug": "some-slug",
    }

    async with httpx.AsyncClient() as client:
        article = await news_agent._fetch_article(client, post)

    assert article["title"] == "some-slug"   # og:title absent -> slug
    assert article["date"] == "2024-05-10"   # published_time absent -> post date
    assert article["excerpt"] == ""          # description absent -> empty
