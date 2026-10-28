# PriorAuth Agent

Evidence-grounded prior authorization review using agentic retrieval. The system turns a payer policy into a structured criteria checklist, matches each criterion to evidence in a clinical note or marks it missing, cites the exact policy and note text, applies a deterministic readiness scorer, and drafts only from verified claims. A human makes the final submit decision.

**It never approves, denies, or submits a prior authorization. It never gives medical advice.** Its only outputs are documentation-readiness states: `READY_FOR_HUMAN_REVIEW`, `NOT_READY`, or `NEEDS_MANUAL_REVIEW`.

## The problem

Prior authorization paperwork usually fails for checkable reasons: a required finding is missing, a therapy duration is too short, a code is not supported, a note contradicts itself, or the policy version is stale. A retrieval-only assistant can hide those failures behind a confident draft. This system makes the checklist explicit, cites every met criterion to an exact note excerpt, lists gaps separately, and forces a human to review the result.

## How it works

```
Clinical note / case
        |
        v
FastAPI POST /reviews  or  Streamlit app  or  evaluation script
        |
        v
Google ADK Runner (Runner.run_async) with three FunctionTools
  1. search_policy_chunks: retrieve policy chunks (Vertex embeddings,
     BigQuery VECTOR_SEARCH, cosine similarity)
  2. validate_case_codes: validate diagnosis and procedure codes
  3. extract_evidence: Gemini structured extraction against the
     retrieved chunks and the note
        |
        v
Deterministic safeguards (no model output can override these)
  - Citation verification: a met claim keeps its status only if its
    excerpt appears verbatim in the note; otherwise it is downgraded
    to missing
  - Code validation: unsupported or invalid codes block readiness
  - Exclusion, contradiction, and stale-policy rules
  - Pathway scorer: exclusion fired -> NOT_READY; contradiction ->
    NEEDS_MANUAL_REVIEW; invalid code or stale policy ->
    NEEDS_MANUAL_REVIEW; otherwise READY only when a full pathway
    is met, NEEDS_MANUAL_REVIEW when the only non-met criteria are
    uncertain, otherwise NOT_READY
        |
        v
ReviewResult: readiness, criterion results with citations and exact
excerpts, gaps, critic findings, draft letter, audit entry
```

Key design rule: the language model interprets evidence, but deterministic rules decide readiness. A met claim without a verbatim excerpt, a firing exclusion, or a missing required criterion can never produce `READY_FOR_HUMAN_REVIEW`.

## Tech stack

- Python 3.12, Pydantic, FastAPI, Streamlit, Docker, pytest
- Google ADK (Agent Development Kit) with `Runner.run_async`
- Vertex AI: Gemini generation, `text-embedding-004` (dimension 768)
- BigQuery with `VECTOR_SEARCH` (dataset `priorauth_agent`, data location `us-central1`)
- PyMuPDF for policy document parsing, Cloud Storage layout in `gcp/`

## Procedures covered

Three procedures, each with a simplified policy subset (see the limitation below):

- Lumbar spine MRI: Aetna CPB 0236
- Knee arthroscopy: Aetna CPB 0673, knee osteoarthritis selected treatments
- Biologic infusion, Crohn disease only: Cigna IP0660, infliximab intravenous products, effective 03/15/2026

## Verified results (2026-10-27, 30-case annotated set)

All figures below are for this 30-case set only (10 cases per procedure). They must not be generalized to other case sets, real prior authorization packets, or clinical use.

| System | Criterion | Case readiness | False-ready | Missing recall | Citation | Latency p50 / p95 | Cost |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Full system, citation verification on | 171/200 | 28/30 | 0/25 | 12/14 | 89/89 verified | 28,834.6 ms / 62,187.2 ms | $0.0784 |
| Corrected baseline, one call per case, no verifier, no scorer | 176/200 | 8/30 | 18/25 | 13/14 | 90/99 raw | 10,895.2 ms / 14,518.9 ms | $0.0463 |
| Pilot, full system, 3 cases | 16/20 | 2/3 | 0/3 | 3/4 | 8/8 | p50 30,285.4 ms | $0.0081 |

The no-citation ablation scored 173/200, case 28/30, false-ready 0/25. Citation verification therefore did **not** demonstrably help on this set (delta criterion -0.01), and the verifier cannot explain that delta: it acts only on predicted met claims, and none of the 5 differing criteria was predicted met in the full arm.

### Reading the baseline comparison honestly

