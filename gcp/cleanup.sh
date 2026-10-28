#!/bin/bash
# Delete the temporary Cloud Run service. This does NOT delete the
# priorauth_agent dataset or its tables, and never touches Delivery
# Experience resources. Run after screenshots.
set -euo pipefail
gcloud config set project delivery-experience-511901
gcloud run services delete priorauth-agent-demo --region us-central1 --quiet || true
gcloud run services list --region us-central1
echo "Cleanup done. Verify the list above shows 0 PriorAuth services."
echo "NOTE: this script does not delete the Artifact Registry image/repo from a --source build, and does not disable the Cloud Build API. Delete those manually and confirm, as in gcp/cleanup.md."
