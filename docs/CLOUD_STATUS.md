# Cloud status: CLOUD EVAL VERIFIED 2026-10-27, DEPLOYMENT FAILED

Current status supersedes all 'cloud pending' lines in the body below, which are preserved under 'History (superseded)' for audit purposes. Verified model: gemini-3.5-flash at global, data us-central1. Full system 30/30: criterion 171/200, case 28/30, false-ready 0/25. Deployment FAILED on IAM; no URL, screenshot, or deployed review exists. See docs/EVAL_RESULTS_2026-10-27.md, docs/DEPLOYMENT.md.

## History (superseded, preserved below)

## Status line, read this first

- LOCAL VERIFIED: local deterministic engine, FastAPI app, Streamlit
  syntax check, pytest, and local evaluation all ran in this environment.
  See VALIDATION_LOCAL.md.
- CLOUD EVAL VERIFIED 2026-10-27, DEPLOYMENT FAILED: cloud evaluation,
  baseline, and ablation ran in Cloud Shell and are recorded in
  docs/EVAL_RESULTS_2026-10-27.md. Cloud Run deployment FAILED on IAM
  permissions and is NOT claimed. No deployed screenshot exists.
- This VM, verified in this session: no gcloud CLI, no
  ~/.config/gcloud, no Application Default Credentials, no GCP
  connector. Previous GCP access was browser Cloud Shell only, after
  the user signed in herself as anumsagheer3@gmail.com and clicked
  Authorize. That is the only cloud sign-in step to list. Do NOT ask
  the user for passwords, API keys, or service account JSON in chat,
  and never put credentials in code, logs, or ZIPs.

## GCP gate, authorized in principle by the user, 2026-10-27

- Reuse existing project delivery-experience-511901 only. Do NOT
  create a new project, do NOT modify billing, budgets, caps, IAM, or
  quotas, do NOT modify, overwrite, or delete any existing Delivery
  Experience resources.
- Use clear new names only: BigQuery dataset priorauth_agent, and a
  bucket for policy metadata named in gcp/setup.sh.
- Hard ceiling for PriorAuth: $10 total additional spend, including
  dev, testing, eval, and deployment. This is a ceiling, not
  pre-authorization to spend it.
- Stop rule: stop at $8. Do not exceed $10 under any circumstances.
- BEFORE any billable cloud operation, the main agent will present a
  consolidated cost estimate to the user and get one approval. Until
  that approval arrives, continue local work only. Do NOT start
  billable cloud operations, do NOT enable paid APIs for execution,
  and do NOT deploy Cloud Run yet. The scripts below are prepared,
  not executed.
- No billing, budget, cap, IAM, or quota changes are authorized.

## Usage tracking

| Item | Estimated cost | Actual cost | Notes |
| --- | --- | --- | --- |
| BigQuery dataset priorauth_agent and tables | Modeled, under $1 for small test loads, see gcp/cost_estimation.md | (blank, to be filled by Cloud Shell run) | Small synthetic tables only |
| GCS bucket for policy metadata | Modeled, under $1 for small files | (blank) | Metadata only, no policy PDFs |
| Vertex AI API enablement and test calls | Modeled, see gcp/cost_estimation.md | (blank) | Stop at $8, ceiling $10 |
| Cloud Run temporary deployment for screenshots | Modeled, under $2 for a short-lived service | (blank) | Delete service after screenshots |
| Total | Modeled total kept inside the $10 ceiling, see gcp/cost_estimation.md | (blank, total to be filled by Cloud Shell run) | Stop at $8 |

If actual usage approaches $8, stop all cloud work, delete the
temporary Cloud Run service, and report to the user before spending more.

## Model availability change, documented, not executed

- Original brief model: gemini-2.5-flash.
- HISTORICAL (superseded): Cloud default model then: gemini-3.8-flash. Verified model is now gemini-3.5-flash at global.
- Superseded for Vertex use: gemini-2.5-flash.
- Vertex retirement date recorded from the October 2026 search summary
  in this session: October 20, 2026, for gemini-2.5-flash,
  gemini-2.5-pro, and gemini-2.5-flash-lite on Vertex AI, now called
  Gemini Enterprise Agent Platform, with recommended replacements
  gemini-3.8-flash or gemini-3.5-flash-lite for 2.5 Flash.
