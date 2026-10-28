# Baseline validation, 2026-10-27 audit

Status: code investigation only, from `scripts/baseline.py`,
`scripts/evaluate_real.py`, `scripts/eval_metrics.py`,
`src/priorauth/real_pipeline.py`, and the transcribed 2026-10-27
results. No cloud rerun was made in this audit; at audit time the corrected
baseline prompt had not yet been rerun. UPDATE 2026-10-28: the corrected
baseline WAS rerun on 2026-10-27 (completed 10:52 PM ET, criterion
176/200, case 8/30, false-ready 18/25), and its raw file is now included
unchanged in the GitHub pack at evidence/cloud_eval_2026-10-27/raw/results_baseline_corrected.json.
The 2026-10-27 baseline numbers below remain the as-run numbers, with
the flaw disclosed, not silently replaced.

## As-run numbers (do not quote without the flaw)

- Full system, 30/30: criterion 171/200, case 28/30, false-ready 0/25.
- Baseline, 30/30: criterion 14/200, case 13/30, false-ready 11/25,
  missing-evidence recall 14/14, citation precision not applicable
  (0/0), cost $0.0273, tokens recorded 0/0 (incomplete, see below).

## What was checked and found

### No label-mapping bug, no denominator bug

Both scripts copy gold readiness and gold criterion outcomes verbatim
from the case record, and both call the same `compute_metrics`
function in `scripts/eval_metrics.py`. Denominators are identical:
200 criteria (lumbar 4 + knee 7 + biologic 9, times 10 cases each),
30 cases, 25 gold non-ready cases (12 NEEDS_MANUAL_REVIEW + 13
NOT_READY, gold READY = 5), 14 gold missing criteria. There is no
denominator mismatch to explain the gap.

### Output parsing: same missing-default, different vocabulary discipline

- Baseline (`scripts/baseline.py`, `_one_case`): the model output is
  parsed as JSON, then each policy criterion is filled from
  `pred.get(criterion_id, "missing")`. A criterion the model did
  not return, or returned under a non-matching ID, therefore counts
  as a prediction of "missing", not as excluded. Unparseable JSON
  propagates (it is not silently counted), and only 429 errors are
  recorded as not completed. A completed 30/30 run therefore implies
  all 30 baseline JSON outputs parsed.
- Full system: omitted criteria are also filled as "missing", and
  unknown IDs are dropped. The difference is not the default, it is
  what the model was told (next section).

### The decisive flaw: the baseline prompt withheld the checklist

The baseline prompt used for the 2026-10-27 run gave the policy ID
and title, retrieved chunk texts only (chunk IDs and sections
dropped), and the clinical note, then asked for readiness and "one
status per criterion", with no criterion list and no status
vocabulary. The retrieved chunks themselves contain no criterion IDs
(all 7 chunks in `data/policy_chunks.json` are paraphrases with no
LUM-01, KNE-04, or BIO-01 strings). The only place those IDs exist
is `policy.criteria`, which the baseline prompt never included.

The full system prompt, in `src/priorauth/real_pipeline.py`
(`extract_evidence_with_gemini`), includes the full criterion list
(ID, kind, section, text), the status list (met, not_met, uncertain,
contradictory, missing, not_applicable, fired, not_fired), the
missing-vs-not_met and uncertain and contradictory rules, the exact
excerpt requirement, patient age, and diagnosis and procedure codes,
plus deterministic code validation, citation verification, and the
pathway scorer in `finalize_review`.

Consequence: the baseline could not reliably emit matching IDs or
status strings, so nearly every non-missing gold label was
unreachable by exact match, while gold missing labels were "correct"
by default. That arithmetic is exactly consistent with the reported
numbers: criterion-correct 14 equals the gold missing count (14),
missing recall 14/14 follows from the same default, while readiness
(whose three vocabulary strings WERE given in the prompt) still
scored 13/30.

This is a hypothesis about row-level composition, not a proven
row-level fact: no local baseline row file exists to confirm it, and
the raw Cloud Shell JSON files were not available in this audit.
The code fact is verified (prompt withheld the checklist, scoring
is exact-match with default-missing); the row-level inference is
stated as such. Either way, the dominant mechanism is the withheld
checklist, not a demonstrated clinical-judgment failure on 186
criteria.

