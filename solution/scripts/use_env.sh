#!/usr/bin/env bash
# Load the values from local.env into the current shell.
# Usage:  source ./scripts/use_env.sh
#
# This is meant to be SOURCED, not executed, so the exports survive in your shell.

ENV_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/local.env"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "use_env.sh: $ENV_FILE not found" >&2
  return 1 2>/dev/null || exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

if [[ -n "${GEMINI_API_KEY:-}" ]]; then
  echo "✓ GEMINI_API_KEY loaded (Gemini will be used for email drafting)"
elif [[ -n "${OPENAI_API_KEY:-}" ]]; then
  echo "✓ OPENAI_API_KEY loaded (OpenAI will be used for email drafting)"
else
  echo "⚠  No LLM key set in local.env — the template generator will be used."
fi
