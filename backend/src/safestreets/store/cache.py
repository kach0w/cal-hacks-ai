"""Typed JSON get/set helpers over Redis."""
from __future__ import annotations

import json
from typing import Any

from safestreets.store.redis_client import get_redis


async def get_json(key: str) -> Any | None:
    raw = await get_redis().get(key)
    return json.loads(raw) if raw else None


async def set_json(key: str, value: Any, ttl: int | None = None) -> None:
    raw = json.dumps(value, default=str)
    if ttl:
        await get_redis().set(key, raw, ex=ttl)
    else:
        await get_redis().set(key, raw)


async def incr_set(key: str, member: str) -> int:
    """Add member to a set, return new cardinality (used for coalition counts)."""
    r = get_redis()
    await r.sadd(key, member)
    return await r.scard(key)
