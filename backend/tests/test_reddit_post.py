"""Tests for the Reddit post agent: city -> subreddit resolution and the post builder.

The LLM and the reverse-geocode are stubbed, so this asserts on behaviour (which subreddit,
JSON parsing, graceful fallback) rather than on a live model.
"""
from __future__ import annotations

import types

import pytest

from safestreets.lastmile import ask
from safestreets.models.analysis import RedditPost
from safestreets.models.intersection import Intersection


# --------------------------------------------------------------------------- #
# subreddit_for_city
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "city,expected",
    [
        ("Berkeley", "berkeley"),
        ("San Francisco", "sanfrancisco"),
        ("New York", "nyc"),
        ("Los Angeles", "losangeles"),
        ("St. Louis", "stlouis"),
        ("Oakland", "oakland"),
        (None, "city"),
        ("", "city"),
    ],
)
def test_subreddit_for_city(city, expected):
    assert ask.subreddit_for_city(city) == expected


# --------------------------------------------------------------------------- #
# build_reddit_post
# --------------------------------------------------------------------------- #
def _fake_anthropic(text: str):
    """A stand-in Anthropic client whose messages.create returns `text`."""
    block = types.SimpleNamespace(type="text", text=text)
    response = types.SimpleNamespace(content=[block])

    class _Messages:
        async def create(self, **kwargs):
            return response

    return types.SimpleNamespace(messages=_Messages())


def _intersection(city=None):
    return Intersection(id="x", address="Bancroft Ave & Fulton St", lat=37.87, lng=-122.27, city=city)


async def test_build_reddit_post_uses_city_subreddit_and_parses_json(monkeypatch):
    monkeypatch.setattr(
        ask, "get_anthropic", lambda: _fake_anthropic('{"title": "Almost got hit at Bancroft", "body": "Anyone else?"}')
    )
    post = await ask.build_reddit_post([], _intersection(city="Berkeley"), {"crash_data": []})

    assert isinstance(post, RedditPost)
    assert post.subreddit == "berkeley"
    assert post.title == "Almost got hit at Bancroft"
    assert post.body == "Anyone else?"


async def test_build_reddit_post_reverse_geocodes_when_city_missing(monkeypatch):
    async def reverse_city(lat, lng):
        return "Oakland"

    monkeypatch.setattr(ask.google_maps, "reverse_city", reverse_city)
    monkeypatch.setattr(ask, "get_anthropic", lambda: _fake_anthropic('{"title": "t", "body": "b"}'))

    post = await ask.build_reddit_post([], _intersection(city=None), {"crash_data": []})
    assert post.subreddit == "oakland"


async def test_build_reddit_post_falls_back_when_output_isnt_json(monkeypatch):
    monkeypatch.setattr(ask, "get_anthropic", lambda: _fake_anthropic("just some prose, no json here"))
    post = await ask.build_reddit_post([], _intersection(city="Berkeley"), {"crash_data": []})

    assert post.subreddit == "berkeley"
    assert post.body == "just some prose, no json here"
    assert "Bancroft Ave & Fulton St" in post.title  # synthesized fallback title
