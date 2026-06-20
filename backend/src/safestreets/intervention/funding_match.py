"""Maps an intervention to the funding programs that could pay for it."""
from __future__ import annotations

from safestreets.intervention.library import funding_programs
from safestreets.models.funding import FundingProgram
from safestreets.models.intervention import Intervention


def programs_for(intervention: Intervention) -> list[FundingProgram]:
    catalog = funding_programs()
    return [catalog[k] for k in intervention.funding_program_keys if k in catalog]
