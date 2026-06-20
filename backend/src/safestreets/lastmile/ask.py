"""Builds 'The Ask': the specific, costed request in language a city understands."""
from __future__ import annotations

from safestreets.models.finding import Finding


def build_ask(finding: Finding) -> str | None:
    iv = finding.intervention
    if not iv:
        return None
    cost = ""
    if iv.cost_low is not None:
        unit = iv.cost_unit
        cost = (
            f" Estimated ${iv.cost_low:,.0f}"
            + (f"-${iv.cost_high:,.0f}" if iv.cost_high and iv.cost_high != iv.cost_low else "")
            + f" {unit.replace('USD', '').strip() or ''}".rstrip()
        )
    return f"{iv.name} at the {finding.condition.zone.value}.{cost} {iv.evidence}".strip()
