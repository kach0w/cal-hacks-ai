"""Builds the social media post, the local-subreddit Reddit post, and the council report"""
from __future__ import annotations
import json
import re
from datetime import date
from typing import Any

from safestreets.clients import google_maps
from safestreets.clients.anthropic_client import call_with_backoff, get_anthropic
from safestreets.config import get_settings
from safestreets.models.analysis import RedditPost
from safestreets.models.finding import Finding, FindingStatus
from safestreets.models.intersection import Intersection

_CITY_SUBREDDITS = {
    "new york": "nyc",
    "new york city": "nyc",
    "san francisco": "sanfrancisco",
    "los angeles": "losangeles",
    "san jose": "sanjose",
    "san diego": "sandiego",
    "washington": "washingtondc",
    "washington dc": "washingtondc",
    "new orleans": "neworleans",
    "las vegas": "vegas",
    "salt lake city": "saltlakecity",
}


def subreddit_for_city(city: str | None) -> str:
    key = (city or "").strip().lower()
    if key in _CITY_SUBREDDITS:
        return _CITY_SUBREDDITS[key]
    slug = re.sub(r"[^a-z0-9]", "", key)
    return slug or "city"


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
    """Single Claude call returning (social_post, council_report)."""
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
- To: City Council Transportation Committee, City of {intersection.city or "the City"}
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


_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


async def build_reddit_post(
    findings: list[Finding],
    intersection: Intersection,
    community_data: dict[str, Any],
) -> RedditPost:
    client = get_anthropic()
    settings = get_settings()

    city = intersection.city or await google_maps.reverse_city(intersection.lat, intersection.lng) or settings.demo_city
    subreddit = subreddit_for_city(city)
    confirmed = [f for f in findings if f.status == FindingStatus.CONFIRMED]

    prompt = f"""Write a Reddit post for r/{subreddit} from a real person who lives in {city} and is worried about a dangerous intersection in their neighborhood. It should read like an actual frustrated/concerned local typed it out — NOT a press release, NOT a PSA, NOT marketing.

Intersection: {intersection.address}
Crash record: {_crash_summary(community_data)}
What's wrong and the fixes that would help:
{_findings_summary(confirmed or findings[:2])}

Voice and style rules:
- First person, casual, the way people actually post on a city subreddit. Contractions, plain words.
- Open with a real human hook (e.g. "Does anyone else avoid...", "I almost got hit at...", "Am I crazy or is ... a death trap").
- Mention the specific intersection and one or two concrete problems. You can cite the crash number once, naturally, but don't dump statistics.
- Ask the community if others have noticed / had close calls, and mention you're thinking of contacting the city or council.
- NO hashtags. NO emoji spam (one is fine, none is better). NO em-dashes. NO corporate or AI-sounding phrasing.
- Keep the title short and natural. Body 80-160 words.

Return ONLY a JSON object: {{"title": "...", "body": "..."}}"""

    resp = await client.messages.create(
        model=settings.claude_text_model,
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(b.text for b in resp.content if b.type == "text").strip()

    title = f"Is {intersection.address} as dangerous as it feels?"
    body = text
    m = _JSON_RE.search(text)
    if m:
        try:
            data = json.loads(m.group(0))
            title = str(data.get("title") or title).strip()
            body = str(data.get("body") or text).strip()
        except json.JSONDecodeError:
            pass

    return RedditPost(subreddit=subreddit, title=title, body=body)
