"""Aggregates resident reports on the same corridor. Political will is a numbers game;
the tool does the organizing math."""
from __future__ import annotations

from safestreets.store import cache, keys


async def add_report(corridor_id: str, resident_token: str) -> int:
    try:
        return await cache.incr_set(keys.coalition_key(corridor_id), resident_token)
    except Exception:
        return 0


async def count(corridor_id: str) -> int:
    try:
        from safestreets.store.redis_client import get_redis
        return await get_redis().scard(keys.coalition_key(corridor_id))
    except Exception:
        return 0
