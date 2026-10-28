# Verified cloud evaluation results, 2026-10-27

## Source note, read first

This file summarizes results whose raw JSON files ARE included unchanged in evidence/cloud_eval_2026-10-27/raw/ in the GitHub pack. The original full-system files came from Cloud Shell at ~/pa_final4/priorauth-agent/eval/ via the user upload, and the corrected baseline raw file came from Cloud Shell at ~/pa_baseline_rerun/priorauth-agent/eval/ via a later user upload, copied byte-for-byte and recomputed from its rows.

- Run window: 2026-10-27, 9:59 AM to 1:12 PM ET, fresh controlled
  attempt, user approved.
- Project: delivery-experience-511901. Account: anumsagheer3@gmail.com.
- Model: gemini-3.5-flash. Model location: global. Data location:
  us-central1. Embedding model: text-embedding-004, dimension 768.
- Repo used in Cloud Shell: pa_adk_transfer4.zip, extracted to
  ~/pa_final4/priorauth-agent/.
- All metrics below are for this 30-case annotated set only. They
  must not be generalized to other case sets, to typical prior
  authorization packets, or to real clinical notes.
- Policies are simplified faithful subsets, not complete policies.
  Cigna IP0660 is 22 pages and was not fully re-read. A human must
  read the full, current policy before any real use.
- This system never approves, denies, or submits a prior
  authorization, and gives no medical advice. Readiness states are
  documentation readiness only: READY_FOR_HUMAN_REVIEW, NOT_READY,
  NEEDS_MANUAL_REVIEW. A human makes the final decision.

## Cap and spend

- Before this attempt: about $28.76 used against a $10.00 Vertex AI
  cap, Configured.
- Raised for this attempt only: to $50, console saved.
- Restored after cloud testing: to $10 at about 1:07 to 1:08 PM ET,
  console saved. Final console display: about $33.05 used against
  $10.00, Configured.
- Console delta for this attempt: about $4.29. This is below the
  $8 stop and the $10 ceiling.
- Script-estimated model spend for this attempt: about $0.22 total,
  broken down as pilot $0.0081, first full partial $0.0328,
  baseline $0.0273, no-citation ablation $0.0751, complete full
  rerun $0.0784. These are script estimates at repo rates, not
  console-billed amounts.
- UNRESOLVED GAP: the console delta (about $4.29) is much larger
  than the script-estimated model spend (about $0.22). Do not
  attribute the console delta to PriorAuth alone. Possible
  explanations include console display lag and other Vertex
  usage during the day, but neither is proven. This gap is
  unresolved and must stay unresolved in any summary.

## BigQuery deduplication

- Dataset: priorauth_agent, us-central1, project
  delivery-experience-511901 only. No Delivery Experience
  resources were touched.
- Before dedup: policies 6, criteria 40, policy_chunks 14,
  cases 30. These were duplicates from two earlier loads.
- After dedup, using gcp/sql/deduplicate_existing_tables.sql:
  policies 3, criteria 20, policy_chunks 7, cases 30. These are
  the exact clean counts, verified.
- The idempotent loader then inserted 0 rows and skipped
  3 policies, 20 criteria, 7 policy chunks, and 30 cases.

## Cloud test gate

- Result: 43 passed, 3 failed, 1 skipped, 317.10 seconds.
- The 3 failures are credential-expectation tests:
  test_api.py test_post_review_without_credentials_is_503,
  test_api_real.py test_health_reports_real_mode_and_no_credentials_locally,
  and test_api_real.py test_review_without_credentials_fails_clearly_not_mocked,
  each asserting 200 == 503.
- INFERENCE, NOT PROVEN: Cloud Shell provides Application Default
  Credentials, so tests that assume no credentials fail there.
  This root cause is unresolved and is stated as an inference
  only. Do not present local test passes as erasing these 3
  cloud gate failures.
- The pilot gate then passed, so work proceeded. That does not
  make the 3 failures disappear.

## Pilot, n=3, pilot only, not full performance

- Attempted 3, completed 3, not completed 0.
- Criterion accuracy: 16/20 = 0.8.
- Case readiness accuracy: 2/3 = 0.6667.
- False-ready rate: 0/3 non-ready = 0.0. Note the denominator
  here is the pilot non-ready count reported by Cloud Shell,
  not the full set denominator of 25.
- Missing-evidence recall: 3/4 = 0.75.
- Citation precision: 8/8 = 1.0.
- Retrieval recall proxy: 3/3 = 1.0. This proxy is weak, as
  documented elsewhere, because no chunk-level gold set exists.
- Latency: p50 30285.4 ms, p95 32936.2 ms, mean 30716.3 ms.
  With n=3, p95 is effectively the slowest case, not a stable
  percentile.
