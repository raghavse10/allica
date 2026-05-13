"""Text normalisation helpers.

Pure functions only. No I/O, no logging, no domain knowledge — just string
shaping that several pipeline stages need.
"""

from __future__ import annotations

from urllib.parse import urlparse

from .constants import DEFAULT_GREETING
from .patterns import HONORIFIC_RE, WHITESPACE_RUN_RE, WORD_RE


def normalise_text(value: str | None) -> str:
    """Return a lowercased, whitespace-collapsed copy of `value`."""
    if not value:
        return ""
    return WHITESPACE_RUN_RE.sub(" ", value).strip().lower()


def normalise_host(url: str | None) -> str:
    """Return the lowercased host of `url`, sans `www.` prefix.

    Returns "" for missing or unparseable URLs. Adds an implicit `http://`
    scheme so bare domains parse correctly.
    """
    if not url:
        return ""
    candidate = url.strip()
    if "://" not in candidate:
        candidate = "http://" + candidate
    try:
        host = urlparse(candidate).hostname or ""
    except ValueError:
        return ""
    return host.lower().lstrip("www.")


def derive_first_name(contact: str | None) -> str:
    """Return the contact's first name (or a safe fallback greeting word)."""
    if not contact:
        return DEFAULT_GREETING
    cleaned = HONORIFIC_RE.sub("", contact.strip())
    return cleaned.split()[0] if cleaned else DEFAULT_GREETING


def count_words(text: str) -> int:
    """Simple word-count using a `\\b\\w+\\b` regex."""
    return len(WORD_RE.findall(text))