- Distinction: on the Gemini Developer API, the same 2.5 models were
  listed with no shutdown date announced and limited to users who had
  actively used them, with guidance for new projects to use the latest
  models. That Developer API listing does NOT change the Vertex plan
  for this GCP Vertex project, where gemini-3.8-flash was then the planned default (superseded).
- No model call was executed in this environment. No Gemini API call
  succeeded, and none is claimed.
- Final model availability must be rechecked at cloud enablement time
  before any paid call, because model listings change.
- The local deterministic engine never depends on any model. Cloud
  mode, if enabled, would only draft or summarize inside the
  deterministic checklist guardrails, never decide readiness alone.

## SDK versions checked, without executing a cloud call

- google-adk 2.x, docs at adk.dev, model string gemini-2.5-flash in
  the original brief, now superseded for Vertex by gemini-3.8-flash.
- Python 3.10 plus is required for ADK, so Python 3.12 is compatible.
- ADK 2.0 workflow runtime notes: agents, tools, and runners are the
  documented building blocks; local tests here do not import ADK, so
  no ADK version is claimed as installed. google-adk was checked as
  not installed in this VM.
- Third-party pricing pages are not official Google pricing. The
  consolidated estimate presented to the user must be rechecked
  against official Google Cloud pricing at approval time.

## Exact steps to enable cloud mode, for the Cloud Shell run only

1. In the browser, open Cloud Shell, sign in as the account owner,
   and click Authorize when prompted. No password, key, or service
   account JSON is requested in chat.
2. Run gcp/setup.sh verbatim from the repo root in Cloud Shell. It
   uses project delivery-experience-511901, dataset priorauth_agent,
   and the bucket name in that script, and it does not touch Delivery
   Experience resources.
3. Run the BigQuery schema in gcp/sql/schema.sql.
4. Recheck model availability and official Google Cloud pricing, then
   confirm the consolidated estimate with the user and get one
   approval before any billable call.
5. Run the cloud eval steps in gcp/setup.sh, record actual costs in
   the usage tracking table above, and stop at $8.
6. Deploy Cloud Run temporarily with gcp/cloudrun.yaml, take real
   screenshots, then delete the service with the delete command in
   gcp/setup.sh. Record the deletion in this file.
7. If any step cannot be verified, report it as pending, not done.

## Cloud Run config prepared, not deployed

See gcp/cloudrun.yaml. It is a prepared config only. No service was
created from this VM.

## Cloud Step 1, VERIFIED 2026-10-27 (main agent, Cloud Shell)

- Project delivery-experience-511901, account anumsagheer3@gmail.com.
- Cloud Run API enabled only in this step. Vertex AI, BigQuery, and
  Cloud Storage were already enabled and were not re-enabled.
- BigQuery dataset priorauth_agent created in us-central1, with 6
  empty tables from gcp/sql/schema.sql: audit_log, cases, criteria,
  policies, policy_chunks, reviews. No Delivery resources modified.
- Cloud Run services in us-central1: 0. No deployment yet, no data
  load yet, no Gemini eval yet. Cost for this step: $0 shown.
  The $28 out of $300 credits used display is pre-existing, not a
  PriorAuth charge.

## Cloud Step 2, BLOCKED 2026-10-27 03:32 AM ET, RETRY APPROVED 03:33 AM ET

- Step 2 stopped at the first Vertex AI embedding check with a
  spend cap breach for project delivery-experience-511901.
- No cases ran, no metrics exist, dataset tables still empty,
  no billing or IAM change was made by Muse in that attempt.
- ADK Runner integration audit was still running locally at that
  time; it is now completed in this repo, see docs/ADK_INTEGRATION.md.
- APPROVED 2026-10-27 03:33 AM ET: Anum approved raising the
  Vertex cap and retrying the eval. Plan, following the Oct 17
  precedent ($10 to $50, restored to $10 on Oct 18 after training):
  temporarily raise the Delivery Experience Vertex AI cap to $50,
  run the final ADK-driven eval ONCE ONLY, then restore the cap
  to $10 after the final eval. Do not run the old pipeline eval
  first, to avoid paying twice against the $10 PriorAuth ceiling
  and $8 stop. Do not change any other budget, cap, billing, or
  IAM setting. The cap raise and restore are browser Cloud Shell
  work for the main agent, not for this VM, which has no gcloud.
