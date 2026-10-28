# Failure analysis, final 30-case run, 2026-10-27

Model: gemini-3.5-flash at global, data us-central1, project
delivery-experience-511901. Full system 30/30: criterion 171/200,
case 28/30, false-ready 0/25, missing-evidence recall 12/14,
citation precision 89/89. The 4 failures below are the complete
failure list for the final run. No prediction or gold label was
modified to produce these metrics.

Raw-artifact gap, stated for every case: the exact Gemini
prediction text, the retrieved evidence for each case, and the
citation verifier output are NOT in local files. The local
`eval/results/` directory contains only local deterministic
guardrail outputs, not `results_real.json`. Those per-case details
are unavailable locally and must come from the raw Cloud Shell
files at `~/pa_final4/priorauth-agent/eval/`, which are being
retrieved separately. Nothing below reconstructs them.

## Deterministic scoring path, shared by all four

`src/priorauth/tools.py`, `checklist_scorer`, in this order, and no
model output overrides it:

1. Any `fired` exclusion -> NOT_READY.
2. Any `contradictory` -> NEEDS_MANUAL_REVIEW.
3. Code validation `invalid`/`unsupported`, or stale policy version
   -> NEEDS_MANUAL_REVIEW.
4. Pathway rule: READY only if some pathway's every required
   criterion is `met`; if some pathway's required criteria are all
   `met`/`uncertain` with at least one `uncertain` ->
   NEEDS_MANUAL_REVIEW; otherwise NOT_READY.

`code_validator` checks diagnosis codes against the policy's
supported list and the procedure code against the policy's procedure
list. For all four cases below, codes and versions were verified
deterministically from local files, so the code and stale-policy
branches are excluded as explanations for any of the four predicted
outcomes (assuming the deterministic validator ran, which is the
documented pipeline behavior).

Citation verifier path, shared by all four:
`src/priorauth/real_pipeline.py`, `finalize_review`, builds claims
only for predicted `met` results with excerpts, using only the first
excerpt. `tools.citation_verifier` downgrades a failing `met` to
`missing` and clears its excerpts; it cannot change `uncertain`,
`missing`, or `not_met`. It checks verbatim substring presence, not
semantic entailment. See `docs/CITATION_ABLATION_2026-10-27.md`.

## 1. EVAL-PMC-LUM-01, lumbar MRI, readiness mismatch

- Policy: AETNA_CPB_0236, version 2026 (current). Diagnosis M54.16
  supported; procedure 72148 supported.
- Gold: NEEDS_MANUAL_REVIEW. Predicted: NOT_READY.
- Gold criterion outcomes: LUM-01 uncertain, LUM-02 uncertain,
  LUM-03 not_applicable, LUM-EX-01 not_fired.
- Criterion text: LUM-01 (required): "Persistent back pain with
  radiculopathy evidenced by pain plus objective motor or reflex
  changes in the specific nerve root distribution." LUM-02
  (required): "No improvement after 6 weeks of conservative therapy
  (moderate activity, analgesics, NSAIDs, muscle relaxants)."
  Pathway LUM-A requires [LUM-01, LUM-02]; pathway LUM-B (red flag)
  requires [LUM-03].
- Case input (from `data/eval_cases.json`, published vignette,
  source PMC11475090, category ambiguous): 13-year-old girl, low back
  pain after a fall during sports three months earlier, tingling
  over the posterior bilateral lower limbs, straight leg raise
  positive at 50 degrees on the left and 60 degrees on the right, no
  neuro deficit, no bowel or bladder involvement, and no significant
  improvement with conservative treatment. MRI showed disc
  desiccation with diffuse disc bulge at L4-L5.
- Gold rationale, verified from the input: radiculopathy needs
  objective motor or reflex changes, which are not documented, so
  LUM-01 is uncertain, not met. Conservative duration is not stated,
  so LUM-02 is uncertain, not met.
- Deterministic scoring, gold: no fired exclusion, no contradiction,
  codes valid, version current, LUM-A required criteria both
  uncertain (all met/uncertain, at least one uncertain) ->
  NEEDS_MANUAL_REVIEW. LUM-B does not rescue this because LUM-03 is
  not_applicable, not met.
