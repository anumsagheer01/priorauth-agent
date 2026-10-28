# Per-case readiness summary, full system, 2026-10-27

Cloud Shell read summary, NOT the raw file. This table is derived
from two verified sources only: the gold labels in
data/eval_cases.json in this repo, and the two reported readiness
mismatches in the Cloud Shell full-run report (EVAL-PMC-LUM-01 and
EVAL-BIO-05, both gold NEEDS_MANUAL_REVIEW, predicted NOT_READY).
All other 28 cases are recorded as predicted equals gold, which is
exactly what case readiness accuracy 28/30 with only those two
readiness mismatches requires. No per-case latency, token split,
retrieved chunk, excerpt, or Gemini prediction text is included
here, because those per-case values were NOT available locally
and are NOT invented. To check them, use the raw file
results_real.json in Cloud Shell at
~/pa_final4/priorauth-agent/eval/ (see EVIDENCE_README.md).

| case_id | procedure | source_type | gold_readiness | predicted_readiness | case_correct | criterion_note |
|---|---|---|---|---|---|---|
| EVAL-PMC-LUM-01 | lumbar_mri | published_case_report | NEEDS_MANUAL_REVIEW | NOT_READY | readiness_mismatch |  |
| EVAL-PMC-KNE-01 | knee_arthroscopy | published_case_report | NOT_READY | NOT_READY | correct | Criterion KNE-02: gold missing, predicted met (missing-called-met). Case readiness still correct. |
| EVAL-PMC-BIO-01 | biologic_infusion | published_case_report | NOT_READY | NOT_READY | correct |  |
| EVAL-LUM-01 | lumbar_mri | structured_test_fixture | READY_FOR_HUMAN_REVIEW | READY_FOR_HUMAN_REVIEW | correct |  |
| EVAL-LUM-02 | lumbar_mri | structured_test_fixture | NEEDS_MANUAL_REVIEW | NEEDS_MANUAL_REVIEW | correct |  |
| EVAL-LUM-03 | lumbar_mri | structured_test_fixture | NEEDS_MANUAL_REVIEW | NEEDS_MANUAL_REVIEW | correct |  |
| EVAL-LUM-04 | lumbar_mri | structured_test_fixture | NOT_READY | NOT_READY | correct |  |
| EVAL-LUM-05 | lumbar_mri | structured_test_fixture | READY_FOR_HUMAN_REVIEW | READY_FOR_HUMAN_REVIEW | correct |  |
| EVAL-LUM-06 | lumbar_mri | structured_test_fixture | NEEDS_MANUAL_REVIEW | NEEDS_MANUAL_REVIEW | correct |  |
| EVAL-LUM-07 | lumbar_mri | structured_test_fixture | NEEDS_MANUAL_REVIEW | NEEDS_MANUAL_REVIEW | correct |  |
| EVAL-LUM-08 | lumbar_mri | structured_test_fixture | NOT_READY | NOT_READY | correct |  |
| EVAL-LUM-09 | lumbar_mri | structured_test_fixture | NEEDS_MANUAL_REVIEW | NEEDS_MANUAL_REVIEW | correct |  |
| EVAL-KNE-01 | knee_arthroscopy | structured_test_fixture | READY_FOR_HUMAN_REVIEW | READY_FOR_HUMAN_REVIEW | correct |  |
| EVAL-KNE-02 | knee_arthroscopy | structured_test_fixture | NOT_READY | NOT_READY | correct |  |
| EVAL-KNE-03 | knee_arthroscopy | structured_test_fixture | NOT_READY | NOT_READY | correct |  |
| EVAL-KNE-04 | knee_arthroscopy | structured_test_fixture | NEEDS_MANUAL_REVIEW | NEEDS_MANUAL_REVIEW | correct |  |
| EVAL-KNE-05 | knee_arthroscopy | structured_test_fixture | READY_FOR_HUMAN_REVIEW | READY_FOR_HUMAN_REVIEW | correct |  |
| EVAL-KNE-06 | knee_arthroscopy | structured_test_fixture | NOT_READY | NOT_READY | correct |  |
| EVAL-KNE-07 | knee_arthroscopy | structured_test_fixture | NEEDS_MANUAL_REVIEW | NEEDS_MANUAL_REVIEW | correct |  |
| EVAL-KNE-08 | knee_arthroscopy | structured_test_fixture | NEEDS_MANUAL_REVIEW | NEEDS_MANUAL_REVIEW | correct |  |
| EVAL-KNE-09 | knee_arthroscopy | structured_test_fixture | NOT_READY | NOT_READY | correct |  |
| EVAL-BIO-01 | biologic_infusion | structured_test_fixture | READY_FOR_HUMAN_REVIEW | READY_FOR_HUMAN_REVIEW | correct |  |
| EVAL-BIO-02 | biologic_infusion | structured_test_fixture | NOT_READY | NOT_READY | correct |  |
| EVAL-BIO-03 | biologic_infusion | structured_test_fixture | NOT_READY | NOT_READY | correct |  |
| EVAL-BIO-04 | biologic_infusion | structured_test_fixture | NOT_READY | NOT_READY | correct | Criterion BIO-05: gold missing, predicted met (missing-called-met). Case readiness still correct. |
| EVAL-BIO-05 | biologic_infusion | structured_test_fixture | NEEDS_MANUAL_REVIEW | NOT_READY | readiness_mismatch |  |
| EVAL-BIO-06 | biologic_infusion | structured_test_fixture | NOT_READY | NOT_READY | correct |  |
| EVAL-BIO-07 | biologic_infusion | structured_test_fixture | NEEDS_MANUAL_REVIEW | NEEDS_MANUAL_REVIEW | correct |  |
| EVAL-BIO-08 | biologic_infusion | structured_test_fixture | NOT_READY | NOT_READY | correct |  |
| EVAL-BIO-09 | biologic_infusion | structured_test_fixture | NEEDS_MANUAL_REVIEW | NEEDS_MANUAL_REVIEW | correct |  |

Counts check: gold READY 5, NOT_READY 13, NEEDS_MANUAL_REVIEW 12;
predicted READY 5, NOT_READY 15, NEEDS_MANUAL_REVIEW 10;
case correct 28/30, false-ready 0/25 (no gold non-ready case
predicted READY).
