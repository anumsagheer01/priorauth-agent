#!/bin/bash
# Prepared Cloud Shell script, NOT executed from this VM.
# Run verbatim in Cloud Shell only, after the user approves the
# consolidated cost estimate. Stop at $8, ceiling $10.
# Project: delivery-experience-511901. Dataset: priorauth_agent.
# Do NOT modify billing, budgets, caps, IAM, quotas, or any Delivery
# Experience resources. Do NOT create a new project.
set -e
export PROJECT_ID=delivery-experience-511901
export DATASET=priorauth_agent
export BUCKET=priorauth-agent-metadata-511901
export REGION=us-central1
gcloud config set project "$PROJECT_ID"
# Enable APIs as needed for this scope only.
gcloud services enable bigquery.googleapis.com storage.googleapis.com run.googleapis.com aiplatform.googleapis.com
# Create the new dataset only. Never touch existing datasets.
bq mk --dataset --location=US "$PROJECT_ID:$DATASET" || echo "Dataset may already exist; check before continuing."
# Create the new metadata bucket only. Never reuse a Delivery Experience bucket.
gsutil mb -p "$PROJECT_ID" -l US "gs://$BUCKET" || echo "Bucket may already exist; check before continuing."
# Load schema.
bq query --use_legacy_sql=false < gcp/sql/schema.sql
# Upload metadata only, no policy PDFs, no PHI, no secrets.
gsutil cp data/policies.json "gs://$BUCKET/policies/policies.json"
gsutil cp data/policy_chunks.json "gs://$BUCKET/policies/policy_chunks.json"
gsutil cp data/cases.json "gs://$BUCKET/cases/cases.json"
echo "Setup prepared. Recheck official pricing and model availability before any billable call."
echo "Temporary Cloud Run deploy, for screenshots only, after approval:"
echo "gcloud run deploy priorauth-agent --source . --project $PROJECT_ID --region $REGION --allow-unauthenticated"
echo "Delete after screenshots:"
echo "gcloud run services delete priorauth-agent --project $PROJECT_ID --region $REGION --quiet"
