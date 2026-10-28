# Deployment, reproducibly, without IAM changes in this audit

Status: NOT DEPLOYED. The temporary Cloud Run deployment attempted
on 2026-10-27 FAILED with PERMISSION_DENIED: the default service
account is missing required IAM permissions for Cloud Build. No
service URL, no deployed review, no screenshot, and no deployed log
exists. Cleanup confirmed 0 PriorAuth Cloud Run services, the empty
Artifact Registry repository was deleted, and the Cloud Build API was
disabled again. Fixing the failure requires IAM changes that were
explicitly NOT authorized in this audit, so no IAM change was made
here, and the deploy was not retried with IAM changes.

This document makes the application reproducibly deployable and
gives exact instructions and required roles, so a future deploy can
be attempted after separate IAM authorization. It does not claim a
successful deployment.

## What was fixed in this audit (2026-10-27)

The deploy artifacts as shipped before this audit would NOT have
produced a working real review even with IAM fixed:

- Dockerfile installed `requirements.txt` only, omitting
  `requirements-cloud.txt` (google-adk, google-cloud-bigquery,
  google-cloud-storage). In the container, `adk_available()` would
  report ADK unavailable and real reviews would fail. Fixed:
  Dockerfile now installs both requirement files.
- Service name was inconsistent: `gcp/cloudrun.yaml` said
  `priorauth-agent`, while `gcp/deploy_cloudrun.sh` and
  `gcp/cleanup.sh` used `priorauth-agent-demo`, and `gcp/cleanup.md`
  step 1 said `priorauth-agent`. Fixed: all now use
  `priorauth-agent-demo`, matching the scripted deploy and cleanup.
- `gcp/cloudrun.yaml` contained placeholder model values
  (`SET_TO_CLOUD_SHELL_VERIFIED_MODEL`) and must never be applied
  verbatim. Fixed: the YAML now records the verified pair from
  2026-10-27 (gemini-3.5-flash at global, data us-central1) as a
  record, with a re-verify warning. The scripted deploy path
  (`--source .` with `--set-env-vars`) takes precedence over the YAML.
- Deploy script set env vars the runtime code does not read
  (`PRIORAUTH_PROJECT`, `PRIORAUTH_LOCATION`, `BIGQUERY_DATASET`).
  Fixed: the script now sets the names `CloudConfig` actually reads:
  `GOOGLE_CLOUD_PROJECT`, `PRIORAUTH_DATA_LOCATION`,
  `PRIORAUTH_DATASET`, `PRIORAUTH_EMBEDDING_MODEL`,
  `PRIORAUTH_MODEL`, `PRIORAUTH_MODEL_LOCATION`.
- `.env.example` used stale variable names and the failed model
  gemini-3.8-flash. Fixed: it now uses the `PRIORAUTH_*` names the
  code reads, with gemini-3.5-flash at global, and a re-verify
  warning. Do NOT use gemini-3.8-flash: it returned 404 in
  us-central1 for this project on 2026-10-27.
- Streamlit scope: the container serves FastAPI only on port 8000.
  It does NOT start Streamlit, even though the old Dockerfile exposed
  port 8501. Fixed: port 8501 is no longer exposed. If a UI demo is
  wanted, run Streamlit separately with
  `PRIORAUTH_API_URL=<service URL>`.
- Cleanup scope: `gcp/cleanup.sh` deletes only the service and lists
  services. It does NOT delete the Artifact Registry image/repo from
  a `--source` build, and does NOT disable the Cloud Build API. The
  2026-10-27 clean state required those manual steps. Fixed:
  `gcp/cleanup.sh` and `gcp/cleanup.md` now state this explicitly;
  do not assume cleanup.sh alone reproduces that clean state.
- Public access: the script uses `--allow-unauthenticated` and the
  YAML sets ingress to all. That is acceptable only for a temporary,
  test-data-only demo, then deleted. Do not leave it running, and
  do not put real patient data through it.

## Exact deployment instructions (to follow after IAM approval)

Prerequisites, in order:

1. Verify a model with a minimal live call at the intended endpoint
   first, and record the exact verified pair. The verified pair on
   2026-10-27 was model gemini-3.5-flash, model location global,
   data location us-central1. Re-verify at deploy time; do not
   assume it is still valid.
2. Obtain separate approval for the IAM roles below, and confirm
   the exact denied permission from the failed deploy log before
   granting anything broad. The exact denied permission cannot be
   determined from local files; no deploy log is in this repo.
3. Reconcile the artifacts (done in this audit, listed above) and
   confirm the service name, region, port, and env names match
   between `gcp/cloudrun.yaml`, `gcp/deploy_cloudrun.sh`, and
   `gcp/cleanup.sh`.
