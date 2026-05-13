"""Salted SHA-256 for email/notes; short sanitised notes excerpt for UI only."""

from __future__ import annotations

import hashlib
import re

from .config import db_settings


_MAX_EXCERPT_CHARS = 80


def hash_pii(value: str | None) -> str | None:
    """Return a deterministic, salted SHA-256 hex digest for `value`."""
    if not value:
        return None
    salt = db_settings().pii_salt
    digest = hashlib.sha256(f"{salt}::{value.strip().lower()}".encode("utf-8"))
    return digest.hexdigest()


def excerpt_notes(notes: str | None) -> str | None:
    """Return a single-line, length-capped excerpt of `notes` for display."""
    if not notes:
        return None
    flat = re.sub(r"\s+", " ", notes).strip()
    if len(flat) <= _MAX_EXCERPT_CHARS:
        return flat
    return flat[: _MAX_EXCERPT_CHARS - 1].rstrip() + "…"
