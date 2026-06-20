"""The durable record: was this corridor raised, and did anything happen?
Turns a buried line in council minutes into a citable, shareable fact."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class ActionStatus(str, Enum):
    NO_ACTION_RECORDED = "no_action_recorded"
    ACTION_RECORDED = "action_recorded"
    UNKNOWN = "unknown"


class AccountabilityEvent(BaseModel):
    intersection_id: str
    date: str                       # when the corridor was raised
    source: str                     # "council_minutes" | "311" | "safestreets_submission"
    summary: str
    action_status: ActionStatus = ActionStatus.UNKNOWN