- When the cap is raised, run the revised Step 2 below from the
  revised repo copy, not from the old 03:22 EDT ZIP, because the
  old code did not genuinely drive ADK tools through Runner.

## Cloud Step 2, final attempt, FAILED 2026-10-27 03:57 AM ET

- 0 of 30 cases ran. No metrics, no baseline, no ablation, no
  deployment, no screenshots. Nothing in this repo may present
  any metric as model performance from this attempt.
- Cause 1, model name: gemini-3.8-flash returned 404 NOT_FOUND
  for Publisher model projects/delivery-experience-511901/
  locations/us-central1/publishers/google/models/gemini-3.8-flash.
  That name, previously assumed from Google's recommended
  replacement list, is NOT available in Vertex AI us-central1
  for this project. Documentation alone is not proof for this
  project. See docs/MODEL_CANDIDATES.md for the full candidate
  table and the verification steps required before any rerun.
- Cause 2, test gate: tests/test_adk_agent.py contained a
  no-credentials test expecting CloudNotConfigured. In
  credentialed Cloud Shell it instead made a real Vertex call,
  so the test cannot pass there, and the script stopped under
  set -euo pipefail before any eval. That test is now moved,
  not deleted, to tests/test_adk_no_credentials.py, where it
  skips if credentials are present. The cloud script now runs
  only tests/test_adk_agent.py and tests/test_citation_critic.py.
- What did pass in that attempt: embedding model
  text-embedding-004, dimension 768, verified. ADK code check
  passed: Runner.run_async, create_session, and
  get_function_calls were present in the extracted repo.
- Incremental PriorAuth spend for the attempt: about $0.00,
  well under the $8 stop and $10 ceiling.
- Vertex cap after the attempt: restored to $10, as instructed,
  now showing about $28.17 used against a $10 limit for
  October, so Vertex may be paused until the November 1
  monthly reset unless the cap is temporarily raised again
  with the account owner's approval.
- Do not rerun with a guessed model name. Verify an available
  model in Cloud Shell first, fix the test gate (now done in
  this repo), and get approval for the verified model and any
  further temporary cap raise.

## Model endpoint fix, 2026-10-27, local only, no cloud call

- Before this fix, one location field drove the ADK Gemini
  client, the Vertex init, and BigQuery, so every model call
  went to us-central1, where gemini-3.5-flash, gemini-3.5-flash-lite,
  and gemini-3.8-flash all returned 404 for this project.
- After this fix, model location and data location are separate:
  PRIORAUTH_MODEL_LOCATION, default "global", is used only for
  Gemini generation calls (ADK client_kwargs and gemini_generate);
  PRIORAUTH_DATA_LOCATION / GOOGLE_CLOUD_LOCATION, default
  us-central1, is used for BigQuery dataset priorauth_agent and
  for embeddings. The dataset does not move.
- "global" is the user-approved test endpoint for
  gemini-3.5-flash on 2026-10-27, confirmed by the user from
  Google official documentation as supported on global and us,
  not us-central1. It is a documented candidate only until a
  minimal live call succeeds at global in Cloud Shell. No
  global call is claimed as successful in this repo.
- Cloud Shell order, per the user 2026-10-27 08:44 AM ET:
  first fix this configuration, then run one minimal live
  verification call at global, without raising the spending
  cap until configuration and availability checks are
  complete. If the cap blocks that call, temporarily raise
  it to $50 under the $10 incremental budget and $8 stop
  rule. Only after the minimal call succeeds, run a 2 to 3
  case ADK pilot, then the full eval, baseline, ablation,
  and deployment. Restore the cap to $10 after cloud
  execution, even on failure.

## Cloud Step 2, revised, exact commands for the main agent

Run in Cloud Shell, from the revised repo copy, after confirming
the dataset above still exists and Cloud Shell shows project
delivery-experience-511901, and ONLY after completing the
verification steps in docs/MODEL_CANDIDATES.md:
  export PRIORAUTH_MODEL=gemini-3.5-flash
  export PRIORAUTH_MODEL_LOCATION=global
  bash gcp/cloud_step2_load_and_eval.sh
