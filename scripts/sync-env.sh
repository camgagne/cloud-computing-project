#!/usr/bin/env bash
# Deprecated: Cognito config is now frontend/public/config.json (no .env).
exec "$(cd "$(dirname "$0")" && pwd)/sync-config.sh" "$@"
