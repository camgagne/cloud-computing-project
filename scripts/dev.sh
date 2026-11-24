#!/usr/bin/env bash
# Daily local run: refresh config.json from the stack, then start Vite.
# Usage: ./scripts/dev.sh [name]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

NAME="${1:-}"
NAME_FILE="$ROOT/scripts/.deploy-name"

if [[ -z "$NAME" && -f "$NAME_FILE" ]]; then
  NAME="$(tr -d '[:space:]' < "$NAME_FILE")"
fi

CONFIG="$ROOT/frontend/public/config.json"

if [[ ! -f "$CONFIG" ]]; then
  if [[ -z "$NAME" ]]; then
    echo "No config.json yet. Run ./scripts/setup.sh <name> once first."
    exit 1
  fi
  "$ROOT/scripts/sync-config.sh" "$NAME"
elif [[ -n "$NAME" ]]; then
  "$ROOT/scripts/sync-config.sh" "$NAME" || true
fi

if [[ ! -d "$ROOT/frontend/node_modules" ]]; then
  (cd frontend && npm install)
fi

cd frontend
exec npm run dev
