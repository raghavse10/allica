"""Filesystem path discovery.

The package is run from a few different CWDs (CLI from `solution/`, tests
from anywhere, uvicorn from a deployed container, etc.). We discover the
repo root by walking up until we see the bundled `data/` folder.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final


def _find_repo_root() -> Path:
    """Walk upwards from this file until the bundled `data/` folder appears."""
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        if (parent / "data" / "companies_house_stub.json").exists():
            return parent
    # Fall back to a sensible guess so imports never crash at startup.
    return here.parents[3]


REPO_ROOT: Final[Path] = _find_repo_root()
DEFAULT_REGISTRY_PATH: Final[Path] = REPO_ROOT / "data" / "companies_house_stub.json"
DEFAULT_LEADS_PATH: Final[Path] = REPO_ROOT / "data" / "leads_small.json"
DEFAULT_EVALS_PATH: Final[Path] = REPO_ROOT / "evals" / "cases.json"
