"""Loads the intervention and funding-program libraries from JSON."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from safestreets.models.funding import FundingProgram
from safestreets.models.intervention import Intervention

_DATA = Path(__file__).parent / "data"


@lru_cache
def interventions() -> dict[str, Intervention]:
    rows = json.loads((_DATA / "interventions.json").read_text())
    return {r["key"]: Intervention(**r) for r in rows}


@lru_cache
def funding_programs() -> dict[str, FundingProgram]:
    rows = json.loads((_DATA / "funding_programs.json").read_text())
    return {r["key"]: FundingProgram(**r) for r in rows}
