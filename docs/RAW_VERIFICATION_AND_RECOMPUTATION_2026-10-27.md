# Raw verification and recomputation, cloud evaluation 2026-10-27

This document is based on the original raw files in
`evidence/cloud_eval_2026-10-27/raw/`, verified unchanged
from the user's upload of PriorAuth_Raw_Evidence.zip.
It replaces the earlier transcription-only record. Where
this document and an earlier summary disagree, the raw
files win. No prediction, gold label, or raw record was
modified, reconstructed, or fabricated here.

Model: gemini-3.5-flash. Model location: global.
Data location: us-central1. Project:
delivery-experience-511901. Embedding: text-embedding-004.
Run window: 2026-10-27, 9:59 AM to 1:12 PM ET.

## 1. Raw file verification

All seven files were present, with Cloud Shell sizes
exactly matched. Six hashes match the previously recorded
64-character sha256 hashes exactly. The seventh,
results_baseline.json, does not match the hash string in
earlier notes because that string is only 63 characters
long, missing one '7' at position 28; it cannot be a
sha256 hash. The actual baseline file is identical across
the user upload, the verification copy, and the copy in
`raw/`, its size is exactly 104563 bytes as recorded in
Cloud Shell, and its rows recompute to the reported
baseline metrics below. The file was not altered to match
the erroneous recorded string. Use the hash in
`evidence/cloud_eval_2026-10-27/EVIDENCE_README.md`.

Credential scan over the raw files: 0 matches for
password, api_key, private_key, service_account, AIza,
ya29, BEGIN PRIVATE, secret, bearer. Nothing was removed
and no substantive record was altered. No standalone
.log files were found in the Cloud Shell project
directory, so no evaluation log is included; that
absence is stated, not filled in.

## 2. Recomputed metrics, with denominators

