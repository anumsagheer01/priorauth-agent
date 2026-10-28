# Corrected baseline rerun, 2026-10-27 - summary

## Status and raw-file inclusion

This summary is the current baseline comparison. The original as-run baseline
(result below, labeled SUPERSEDED) is history only and must not be quoted as
the current baseline.

The raw corrected baseline JSON file IS included in this pack, unchanged,
at `evidence/cloud_eval_2026-10-27/raw/results_baseline_corrected.json`
(116,872 bytes, SHA-256 ed13f335aff8b1452a8419b39b33e1fa63e35a31710f18d115caff1d60986ff9).
It was supplied by the user as the original Cloud Shell file from
`~/pa_baseline_rerun/priorauth-agent/eval/results_baseline_corrected.json`,
copied byte-for-byte with no modification, renaming, or reformatting,
and its size and SHA-256 were verified again after copying. Its metrics
were independently recomputed from its rows with
`scripts/eval_metrics.py` and match its embedded metrics exactly:
criterion 176/200, case 8/30, false-ready 18/25, missing recall 13/14,
citation raw 90/99, retrieval proxy 30/30, latency p50 10895.2 ms,
p95 14518.9 ms, mean 11290.1 ms, tokens prompt 24488, output 7457,
total 31945, cost $0.0463 total, $0.0015 per case, by procedure lumbar
case 4/10 and criterion 28/40, knee case 3/10 and criterion 61/70,
biologic case 1/10 and criterion 87/90, failures list 23 entries
(22 case readiness: 18 false_ready, 4 readiness_mismatch, plus
1 criterion missing_called_met for EVAL-PMC-KNE-01 KNE-02).
This summary is NOT a reconstruction of that file. No per-case corrected
baseline row, retrieved chunk, excerpt, or Gemini prediction text is
reproduced here beyond the failure lists below, which are from the
approved rerun report and are confirmed by the included raw file.

The original baseline raw file, `evidence/cloud_eval_2026-10-27/raw/results_baseline.json`,
is kept unchanged and is labeled SUPERSEDED. It is NOT overwritten.

## Run record

- Approved rerun: 2026-10-27, 9:51 to 10:52 PM ET, user-approved on the
  terms stated in the rerun assignment.
- Project: delivery-experience-511901. Model: gemini-3.5-flash at global.
  Data location: us-central1. Dataset: priorauth_agent.
- Scope: corrected baseline only, same 30 cases as the full system,
  real retrieval, one Gemini call per case, no citation verifier,
  no deterministic scorer. No full system rerun, no deployment.
- Verification: the first minimal "Say OK" call failed with 403 spend cap.
  The Vertex AI cap was lifted to $50, the retry succeeded with response
  OK in 4229.2 ms, tokens prompt 2, output 1, total 75, via the
  gemini_generate path, not an ADK Runner run.
- Cap: before $10, usage about $33.05. Lifted to $50 at 10:16 PM.
  Restored to $10 at 10:52 PM, final usage about $33.69.
  Console delta about $0.64. Script estimate $0.0463.
  Both are well under the $8 stop and the $10 incremental ceiling.
  No IAM, billing, or other cap change was made.
- First baseline attempt aborted after 4 cases with the same 403.
  Cause is unproven; transient lift propagation is a hypothesis only.
  That partial was discarded, the run was retried from the start,
  and no model, prompt, or gold label was changed.

## Corrected baseline results, 30 of 30, 0 not completed

- Criterion accuracy: 176/200 = 0.88. Errors: 24.
- Case readiness accuracy: 8/30 = 0.2667.
- False-ready rate: 18/25 = 0.72.
- Missing-evidence recall: 13/14 = 0.9286.
- Citation, raw: 90/99 = 0.9091. This is NOT comparable to the full
  system's verified 89/89, because the baseline has no citation
  verifier and its citation denominator is defined differently.
- Retrieval recall proxy: 30/30.
- Latency: p50 10895.2 ms, p95 14518.9 ms, mean 11290.1 ms.
- Tokens: prompt 24488, output 7457, total 31945.
- Cost: $0.0463 total, $0.0015 per case, script estimate.

