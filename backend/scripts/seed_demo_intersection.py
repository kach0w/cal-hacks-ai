"""Preload the demo intersection so the live demo is reliable.

Stores a known Intersection + curated community data in Redis so the team can demo
without depending on live scrapes succeeding on stage. Swap in your chosen FARS case.
"""
from __future__ import annotations

import asyncio

from safestreets.agents.image_fetcher import fetch_images
from safestreets.models.intersection import Intersection
from safestreets.store import cache, keys

# Example anchor: International Blvd & 35th Ave, Oakland (replace with your FARS pick)
DEMO_LAT = 37.7706
DEMO_LNG = -122.2215


async def main() -> None:
    images = await fetch_images(DEMO_LAT, DEMO_LNG)
    intersection = Intersection(
        id="oakland-international-35th",
        address="International Blvd & 35th Ave, Oakland, CA",
        lat=DEMO_LAT,
        lng=DEMO_LNG,
        city="Oakland",
        images=images,
    )
    await cache.set_json(
        keys.intersection_key(DEMO_LAT, DEMO_LNG),
        intersection.model_dump(),
        ttl=keys.VISION_TTL,
    )
    # TODO: also seed curated crash/311/news/council data under keys.scrape_key(...)
    print(f"seeded {intersection.id} with {len(images)} images")


if __name__ == "__main__":
    asyncio.run(main())
