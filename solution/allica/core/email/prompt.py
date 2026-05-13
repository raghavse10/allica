"""LLM prompt + response parsing.

Kept provider-agnostic so the same prompt and parser are reused by every
LLM backend.
"""

from __future__ import annotations

import json

from ..constants import LLM_MAX_RAW_NOTES_CHARS
from ..patterns import JSON_FENCE_RE, JSON_OBJECT_RE
from ..schemas import InboundLead
from .context import EmailContext


SYSTEM_PROMPT = """You are a UK SME lending GTM assistant for Allica.

Write a single first-touch email. Hard constraints:
- Total length 110–170 words in the BODY (not counting subject).
- Tone: pragmatic, respectful, jargon-light.
- Personalise with the contact's first name and reference one specific piece
  of enrichment context (sector, age, or stated need).
- Exactly ONE clear call to action: propose a short 20-minute call.
- Do NOT promise guaranteed approval.
- Do NOT state any approval timeline in hours or days.
- Do NOT invent specific interest rates, fees or terms.
- Do NOT claim "lowest" or "best" anything.
- If you reference rates / pricing / terms, end the body with exactly:
  "Subject to status and credit checks. Terms apply."

Return STRICTLY a JSON object with two string fields: "subject" and "body".
No markdown, no extra commentary.
"""


def build_user_payload(ctx: EmailContext, lead: InboundLead) -> str:
    """Build the user-message JSON payload sent to the LLM."""
    return "Lead context (JSON):\n" + json.dumps(
        {
            "company_name": ctx.company_name,
            "contact_first_name": ctx.contact_first_name,
            "sector": ctx.sector or "unknown",
            "inferred_need": ctx.inferred_need,
            "incorporated_on": ctx.incorporated_on or "unknown",
            "raw_notes": (lead.notes or "")[:LLM_MAX_RAW_NOTES_CHARS],
        }
    )


def parse_subject_body(raw: str) -> tuple[str, str] | None:
    """Tolerant parser — accepts plain JSON, fenced JSON, or JSON inside prose."""
    if not raw:
        return None
    text = raw.strip()
    if text.startswith("```"):
        text = JSON_FENCE_RE.sub("", text)
    parsed: dict | None = None
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        match = JSON_OBJECT_RE.search(text)
        if match:
            try:
                parsed = json.loads(match.group(0))
            except json.JSONDecodeError:
                parsed = None
    if not isinstance(parsed, dict):
        return None
    subject = str(parsed.get("subject", "")).strip()
    body = str(parsed.get("body", "")).strip()
    if not subject or not body:
        return None
    return subject, body
