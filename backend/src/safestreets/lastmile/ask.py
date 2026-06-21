"""Builds the social media post and the formal council report"""
from __future__ import annotations
import json
from typing import Any

from safestreets.clients.anthropic_client import get_anthropic
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


async def build_social_post(
    findings: list[Finding],
    intersection: Intersection,
    community_data: dict[str, Any],
) -> str:
    confirmed = [f for f in findings if f.status == FindingStatus.CONFIRMED]
    client = get_anthropic()
    settings = get_settings()

    prompt = f"""Write a short, urgent social media post (Twitter/Instagram length, under 280 characters if possible, max 400)
advocating for safety fixes at this intersection. Make it human, specific, and actionable — not generic.

Intersection: {intersection.address}
Crash record: {_crash_summary(community_data)}
Top confirmed problems and fixes:
{_findings_summary(confirmed or findings[:2])}
Council record: {json.dumps(community_data.get("council", []), default=str)}

Rules:
- Lead with the human cost, not the statistics
- Name the specific fix and its cost
- End with a call to action (contact city, attend meeting, share)
- No hashtag spam — at most 2 relevant hashtags
- No AI-sounding language"""

    resp = await client.messages.create(
        model=settings.claude_text_model,
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in resp.content if b.type == "text").strip()


async def build_council_report(
    findings: list[Finding],
    intersection: Intersection,
    community_data: dict[str, Any],
) -> str:
    client = get_anthropic()
    settings = get_settings()

    council_records = community_data.get("council", [])
    accountability_note = (
        f"This corridor was raised in council minutes on {council_records[0]['date']} with no recorded action."
        if council_records else "No prior council record found."
    )

    from datetime import date
    today = date.today().strftime("%B %d, %Y")

    prompt = f"""Write a formal letter to submit to a city council transportation committee requesting pedestrian safety improvements. Format it exactly as a real letter — no markdown, no headers with pound signs, no bullet asterisks. Use plain prose paragraphs with blank lines between them.

The letter structure should be:
- Date line: {today}
- Blank line
- To: City Council Transportation Committee, City of Berkeley
- From: SafeStreets Community Safety Initiative
- Re: Pedestrian Safety Hazards at {intersection.address}
- Blank line
- Opening paragraph: purpose of the letter and urgency
- Body paragraphs: one per finding, describing the observed condition, the evidence or data supporting it, and the recommended intervention with estimated cost and applicable funding program (SS4A, HSIP, or capital work order)
- Crash record paragraph: {_crash_summary(community_data)}
- Prior notice paragraph: {accountability_note}
- Closing paragraph: specific numbered requests (written out as "First, ... Second, ... Third, ...")
- Sign-off: Respectfully submitted, SafeStreets Safety Analysis System

Intersection: {intersection.address}
Findings:
{_findings_summary(findings)}

Write only the letter text. No markdown formatting whatsoever. No asterisks, no pound signs, no dashes as bullets. Plain text letter."""

    resp = await client.messages.create(
        model=settings.claude_text_model,
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in resp.content if b.type == "text").strip()
