#!/usr/bin/env bash
# First-time (or stack-change) deploy. Cognito IDs are written into config.json
# on S3 automatically — no .env file.
# Usage: ./scripts/setup.sh <name>
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

NAME="${1:-}"
NAME_FILE="$ROOT/scripts/.deploy-name"

if [[ -z "$NAME" && -f "$NAME_FILE" ]]; then
  NAME="$(tr -d '[:space:]' < "$NAME_FILE")"
fi

if [[ -z "$NAME" ]]; then
  echo "Usage: ./scripts/setup.sh <name>"
  echo "  name is the CDK context value (cdk deploy -c name=...)"
  exit 1
fi

echo "$NAME" > "$NAME_FILE"
STACK="Group4ProjectStack-$NAME"

if [[ ! -d "$ROOT/.venv" ]]; then
  echo "Creating Python venv..."
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source "$ROOT/.venv/bin/activate"
pip install -q -r requirements.txt

if [[ ! -d "$ROOT/frontend/node_modules" ]]; then
  echo "Installing frontend dependencies..."
  (cd frontend && npm install)
fi

echo "Building frontend..."
(cd frontend && npm run build)

echo "Deploying stack $STACK..."
export JSII_SILENCE_WARNING_UNTESTED_NODE_VERSION=1
cdk deploy -c "name=$NAME" --require-approval never

# So local ./scripts/dev.sh works without copying IDs by hand
"$ROOT/scripts/sync-config.sh" "$NAME"

echo
echo "Done. Cognito config is on the live site as /config.json."
echo "  Local:  ./scripts/dev.sh"
echo "  Live:   (see DistributionDomainName in the deploy output above)"
