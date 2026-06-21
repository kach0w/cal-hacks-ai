"""Builds the social media post, the local-subreddit Reddit post, and the council report"""
from __future__ import annotations
import json
import re
from typing import Any

from safestreets.clients import google_maps
from safestreets.clients.anthropic_client import get_anthropic
from safestreets.config import get_settings
from safestreets.models.analysis import RedditPost
from safestreets.models.finding import Finding, FindingStatus
from safestreets.models.intersection import Intersection

# Cities whose subreddit isn't just the slugified name. Everything else slugifies
# (e.g. 'Berkeley' -> r/berkeley); this map fixes the well-known exceptions.
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
    """Map a city name to its local subreddit name (bare, no 'r/')."""
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


_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


async def build_reddit_post(
    findings: list[Finding],
    intersection: Intersection,
    community_data: dict[str, Any],
) -> RedditPost:
    """A post for the city's local subreddit, written like a real fed-up neighbor — not a PSA.

    The subreddit is chosen from the street's actual city (reverse-geocoded when the
    intersection didn't carry one), so the post lands in the community that can act on it.
    """
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
- NO hashtags. NO emoji spam (one is fine, none is better). NO em-dashes. NO corporate or AI-sounding phrasing like "moreover", "furthermore", "in conclusion", "as a concerned resident", "let's work together".
- Keep the title short and natural, like a real Reddit title (no clickbait, no ALL CAPS).
- Body 80-160 words.

Return ONLY a JSON object: {{"title": "...", "body": "..."}} with the body as a single string (use \\n\\n between paragraphs if needed)."""

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