Recomputed with scripts/recompute_metrics.py and with
scripts/eval_metrics.py directly, from the raw rows.
Percentiles use the repo's own method, documented in
eval_metrics.py: p50 = sorted[n//2], p95 =
sorted[int(n*0.95)]. A linear-interpolation percentile
gives slightly different p50/p95 values; that is a
method difference, not a metric mismatch, and the repo
method reproduces the embedded values exactly.

### Full system, citation verification on, 30/30

- Cases attempted 30, completed 30, not completed 0.
- Criterion accuracy 171/200 = 0.855.
- Case readiness accuracy 28/30 = 0.9333.
- False-ready rate 0/25 = 0.0.
- Missing-evidence recall 12/14 = 0.8571.
- Citation precision 89/89 = 1.0.
- Retrieval recall proxy 30/30 = 1.0 (weak proxy, see
  eval_metrics.py: at least one retrieved chunk contains
  a gold keyword; there is no chunk-level gold set).
- Latency p50 28834.6 ms, p95 62187.2 ms, mean 33657.8 ms.
- Token usage prompt 30864, output 14741.
- Cost total $0.0784 script estimate, mean $0.0026/case.
- By procedure: lumbar_mri case 9/10, criterion 28/40;
  knee_arthroscopy case 10/10, criterion 58/70;
  biologic_infusion case 9/10, criterion 85/90.
- ADK tool calls: search_policy_chunks 30,
  validate_case_codes 30, extract_evidence 30;
  30 ADK sessions, one per case.

Recomputation result: MATCH on every compared value
(counts, accuracies, latency by the repo method, tokens,
cost, by-procedure counts).

### No-citation ablation, 30/30

- Criterion 173/200 = 0.865. Case 28/30 = 0.9333.
  False-ready 0/25 = 0.0. Missing recall 12/14 = 0.8571.
  Citation 90/90 = 1.0. Retrieval 30/30 = 1.0.
- Latency p50 31890.5 ms, p95 278082.1 ms,
  mean 75289.8 ms. Cost $0.0751, mean $0.0025/case.
  Tokens prompt 30673, output 13902.
- Recomputation result: MATCH on every compared value.

### Original as-run baseline, 30/30, SUPERSEDED BY CORRECTED BASELINE RERUN 2026-10-27

- Criterion 14/200 = 0.07. Case 13/30 = 0.4333.
  False-ready 11/25 = 0.44. Missing recall 14/14 = 1.0.
  Citation 0/0 = null (no scored citations, not zero
  quality). Retrieval 30/30 = 1.0.
- Latency p50 11338.9 ms, p95 291571.7 ms,
  mean 40661.1 ms. Cost $0.0273, mean $0.0009/case.
- Recomputation result: MATCH on every count, accuracy,
  latency (repo method), and cost. ONE GENUINE MISMATCH:
  embedded token total is prompt 0, output 0, while the
  rows sum to prompt 12020 and candidates 4874
  (sum of total_token_count across rows is 60343, a
  different field and not used here). The embedded 0/0
  is the known old-code bug: the as-run metrics code
  summed only evidence_*/draft_* token keys, while
  baseline rows carry prompt_token_count /
  candidates_token_count. The audit-fixed eval_metrics.py
  now sums both key sets. Do not use 0/0 for any token
  comparison. The corrected values from the rows are
  prompt 12020, candidates 4874. scripts/recompute_metrics.py
  now checks token totals as well as the other metrics:
  it reports this token mismatch and exits with code 1,
  while all other recomputed values match. That exit
  code is the honest result, not a failure of the
  recomputation itself.

### Pilot, 3/3, pilot only, never full performance

- Criterion 16/20 = 0.8. Case 2/3 = 0.6667.
  False-ready 0/3 non-ready = 0.0. Missing recall
  3/4 = 0.75. Citation 8/8 = 1.0. Retrieval 3/3 = 1.0.
- Latency p50 30285.4 ms, p95 32936.2 ms (repo method;
  with only 3 cases, p95 is the largest value by that
  method), mean 30716.3 ms. Cost $0.0081.
  Tokens prompt 3228, output 1523.
- Recomputation result: MATCH.

### Superseded partial14, 14 completed of 30 attempted

- Criterion 55/70 = 0.7857. Case 13/14 = 0.9286.
  False-ready 0/11 = 0.0. Missing recall 5/6 = 0.8333.
  Citation 28/28 = 1.0. Retrieval 14/14 = 1.0.
- Latency p50 26011.4 ms, p95 46824.1 ms,
  mean 28643.3 ms. Cost $0.0328.
  Tokens prompt 13758, output 5987.
- The file records cases_attempted 30, cases_completed
  14, cases_not_completed 0: the 16 uncompleted cases
  were not recorded in not_completed_cases. This
  partial is NOT a full-run result and must not be
  quoted as one. Its missingness was procedure
  concentrated (all 16 missing were knee 7 and
  biologic 9, zero lumbar), consistent with a
  run-order infrastructure crash after case 14
  (inferred, not confirmed), not a case-difficulty
  pattern. The final 30/30 run has no failed cases,
  so no failed-case bias investigation applies to
  the final metrics.

## 3. Citation ablation, exact differing criteria

Comparing full (results_real.json) and no-citation
(results_no_citation_check.json) row by row, there are
exactly 5 criterion differences, and no readiness
difference. Net effect: no-citation is correct on 2
more criteria, full is correct on 0 more, and 3
differences change neither arm's correctness. That
gives 173 vs 171, delta -0.01 for full minus
no-citation. Case accuracy, false-ready rate,
missing recall, and citation precision are unchanged
in aggregate (citation 89/89 vs 90/90 is a denominator
difference of 1 met excerpt, not a precision change).

Exact differences (gold, full, no-citation):

1. EVAL-PMC-KNE-01, KNE-05: gold not_applicable,
   full missing (wrong), no-citation not_applicable
   (correct). Full excerpt list is empty, notes say
   the note does not document a displaced bucket
   handle tear.
2. EVAL-LUM-06, LUM-03: gold not_applicable,
   full missing (wrong), no-citation uncertain
   (wrong). Neither arm is correct.
3. EVAL-LUM-08, LUM-03: gold not_applicable,
   full missing (wrong), no-citation uncertain
   (wrong). Neither arm is correct.
4. EVAL-LUM-09, LUM-03: gold not_applicable,
   full uncertain (wrong), no-citation missing
   (wrong). Neither arm is correct.
5. EVAL-BIO-09, BIO-04: gold met, full uncertain
   (wrong), no-citation met (correct). Full notes
   say initial dosing is specified but maintenance
   dosing frequency is not documented.

What the verifier changed: on the evidence in the
rows, NOTHING that explains this delta. The citation
verifier, in src/priorauth/tools.py, acts only on
predicted met claims: it requires a complete policy
citation, a verbatim excerpt in the note, and an
excerpt the extractor found for that criterion, and
it downgrades a failing met claim to missing only.
None of the five differing criteria is predicted met
in the full arm (full statuses are missing, missing,
missing, uncertain, uncertain). A verifier that only
acts on met claims cannot have produced those five
differences. The only met claim among the five is
BIO-04 in the no-citation arm, where the verifier
was off. The delta is therefore run-to-run Gemini
variation between two separate, unpaired runs, not
a demonstrated verifier effect. This is a verified
conclusion from the raw rows, stronger than the
earlier hypothesis that the verifier "could
plausibly" cost 2 criteria.

Citation precision, separately: full 89/89, no-citation
90/90, where the denominator is predicted met claims
with an excerpt, counted per excerpt. Because the
full-arm precision is computed after verification,
it has a survivorship effect and cannot by itself
demonstrate that the verifier caught anything.
No measured grounding benefit beyond verbatim
presence is demonstrated in these files: the
verifier checks verbatim substring presence, not
semantic entailment, and both missing-called-met
errors below survived it.

Claim rule for all packs: do NOT claim citation
verification improved accuracy or prevented
false-ready decisions. The observed result is the
opposite direction on criterion accuracy (-0.01)
and no change on false-ready rate.

## 4. Four final failures, from the raw rows

Deterministic scoring, for reference, in
src/priorauth/tools.py checklist_scorer, in order:
exclusion fired means NOT_READY; contradiction means
NEEDS_MANUAL_REVIEW; invalid/unsupported codes or a
stale policy version means NEEDS_MANUAL_REVIEW; with
pathways, READY requires a pathway whose every
required criterion is met, a pathway whose only
non-met criteria are uncertain means
NEEDS_MANUAL_REVIEW, otherwise NOT_READY. No model
output can override these rules. Critic findings in
the rows are the pre-check (pathway/exclusion)
notes, not a separate verifier output field; there
is no before/after verifier status stored per
criterion in the raw rows, so verifier action on a
specific claim is inferred only from its final
status, excerpt, and the verifier rules, and is
labeled as such below.

### 4.1 EVAL-PMC-LUM-01, readiness mismatch
Gold NEEDS_MANUAL_REVIEW, predicted NOT_READY,
latency 35595.9 ms, lumbar_mri, published case
report. Case input: 13-year-old girl, low back pain
after a fall during sports three months earlier,
tingling over posterior bilateral lower limbs,
straight leg raise positive at 50 degrees left and
60 degrees right, no neuro deficit, no bowel or
bladder involvement, no significant improvement
with conservative treatment; MRI disc desiccation
with diffuse disc bulge at L4-L5 causing severe
compromise of bilateral lateral recesses. Codes
M54.16 / 72148, both valid.
Policy AETNA_CPB_0236: LUM-01 requires persistent
back pain with radiculopathy shown by pain plus
objective motor or reflex changes in a specific
nerve root distribution; LUM-02 requires no
improvement after 6 weeks of conservative therapy;
LUM-03 is a conditional red-flag pathway; LUM-EX-01
is the duplicative-MRI exclusion.
Gold criteria: LUM-01 uncertain, LUM-02 uncertain,
LUM-03 not_applicable, LUM-EX-01 not_fired.
Predicted criteria: LUM-01 not_met, excerpt "no
neuro deficit", notes say that statement negates
objective motor or reflex changes; LUM-02 met,
excerpts "after a fall during sports three months
earlier" and "no significant improvement with
conservative treatment", notes say three months is
longer than the 6-week threshold; LUM-03 missing,
no red-flag pathways documented; LUM-EX-01
not_fired. Retrieved chunks: CH-0236-01 and
CH-0236-03 (Lumbar spine MRI criteria), CH-0236-02
(Red flag pathways), method vertex_embedding_cosine.
Critic: "Pre-check: No pathway fully met. Non-met
criteria: LUM-01, LUM-03." Deterministic result:
NOT_READY, because no pathway is fully met and a
not_met/missing blocker is present.
Root cause, verified: the model collapsed uncertain
into decided statuses in both directions. For
LUM-01 it treated "no neuro deficit" as a negation
of objective motor/reflex changes, while the gold
annotation treats the objective finding as
uncertain: tingling and a positive straight leg
raise plus severe MRI compromise are present, but
no documented motor or reflex examination is
stated. For LUM-02 it treated three months of
symptoms with no improvement as 6 weeks of
conservative therapy, while the note states no
therapy components or duration. The verifier did
not change either outcome: LUM-02's excerpts are
verbatim in the note, so the verbatim check passes
even though the semantic inference (duration and
components) is unsupported, and LUM-01 is not a
met claim, so the verifier does not act on it.
Potential improvement: require an explicit
uncertain rule for "no documented examination" vs
"examination documented as negative", and require
therapy duration plus components before marking a
conservative-therapy criterion met; a human
reviewer should resolve uncertain pathways, which
is exactly what the gold NEEDS_MANUAL_REVIEW
state is for.

### 4.2 EVAL-PMC-KNE-01, KNE-02 missing called met
Gold case NOT_READY, predicted case NOT_READY
(case-level correct). Gold KNE-02 missing,
predicted met. Latency 31181.1 ms, knee_arthroscopy,
published case report. Case input: 18-year-old
male, left knee pain and mechanical symptoms,
locking and catching, for 2 years, medial joint
line tenderness, range of motion 0 to 130 degrees,
left knee radiographs unremarkable; MRI confirmed
a discoid medial meniscus with a horizontal
oblique tear of the posterior horn. Codes M23.32 /
29881, valid.
Policy AETNA_CPB_0673, KNE-02: "No more than mild
osteoarthritis (Kellgren-Lawrence 0, 1, or 2, or
modified Outerbridge Grade 0, 1, or 2)."
Gold criteria: KNE-01 met, KNE-02 missing,
KNE-03 met, KNE-04 missing, KNE-05 not_applicable,
exclusions not_fired. Predicted KNE-02: met,
excerpt "left knee radiographs unremarkable",
notes "Unremarkable radiographs indicate there is
no more than mild osteoarthritis." Retrieved
chunks: CH-0673-02 (Exclusions), CH-0673-01
(Knee arthroscopy criteria). Critic: "No pathway
fully met. Non-met criteria: KNE-04, KNE-05."
Deterministic result: NOT_READY, because KNE-04
is missing, so the KNE-02 error did not produce a
false-ready case; it was masked at case level by
redundancy, not caught by the verifier.
Root cause, verified: semantic entailment failure,
not a verbatim failure. No Kellgren-Lawrence or
Outerbridge grade appears anywhere in the note.
The model inferred a grade ceiling from
"unremarkable" radiographs. The excerpt is
verbatim, so the citation verifier passes it;
the verifier checks that the words appear, not
that they entail a KL 0-2 grade. Potential
improvement: a grade-required rule for KNE-02:
no stated KL/Outerbridge grade means missing or
uncertain, never met from "unremarkable" alone,
and a semantic check that an excerpt actually
states the criterion's threshold, not merely a
related finding.

### 4.3 EVAL-BIO-04, BIO-05 missing called met
Gold case NOT_READY, predicted case NOT_READY
(case-level correct). Gold BIO-05 missing,
predicted met. Latency 27968.4 ms,
biologic_infusion, structured fixture. Case input:
"Moderate to severe Crohn disease, prescribed by
a gastroenterologist. Dosing 5 mg per kg at weeks
0, 2, and 6. Failed corticosteroids. Untreated
latent tuberculosis documented." Codes K50.90 /
J1745, valid.
Policy CIGNA_IP0660, BIO-05: "TB screening
documented before initiation." BIO-EX-02 is the
exclusion "untreated latent TB". Gold criteria:
BIO-01 to BIO-04 met, BIO-05 missing, BIO-06 met,
BIO-EX-01 not_fired, BIO-EX-02 fired,
BIO-EX-03 not_fired. Predicted BIO-05: met,
excerpt "Untreated latent tuberculosis
documented.", with no notes. The SAME excerpt is
also used for BIO-EX-02 fired. Retrieved chunks:
CH-IP0660-01 (Initial therapy criteria, Crohn
disease), CH-IP0660-02 (Exclusions). Critic:
"Exclusion fired: BIO-EX-02. An exclusion cannot
be overridden." Deterministic result: NOT_READY,
by the exclusion rule, regardless of BIO-05.
Root cause, verified: the model conflated two
different TB statements. Documented untreated
latent TB proves the exclusion, not screening
before initiation; the note contains no screening
statement at all. The excerpt is verbatim, so the
verifier passes it, and because the same excerpt
supports the exclusion, the error is invisible
unless a reviewer reads the criterion text against
the excerpt. This is safety-relevant even though
the case stayed NOT_READY: in a case without a
firing exclusion, the same error would contribute
to a false-ready case. Potential improvement: an
exclusion-aware check that bars using an exclusion
excerpt as support for the corresponding required
criterion, and a screening-specific requirement
that the excerpt mention screening, a test, or a
result before initiation.

### 4.4 EVAL-BIO-05, readiness mismatch
Gold NEEDS_MANUAL_REVIEW, predicted NOT_READY,
latency 26140.1 ms, biologic_infusion, structured
fixture. Case input: "Moderate to severe Crohn
disease, prescribed by a primary care physician,
with possible gastroenterology input that is not
documented as a consultation. Dosing 5 mg per kg
at weeks 0, 2, and 6. TB screening documented
before initiation. Failed corticosteroids."
Codes K50.90 / J1745, valid.
Policy CIGNA_IP0660, BIO-02: "Medication
prescribed by or in consultation with a
gastroenterologist." Gold criteria: BIO-01 met,
BIO-02 uncertain, BIO-03 to BIO-06 met, all
exclusions not_fired. Predicted BIO-02: not_met,
excerpt "prescribed by a primary care physician,
with possible gastroenterology input that is not
documented as a consultation.", no notes.
Retrieved chunks: CH-IP0660-01, CH-IP0660-02.
Critic: "No pathway fully met. Non-met criteria:
BIO-02." Deterministic result: NOT_READY, because
a not_met blocker is present; had BIO-02 been
uncertain with all other required criteria met,
the pathway rule would have given
NEEDS_MANUAL_REVIEW, matching gold.
Root cause, verified: the model collapsed
"possible but not documented as a consultation"
into not_met instead of uncertain. The note
explicitly marks the consultation as possible
and undocumented, which is the textbook
uncertain case, not a documented absence.
Potential improvement: an explicit rule that
"possible, not documented" maps to uncertain,
never to not_met, and a reviewer prompt that
surfaces the exact consultation wording.

### Failure pattern, overall

All four failures are Gemini interpretation errors
at the uncertain/missing boundary, not retrieval
failures (every case retrieved the correct policy
chunks by the vertex_embedding_cosine method),
not code-validation failures (all codes valid),
and not deterministic-scorer failures (the scorer
correctly applied its rules to the predicted
statuses). Two are readiness mismatches caused
by collapsing uncertain into not_met/missing,
and two are missing-called-met errors caused by
inferring a threshold from a related but
insufficient finding. The citation verifier
caught none of the four, because it checks
verbatim presence, not semantic entailment, and
because two of the four are not met claims at
all. That is the central limitation to carry
into interviews: verbatim grounding is necessary
but not sufficient.

## 5. Original baseline, raw row analysis

Every baseline row (30/30) has the same criterion
pattern: all predicted criterion statuses are
"missing" (200/200), with empty evidence excerpts.
Its criterion accuracy of 14/200 is therefore
exactly the 14 gold missing criteria, and its
missing recall of 14/14 is a consequence of
predicting missing for everything, not evidence
that the baseline detected missing evidence.
Its readiness guesses vary (13/30 correct, 11/25
false-ready), so generation did happen: token
usage is non-zero in the rows, latency is
non-zero, and retrieval is real (2 to 3 chunks
per case, method vertex_embedding_cosine, same
chunks as the full system for the same policies).
What did not happen is criterion output: either
the model returned no criterion outcomes, or it
returned IDs/statuses that did not exact-match
the gold IDs, and the parser defaulted every
unmatched criterion to missing (see
scripts/baseline.py, pred.get(criterion_id,
"missing")). The raw rows do not store the
model's raw response text, so the exact
as-run prompt output cannot be reconstructed
from the raw file; that specific step is
unverified, while the row-level pattern and the
parser default are verified. The audit finding
stands: the as-run prompt withheld the criterion
list and status vocabulary that exact-match
scoring requires, and the corrected prompt now
in scripts/baseline.py includes the same
criterion list (ID, kind, section, text) and
status semantics as the full system. A corrected
rerun is therefore expected to change the
criterion comparison materially, and the
original 14/200 must NOT be quoted as the
model's criterion-judgment accuracy or as the
pure value of the structured workflow. The
original baseline is SUPERSEDED BY CORRECTED BASELINE RERUN 2026-10-27;
no new baseline number is produced in this
local task, because the corrected rerun is a
separate, approved cloud task.

## 6. Remaining limitations, honestly stated

- Raw files are included unchanged, but no
  evaluation log or error log exists in the
  Cloud Shell record, so the metadata
  RefreshError crash and the Cloud Shell drops
  during the first full run remain undiagnosed
  from logs.
- The citation verifier's per-claim
  before/after status is not stored in the raw
  rows, so verifier action on individual claims
  is inferred from final statuses and the
  verifier rules, as labeled above, not read
  from a verifier log.
- Baseline raw response text is not stored, so
  the exact as-run model output that produced
  all-missing criteria cannot be recovered.
- Deployment remains FAILED on IAM permissions
  for the Cloud Build default service account;
  no URL, screenshot, or deployed review exists,
  and no IAM change was made.
- Spend attribution gap remains unresolved:
  console Vertex delta about $4.29 versus
  script-estimated model spend about $0.22 for
  the 2026-10-27 attempt, both below the $8 stop
  and $10 ceiling. Do not attribute the full
  console delta to PriorAuth alone.
- All metrics are for this 30-case annotated
  set only and must not be generalized to other
  case sets, real prior authorization packets,
  or clinical use. Policies are simplified
  subsets, not complete policies; Cigna IP0660
  is 22 pages and was not fully re-read, and a
  human must re-read it before any real use.
  No medical advice, no approve/deny/submit
  decision, readiness states only, human makes
  the final decision.
- The corrected baseline rerun is not part of
  this local task; its result has now been inserted: the corrected baseline raw file is included unchanged and recomputed, see the corrected baseline summary.


## Addendum: corrected baseline rerun, 2026-10-27

Any "SUPERSEDED PENDING RERUN" label in this document is superseded by
the corrected baseline rerun on 2026-10-27: criterion 176/200, case
8/30, false-ready 18/25, missing recall 13/14, latency p50 10.9 s,
p95 14.5 s, cost $0.0463. The original baseline (14/200, 13/30, 11/25)
remains superseded history only. The corrected baseline raw JSON file IS now included locally, unchanged, in the GitHub pack at evidence/cloud_eval_2026-10-27/raw/results_baseline_corrected.json (116,872 bytes, SHA-256 ed13f335aff8b1452a8419b39b33e1fa63e35a31710f18d115caff1d60986ff9); see corrected_baseline_summary_2026-10-27.md.


## Update 2026-10-28: corrected baseline raw file now included and recomputed

The corrected baseline raw file, results_baseline_corrected.json
(116,872 bytes, SHA-256 ed13f335aff8b1452a8419b39b33e1fa63e35a31710f18d115caff1d60986ff9),
is now included unchanged in evidence/cloud_eval_2026-10-27/raw/,
copied byte-for-byte from the user upload of the Cloud Shell original.
Running scripts/recompute_metrics.py against evidence/raw/ gives:
full system OK, no-citation ablation OK, corrected baseline OK
(criterion 176/200, case 8/30, false-ready 18/25, missing recall
13/14, citation raw 90/99, retrieval proxy 30/30, latency p50
10895.2 ms, p95 14518.9 ms, mean 11290.1 ms, tokens prompt 24488,
output 7457, total 31945, cost $0.0463, by procedure lumbar case
4/10 and criterion 28/40, knee case 3/10 and criterion 61/70,
biologic case 1/10 and criterion 87/90, failures list 23 entries),
and the original baseline token mismatch only (embedded 0/0 vs
rows prompt 12020, candidates 4874), so the script exits 1 as the
honest result. Missing recall here means gold missing not called
met (missing, uncertain, or not_met), so 13/14 with only
1 missing_called_met; it is NOT predicting missing for everything.
