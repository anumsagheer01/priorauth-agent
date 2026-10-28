#!/bin/bash
# Temporary Cloud Run deploy for screenshots only, then delete.
# Uses the existing cloudrun.yaml pattern: FastAPI on port 8000.
# NOTE (2026-10-27 audit): this container serves FastAPI only, not
# Streamlit. PRIORAUTH_PROJECT, PRIORAUTH_LOCATION, and BIGQUERY_DATASET
# are NOT read by the runtime code and were removed from --set-env-vars;
# the code reads GOOGLE_CLOUD_PROJECT, PRIORAUTH_DATA_LOCATION, and
# PRIORAUTH_DATASET. Service name must stay priorauth-agent-demo to
# match gcp/cleanup.sh and gcp/cleanup.md.
# After screenshots, run: bash gcp/cleanup.sh
set -euo pipefail
export PROJECT_ID=delivery-experience-511901
# Same single configuration point as the eval script. The demo must
# use the same Cloud Shell-verified model name as the eval, not the
# UNVERIFIED gemini-3.8-flash fallback. Stop if it is not set.
if [ -z "${PRIORAUTH_MODEL:-}" ]; then
  echo "ERROR: PRIORAUTH_MODEL is not set. Set it to the Cloud Shell-verified model name used for the eval, then rerun."
  exit 1
fi
if [ -z "${PRIORAUTH_MODEL_LOCATION:-}" ]; then
  echo "ERROR: PRIORAUTH_MODEL_LOCATION is not set. Set it to the Cloud Shell-verified model endpoint used for the eval (approved test endpoint: global), then rerun."
  exit 1
fi
gcloud config set project $PROJECT_ID
cd "$(dirname "$0")/.."
gcloud run deploy priorauth-agent-demo --source . --region us-central1 \
  --allow-unauthenticated --port 8000 --memory 1Gi --max-instances 1 \
  --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID,PRIORAUTH_DATA_LOCATION=us-central1,PRIORAUTH_DATASET=priorauth_agent,PRIORAUTH_EMBEDDING_MODEL=text-embedding-004,PRIORAUTH_MODEL=$PRIORAUTH_MODEL,PRIORAUTH_MODEL_LOCATION=$PRIORAUTH_MODEL_LOCATION
echo "Service URL above. Take screenshots, then run bash gcp/cleanup.sh immediately."
