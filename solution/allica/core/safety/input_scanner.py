"""Flag risky wording in prospect notes (informational; no rewriting)."""

from __future__ import annotations

from ..schemas import SafetyFlag
from .rules import BANNED_RULES


def scan_input_for_risk(notes: str | None) -> list[SafetyFlag]:
    if not notes:
        return []
    flags: list[SafetyFlag] = []
    for rule in BANNED_RULES:
        if rule.pattern.search(notes):
            flags.append(
                SafetyFlag(
                    code=f"prospect_{rule.code}",
                    severity="warning",
                    message=(
                        f"Prospect used phrase matching /{rule.pattern.pattern}/ — "
                        "ensure response does not echo or accept that framing."
                    ),
                )
            )
    return flags