By procedure, corrected baseline:
- Lumbar spine MRI: case 4/10, criterion 28/40.
- Knee arthroscopy: case 3/10, criterion 61/70.
- Biologic infusion: case 1/10, criterion 87/90.
- Sums check: cases 4 + 3 + 1 = 8; criteria 28 + 61 + 87 = 176.

## Failures, as reported in the approved rerun report

Case readiness failures: 22 cases, comprising 18 false_ready and
4 readiness_mismatch, plus 1 criterion entry in the failures list.
Gold and predicted readiness are shown as gold -> predicted.

- EVAL-PMC-LUM-01: NEEDS_MANUAL_REVIEW -> READY_FOR_HUMAN_REVIEW, false_ready.
- EVAL-PMC-KNE-01: NOT_READY -> READY_FOR_HUMAN_REVIEW, false_ready, and criterion KNE-02 gold missing predicted met, missing_called_met.
- EVAL-PMC-BIO-01: NOT_READY -> NEEDS_MANUAL_REVIEW, readiness_mismatch.
- EVAL-LUM-04: NOT_READY -> READY_FOR_HUMAN_REVIEW, false_ready.
- EVAL-LUM-06: NEEDS_MANUAL_REVIEW -> READY_FOR_HUMAN_REVIEW, false_ready.
- EVAL-LUM-07: NEEDS_MANUAL_REVIEW -> READY_FOR_HUMAN_REVIEW, false_ready.
- EVAL-LUM-08: NOT_READY -> READY_FOR_HUMAN_REVIEW, false_ready.
- EVAL-LUM-09: NEEDS_MANUAL_REVIEW -> READY_FOR_HUMAN_REVIEW, false_ready.
- EVAL-KNE-02: NOT_READY -> READY_FOR_HUMAN_REVIEW, false_ready.
- EVAL-KNE-03: NOT_READY -> READY_FOR_HUMAN_REVIEW, false_ready.
- EVAL-KNE-05: READY_FOR_HUMAN_REVIEW -> NEEDS_MANUAL_REVIEW, readiness_mismatch.
- EVAL-KNE-06: NOT_READY -> NEEDS_MANUAL_REVIEW, readiness_mismatch.
- EVAL-KNE-07: NEEDS_MANUAL_REVIEW -> READY_FOR_HUMAN_REVIEW, false_ready.
- EVAL-KNE-09: NOT_READY -> NEEDS_MANUAL_REVIEW, readiness_mismatch.
- EVAL-BIO-02: NOT_READY -> READY_FOR_HUMAN_REVIEW, false_ready.
- EVAL-BIO-03: NOT_READY -> READY_FOR_HUMAN_REVIEW, false_ready.
- EVAL-BIO-04: NOT_READY -> READY_FOR_HUMAN_REVIEW, false_ready.
- EVAL-BIO-05: NEEDS_MANUAL_REVIEW -> READY_FOR_HUMAN_REVIEW, false_ready.
- EVAL-BIO-06: NOT_READY -> READY_FOR_HUMAN_REVIEW, false_ready.
- EVAL-BIO-07: NEEDS_MANUAL_REVIEW -> READY_FOR_HUMAN_REVIEW, false_ready.
- EVAL-BIO-08: NOT_READY -> READY_FOR_HUMAN_REVIEW, false_ready.
- EVAL-BIO-09: NEEDS_MANUAL_REVIEW -> READY_FOR_HUMAN_REVIEW, false_ready.

Criterion errors, all 24, shown as gold -> predicted:

