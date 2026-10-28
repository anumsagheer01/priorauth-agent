# Cleanup, Cloud Shell run only

These commands are prepared, not executed from this VM. Run them in
Cloud Shell after screenshots, and record the result in
docs/CLOUD_STATUS.md.

1. Delete the temporary Cloud Run service:
   gcloud run services delete priorauth-agent-demo --project delivery-experience-511901 --region us-central1 --quiet
2. Optionally delete the BigQuery dataset only if the user approves
   in a later step. Do NOT delete it automatically, and never delete
   any Delivery Experience dataset.
3. Confirm billing usage in the Cloud Console, compare it to the $8
   stop rule and the $10 ceiling, and record actual costs in
   docs/CLOUD_STATUS.md.

4. cleanup.sh alone does NOT delete the Artifact Registry image/repo
   created by a --source build, and does NOT disable the Cloud Build
   API. After cleanup.sh confirms 0 PriorAuth services, delete that
   image/repo manually and disable Cloud Build API again only if that
   was its prior state, then confirm both. The 2026-10-27 attempt
   required those manual steps; do not assume cleanup.sh alone
   reproduces that clean state.