- Cost: $0.0081 total, script estimate, not a billed amount.
- Tokens: prompt 3228, output 1523.
- ADK tool calls: 3 each for search_policy_chunks,
  validate_case_codes, and extract_evidence. Tool events:
  7 per case, non-empty for every case.
- By procedure:
  - Lumbar: criterion 1/4 = 0.25, case accuracy 0/1 = 0.0.
  - Knee: criterion 6/7 = 0.8571, case accuracy 1/1 = 1.0.
  - Biologic: criterion 9/9 = 1.0, case accuracy 1/1 = 1.0.
- Pilot failures:
  - EVAL-PMC-LUM-01, lumbar, gold NEEDS_MANUAL_REVIEW,
    predicted NOT_READY, readiness mismatch.
  - EVAL-PMC-KNE-01, knee, criterion KNE-02, gold missing,
    predicted met, missing called met.

## Full system, citation verification on, 30/30

- Attempted 30, completed 30, not completed 0. This is a
  complete 30-case run.
- Criterion accuracy: 171/200 = 0.855.
- Case readiness accuracy: 28/30 = 0.9333.
- False-ready rate: 0/25 = 0.0. Denominator 25 is gold
  non-ready cases. Do not generalize this 0/25 to other
  case sets.
- Missing-evidence recall: 12/14 = 0.8571.
- Citation precision: 89/89 = 1.0.
- Retrieval recall proxy: 30/30 = 1.0, weak proxy, see above.
- Latency: p50 28834.6 ms, p95 62187.2 ms, mean 33657.8 ms.
- Cost: $0.0784 total, $0.0026 per case, script estimate,
  not a billed amount.
- Tokens: prompt 30864, output 14741.
- ADK tool calls: 30 each for search_policy_chunks,
  validate_case_codes, and extract_evidence.
- By procedure:
  - Lumbar: case accuracy 9/10 = 0.9, criterion 28/40 = 0.7.
  - Knee: case accuracy 10/10 = 1.0, criterion 58/70 = 0.8286.
  - Biologic: case accuracy 9/10 = 0.9, criterion 85/90 = 0.9444.

## Baseline, simple RAG, 30/30

- Simple single-call RAG baseline, no structured schema, no
  citation verifier, no pathway scorer.
- Attempted 30, completed 30, not completed 0.
- Criterion accuracy: 14/200 = 0.07.
- Case readiness accuracy: 13/30 = 0.4333.
- False-ready rate: 11/25 = 0.44.
- Missing-evidence recall: 14/14 = 1.0.
- Citation precision: not applicable, 0/0, because the
  baseline produces no verified citation claims in this
  measurement. Do not report this as 0 percent or 100 percent.
- Retrieval recall proxy: 30/30 = 1.0, weak proxy, see above.
- Latency: p50 11338.9 ms, p95 291571.7 ms, mean 40661.1 ms.
  The p95 is far above p50, which indicates at least one
  very slow baseline case in this run, not a stable tail
  estimate from a large sample.
- Cost: $0.0273, script estimate, not a billed amount.
- Tokens recorded: 0 prompt, 0 output. This is what Cloud
  Shell reported for the baseline, not a claim that the
  baseline used no tokens. Token recording for the baseline
  is therefore incomplete and must not be used for a
  cost-per-token comparison.

## No-citation-verification ablation, 30/30

- Attempted 30, completed 30, not completed 0.
- Criterion accuracy: 173/200 = 0.865.
- Case readiness accuracy: 28/30 = 0.9333.
- False-ready rate: 0/25 = 0.0.
- Missing-evidence recall: 12/14 = 0.8571.
- Citation precision: 90/90 = 1.0.
- Retrieval recall proxy: 30/30 = 1.0, weak proxy, see above.
- Latency: p50 31890.5 ms, p95 278082.1 ms, mean 75289.8 ms.
  Again, p95 far above p50 indicates very slow cases in
  this arm, not a stable tail estimate.
- Cost: $0.0751, script estimate, not a billed amount.

## Ablation delta, full minus no-citation

- Criterion accuracy delta: -0.01 (171/200 vs 173/200).
- Case readiness accuracy delta: 0.0 (28/30 vs 28/30).
- False-ready rate delta: 0.0 (0/25 vs 0/25).
- Missing-evidence recall delta: 0.0 (12/14 vs 12/14).
- Citation precision delta: 0.0 (89/89 vs 90/90, same rate,
  one more claim in the no-citation arm).
