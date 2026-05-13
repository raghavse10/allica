"""Rewrite banned phrases in subject/body; append disclaimer when terms appear."""

from __future__ import annotations

import re

from ..schemas import SafetyFlag
from .rules import BANNED_RULES, REQUIRED_DISCLAIMER, TERMS_TRIGGER_RE


def _apply_banned_rules(text: str, flags: list[SafetyFlag]) -> str:
    for rule in BANNED_RULES:
        if rule.pattern.search(text):
            flags.append(
                SafetyFlag(code=rule.code, severity=rule.severity, message=rule.message)
            )
            text = rule.pattern.sub(rule.replacement, text)
    return text


def _ensure_disclaimer(body: str, flags: list[SafetyFlag]) -> tuple[str, bool]:
    if REQUIRED_DISCLAIMER in body:
        return body, True
    if not TERMS_TRIGGER_RE.search(body):
        return body, False
    body = body.rstrip() + "\n\n" + REQUIRED_DISCLAIMER
    flags.append(
        SafetyFlag(
            code="disclaimer_appended",
            severity="info",
            message="Appended required pricing/terms disclaimer.",
        )
    )
    return body, True


def _tidy(text: str, *, single_line: bool) -> str:
    if single_line:
        return re.sub(r"\s{2,}", " ", text).strip()
    return re.sub(r"[ \t]{2,}", " ", text)


def sanitise_email(
    subject: str, body: str
) -> tuple[str, str, list[SafetyFlag], bool]:
    """Sanitise the email and return `(subject, body, flags, used_disclaimer)`."""
    flags: list[SafetyFlag] = []
    subject = _apply_banned_rules(subject, flags)
    body = _apply_banned_rules(body, flags)
    body, used_disclaimer = _ensure_disclaimer(body, flags)
    return _tidy(subject, single_line=True), _tidy(body, single_line=False), flags, used_disclaimer