The model name and endpoint above are the documented
candidates for the global test, not verified values. The
script now refuses to run without both variables set. If
the minimal live verification call at global has not yet
succeeded, run that call first and stop on failure; do not
run the full script on an unverified model and endpoint.
The script now refuses to run without PRIORAUTH_MODEL set, so
it can no longer silently fall back to gemini-3.8-flash.
That first runs ADK and citation tests with no model call, then
loads BigQuery tables, verifies the embedding model and
dimension, generates embeddings, runs the 30-case real ADK eval,
the baseline, and the no-citation-verification ablation arm, and
writes eval/results_real.json, eval/results_baseline.json,
eval/results_no_citation_check.json, eval/ablation_report.txt,
and eval/false_ready_report.txt.
Then, for a temporary demo only:
  bash gcp/deploy_cloudrun.sh
Take screenshots and logs, then immediately:
  bash gcp/cleanup.sh
Stop all cloud work if estimated spend reaches $8. Ceiling is $10.
Do not claim eval, deployment, or screenshots as done until these
commands have actually run and their outputs are recorded.

## Global verification and pilot, SUCCEEDED as pilot only, 2026-10-27

- Model and endpoint, verified by a minimal live call, not by
  documentation: gemini-3.5-flash at global responded "OK" in
  2.04 s, from ~/pa_final3/priorauth-agent/ with transfer3,
  model_location global, data_location us-central1, via ADK
  Gemini vertexai=True. This supersedes the us-central1 404s
  for gemini-3.8-flash, gemini-3.5-flash-lite, and
  gemini-3.5-flash. Global availability is now verified for
  this project; us-central1 availability is not.
- ADK pilot, pilot only, n=3, not full performance: 3 cases
  (EVAL-PMC-LUM-01, KNE-01, BIO-01), 7 tool events per case,
  3 tool calls each for policy search, code validation, and
  evidence extraction. Criterion accuracy 15/20, case
  readiness 2/3, false-ready 0, missing-evidence recall 3/4,
  citation precision 8/8, retrieval proxy 3/3, latency p50
  28.4 s and p95 96.4 s (with n=3, p95 is effectively the
  slowest case, not a stable percentile), tokens prompt 3270
  and output 1610, estimated cost $0.0085 total. None of
  these numbers may be presented as full-eval performance:
  the pilot is 3 cases, chosen as a smoke test, not the
  30-case eval.

## Full eval, STOPPED ON 429, 2026-10-27 09:50 AM ET, no full results

- After the source_type column was added to
  priorauth_agent.cases in Cloud Shell only, the full script
  was rerun. BigQuery loaded cases 30, policy_chunks 14,
  and policies 6, with duplicates from two loads (clean
  counts from the repo data files are cases 30, policy_chunks
  7, policies 3, criteria 20; criteria therefore stands at
  40 after two loads, by the same mechanism, and must be
  verified in Cloud Shell before any rerun relies on it).
  Embeddings completed.
- Then scripts/evaluate_real.py aborted with 429
  RESOURCE_EXHAUSTED and no results_real.json was written,
  because that script had no sleep, retry, exception, or 429
  handling at all. Full eval completed: 0 of 30 cases. No
  results_real.json, no baseline, no ablation, no
  false-ready report, no deployment, and no screenshots
  exist from this attempt. Per the rate-limit stop rule, no
  further model calls were made in that attempt, and the
  Vertex cap was restored to $10 afterward (see below).
  A fresh retry is a new decision, not an automatic
  continuation of the stopped attempt.

## Local fixes for the 429 stop and the duplicate load, 2026-10-27, local only

- 429 handling, scripts/rate_limit.py, used by both
  scripts/evaluate_real.py and scripts/baseline.py: a 429 is
  detected by exception class name, numeric code/status, or
  the strings "429" / "RESOURCE_EXHAUSTED". The affected case
  is retried at most 3 times, with 10s / 20s / 40s backoff,
  never in a tight loop and never indefinitely. A small
  pause between cases (PRIORAUTH_EVAL_CASE_DELAY_SECONDS,
  default 5 seconds) is also added, on top of retry backoff.
  If a case still fails, it is recorded in
  not_completed_cases with its error, the remaining cases
  still run, and the report is rewritten after every case
  and states cases_attempted, cases_completed, and
  cases_not_completed, with metrics computed over completed
  cases only and labeled as such. Failed cases are never
  given invented results. Exit code 0 from these scripts
  means a report was written, not that every case
  completed; check cases_not_completed.