- Deterministic scoring, predicted NOT_READY, deduction not
  reconstruction: since code/stale and contradiction branches would
  yield NEEDS_MANUAL_REVIEW, the predicted output must have contained
  either a fired exclusion or a missing/not_met required criterion
  blocking every pathway. The exact predicted per-criterion statuses
  are unavailable locally, must come from raw artifacts.
- Citation verifier: it cannot touch uncertain/missing/not_met, so
  it cannot directly convert an uncertain pathway into NOT_READY.
  The only verifier-mediated route would be a pre-verification
  LUM-A of [met, uncertain] losing its met to a failed verbatim
  check, becoming [missing, uncertain] and scoring NOT_READY.
  Hypothesis, unverified: it requires pre-verification statuses
  that are not local.
- Verified vs hypothesis: VERIFIED: gold is uncertain on both LUM-A
  criteria for the reasons above; predicted NOT_READY is inconsistent
  with any all-met/uncertain pathway state. HYPOTHESIS (not
  verified): the model likely collapsed uncertain into missing or
  not_met, for example reading "no neuro deficit" as negating
  radiculopathy, or "no significant improvement with conservative
  treatment" (no duration) as satisfying or negating LUM-02. The
  exact Gemini prediction text and excerpts are unavailable locally.
- Potential improvement, stated as a proposal, not a tested fix:
  prompt and scorer guidance that explicitly distinguishes "no
  duration stated" (uncertain) from "duration stated and too short"
  (not_met/missing), and a paired pre/post-verification log so a
  verifier downgrade can be distinguished from a model uncertain
  collapse in future runs.

## 2. EVAL-PMC-KNE-01, knee arthroscopy, missing called met, case correct

- Policy: AETNA_CPB_0673, version 2024-09-11 (current). Diagnosis
  M23.32 supported; procedure 29881 supported.
- Gold case: NOT_READY. Predicted case: NOT_READY (correct).
  Criterion error: KNE-02 gold missing, predicted met
  (missing_called_met). All other gold outcomes: KNE-01 met, KNE-03
  met, KNE-04 missing, KNE-05 not_applicable, KNE-EX-01 not_fired,
  KNE-EX-02 not_fired.
- Criterion text: KNE-02 (required): "No more than mild
  osteoarthritis (Kellgren-Lawrence 0, 1, or 2, or modified
  Outerbridge Grade 0, 1, or 2)."
- Case input (published vignette, source PMC7993418, category
  missing_evidence): 18-year-old male, left knee pain and mechanical
  symptoms, locking and catching, for 2 years, medial joint line
  tenderness, range of motion 0 to 130 degrees, left knee radiographs
  unremarkable. MRI confirmed a discoid medial meniscus with a
  horizontal oblique tear of the posterior horn of the medial
  meniscus.
- Gold rationale, verified from the input: no Kellgren-Lawrence
  grade and no physical therapy are documented, so those criteria
  are missing. Verified from the note text itself: no
  Kellgren-Lawrence or Outerbridge grade appears anywhere in the
  note, so gold missing is directly supported by the stored input.
- Deterministic scoring: no fired exclusion, no contradiction,
  codes valid, version current. Pathways: KNE-A requires [KNE-01,
  KNE-02, KNE-03, KNE-04]; KNE-B requires [KNE-01, KNE-02, KNE-03,
  KNE-05]. Even with erroneous KNE-02 met, KNE-04 is gold missing
  (no physical therapy in the note) and KNE-05 is not_applicable, so
  neither pathway is fully met -> NOT_READY. The case-level
  correctness is therefore redundancy, not correctness of the
  KNE-02 judgment: had KNE-04 also been wrongly called met, KNE-A
  would have scored READY. Exact predicted KNE-04/KNE-05 statuses are
  unavailable locally, must come from raw artifacts.