The corrected baseline scored **higher** on criterion accuracy (176 vs 171) but **much worse** on case readiness (8 vs 28) and false-ready decisions (18 vs 0). The original as-run baseline (14/200, 13/30, 11/25) is superseded history only: its prompt withheld the criterion list and status vocabulary, so ID mismatches defaulted to missing, and its embedded token total of 0/0 is incomplete (a known old-code bug). Once the prompt was corrected, the criterion gap reversed, which shows that part of the original gap was prompt artifact, not workflow value. The full system's genuine value is readiness determination and false-ready prevention through the deterministic scorer and safeguards. The corrected baseline is not the full system, and its raw citation figure (90/99) is not comparable to the full system's post-verification figure (89/89), because the baseline has no verifier.

### Failures (full system, 4 of 30 cases)

All four are Gemini interpretation errors at the uncertain/missing boundary, not retrieval failures (the correct chunks were retrieved), not code-validation failures (all codes were valid), and not scorer failures:

- `EVAL-PMC-LUM-01`, readiness mismatch: uncertain collapsed both ways.
- `EVAL-PMC-KNE-01`, KNE-02 missing called met: no Kellgren-Lawrence or Outerbridge grade appears in the note; the model inferred it from unremarkable radiographs.
- `EVAL-BIO-04`, BIO-05 missing called met: documented untreated latent tuberculosis was conflated with TB screening before initiation. The case stayed NOT_READY only because the exclusion fired.
- `EVAL-BIO-05`, readiness mismatch: a possible but undocumented gastroenterology consultation was collapsed to not_met instead of uncertain.

Full detail is in `docs/FAILURE_ANALYSIS_2026-10-27.md`. Corrected baseline failures: 22 case readiness failures (18 false-ready, 4 readiness mismatch) plus 1 criterion entry; 24 criterion errors, 16 with gold not_applicable, 13 predicted missing, concentrated in LUM-03 and KNE-05.

## Repository layout

```
src/priorauth/   ADK agent, real pipeline, deterministic tools and scorer,
                 FastAPI app, cloud clients
app/             Streamlit demo application
data/            policies.json (simplified subsets), eval_cases.json (30 cases),
                 guardrail_cases.json (60 templated guardrail cases, not model
                 performance), policy_chunks.json, labeling_rubric.md
scripts/         evaluate_real.py, baseline.py (corrected prompt),
                 ablation.py, eval_metrics.py, recompute_metrics.py, and more
tests/           full test suite (49 passed, 1 skipped in local verification;
                 the skipped test is opt-in and credentialed, by design)
gcp/             BigQuery schema, load and dedup scripts, Cloud Run config
                 and deploy script, cost estimation
docs/            architecture, ADK integration, configuration, deployment,
                 evaluation results, baseline validation, citation ablation,
                 failure analysis, raw verification, data provenance,
                 simplified-vs-complete policies
evidence/        cloud evaluation summaries and raw files (see below)
```

## Reproduce the work

