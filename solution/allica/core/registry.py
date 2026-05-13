"""Companies House registry adapter.

In production this would be a real HTTP client with caching, retries and
rate-limiting. For this exercise it is a thin wrapper around a JSON file,
designed so the *interface* is what callers depend on — not the storage.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


class CompaniesHouseStub:
    """In-memory registry. Lookups are case-insensitive on company name."""

    def __init__(self, data: dict[str, dict]) -> None:
        self._by_name = {self._norm(name): record for name, record in data.items()}

    @classmethod
    def from_path(cls, path: str | Path) -> "CompaniesHouseStub":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    @staticmethod
    def _norm(name: str | None) -> str:
        return (name or "").strip().lower()

    def lookup(self, company_name: str | None) -> Optional[dict]:
        return self._by_name.get(self._norm(company_name))
