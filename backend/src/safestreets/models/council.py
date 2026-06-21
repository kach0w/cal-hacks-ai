"""A city council member resolved for an intersection's jurisdiction."""
from __future__ import annotations

from pydantic import BaseModel


class CouncilContact(BaseModel):
    name: str                      # "Councilmember, District 4" when no name is published
    email: str
    district: str | None = None    # district number/label the intersection falls in
    role: str = "Councilmember"
    source: str = "socrata"        # "socrata" | "config" | "general_inbox"
