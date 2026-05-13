"""Shared compiled regex patterns.

Compiling once at module import is meaningfully faster than recompiling per
call, and putting them all here means a security/policy change is a one-file
diff rather than a grep.
"""

from __future__ import annotations

import re
from typing import Final


# Pragmatic email shape — paired with EMAIL_MAX_LENGTH cap upstream.
EMAIL_RE: Final[re.Pattern[str]] = re.compile(
    r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$"
)

# Honorific stripped from contact names before deriving a first name.
HONORIFIC_RE: Final[re.Pattern[str]] = re.compile(
    r"^(dr|mr|mrs|ms|miss|mx)\.?\s+", re.IGNORECASE
)

# Whitespace collapser: any run of whitespace → single space.
WHITESPACE_RUN_RE: Final[re.Pattern[str]] = re.compile(r"\s+")

# Sentence splitter. Pragmatic — does not handle abbreviations like "Dr.".
SENTENCE_SPLIT_RE: Final[re.Pattern[str]] = re.compile(r"(?<=[.!?])\s+")

# A literal word, used for word-count of a body.
WORD_RE: Final[re.Pattern[str]] = re.compile(r"\b\w+\b")

# Detects markdown JSON code fences a model might wrap output in.
JSON_FENCE_RE: Final[re.Pattern[str]] = re.compile(
    r"^```(?:json)?\s*|\s*```$", re.IGNORECASE
)

# Greedy {...} extractor for last-ditch JSON parsing.
JSON_OBJECT_RE: Final[re.Pattern[str]] = re.compile(r"\{.*\}", re.DOTALL)