- Plain statement: citation verification did NOT
  demonstrably help on this 30-case set. The same 4
  prediction failures occur in both arms, differing only
  in knee criterion counts (58 vs 59) and biologic
  criterion counts (85 vs 86). Do not claim a citation
  verification gain from this run. The verifier may still
  matter for safety on other inputs, but that is not
  demonstrated here.

## Final prediction failures, reported separately

These are the only prediction failures in the complete
30/30 full run. There were no other failures, and no case
failed to complete in the final run.

1. EVAL-PMC-LUM-01, lumbar, gold NEEDS_MANUAL_REVIEW,
   predicted NOT_READY, readiness mismatch.
2. EVAL-PMC-KNE-01, knee, case correct NOT_READY,
   criterion KNE-02, gold missing, predicted met,
   missing called met.
3. EVAL-BIO-04, biologic, case correct NOT_READY,
   criterion BIO-05, gold missing, predicted met,
   missing called met.
4. EVAL-BIO-05, biologic, gold NEEDS_MANUAL_REVIEW,
   predicted NOT_READY, readiness mismatch.

Safety note: the two missing-called-met errors are
safety-relevant even though neither produced a
false-ready case, because both cases were still predicted
NOT_READY overall. A missing-called-met error on a case
that is otherwise ready would be more dangerous, and
that pattern is not ruled out by this run.

Failed-case bias investigation, final run: no case
failed to complete in the final run (0 not completed),
so no failed-case bias investigation applies to the
final 30/30 metrics. The denominators above are complete.

## Superseded first-run partial, for the record only

This partial is NOT the final result and must never be
quoted as the full eval result.

- The first full run completed 14 cases, then crashed
  with a metadata RefreshError, reported as a service
  account info missing email field. The 16 uncompleted
  cases were not recorded in not_completed_cases.
- Partial metrics, completed cases only: criterion
  55/70 = 0.7857, case readiness 13/14 = 0.9286,
  cost $0.0328, script estimate.
- A 429 was also seen in the first run and handled by
  bounded retry.
- Bias note for that partial only: missingness was
  concentrated by procedure. All 16 missing cases were
  knee 7 and biologic 9, with zero lumbar missing.
  Completed cases were lumbar 10/14, knee 3/14,
  biologic 1/14, versus the full set balance of 10/30
  per procedure. By gold readiness, missing cases were
  spread: NOT_READY 8, NEEDS_MANUAL_REVIEW 6, READY 2.
  All 3 published case report cases completed, and all
  16 missing cases were structured fixtures. This is
  consistent with a run-order infrastructure crash after
  case 14, inferred, not confirmed, not a case-difficulty
  pattern. Those 14-case metrics were not representative
  and are superseded by the complete 30/30 rerun.
- The credential path recovered on its own for the
  no-citation and full reruns. No new ADC sign-in was
  started. The root cause of the RefreshError, and of
  about 14 Cloud Shell drops during the day, remains
  undiagnosed and unresolved.

## Deployment, FAILED, do not claim

- Cloud Run deploy for priorauth-agent-demo failed with
  PERMISSION_DENIED: the default service account was
  missing required IAM permissions for Cloud Build.
- Fixing this would require IAM changes that were
  explicitly NOT authorized, so it was not retried with
  IAM changes.
- No service URL, no deployed review, no screenshot, and
  no deployed log exists from this attempt.
- Cleanup confirmed: 0 PriorAuth Cloud Run services.
- Temporary Artifact Registry repository
  cloud-run-source-deploy (0 MB, no image pushed) was
  deleted, and the Cloud Build API, enabled during the
  deploy attempt, was disabled again, restoring the
  pre-attempt state.
- Any future deployment needs separate user authorization
  for the IAM changes, plus a fresh deploy attempt.

## What remains unresolved

1. Deployment IAM: Cloud Build permissions for the
   default service account are missing, and IAM changes
   were not authorized. No deployed review exists.
2. Spend attribution gap: console delta about $4.29
   versus script-estimated model spend about $0.22.
   Do not attribute the console delta to PriorAuth alone.
3. Metadata RefreshError root cause, and about 14 Cloud
   Shell drops during the day: undiagnosed.
4. Cloud test gate: 3 credential-expectation test
   failures, root cause stated as inference only, not
   proven. Local test passes do not erase them.
5. Baseline token recording: 0/0 recorded, incomplete,
   so no token or cost-per-token comparison for the
   baseline is valid from this run.
6. Citation verification gain: not demonstrated on this
   30-case set, delta -0.01 on criterion accuracy.
7. Raw Cloud Shell JSON files ARE included unchanged in evidence/cloud_eval_2026-10-27/raw/, so any re-check can be done locally against those files; the Cloud Shell originals were at ~/pa_final4/priorauth-agent/eval/.