- EVAL-PMC-LUM-01: LUM-01 uncertain -> not_met; LUM-02 uncertain -> met; LUM-03 not_applicable -> missing.
- EVAL-PMC-KNE-01: KNE-02 missing -> met; KNE-05 not_applicable -> not_met.
- EVAL-LUM-01: LUM-03 not_applicable -> missing.
- EVAL-LUM-02: LUM-03 not_applicable -> uncertain.
- EVAL-LUM-03: LUM-03 not_applicable -> contradictory.
- EVAL-LUM-04: LUM-03 not_applicable -> missing.
- EVAL-LUM-06: LUM-03 not_applicable -> missing.
- EVAL-LUM-07: LUM-03 not_applicable -> missing.
- EVAL-LUM-08: LUM-03 not_applicable -> missing.
- EVAL-LUM-09: LUM-02 uncertain -> contradictory; LUM-03 not_applicable -> missing.
- EVAL-KNE-01: KNE-05 not_applicable -> missing.
- EVAL-KNE-02: KNE-05 not_applicable -> missing.
- EVAL-KNE-03: KNE-05 not_applicable -> missing.
- EVAL-KNE-05: KNE-04 missing -> not_met.
- EVAL-KNE-06: KNE-05 not_applicable -> missing.
- EVAL-KNE-08: KNE-05 not_applicable -> missing.
- EVAL-KNE-09: KNE-05 not_applicable -> missing.
- EVAL-BIO-02: BIO-05 missing -> not_met.
- EVAL-BIO-05: BIO-02 uncertain -> not_met.
- EVAL-BIO-06: BIO-05 contradictory -> met.

Pattern: 16 of the 24 criterion errors have gold not_applicable,
13 of them predicted missing, concentrated in LUM-03 and KNE-05.

## Comparison to the full system

Full system, 2026-10-27, citation verification on, 30/30:
criterion 171/200, case 28/30, false-ready 0/25, missing recall 12/14,
citation 89/89, latency p50 28834.6 ms, p95 62187.2 ms, cost $0.0784.

- Criterion accuracy: corrected baseline 176/200 vs full 171/200.
  The gap is REVERSED, by 5 criteria. Essentially all of the original
  criterion gap (171 vs the flawed as-run baseline's 14/200) was
  prompt artifact, not structured-workflow value on criterion judgment.
- Missing-evidence recall: corrected baseline 13/14 vs full 12/14,
  a difference of 1, also consistent with prompt artifact.
- Case readiness accuracy: corrected baseline 8/30 vs full 28/30.
  The gap WIDENED to 20 cases. The corrected baseline is also 5 cases
  worse than even the flawed as-run baseline on this measure (8 vs 13).
  Single-run variance may contribute, but the direction is unambiguous.
- False-ready rate: corrected baseline 18/25 vs full 0/25, and worse
  than the as-run baseline's 11/25.
- Citation: not like-for-like. Corrected baseline raw 90/99 has no
  verifier; full system verified 89/89 is computed after verification.
  Do not compare them as if they were the same measure.
- Latency and cost: lower for the baseline, as expected for one call
  per case versus a multi-step ADK workflow (p50 10.9 s vs 28.8 s;
  $0.0463 vs $0.0784).

Plain conclusion: the corrected prompt recovers and slightly exceeds
the full system on criterion judgment and missing recall, so that part
of the original comparison was prompt artifact. The full system's
genuine structured-workflow value is in readiness determination and
false-ready prevention, through the deterministic scorer and the
guardrails the baseline lacks, where the corrected baseline remains
far behind. The corrected baseline is NOT the full system.

## Original baseline, superseded history only

Original as-run baseline, 30/30, raw file in `raw/results_baseline.json`:
criterion 14/200, case 13/30, false-ready 11/25, missing recall 14/14,
citation not applicable 0/0, retrieval proxy 30/30, cost $0.0273,
tokens recorded 0/0 (incomplete, known old-code bug; rows sum to
prompt 12020, candidates 4874).

Why it is superseded: its prompt withheld the criterion list and
status vocabulary that exact-match scoring requires, so every
predicted criterion status in its rows is missing (200/200), with
empty evidence excerpts. Its 14/200 equals the 14 gold missing
criteria and must not be quoted as criterion-judgment accuracy.
The corrected rerun above replaces it as the current comparison.

## What this summary does not claim

- It does not claim the corrected baseline raw file is included.
- It does not claim citation verification improved accuracy.
  The ablation delta is -0.01 (full 171/200 vs no-citation 173/200),
  and the verifier cannot explain that delta, because none of the
  five differing criteria is predicted met in the full arm.
- It does not claim successful Cloud Run deployment. Deployment
  FAILED on IAM permissions, with no URL, screenshot, or deployed
  review.
- All metrics are for this 30-case annotated set only and must not
  be generalized to other case sets, real prior authorization
  packets, or clinical use.
