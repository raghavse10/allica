"""Score → band conversion (sourced from docs/gtm_playbook.md)."""

from __future__ import annotations

from ..constants import SCORE_BAND_HIGH_MIN, SCORE_BAND_MEDIUM_MIN


def band_for_score(value: float) -> str:
    if value > SCORE_BAND_HIGH_MIN:
        return "high"
    if value >= SCORE_BAND_MEDIUM_MIN:
        return "medium"
    return "low"