- Idempotent load, gcp/load_to_bigquery.py: before inserting,
  the loader queries existing primary keys (policies by
  policy_id, criteria by policy_id + criterion_id,
  policy_chunks by chunk_id, cases by case_id) and skips
  rows already present, reporting inserted and skipped
  counts. A rerun therefore adds no new duplicates. It does
  NOT remove duplicates already in the tables; see the
  next bullet.
- Schema fix, gcp/sql/schema.sql: the cases table now
  defines source_type STRING, matching the loader, so a
  fresh dataset creation does not repeat the "no such
  field source_type" failure that caused the first load to
  stop after policies and chunks.
- Existing-table cleanup, gcp/sql/deduplicate_existing_tables.sql:
  Cloud Shell only, never run by the cloud script. Record
  row counts before and after, run the four CREATE OR
  REPLACE statements, and confirm clean counts (policies 3,
  criteria 20, policy_chunks 7, cases 30) before rerunning
  the loader, which should then report 0 inserted for
  every table.
- Tests, local only, no cloud call: 47 passed in total,
  including 7 new tests in
  tests/test_rate_limit_and_idempotent_load.py covering
  429 detection, bounded retry with backoff, a simulated
  429 on one eval case with partial output and correct
  denominators, a baseline 429 retry, a second load that
  does not duplicate rows (3 / 20 / 7 / 30, not 6 / 40 /
  14), and source_type in the schema cases table.

## Cap and spend, after the 429 stop, 2026-10-27

- Vertex AI cap restored to $10 after cloud execution,
  as required, including on failure. Console display at
  restore: about $28.76 used against the $10 limit.
  Script-estimated PriorAuth spend for the pilot:
  $0.0085, well under the $8 stop and $10 ceiling. No
  full-eval spend is claimed, because no full-eval case
  completed.

## What a later fresh attempt must do differently

1. Use only the fixed scripts in this repo (429 handling,
   idempotent load, schema with source_type, separate model
   and data locations). Do not rerun the old load blindly,
   and do not use transfer2 or any pre-fix package.
2. In Cloud Shell, deduplicate the existing tables first
   with gcp/sql/deduplicate_existing_tables.sql, record
   counts before and after, and confirm clean counts
   (3 / 20 / 7 / 30) before the eval.
3. Set PRIORAUTH_MODEL=gemini-3.5-flash and
   PRIORAUTH_MODEL_LOCATION=global (verified by the
   minimal live call above; data location stays
   us-central1), and recheck pricing for that model before
   the full run, keeping the $10 ceiling and $8 stop.
4. Raise the Vertex cap to $50 again ONLY with a fresh
   user approval for that attempt, restore it to $10
   after cloud execution, even on failure, and report
   spend before and after with the incremental amount.
5. Run the pilot again if the scripts changed since the
   pilot, then the full eval, baseline, and ablation, and
   accept partial output only with its denominators
   stated: a report with cases_not_completed greater than
   0 is not a full 30-case result, and must not be
   presented as one.
6. No deployment, screenshot, or full-eval metric may be
   claimed until that fresh attempt actually produces
   them.

## Fresh controlled attempt, VERIFIED CLOUD EVAL, DEPLOYMENT FAILED, 2026-10-27 9:59 AM to 1:12 PM ET

Full verified results, with denominators, are in
docs/EVAL_RESULTS_2026-10-27.md. This section is a summary only.

- Model: gemini-3.5-flash at global, data us-central1, project
  delivery-experience-511901, from ~/pa_final4/priorauth-agent/
  using pa_adk_transfer4.zip.
- Cap: before about $28.76 / $10.00, raised to $50 for this
  attempt only, restored to $10 at about 1:07 to 1:08 PM ET,
  final about $33.05 / $10.00, Configured. Console delta
  about $4.29, below the $8 stop and $10 ceiling.
  Script-estimated model spend about $0.22 total. The gap
  between console delta and script estimates is UNRESOLVED;
  do not attribute the console delta to PriorAuth alone.
