"""The durable record: when was this corridor raised, and did anything happen?
Turns 'mentioned twice, no action' from a buried PDF line into a citable fact."""
from __future__ import annotations

from typing import Any

from safestreets.models.accountability import AccountabilityEvent, ActionStatus
from safestreets.store import cache, keys


async def build_log(intersection_id: str, community_data: dict[str, Any]) -> list[AccountabilityEvent]:
    """Derives events from council mentions + 311 history; persists them (no TTL).
    TODO: detect whether a later record shows action taken to set ActionStatus."""
    events: list[AccountabilityEvent] = []
    for c in community_data.get("council", []):
        events.append(
            AccountabilityEvent(
                intersection_id=intersection_id,
                date=c.get("date", "unknown"),
                source="council_minutes",
                summary=c.get("summary", "corridor referenced in council minutes"),
                action_status=ActionStatus.NO_ACTION_RECORDED,
            )
        )
    if events:
        await cache.set_json(keys.accountability_key(intersection_id), [e.model_dump() for e in events])
    return events