- Citation verifier: the erroneous KNE-02 met survived verification
  in the full arm, so its first excerpt passed the verifier:
  citation complete (constructed from the policy) and excerpt a
  verbatim substring of the note. This is the verifier's central
  limitation, verified by code: verbatim presence is not semantic
  support. A verbatim sentence such as "left knee radiographs
  unremarkable" can pass the quote check while not establishing
  KL <= 2. The exact excerpt quoted is unavailable locally, must
  come from raw artifacts, and is not reconstructed here.
  HYPOTHESIS (not verified): the model inferred mild or no OA from
  "radiographs unremarkable" or from the discoid-meniscus MRI
  finding. This error is present in both arms, so the verifier
  neither caused nor cured it.
- Potential improvement, proposal only: require, for grade-based
  criteria, an excerpt containing the grade itself, not merely a
  verbatim sentence from the note, or a structured grade field
  check; and a semantic entailment check in addition to the
  substring check. Neither is implemented or tested in this audit.

## 3. EVAL-BIO-04, biologic infusion, missing called met, case correct

- Policy: CIGNA_IP0660, version 2026 (current). Diagnosis K50.90
  supported; procedure J1745 supported.
- Gold case: NOT_READY. Predicted case: NOT_READY (correct).
  Criterion error: BIO-05 gold missing, predicted met
  (missing_called_met). All other gold outcomes: BIO-01 met, BIO-02
  met, BIO-03 met, BIO-04 met, BIO-06 met, BIO-EX-01 not_fired,
  BIO-EX-02 fired, BIO-EX-03 not_fired.
- Criterion text: BIO-05 (required): "TB screening documented
  before initiation."
- Case input (structured test fixture, synthetic, category
  exclusion): moderate to severe Crohn disease, prescribed by a
  gastroenterologist, dosing 5 mg per kg at weeks 0, 2, and 6, failed
  corticosteroids, untreated latent tuberculosis documented.
- Gold rationale, verified from the input: untreated latent TB
  exclusion fires (BIO-EX-02). Verified from the note text itself:
  no TB-screening-before-initiation statement appears, no
  Quantiferon or pre-initiation TB test language. The note's only TB
  sentence documents untreated latent TB, which is the BIO-EX-02
  exclusion finding, not BIO-05 screening documentation.
- Deterministic scoring: scorer rule 1 takes precedence over
  everything: any fired exclusion -> NOT_READY, regardless of
  pathway state. Gold BIO-EX-02 fired alone determines gold
  NOT_READY. For the predicted outcome, NOT_READY is consistent with
  a fired exclusion, but exact predicted BIO-EX-02 status is
  unavailable locally, must come from raw artifacts. The deduction
  licensed by the code is only that predicted output contained a
  fired exclusion or a missing/not_met pathway blocker
  (contradiction/code/stale would have yielded NEEDS_MANUAL_REVIEW,
  and codes/version are deterministically valid/current). Either
  way, the BIO-05 error cannot flip this case to READY while the
  exclusion blocker stands.
- Citation verifier: as with KNE-02, the erroneous BIO-05 met
  survived verification in the full arm, so its first excerpt passed
  the verbatim and complete-citation checks. Again the code-verified
  lesson: the verifier checks substring presence, not whether the
  excerpt entails the criterion. A verbatim sentence about untreated
  latent TB can pass while proving the exclusion rather than
  pre-initiation screening. The exact quoted excerpt and verifier
  finding are unavailable locally, must come from raw artifacts.
  HYPOTHESIS (not verified): the model conflated "untreated latent
  tuberculosis documented" (evidence that TB status was somehow
  assessed) with "TB screening documented before initiation".
  Present in both arms; verifier neither caused nor cured it.
- Safety note: this error class is safety-relevant even though this
  case stayed NOT_READY, because on an otherwise-ready case the same
  error could contribute to a false READY.

## 4. EVAL-BIO-05, biologic infusion, readiness mismatch

- Policy: CIGNA_IP0660, version 2026 (current). Diagnosis K50.90
  supported; procedure J1745 supported.
