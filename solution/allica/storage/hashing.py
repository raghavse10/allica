"""Canonical JSON + SHA-256 for POST /run idempotency."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def compute_payload_hash(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
