"""Estimate the number of call-to-action sentences in an email body."""

from __future__ import annotations

import re
from typing import Final

from ..patterns import SENTENCE_SPLIT_RE


_CTA_PHRASES: Final[tuple[str, ...]] = (
    r"\bbook a (?:short )?call\b",
    r"\bschedule a call\b",
    r"\breply (?:to|with)\b",
    r"\blet me know\b",
    r"\bget in touch\b",
    r"\bset up a (?:quick )?(?:call|chat|conversation)\b",
    r"\bare you (?:free|available)\b",
    r"\bhappy to (?:walk|jump|chat|share)\b",
    # "Would a short call ... work" / "Would next week work"
    r"\bwould\b[^.?!]*\bwork (?:for you)?\b",
    r"\bcall\b[^.?!]*\?",
)

_CTA_RE: Final[re.Pattern[str]] = re.compile("|".join(_CTA_PHRASES), re.IGNORECASE)


def count_ctas(body: str) -> int:
    sentences = SENTENCE_SPLIT_RE.split(body)
    return sum(1 for s in sentences if _CTA_RE.search(s))