- Gold: NEEDS_MANUAL_REVIEW. Predicted: NOT_READY.
- Gold criterion outcomes: BIO-01 met, BIO-02 uncertain, BIO-03 met,
  BIO-04 met, BIO-05 met, BIO-06 met, BIO-EX-01/02/03 all not_fired.
  Pathway BIO-A requires [BIO-01, BIO-02, BIO-03, BIO-04, BIO-05,
  BIO-06].
- Criterion text, the uncertain one: BIO-02 (required): "Medication
  prescribed by or in consultation with a gastroenterologist."
- Case input (structured test fixture, synthetic, category
  ambiguous): moderate to severe Crohn disease, prescribed by a
  primary care physician, with possible gastroenterology input that
  is not documented as a consultation, dosing 5 mg per kg at weeks 0,
  2, and 6, TB screening documented before initiation, failed
  corticosteroids.
- Gold rationale, verified from the input: possible specialist input
  is uncertain, not met. The prescriber is explicitly a primary care
  physician, and the gastroenterology input is explicitly "possible"
  and "not documented as a consultation", matching gold uncertain
  (possible/undocumented input is neither confirmed consultation nor
  explicit negation).
- Deterministic scoring, gold: no fired exclusion, no contradiction,
  codes valid, version current, BIO-A required criteria all
  met/uncertain with BIO-02 uncertain -> NEEDS_MANUAL_REVIEW.
- Deterministic scoring, predicted NOT_READY, deduction not
  reconstruction: code/stale and contradiction branches would yield
  NEEDS_MANUAL_REVIEW, so predicted output must have contained a
  fired exclusion or a missing/not_met required criterion blocking
  BIO-A (the single pathway for this policy). Exact predicted
  statuses, including predicted BIO-02, are unavailable locally,
  must come from raw artifacts.
- Citation verifier: same structure as case 1. The verifier cannot
  touch uncertain/missing/not_met, so it cannot directly turn an
  uncertain pathway into NOT_READY. The only verifier-mediated route
  would be a pre-verification BIO-A of [five met, one uncertain]
  losing a met to a failed verbatim check, becoming a missing in the
  pathway and scoring NOT_READY. Hypothesis, unverified, without
  pre/post-verification statuses.
- Verified vs hypothesis: VERIFIED: gold NEEDS_MANUAL_REVIEW follows
  deterministically from BIO-02 uncertain with all other BIO-A
  criteria met; predicted NOT_READY requires a predicted
  missing/not_met/fired blocker that gold does not have.
  HYPOTHESIS (not verified): the model most plausibly called BIO-02
  not_met (from "prescribed by a primary care physician") or missing
  instead of uncertain, collapsing the uncertain-pathway branch into
  the no-pathway-fully-met branch. The exact Gemini prediction text
  is unavailable locally, must come from raw artifacts.
- Potential improvement, proposal only: explicit uncertain
  handling in the extraction prompt for "possible but undocumented"
  language, and a paired pre/post-verification log in future runs.

## Cross-cutting conclusions

1. Do not claim a citation-verification accuracy gain or false-ready
   prevention from this run. Full vs no-citation: criterion -0.01,
   case 0.0, false-ready 0.0, missing recall 0.0, citation precision
   1.0 vs 1.0.
2. The verifier's failure mode is visible in the data: both
   missing-called-met errors survived it, because it checks verbatim
   substring presence, not entailment. Any future claim about
   grounding must come from a metric that checks semantic support,
   or from paired pre/post-verification outputs, neither of which
   exists locally.
3. The two readiness mismatches (LUM-01, BIO-05) are
   uncertain-handling errors, not citation errors on the evidence
   available. Both hinge on the uncertain-vs-missing/not_met
   distinction, which the verifier cannot touch directly; a
   verifier-mediated contribution is possible but unproven without
   raw artifacts.
4. To close every open item above, retrieve the raw Cloud Shell
   files (`results_real.json` and `results_no_citation_check.json`
   rows, including `criterion_results`, `critic_findings`, and
   pre-verification statuses if logged). Until those are retrieved,
   the differing-criteria IDs for the ablation, the exact predicted
   statuses for LUM-01/BIO-05, and the exact quoted excerpts for
   KNE-02/BIO-05 must remain stated as unavailable, not reconstructed.
