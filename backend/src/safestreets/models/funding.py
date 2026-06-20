"""A funding mechanism a fix could be paid for with. who_applies matters: for SS4A
it's the city, not the resident — so the actionable ask is 'is our corridor in the
city's Action Plan', which is a far sharper lever."""
from __future__ import annotations

from pydantic import BaseModel


class FundingProgram(BaseModel):
    key: str
    name: str
    administrator: str
    who_applies: str                 # "local government" | "n/a (work order)" | ...
    applies_to: str                  # plain-language scope
    note: str = ""
    url: str = ""