- Dedup, priorauth_agent only: before policies 6, criteria 40,
  policy_chunks 14, cases 30; after policies 3, criteria 20,
  policy_chunks 7, cases 30, exactly clean counts verified.
  Loader then inserted 0, skipped 3/20/7/30. No Delivery
  resources touched.
- Cloud test gate: 43 passed, 3 failed, 1 skipped, 317.10 s.
  The 3 failures are credential-expectation tests asserting
  200 == 503. Root cause is an unresolved inference (Cloud
  Shell provides ADC, so no-credentials assumptions fail).
  Local passes do not erase these failures.
- Pilot, n=3, pilot only: attempted 3, completed 3, not
  completed 0; criterion 16/20, case 2/3, false-ready 0,
  missing-evidence recall 3/4, citation 8/8, retrieval proxy
  3/3, latency p50 30285.4 ms, p95 32936.2 ms, cost $0.0081,
  tokens prompt 3228, output 1523, 7 tool events per case.
- Full system, 30/30, citation verification on: criterion
  171/200 = 0.855, case 28/30 = 0.9333, false-ready 0/25,
  missing-evidence recall 12/14, citation 89/89, retrieval
  proxy 30/30, latency p50 28834.6 ms, p95 62187.2 ms,
  cost $0.0784 total, $0.0026 per case, tokens prompt 30864,
  output 14741, 30 tool calls each for the three ADK tools.
  By procedure: lumbar case 9/10, criterion 28/40; knee
  case 10/10, criterion 58/70; biologic case 9/10,
  criterion 85/90.
- Baseline, simple RAG, 30/30: criterion 14/200 = 0.07,
  case 13/30, false-ready 11/25, missing-evidence recall
  14/14, citation not applicable 0/0, retrieval proxy 30/30,
  latency p50 11338.9 ms, p95 291571.7 ms, cost $0.0273,
  tokens recorded 0/0, incomplete for the baseline.
- No-citation ablation, 30/30: criterion 173/200 = 0.865,
  case 28/30, false-ready 0/25, missing-evidence recall
  12/14, citation 90/90, retrieval proxy 30/30, latency
  p50 31890.5 ms, p95 278082.1 ms, cost $0.0751.
- Ablation delta, full minus no-citation: criterion -0.01,
  case 0.0, false-ready 0.0, citation 0.0, missing-evidence
  recall 0.0. Citation verification did NOT demonstrably
  help on this 30-case set. Same 4 prediction failures in
  both arms.
- Final prediction failures, separately: EVAL-PMC-LUM-01
  readiness mismatch; EVAL-PMC-KNE-01 KNE-02 missing called
  met; EVAL-BIO-04 BIO-05 missing called met; EVAL-BIO-05
  readiness mismatch. No case failed to complete in the
  final run, so no failed-case bias investigation applies
  to the final 30/30 metrics. The two missing-called-met
  errors are safety-relevant even though neither produced
  a false-ready case.
- Superseded first-run partial, record only: 14 completed,
  then a metadata RefreshError crash, partial criterion
  55/70, case 13/14, cost $0.0328, 16 uncompleted cases not
  recorded in not_completed_cases. Missingness was
  procedure-concentrated (knee 7, biologic 9, lumbar 0)
  and not representative. Root cause undiagnosed.
- Deployment FAILED: Cloud Run deploy for
  priorauth-agent-demo failed with PERMISSION_DENIED,
  default service account missing Cloud Build IAM
  permissions. IAM changes were explicitly NOT authorized,
  so no retry with IAM changes was made. No URL, no
  deployed review, no screenshot, no deployed log exists.
  Cleanup confirmed 0 PriorAuth Cloud Run services.
  Temporary Artifact Registry repository
  cloud-run-source-deploy (0 MB, no image pushed) was
  deleted, and Cloud Build API was disabled again.
- Raw Cloud Shell JSON files ARE included unchanged in evidence/cloud_eval_2026-10-27/raw/ in the GitHub pack, including the corrected baseline raw file. See docs/EVAL_RESULTS_2026-10-27.md for the results and unresolved items.
