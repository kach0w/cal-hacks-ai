"""A candidate intervention — framed as an option to discuss with a licensed
engineer, never a verdict."""
from __future__ import annotations

from pydantic import BaseModel, Field


class Intervention(BaseModel):
    key: str                                   # "lpi", "curb_extension", ...
    name: str
    trigger: str
    cost_low: float | None = None
    cost_high: float | None = None
    cost_unit: str = "USD"                      # "USD" | "USD/year"
    evidence: str = ""
    feasibility_caveat: str = ""               # drainage, ADA, transit, right-of-way...
    funding_program_keys: list[str] = Field(default_factory=list)
    disclaimer: str = (
        "Candidate intervention. Real designs must account for drainage, utilities, "
        "ADA, transit, and right-of-way not visible in imagery. Confirm with a "
        "licensed traffic engineer."
    )
