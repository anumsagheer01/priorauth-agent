# Citation ablation, 2026-10-27 audit

Status: code investigation plus transcribed results only. The raw
Cloud Shell JSON files were not available locally in this audit, so
the exact differing criteria cannot be identified here, and none are
invented below. Identification requires the raw eval files, which are
being retrieved separately.

## Transcribed numbers (30/30 in both arms)

- Full system, citation verification on: criterion 171/200, case
  28/30, false-ready 0/25, missing-evidence recall 12/14, citation
  precision 89/89, cost $0.0784.
- No-citation arm, verification off: criterion 173/200, case 28/30,
  false-ready 0/25, missing-evidence recall 12/14, citation
  precision 90/90, cost $0.0751.
- Delta (full minus no-citation): criterion -0.01, case 0.0,
  false-ready 0.0, citation precision 0.0 (rate), missing-evidence
  recall 0.0.
- By procedure, criterion: lumbar 28/40 in both arms; knee 58/70 full
  vs 59/70 no-citation; biologic 85/90 full vs 86/90 no-citation.
- Same 4 prediction failures in both arms (see
  `docs/FAILURE_ANALYSIS_2026-10-27.md`).

## Plain conclusion

Citation verification did NOT demonstrably help on this 30-case
set. It did not improve criterion accuracy (it was 2 criteria
lower), did not change case accuracy, did not change false-ready
rate, and did not change missing-evidence recall. Do NOT claim it
improved accuracy or prevented any false-ready decision on this
run, because the data do not demonstrate that. Any safety value on
other inputs is unproven by this run, not disproven.

## What the verifier actually does

Entry point: `src/priorauth/real_pipeline.py`, `finalize_review`.
If `verify_citations` is True, it calls `tools.citation_verifier`
and records `citation_verifier:deterministic_quote_check`; if False
(as in the ablation arm, via `--no-citation-verification`), it skips
it and records `citation_verifier:disabled_for_ablation`.

A claim is built ONLY for a predicted `met` result with a non-empty
`evidence_excerpts` list, using only the first excerpt. The checks in
`src/priorauth/tools.py`, `citation_verifier`, are:

1. Complete policy citation: citation policy ID and section are
   non-empty only. The code does not compare them against the
   criterion's actual policy or section, despite the docstring
   wording; in this pipeline they are constructed from the correct
   policy and criterion anyway, so this check is effectively
   vacuous here.
2. Excerpt verbatim in the note: Python substring, case-sensitive,
   no fuzzy or paraphrase matching. This is the only operative check
   in practice.
3. Excerpt among the extractor's excerpts for that criterion: also
   effectively vacuous here, because the claim excerpt IS
   `evidence_excerpts[0]`, so it is by construction in that list.

What it does NOT check: semantic entailment (whether the excerpt
actually proves the criterion), policy-text support, or any excerpt
beyond the first. A verbatim sentence that is clinically irrelevant
to the criterion passes. A met result with no excerpts at all
produces no claim and is never verified, so it stays met.

What happens to a failing met claim: it is downgraded to `missing`,
its excerpts are cleared, and a finding is recorded in
`critic_findings`. It is never downgraded to `not_met` or
`uncertain`, and nothing is ever upgraded. Only `met` results are
touched; `missing`, `not_met`, `uncertain`, `contradictory`, and
`fired` statuses pass through unchanged.

## Why it could plausibly lower criterion accuracy by 2

The verifier is one-way and downgrade-only. A gold-correct `met`
whose first excerpt is paraphrased, re-cased, or re-punctuated, and
therefore not an exact substring, becomes `missing`, which is wrong
if gold is `met`, costing one criterion. It can only raise accuracy
in the opposite direction (gold `missing`, predicted `met` with a
bad excerpt, downgraded to `missing`, which is correct). Missing
recall is identical (12/14) in both arms, so no such rescue happened
on this set; the two missing-called-met errors (KNE-02, BIO-05)
survived verification in the full arm.

Case accuracy and false-ready are insulated in the same direction:
`checklist_scorer` only awards READY when an entire pathway is fully
met, so downgrading a `met` to `missing` can only move a case away
from READY or leave an already non-ready case unchanged. If the
downgraded criteria sat in cases already NOT_READY or
NEEDS_MANUAL_REVIEW for other reasons, case accuracy does not move,
consistent with 28/30 in both arms and the same 2 readiness
mismatches. A downgrade can only prevent a false READY, never create
one, and both arms already had 0 false-ready cases, so there was no
false-ready for the verifier to prevent on this set.

## Why the -2 cannot be cleanly attributed to the verifier alone

1. The arms are not paired. `scripts/ablation.py` merely diffs two
   output files from two separate `evaluate_real.py` runs, each
   making its own fresh Gemini extraction calls. Run-to-run variation
   in the model's extraction is therefore a competing explanation
   for part or all of the -2, and the transcription alone cannot
   separate verifier effect from model variation.
2. Arithmetic tension: citation precision is computed in
   `scripts/eval_metrics.py` post-verification, per excerpt.
   Denominator = total excerpts across surviving `met` results.
   Full 89 vs ablation 90 is a gap of exactly one surviving excerpt.
   Under a paired-prediction assumption, two verifier downgrades of
   single-excerpt claims would predict a gap of at least 2. The
   observed gap of 1 is inconsistent with a pure two-downgrade
   story, reinforcing point 1, and/or that the differing predictions
   had different excerpt counts. This is a reason to distrust a
   simple "verifier cost 2 criteria" reading, not a license to
   invent which criteria differ.
3. "Same 4 failures" does not mean identical predictions.
   `eval_metrics.py` appends to `failures` only
   `missing_called_met`, `false_ready`, and `readiness_mismatch`
   cases. A gold-`met` predicted `missing` error, exactly what a
   verifier false downgrade produces, increments the criterion-error
   count but is invisible in the failures list. The full arm can
   therefore carry 2 extra silent criterion errors while still
   showing "the same 4 failures".

## Citation precision, separately

- Full arm: 89/89 = 1.0. No-citation arm: 90/90 = 1.0.
- The denominator is a count of excerpts, not claims. The full arm
  has one fewer surviving `met` excerpt, consistent with a verifier
  downgrade clearing one claim's excerpts, or with one fewer `met`
  prediction in that run; the transcription cannot distinguish these.
- No measured grounding benefit on this set: citation precision is
  1.0 in both arms, false-ready is 0/25 in both, missing recall is
  identical. Because precision is computed post-verification,
  downgraded claims vanish from the full arm's denominator
  (survivorship effect), so the metric cannot demonstrate the
  verifier catching anything.
- The verifier's visible failure mode is in the failure analysis:
  both missing-called-met errors survived it, because it checks
  verbatim substring presence, not entailment. Any future claim
  about grounding must come from a metric that checks semantic
  support, or from paired pre- and post-verification outputs;
  neither exists locally.

## Exact differing criteria: unavailable locally

The transcription gives only procedure-level aggregates (knee 58 vs
59, biologic 85 vs 86, lumbar identical at 28/40). No differing
criterion IDs are named in this document, and none should be
inferred. To identify them, retrieve the raw Cloud Shell files
(`results_real.json` and `results_no_citation_check.json`, including
`criterion_results`, `critic_findings`, and pre-verification
statuses if logged) and diff them row by row.
