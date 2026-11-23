#!/usr/bin/env bash
# Pull Cognito outputs into frontend/public/config.json for local Vite.
# Usage: ./scripts/sync-config.sh [name]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

NAME="${1:-}"
NAME_FILE="$ROOT/scripts/.deploy-name"

if [[ -z "$NAME" && -f "$NAME_FILE" ]]; then
  NAME="$(tr -d '[:space:]' < "$NAME_FILE")"
fi

if [[ -z "$NAME" ]]; then
  echo "Usage: ./scripts/sync-config.sh <name>"
  exit 1
fi

echo "$NAME" > "$NAME_FILE"
STACK="Group4ProjectStack-$NAME"

if ! aws cloudformation describe-stacks --stack-name "$STACK" &>/dev/null; then
  echo "Stack $STACK not found."
  echo "Deploy first: ./scripts/setup.sh $NAME"
  exit 1
fi

get_output() {
  local key="$1"
  aws cloudformation describe-stacks \
    --stack-name "$STACK" \
    --query "Stacks[0].Outputs[?OutputKey=='${key}'].OutputValue" \
    --output text 2>/dev/null || true
}

POOL_ID="$(get_output UserPoolId)"
CLIENT_ID="$(get_output UserPoolClientId)"
REGION="$(get_output CognitoRegion)"

if [[ -z "$POOL_ID" || "$POOL_ID" == "None" || -z "$CLIENT_ID" || "$CLIENT_ID" == "None" ]]; then
  echo "Could not read Cognito outputs from stack $STACK."
  echo "Deploy first: ./scripts/setup.sh $NAME"
  exit 1
fi

if [[ -z "$REGION" || "$REGION" == "None" ]]; then
  REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-us-east-1}}"
fi

mkdir -p "$ROOT/frontend/public"
cat > "$ROOT/frontend/public/config.json" <<EOF
{
  "userPoolId": "$POOL_ID",
  "userPoolClientId": "$CLIENT_ID",
  "region": "$REGION"
}
EOF

echo "Wrote frontend/public/config.json"
