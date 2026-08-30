#!/usr/bin/env bash
# Deploy solodby_agent to Cloud Run via ADK.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

: "${GOOGLE_CLOUD_PROJECT:?Set GOOGLE_CLOUD_PROJECT}"
REGION="${REGION:-us-central1}"
SERVICE_NAME="${SERVICE_NAME:-pr-security-reviewer}"

if ! command -v gcloud >/dev/null 2>&1; then
  echo "gcloud not found. Install: brew install --cask google-cloud-sdk" >&2
  exit 1
fi

if [[ -z "${VIRTUAL_ENV:-}" ]]; then
  # shellcheck disable=SC1091
  source "$ROOT/.venv/bin/activate"
fi

gcloud config set project "$GOOGLE_CLOUD_PROJECT"
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  storage.googleapis.com \
  --project="$GOOGLE_CLOUD_PROJECT"

EXTRA_ENV=()
if [[ -n "${REPORTS_GCS_BUCKET:-}" ]]; then
  EXTRA_ENV+=(--set-env-vars="REPORTS_GCS_BUCKET=${REPORTS_GCS_BUCKET}")
fi
if [[ -n "${GOOGLE_API_KEY:-}" ]]; then
  EXTRA_ENV+=(--set-env-vars="GOOGLE_API_KEY=${GOOGLE_API_KEY},GOOGLE_GENAI_USE_ENTERPRISE=0")
fi

echo "Deploying $SERVICE_NAME to $GOOGLE_CLOUD_PROJECT / $REGION ..."
adk deploy cloud_run \
  --project="$GOOGLE_CLOUD_PROJECT" \
  --region="$REGION" \
  --service_name="$SERVICE_NAME" \
  --with_ui \
  "${EXTRA_ENV[@]}" \
  "$ROOT/solodby_agent"

echo "Done. Open Cloud Run console for URL + screenshot for demo video."