## AUDIT, 2026-10-27 (local, no cloud rerun)

- Baseline validation: docs/BASELINE_VALIDATION_2026-10-27.md.
  The as-run baseline prompt withheld the criterion list and status
  vocabulary, so 14/200 must NOT be quoted as pure reasoning
  accuracy. The corrected prompt in scripts/baseline.py was rerun in the cloud on 2026-10-27 after this audit (see the corrected baseline section below); at audit time it had not yet been rerun. Baseline token total for the as-run run
  was 0/0 (incomplete); fixed in code for future runs.
- Citation ablation: docs/CITATION_ABLATION_2026-10-27.md.
  Citation verification did NOT demonstrably help on this set.
  Exact differing criteria cannot be identified from the
  transcription alone and require the raw eval JSON files.
- Failure analysis: docs/FAILURE_ANALYSIS_2026-10-27.md, with
  verified inputs and unavailable-locally statements for Gemini
  prediction text, retrieved evidence, and verifier output.
- Deployment: docs/DEPLOYMENT.md. Deployment FAILED on IAM; no URL,
  screenshot, or deployed review exists.
- Spend gap: console delta about $4.29 vs script estimate about
  $0.22, unresolved.
- This file remains a transcription, not the raw Cloud Shell JSON
  files. A final regeneration must include the raw artifacts, if
  actually retrieved, in a clearly named evidence directory,
  unchanged, after a credential scan.

## Model default, REMOVED in the 2026-10-27 issue-3 fix

The runtime model fallback that was deliberately left in place
in the 2026-10-27 audit (UNVERIFIED_DEFAULT_MODEL =
gemini-3.8-flash) has now been removed. There is no model
default: PRIORAUTH_MODEL and PRIORAUTH_MODEL_LOCATION must
both be set explicitly, and require_model() in
src/priorauth/cloud_clients.py raises before any Gemini call
if either is unset. The verified pair is gemini-3.5-flash at
global, data us-central1, and a rerun must set
PRIORAUTH_MODEL=gemini-3.5-flash and
PRIORAUTH_MODEL_LOCATION=global explicitly, re-verified with
a minimal live call first. Historical note: gemini-3.8-flash
returned 404 in us-central1 for this project on 2026-10-27
and is not a default anywhere in the current code.

## Raw evidence, verified 2026-10-27 (user upload)

The original raw evaluation files are included unchanged in
evidence/cloud_eval_2026-10-27/raw/, verified by size and
sha256 against the Cloud Shell records (six exact matches;
the baseline recorded hash string in earlier notes was
63 characters, missing one '7', and is corrected in the
evidence README). Full recomputation, exact ablation
differences, and failure analyses from the raw rows are
in docs/RAW_VERIFICATION_AND_RECOMPUTATION_2026-10-27.md.
Key raw-verified corrections to earlier summaries:
citation verification did NOT explain the ablation delta
(all five differing criteria are non-met in the full arm,
so a verifier that acts only on met claims cannot have
caused it; the delta is run-to-run variation), and the
baseline embedded token total 0/0 is wrong (rows sum to
12020 prompt / 4874 candidates). The corrected baseline
rerun is a separate approved cloud task and is NOT
included in this local integration; the original baseline
remains SUPERSEDED BY CORRECTED BASELINE RERUN 2026-10-27.


## Corrected baseline rerun, 2026-10-27 - current comparison

The original as-run baseline (criterion 14/200, case 13/30, false-ready
11/25) is SUPERSEDED. The corrected baseline rerun, 2026-10-27, same
30 cases, gemini-3.5-flash at global, data us-central1, is the current
comparison: criterion 176/200, case 8/30, false-ready 18/25, missing
recall 13/14, latency p50 10.9 s, p95 14.5 s, cost $0.0463. Citation raw
90/99 is not comparable to the full system's verified 89/89. Compared
with the full system (171/200, 28/30, 0/25), the criterion gap reversed
by 5 criteria, so that part of the original gap was prompt artifact;
the genuine full-system value is readiness determination and
false-ready prevention, where the corrected baseline remains far
behind (8/30 vs 28/30, 18/25 vs 0/25). The corrected baseline raw JSON file IS included in this pack, unchanged, at evidence/cloud_eval_2026-10-27/raw/results_baseline_corrected.json (116,872 bytes, SHA-256 ed13f335aff8b1452a8419b39b33e1fa63e35a31710f18d115caff1d60986ff9), copied byte-for-byte from the user upload of the Cloud Shell original and recomputed from its rows. See evidence/cloud_eval_2026-10-27/corrected_baseline_summary_2026-10-27.md
in the GitHub pack, or corrected_baseline_summary_2026-10-27.md in
this pack.