### 1. Install and test locally (no cloud, no model call)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src pytest tests/ -q
```

Expected local result: 49 passed, 1 skipped. The credentialed test is opt-in and skipped without credentials, by design.

### 2. Verify the reported metrics from the raw files (no cloud)

```bash
PYTHONPATH=src python3 scripts/recompute_metrics.py evidence/cloud_eval_2026-10-27/raw/
```

This recomputes the full system and no-citation results exactly, and the corrected baseline exactly. It reports the original baseline token mismatch (embedded 0/0 vs rows prompt 12,020, candidates 4,874) and exits 1 because of that mismatch alone. That exit code is the honest result, not a hidden failure.

### 3. Run the API locally (fails clearly without credentials)

```bash
PYTHONPATH=src uvicorn priorauth.api:app --port 8000
```

`GET /health` reports the real ADK pipeline mode. Without GCP credentials, `POST /reviews` returns 503. It never falls back to a mock.

### 4. Run a real cloud evaluation (requires a GCP project and a budget)

Set every variable explicitly. There is no model default in the code, and `require_model()` raises before any Gemini call if the model or its location is unset.

```bash
export GOOGLE_CLOUD_PROJECT=delivery-experience-511901
export PRIORAUTH_MODEL=gemini-3.5-flash
export PRIORAUTH_MODEL_LOCATION=global
export PRIORAUTH_DATA_LOCATION=us-central1
export PRIORAUTH_DATASET=priorauth_agent
export PRIORAUTH_EMBEDDING_MODEL=text-embedding-004
```

Re-verify the model pair with one minimal live call before any full run: the pair verified on 2026-10-27 (gemini-3.5-flash at global, data us-central1) is not assumed to still hold. See `docs/CONFIGURATION.md` for every variable, and `docs/DEPLOYMENT.md` for the deployment procedure and the IAM roles to request. Set a spending cap before running, and restore any temporary raise immediately after the run.

## Raw evidence

`evidence/cloud_eval_2026-10-27/raw/` contains all 8 original evaluation files, unchanged, verified by size and SHA-256:

| File | Bytes | SHA-256 |
| --- | --- | --- |
| results_real.json | 475,878 | d6869b0598bb741559da0b6aa1f430af72bf096fbc2a97a57cc3346381dad2f7 |
| results_no_citation_check.json | 475,447 | afd54544eb2cb866bd840308120c3c8f2fe99afe49d124286083b6467acacce7 |
| results_baseline.json (superseded) | 104,563 | ba360bd79a319777f9183b0377579dae3b6025ee68347ebe2e05d825bf9bedf2 |
| results_baseline_corrected.json | 116,872 | ed13f335aff8b1452a8419b39b33e1fa63e35a31710f18d115caff1d60986ff9 |
| results_pilot.json | 52,038 | 48756dd82c256562e23b30de80c284b1995f2035f060f2c261688a98e9320140 |
| results_real_partial14.json | 199,995 | b4248e9b966332aaa7a3d13997205be5ba462ad0fdce11b28cde10bef66a3030 |
| ablation_report.txt | 669 | 9e9c38d444b3b3ec59a3c03eef38637f0b3ab25e1722e5f14ad06403aa528154 |
| false_ready_report.txt | 188 | d9630f92ebf0aa140a15dedac0636146a2da1bc845be4d1b21163049e9925ef7 |

Summaries are in the same evidence directory and in `docs/EVAL_RESULTS_2026-10-27.md`. The summaries are not substitutes for the raw files.

## Data provenance

- Policies are simplified faithful subsets, not verbatim text and not complete policies. Aetna CPB 0236 (lumbar spine MRI), Aetna CPB 0673 (knee osteoarthritis selected treatments), and Cigna IP0660 (infliximab intravenous products, effective 03/15/2026, 22 pages total). Only the first pages and the Crohn excerpt of IP0660 were read in detail, and a March 2026 update removed several Crohn initial therapy options. A human must re-read all 22 pages, and the full current policy, before any real use. See `docs/DATA_PROVENANCE.md` and `docs/SIMPLIFIED_VS_COMPLETE_POLICIES.md`.
- Evaluation cases: 3 paraphrased published case reports (PMC11475090, CC BY 4.0; PMC7993418, CC BY; PMC8891723, CC BY-NC 4.0, non-commercial only), each with source URL and license in `data/eval_cases.json`. The other 27 cases are structured test fixtures, clearly labeled, not real patient notes. No PHI, no MIMIC credentialed data, and no MTSamples presented as real.
- No CPT list is redistributed. ICD-10-CM examples come only from policy-supported lists (M54.16, M51.16, M17.0, K50.90). HCPCS J1745 is used in the simplified subset; Q5103 is a different product code and is never silently substituted.

## Limitations (read before reusing anything here)

- Deployment failed: Cloud Run deployment failed on IAM permissions for the Cloud Build default service account. No IAM change was made, and no service URL, screenshot, or deployed review exists. `docs/DEPLOYMENT.md` documents the required roles to request, not changes made.
- Spend attribution gap, unresolved: for the full evaluation, the console Vertex delta was about $4.29 vs a script estimate of about $0.22; for the corrected baseline, about $0.64 vs $0.0463. Both are below the $8 stop used for those runs, but do not attribute the full console delta to this project alone.
- Cloud test gate (43 passed, 3 failed, 1 skipped) root cause is inference only, not proven, and is not erased by local 49-passed runs.
- Verifier before/after status is not stored per criterion in the raw rows, so verifier action on an individual claim is inferred from final status, excerpt, and the verifier rules, as labeled in the analysis docs.
- The original baseline raw response text is not stored in the raw rows, so the exact as-run model output that produced all-missing criteria cannot be recovered.
- The 60/60 result in older material is a templated guardrail test on synthetic cases, never model performance.
- Not clinically validated, not production certified, not ready for real patient information. A `READY_FOR_HUMAN_REVIEW` result means ready for a human to review against the full policy, not approved.

## License

MIT, see `LICENSE`. If you prefer another license, swap that file before publishing.
