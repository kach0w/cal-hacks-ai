"""Generic Socrata (SODA) client for city open-data portals (Chicago, SF, NYC, ...)."""
from __future__ import annotations

import httpx

from safestreets.config import get_settings


async def query(domain: str, dataset_id: str, where: str, limit: int = 200) -> list[dict]:
    url = f"https://{domain}/resource/{dataset_id}.json"
    headers = {}
    token = get_settings().socrata_app_token
    if token:
        headers["X-App-Token"] = token
    params = {"$where": where, "$limit": limit}
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url, params=params, headers=headers)
        resp.raise_for_status()
        return resp.json()
