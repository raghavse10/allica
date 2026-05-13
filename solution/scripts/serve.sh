#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
exec uvicorn allica.api.app:app --reload --port "${PORT:-8000}"
