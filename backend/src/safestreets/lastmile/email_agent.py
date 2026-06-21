"""Email agent: drafts a human, professional email to the council member(s) for an
intersection and packages it as a ready-to-send `.eml` with the council letter PDF
attached.

The agent (Claude) is prompted to sound like a real constituent — raising the concrete
safety concerns, citing the relevant statistics, and ending on a clear call to action —
and to write a proper subject line. We deliver an `.eml` (not a mailto link) because mailto
cannot carry an attachment; the user opens the `.eml` in their own mail client, reviews,
and sends it from their own address with the PDF already attached.
"""
from __future__ import annotations

import json
import re
from email.message import EmailMessage
from email.utils import formatdate
from typing import Any

from pydantic import BaseModel

from safestreets.clients.anthropic_client import get_anthropic
from safestreets.config import get_settings
from safestreets.lastmile.ask import _crash_summary, _findings_summary
from safestreets.models.council import CouncilContact
from safestreets.models.finding import Finding, FindingStatus
from safestreets.models.intersection import Intersection


class EmailDraft(BaseModel):
    subject: str
    body: str
    recipients: list[CouncilContact]


def _stats_summary(community_data: dict[str, Any]) -> str:
    """Hard numbers the email can cite: crashes + open 311 cases."""
    parts = [_crash_summary(community_data)]
    complaints = community_data.get("complaints_311", [])
    if complaints:
        open_n = sum(1 for c in complaints if (c.get("status") or "").lower() not in ("closed", "resolved"))
        parts.append(f"{len(complaints)} city 311 service requests on file ({open_n} not closed)")
    return "; ".join(parts)


def _greeting_names(contacts: list[CouncilContact]) -> str:
    names = [c.name for c in contacts if c.name and c.name not in ("City Council",)]
    return ", ".join(names) if names else "Councilmembers"


_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


def _parse_email(text: str, fallback_subject: str) -> tuple[str, str]:
    """Pull {subject, body} out of the model output, tolerating prose around the JSON."""
    m = _JSON_RE.search(text)
    if m:
        try:
            data = json.loads(m.group(0))
            subject = str(data.get("subject") or "").strip()
            body = str(data.get("body") or "").strip()
            if subject and body:
                return subject, body
        except json.JSONDecodeError:
            pass
    # No usable JSON — treat the whole thing as the body.
    return fallback_subject, text.strip()


async def build_council_email(
    findings: list[Finding],
    intersection: Intersection,
    community_data: dict[str, Any],
    contacts: list[CouncilContact],
) -> EmailDraft:
    client = get_anthropic()
    settings = get_settings()

    confirmed = [f for f in findings if f.status == FindingStatus.CONFIRMED]
    district = next((c.district for c in contacts if c.district), None)
    district_note = f" (Council District {district})" if district else ""

    prompt = f"""You are writing a short email from a concerned resident to their city council member about a dangerous intersection. It must read like a real person wrote it — warm, direct, specific. NOT a form letter and NOT AI-sounding.

Addressed to: {_greeting_names(contacts)}{district_note}
Intersection: {intersection.address}
Key statistics to weave in (use the real numbers, don't invent any): {_stats_summary(community_data)}
Top confirmed safety problems and the recommended fixes:
{_findings_summary(confirmed or findings[:3])}

Write the email so it:
- Opens by naming the intersection and why the writer is worried (the human stake first).
- Cites the relevant statistics naturally in a sentence or two — not as a bulleted dump.
- Names one or two concrete, fundable fixes.
- Ends with a clear call to action (e.g. requesting it be placed on a committee agenda, a site visit, or a written response).
- Mentions that a detailed safety report is attached as a PDF.
- Is 150-250 words, plain prose, no markdown, no bullet characters.
- Signs off as "A concerned Berkeley resident" (no fake name).

Also write a specific, non-clickbait subject line naming the intersection.

Return ONLY a JSON object: {{"subject": "...", "body": "..."}} with the body as a single string using \\n\\n between paragraphs."""

    resp = await client.messages.create(
        model=settings.claude_text_model,
        max_tokens=900,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(b.text for b in resp.content if b.type == "text").strip()
    subject, body = _parse_email(text, fallback_subject=f"Pedestrian safety at {intersection.address}")
    return EmailDraft(subject=subject, body=body, recipients=contacts)


def pdf_filename(intersection: Intersection) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", intersection.address.lower()).strip("-")[:48] or "intersection"
    return f"SafeStreets-{slug}.pdf"


def build_eml(draft: EmailDraft, pdf_bytes: bytes, pdf_name: str) -> str:
    """Assemble a standards-compliant .eml with the PDF attached, as a string."""
    msg = EmailMessage()
    msg["To"] = ", ".join(c.email for c in draft.recipients)
    msg["Subject"] = draft.subject
    msg["Date"] = formatdate(localtime=True)
    msg.set_content(draft.body)
    msg.add_attachment(pdf_bytes, maintype="application", subtype="pdf", filename=pdf_name)
    return msg.as_string()