4. In Cloud Shell, from the repo root:
   ```
   export PRIORAUTH_MODEL=<Cloud-Shell-verified model name>
   export PRIORAUTH_MODEL_LOCATION=<Cloud-Shell-verified model location, e.g. global>
   bash gcp/deploy_cloudrun.sh
   ```
   This sets project delivery-experience-511901, region us-central1,
   port 8000, `--allow-unauthenticated`, memory 1Gi, max instances 1,
   and the env vars listed above.
5. Capture the service URL printed by the deploy command immediately.
6. Verify per the checklist below. Take screenshots of a real review
   only after a 200 review is observed.
7. Immediately after screenshots, clean up:
   ```
   bash gcp/cleanup.sh
   ```
   Then, manually (since cleanup.sh does not do this): delete the
   Artifact Registry image/repo created by the `--source` build, and
   disable the Cloud Build API again if that was its prior state.
   Confirm 0 services with:
   ```
   gcloud run services list --region us-central1
   ```

## IAM roles to request and approve (stated, not granted)

Prefer the narrowest split: build with the build account, deploy
with the deployer account, rather than granting deploy rights to the
build account. Verify each role against the actual PERMISSION_DENIED
detail in the Cloud Console before granting.

Deployer (the human account running `gcloud run deploy --source .`):

- `roles/run.admin` (create and manage the Cloud Run service)
- `roles/iam.serviceAccountUser` on the Cloud Run runtime service
  account (to run the service as that account)
- `roles/cloudbuild.builds.editor` (submit the source build)
- `roles/artifactregistry.writer` (write the built image; admin only
  if repo creation itself is denied)
- `roles/serviceusage.serviceUsageConsumer` (if API enablement or
  usage checks are denied)

Cloud Build default service account
(`<PROJECT_NUMBER>@cloudbuild.gserviceaccount.com`, build step only):

- `roles/cloudbuild.builds.builder`
- `roles/artifactregistry.writer`
- `roles/storage.objectCreator` / `roles/storage.objectViewer` on the
  build staging bucket
- `roles/logging.logWriter`
- Only add `roles/run.admin` and `roles/iam.serviceAccountUser` to
  this account if the deploy is genuinely performed by a build step;
  for the scripted `gcloud run deploy` flow, the deployer account
  above is the one that needs them.

Cloud Run runtime service account (only relevant after a successful
deploy, not the build failure): if the Compute Engine default account
is used, it would separately need `roles/aiplatform.user` (Vertex),
`roles/bigquery.dataViewer` and `roles/bigquery.jobUser` (dataset
`priorauth_agent` in us-central1), and `roles/logging.logWriter`. Do
not conflate this with the build failure.

## Verification checklist for a future deploy

- `gcloud run services list --region us-central1` shows exactly the
  intended service (one service, name priorauth-agent-demo) before
  testing.
- Service URL is recorded (HTTPS) and reachable.
- `GET <URL>/health` returns 200, mode `real_adk_pipeline`,
  engine version `2.0.0-real`, `credentials_present: true`, model
  equal to the Cloud Shell-verified model name, and the model
  location recorded separately from data location us-central1.
- `POST <URL>/reviews` with a known eval case (for example an
  `EVAL-` case from `data/eval_cases.json`) returns 200 with a real
  review ID, per-criterion results, citations and excerpts,
  deterministic readiness, model name matching the verified model,
  latency and token usage, and is explicitly not a mock,
  placeholder, or precomputed result.
- Screenshots capture the real review output (not just `/health`)
  and are saved with the service URL and timestamp.
- `bash gcp/cleanup.sh` is run immediately after screenshots;
  `gcloud run services list --region us-central1` then shows 0
  PriorAuth services.
- Artifact Registry image/repo created by the `--source` build is
  deleted manually and confirmed; Cloud Build API is disabled again
  if that was its prior state (neither is done by cleanup.sh).
- BigQuery dataset `priorauth_agent` is confirmed untouched by
  cleanup; billing is checked against the $8 stop and $10 ceiling
  and recorded.

## What remains unverified

- The exact PERMISSION_DENIED permission, resource, and service
  account from the failed deploy (no log in this repo).
- Current live state of Cloud Run services, Artifact Registry, API
  enablement, or billing in project delivery-experience-511901.
- Whether gemini-3.5-flash at global is still available at a future
  deploy time; it must be re-verified with a minimal live call
  before any redeploy.
- The provenance and command of the cloud test count 43 passed, 3
  failed, 1 skipped; the scripted cloud gate runs only
  `tests/test_adk_agent.py` and `tests/test_citation_critic.py`,
  not the full suite, so that count must have come from a full-suite
  run, not from the scripted gate.
