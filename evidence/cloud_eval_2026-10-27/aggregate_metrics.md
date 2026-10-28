# Aggregate metrics, Cloud Shell reads, 2026-10-27

Model: gemini-3.5-flash. Model location: global. Data location:
us-central1. Project: delivery-experience-511901. Run window:
2026-10-27, 9:59 AM to 1:12 PM ET, from pa_adk_transfer4.zip in
Cloud Shell at ~/pa_final4/priorauth-agent/. All metrics are for
the 30-case annotated set only and must not be generalized.

## Full system, citation verification on, 30/30
Criterion 171/200 = 0.855. Case readiness 28/30 = 0.9333.
False-ready 0/25 = 0.0. Missing-evidence recall 12/14 = 0.8571.
Citation precision 89/89 = 1.0. Retrieval recall proxy 30/30 = 1.0
(weak proxy, no chunk-level gold set). Latency p50 28834.6 ms,
p95 62187.2 ms, mean 33657.8 ms. Cost $0.0784 total, $0.0026 per
case, script estimate, not a billed amount. Tokens prompt 30864,
output 14741. ADK tool calls 30 each for search_policy_chunks,
validate_case_codes, extract_evidence.
By procedure: lumbar case 9/10, criterion 28/40; knee case 10/10,
criterion 58/70; biologic case 9/10, criterion 85/90.

## Baseline, simple RAG, 30/30
Criterion 14/200 = 0.07. Case readiness 13/30 = 0.4333.
False-ready 11/25 = 0.44. Missing-evidence recall 14/14 = 1.0.
Citation precision not applicable, 0/0. Retrieval proxy 30/30.
Latency p50 11338.9 ms, p95 291571.7 ms, mean 40661.1 ms.
Cost $0.0273 script estimate. Tokens recorded 0/0, incomplete,
so no token or cost-per-token comparison for the baseline is
valid. Audit finding, not a rerun: the as-run baseline prompt
withheld the criterion list and status vocabulary, so 14/200
must NOT be quoted as pure reasoning accuracy, and the
171-vs-14 delta must NOT be quoted as the pure value of the
structured workflow. The corrected prompt in scripts/baseline.py WAS rerun in the cloud on 2026-10-27 (completed 10:52 PM ET): criterion 176/200, case 8/30, false-ready 18/25, missing recall 13/14, cost $0.0463; its raw file is now in evidence/cloud_eval_2026-10-27/raw/results_baseline_corrected.json.

## No-citation ablation, 30/30
Criterion 173/200 = 0.865. Case readiness 28/30 = 0.9333.
False-ready 0/25 = 0.0. Missing-evidence recall 12/14 = 0.8571.
Citation precision 90/90 = 1.0. Retrieval proxy 30/30.
Latency p50 31890.5 ms, p95 278082.1 ms, mean 75289.8 ms.
Cost $0.0751 script estimate. Tokens prompt 30673, output 13902.
Delta (full minus no-citation): criterion -0.01, case 0.0,
false-ready 0.0, citation 0.0, missing-evidence recall 0.0.
Citation verification did NOT demonstrably help on this set.
Exact differing criteria were NOT verified in this audit and
are NOT listed here; only knee 58 vs 59 and biologic 85 vs 86
are known, lumbar identical at 28/40.

## Pilot, n=3, pilot only, NOT full performance
Attempted 3, completed 3, not completed 0. Criterion 16/20 = 0.8.
Case readiness 2/3 = 0.6667. False-ready 0 (pilot non-ready
denominator as reported). Missing-evidence recall 3/4 = 0.75.
Citation 8/8 = 1.0. Retrieval proxy 3/3. Latency p50 30285.4 ms,
p95 32936.2 ms, mean 30716.3 ms. Cost $0.0081 script estimate.
Tokens prompt 3228, output 1523. Tool events 7 per case.

## Superseded first-run partial, record only, NOT the final result
Completed 14, then metadata RefreshError crash. Criterion
55/70 = 0.7857. Case readiness 13/14 = 0.9286. Cost $0.0328
script estimate. The 16 uncompleted cases were not recorded
in not_completed_cases. Missingness was procedure-concentrated
(knee 7, biologic 9, lumbar 0) and not representative. Root
cause of the RefreshError and about 14 Cloud Shell drops
during the day remains undiagnosed.

## Cap and spend, 2026-10-27 attempt
Before about $28.76 / $10.00, raised to $50 for this attempt
only, restored to $10 at about 1:07 to 1:08 PM ET, final about
$33.05 / $10.00. Console delta about $4.29, below the $8 stop
and $10 ceiling. Script-estimated model spend about $0.22
total. The gap between console delta and script estimates is
UNRESOLVED; do not attribute the console delta to PriorAuth
alone. Console lag and other Vertex usage during the day are
possible but unproven explanations.

## Deployment, FAILED, do not claim
Cloud Run deploy for priorauth-agent-demo failed with
PERMISSION_DENIED for the Cloud Build default service
account. IAM changes were not authorized, so it was not
retried with IAM changes. No service URL, no deployed review,
no screenshot, no deployed log exists. Cleanup confirmed 0
PriorAuth Cloud Run services. The temporary Artifact Registry
repository was deleted and Cloud Build API was disabled again.
