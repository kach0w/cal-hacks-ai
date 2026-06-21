"""Builds the social media post and the formal council report in a single Claude call."""
from __future__ import annotations
import json
from datetime import date
from typing import Any

from safestreets.clients.anthropic_client import get_anthropic, call_with_backoff
from safestreets.config import get_settings
from safestreets.models.finding import Finding, FindingStatus
from safestreets.models.intersection import Intersection


def _findings_summary(findings: list[Finding]) -> str:
    lines = []
    for i, f in enumerate(findings, 1):
        iv = f.intervention
        cost = f"${iv.cost_low:,}–${iv.cost_high:,} {iv.cost_unit}" if iv else "cost unknown"
        sources = "; ".join(f"{c.source} ({c.date}): {c.excerpt or c.reference}" for c in f.corroboration)
        lines.append(
            f"{i}. [{f.status.value}] {f.condition.zone.value} — {f.condition.observation}\n"
            f"   Fix: {iv.name if iv else 'unknown'} — {cost}\n"
            f"   Evidence: {iv.evidence if iv else ''}\n"
            f"   Corroborated by: {sources or 'none'}"
        )
    return "\n".join(lines)


def _crash_summary(community_data: dict[str, Any]) -> str:
    crashes = community_data.get("crash_data", [])
    total = len(crashes)
    ped = sum(1 for c in crashes if c.get("type") == "pedestrian")
    years = sorted({c["year"] for c in crashes if "year" in c})
    year_range = f"{years[0]}–{years[-1]}" if len(years) > 1 else str(years[0]) if years else "unknown"
    return f"{total} crashes ({ped} pedestrian) recorded {year_range}"


async def build_lastmile(
    findings: list[Finding],
    intersection: Intersection,
    community_data: dict[str, Any],
) -> tuple[str, str]:
    """Single Claude call that returns (social_post, council_report)."""
    client = get_anthropic()
    settings = get_settings()

    confirmed = [f for f in findings if f.status == FindingStatus.CONFIRMED]
    council_records = community_data.get("council", [])
    accountability_note = (
        f"This corridor was raised in council minutes on {council_records[0]['date']} with no recorded action."
        if council_records else "No prior council record found."
    )
    today = date.today().strftime("%B %d, %Y")

    prompt = f"""You must produce TWO outputs for a street safety analysis. Return them as a JSON object with keys "social_post" and "council_report". No other text.

INTERSECTION: {intersection.address}
CRASH RECORD: {_crash_summary(community_data)}
FINDINGS:
{_findings_summary(confirmed or findings[:3])}
COUNCIL: {accountability_note}

=== OUTPUT 1: social_post ===
A short, urgent social media post (under 280 chars, max 400). Human, specific, actionable.
Tone: concerned and hopeful, not violent or accusatory. At most 2 hashtags at the end.
Rules: lead with human cost; name the specific fix and cost; end with a call to action; no AI-sounding language.

=== OUTPUT 2: council_report ===
A formal letter to the city council transportation committee. Plain text only — no markdown, no asterisks, no pound signs.
Structure:
- Date: {today}
- To: City Council Transportation Committee, City of Berkeley
- From: SafeStreets Community Safety Initiative
- Re: Pedestrian Safety Hazards at {intersection.address}
- Opening paragraph stating purpose and urgency
- One body paragraph per finding with condition, evidence, recommended intervention and cost
- Crash record paragraph
- Prior notice paragraph: {accountability_note}
- Closing with numbered requests ("First, ... Second, ... Third, ...")
- Sign-off: Respectfully submitted, SafeStreets Safety Analysis System
Tone: professional, concerned, solution-oriented. No violent or accusatory language.

Return ONLY valid JSON: {{"social_post": "...", "council_report": "..."}}"""

    resp = await call_with_backoff(lambda: client.messages.create(
        model=settings.claude_text_model,
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    ))
    text = "".join(b.text for b in resp.content if b.type == "text").strip()

    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        data = json.loads(text[start:end])
        return data.get("social_post", ""), data.get("council_report", "")
    except Exception:
        return text, ""


# Keep old names as thin wrappers so nothing else breaks
async def build_social_post(findings, intersection, community_data) -> str:
    post, _ = await build_lastmile(findings, intersection, community_data)
    return post


async def build_council_report(findings, intersection, community_data) -> str:
    _, report = await build_lastmile(findings, intersection, community_data)
    return report
