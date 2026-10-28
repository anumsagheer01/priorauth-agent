#!/bin/bash
# Cloud Shell step 2 for PriorAuth, project delivery-experience-511901 only.
# Verified Step 1 state assumed: dataset priorauth_agent in us-central1 with
# 6 empty tables, Cloud Run API enabled, no service deployed, $0 spent.
# This script loads data, verifies the embedding model and dimension,
# generates embeddings, runs the real eval, baseline, and ablation,
# and stops if estimated spend reaches $8 (hard ceiling $10).
# It never touches dei_mart, dei-raw-67129202721, or
# cloud-ai-platform-8fb4e1eb-4323-4dbe-b4e6-1e4dc849d199.
# It never changes billing, budgets, caps, IAM, or quotas.
set -euo pipefail
export PROJECT_ID=delivery-experience-511901
# Data location only: BigQuery dataset priorauth_agent stays in
# us-central1. Model location is separate, see below.
# NOTE: PRIORAUTH_PROJECT and PRIORAUTH_LOCATION are NOT read by
# the runtime code (it reads GOOGLE_CLOUD_PROJECT and
# PRIORAUTH_DATA_LOCATION) and are deliberately not exported here.
export PRIORAUTH_DATA_LOCATION=us-central1
export PRIORAUTH_DATASET=priorauth_agent
# Model endpoint only, separate from data location. Default is NOT
# applied here: Cloud Shell must set it explicitly, so a stale
# us-central1 default can never silently return. The approved
# test endpoint on 2026-10-27 is "global" for gemini-3.5-flash,
# which official documentation lists as supported on global and
# us, not us-central1. That is a documented candidate only until
# a minimal live call succeeds at global in Cloud Shell.
if [ -z "${PRIORAUTH_MODEL_LOCATION:-}" ]; then
  echo "ERROR: PRIORAUTH_MODEL_LOCATION is not set."
  echo "Set it to the approved test endpoint, for example:"
  echo "  export PRIORAUTH_MODEL_LOCATION=global"
  echo "Data location stays us-central1; only the model endpoint changes."
  exit 1
fi
echo "Model endpoint: $PRIORAUTH_MODEL_LOCATION (data location remains us-central1)"
# PRIORAUTH_MODEL is the single configuration point for the model
# name, read in src/priorauth/cloud_clients.py. There is deliberately
# NO fallback here. The previous fallback, gemini-3.8-flash, returned
# 404 NOT_FOUND in us-central1 for this project on 2026-10-27, so
# 0 of 30 eval cases ran. Before running this script, Cloud Shell
# must verify an available model name for this project and region
# (see docs/MODEL_CANDIDATES.md) and export it, for example:
#   export PRIORAUTH_MODEL=gemini-3.5-flash
#   export PRIORAUTH_MODEL_LOCATION=global
# Do not guess a name and do not edit this script to restore a
# guessed fallback. If PRIORAUTH_MODEL is unset, stop here.
if [ -z "${PRIORAUTH_MODEL:-}" ]; then
  echo "ERROR: PRIORAUTH_MODEL is not set."
  echo "The previous default gemini-3.8-flash is UNVERIFIED and returned"
  echo "404 NOT_FOUND in us-central1 for this project on 2026-10-27."
  echo "Verify an available model in Cloud Shell first, then export"
  echo "PRIORAUTH_MODEL to that verified name and rerun this script."
  exit 1
fi
echo "Using verified-by-caller model: $PRIORAUTH_MODEL at model endpoint $PRIORAUTH_MODEL_LOCATION"
echo "If this name and endpoint have not actually been verified in Cloud Shell with a minimal live call, stop now."
echo "Do not raise the spending cap until configuration and model availability checks are complete; if the cap then blocks the call, raise it temporarily to \$50 under the \$10 incremental budget and \$8 stop rule, and restore it to \$10 after cloud execution, even on failure."
# Verify the embedding model before indexing anything. If the dimension
# printed here does not match the table, stop and fix the schema first.
# Do not mix vectors from different embedding models in one index.
export PRIORAUTH_EMBEDDING_MODEL=${PRIORAUTH_EMBEDDING_MODEL:-text-embedding-004}
gcloud config set project $PROJECT_ID
echo "Project: $(gcloud config get-value project)"
echo "Dataset tables:"
bq ls --location=us-central1 $PROJECT_ID:$PRIORAUTH_DATASET
cd "$(dirname "$0")/.."
python3 -m pip install -q -r requirements-cloud.txt
# Cloud gate, no model call: agent tools, Runner routing, and
# citation critic catches. This set is valid in a credentialed
# environment. The no-credentials test is deliberately NOT in this
# list: it lives in tests/test_adk_no_credentials.py, local only,
# where it skips if credentials are present. Running it here would
# make a real Vertex call in Cloud Shell and, on 2026-10-27, stop
# the script under set -euo pipefail before any eval. Likewise,
# do not run the full test suite as the cloud gate: other local-only
# tests (for example tests/test_api_real.py) also expect no credentials.
# If this gate fails, stop here; do not run a cloud eval on
# unverified ADK code.
PYTHONPATH=src python3 -m pytest tests/test_adk_agent.py tests/test_citation_critic.py -q
python3 gcp/embed_policy_chunks.py --verify-only
# Load is idempotent as of the 2026-10-27 fix: load_to_bigquery.py
# queries existing primary keys and skips rows already present, so
# rerunning it adds no new duplicates. It does NOT remove duplicates
# already in the tables from the 2026-10-27 rerun (policies 6,
# policy_chunks 14, criteria 40). Before trusting BigQuery row
# counts or VECTOR_SEARCH, clean those tables first with
# gcp/sql/deduplicate_existing_tables.sql in Cloud Shell, record
# counts before and after (expected clean: policies 3, criteria 20,
# policy_chunks 7, cases 30), and only then rerun this load, which
# should report 0 inserted and N skipped for every table. Do NOT
# rerun the old, non-idempotent load, and do NOT run the full
# eval on duplicated tables without recording the dedup step.
# Eval scripts now handle 429s with bounded retry and partial
# output: a case that still fails after retries is recorded in
# not_completed_cases, the remaining cases still run, and the
# report states cases_attempted / cases_completed /
# cases_not_completed. A partial report is not a full-run result.
python3 gcp/load_to_bigquery.py
python3 gcp/embed_policy_chunks.py
python3 scripts/evaluate_real.py --limit 30 --out eval/results_real.json
python3 scripts/baseline.py --limit 30 --out eval/results_baseline.json
python3 scripts/evaluate_real.py --limit 30 --no-citation-verification --out eval/results_no_citation_check.json
python3 scripts/ablation.py eval/results_real.json eval/results_no_citation_check.json | tee eval/ablation_report.txt
python3 scripts/false_ready_report.py eval/results_real.json | tee eval/false_ready_report.txt
echo "Step 2 complete. Check eval/results_real.json for measured metrics."
echo "If Vertex AI returns a spend cap or quota error at the embedding"
echo "check, stop immediately, do not change billing, budgets, caps,"
echo "IAM, or quotas, and report the exact error to the account owner."
echo "Next: bash gcp/deploy_cloudrun.sh for a temporary demo, then bash gcp/cleanup.sh."