### Comparable retrieval and generation: yes, both real

- Retrieval is the same function (`retrieve_chunks` in
  `src/priorauth/real_pipeline.py`): policy-scoped chunks, Vertex
  `text-embedding-004` embeddings, BigQuery VECTOR_SEARCH top 5 with
  a cosine fallback, no keyword fallback, no mock. The ADK path calls
  the same function through the `search_policy_chunks` tool.
- Generation is real: one Gemini call per case through
  `gemini_generate` in `src/priorauth/cloud_clients.py`, with a JSON
  schema. Cost $0.0273 for 30 cases reflects real token usage, not a
  stub. Non-429 failures propagate rather than falling back to a
  canned answer.

### What is legitimately weaker about the baseline

The case-level gap is a real structured-vs-unstructured difference,
not an artifact: the baseline readiness is an unconstrained model
guess with no pathway rule, no exclusion block, no code check, and
no uncertainty rule. The deterministic `checklist_scorer` in
`src/priorauth/tools.py` blocks READY unless a full pathway is met,
no exclusion fires, codes are valid, and the version is current,
which is why the full system is 0/25 on false-ready while the
baseline is 11/25. That part of the gap should be quoted.

One further caveat: gold readiness was derived from gold outcomes
by the deterministic pathway scorer plus code and version checks, so
the full system's readiness IS that scorer's output, which partly
aligns its case accuracy by construction. This does not explain the
criterion gap (gold criterion outcomes were authored, not
scorer-derived), but it flatters the full system's 28/30 vs 13/30
comparison.

### Token reporting bug, fixed in code, not in the as-run numbers

The 2026-10-27 baseline token total was 0/0 because
`scripts/eval_metrics.py` summed only `evidence_*` and `draft_*`
token keys, while baseline rows store raw Gemini usage
(`prompt_token_count` / `candidates_token_count`). This affected no
accuracy metric, only token reporting. Fixed in this audit:
`eval_metrics.py` now sums both key sets without double-counting a
row that carries both, and `scripts/baseline.py` also exposes the
`evidence_*` keys. The as-run 0/0 figure remains reported as
incomplete for the 2026-10-27 run; do not use it for any token or
cost-per-token comparison for the baseline.

### Citation precision for the baseline: not applicable, not zero quality

Citation precision counts only met claims with excerpts. The
baseline prompt never requested excerpts, so 0/0 means "no scored
citations", not "all citations bad". Do not quote it as a quality
score.

## Correction applied, and what remains to be rerun

`scripts/baseline.py` now includes, in the prompt, the same
criterion list (ID, kind, section, text) and status semantics as the
full system, plus patient age and codes, while still making only one
call and using no citation verification, no code validation, and no
pathway scorer. A test in `tests/test_baseline_prompt.py` asserts
the prompt contains every criterion ID and the status list, and that
token totals are no longer 0/0 for baseline rows.

Until a future cloud rerun with this corrected prompt (which needs
separate billable authorization, not granted in this audit), the
honest summary is: the baseline is genuinely weaker as a single
unstructured call with no guardrails (hence 13/30 cases and 11
false-readies), but its 14/200 criterion score is dominated by a
withheld-checklist artifact and must NOT be quoted as the model's
criterion-judgment accuracy. The 171-vs-14 delta conflates "was the
model told what to score" with "does the structured workflow help";
only a post-fix rerun can isolate the structured workflow's
contribution.

## Spend gap note

This document does not resolve the console spend attribution gap
(console delta about $4.29 vs script-estimated model spend about
$0.22 for the 2026-10-27 attempt). That gap remains documented as
unresolved in `docs/EVAL_RESULTS_2026-10-27.md`.


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
behind (8/30 vs 28/30, 18/25 vs 0/25). The corrected baseline raw JSON file IS included locally, unchanged, in the GitHub pack at evidence/cloud_eval_2026-10-27/raw/results_baseline_corrected.json (116,872 bytes, SHA-256 ed13f335aff8b1452a8419b39b33e1fa63e35a31710f18d115caff1d60986ff9), copied byte-for-byte from the user upload of the Cloud Shell original and recomputed from its rows. See evidence/cloud_eval_2026-10-27/corrected_baseline_summary_2026-10-27.md
in the GitHub pack, or corrected_baseline_summary_2026-10-27.md in
this pack.
