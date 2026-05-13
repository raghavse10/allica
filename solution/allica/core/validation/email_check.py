"""Email-shape validation."""

from __future__ import annotations

from ..constants import EMAIL_MAX_LENGTH
from ..patterns import EMAIL_RE


def is_valid_email(email: str | None) -> bool:
    """Return True if `email` looks like a deliverable email address.

    Pragmatic check (not full RFC 5322) — paired with a length cap to stop
    pathological inputs.
    """
    if not email or len(email) > EMAIL_MAX_LENGTH:
        return False
    return bool(EMAIL_RE.match(email.strip()))
