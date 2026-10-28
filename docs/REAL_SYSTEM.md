# PriorAuth Agent, real system (revision 2.0.0-real)

## CLOUD EVAL VERIFIED 2026-10-27, DEPLOYMENT FAILED (current status, read first)

Cloud evaluation WAS executed 2026-10-27, 9:59 AM to 1:12 PM ET:
gemini-3.5-flash at global, data us-central1, full system 30/30,
criterion 171/200, case 28/30, false-ready 0/25. See
docs/EVAL_RESULTS_2026-10-27.md. Cloud Run deployment FAILED on
IAM, so no deployed URL, screenshot, or deployed review exists.
The sections below that say CLOUD EVAL PENDING, or name
gemini-3.8-flash by default, or us-central1 as the model
location, are the original 2.0.0-real text, preserved as history
and SUPERSEDED. Do not quote them as current.

## CLOUD EVAL PENDING (SUPERSEDED, do not quote as current)

No metric in this document may be presented as model performance
until a Gemini/Vertex pipeline has actually executed in Cloud Shell
and its outputs are recorded in eval/results_real.json,
eval/results_baseline.json, and eval/results_no_citation_check.json.
Until then, every result claim in this document is either a
deterministic guardrail test, a code inspection, or a pending
section, and it is labeled as such.

## ADK audit, 2026-10-27: first 2.0.0-real delivery was not ADK-driven

The first 2.0.0-real delivery built an ADK Agent and Runner, then
ran real_pipeline separately, and recorded a fabricated-looking
"adk_agent:priorauth_agent:gemini-3.8-flash" string as if it were a
tool invocation. That version is superseded. The fixed execution
path, in this repo, is documented in docs/ADK_INTEGRATION.md:
FastAPI and evaluate_real.py call adk_agent.run_via_adk, which
creates a session, drives Runner.run_async, records actual tool
call and response events, feeds tool outputs to deterministic
citation verification and pathway scoring, and records the ADK
session id, tool names, tool event summaries, model name, and
event trace in the audit log. Drafting is after verification only,
and is recorded as a post-verification step, not as an ADK tool
event, because it is not one.

## What is real, what is deterministic, what is pending

- Real code [SUPERSEDED INTRO: cloud execution has since happened, see header]: Google ADK agent in
  src/priorauth/adk_agent.py with model set by PRIORAUTH_MODEL
  [SUPERSEDED TEXT: the original said gemini-3.8-flash by default
  at us-central1; the verified run used gemini-3.5-flash at global,
  data us-central1, and gemini-3.8-flash returned 404 in us-central1]
  (Gemini object with client_kwargs vertexai=True, project
  delivery-experience-511901, see
  docs/ADK_INTEGRATION.md) and tools for policy search, code
  validation, and evidence extraction; Vertex embeddings retrieval
  (text-embedding-004 default, verify dimension in Cloud Shell
  before indexing, never mix models); Gemini structured evidence
  extraction and drafting (src/priorauth/real_pipeline.py);
  BigQuery VECTOR_SEARCH path when the policy_chunks table is loaded.
  "Real code" means the code path is genuine and testable.
  [SUPERSEDED: a cloud run HAS happened since this text was
  written, verified 2026-10-27, see docs/EVAL_RESULTS_2026-10-27.md.]
- Deterministic guardrails only, never a model decision: schema
  validation, code validation, citation quote checking (every quoted
  excerpt must appear verbatim in the note), pathway scoring, stale
  policy blocking, exclusion blocking. No model output can produce
  READY_FOR_HUMAN_REVIEW when a guardrail fails.
- [SUPERSEDED pending list: data load, embedding generation, the
  30-case real eval, baseline, and ablation HAVE since been
  completed in Cloud Shell 2026-10-27; temporary Cloud Run deploy
  FAILED on IAM, so screenshots and a deployed review do NOT
  exist. Exact commands are in gcp/cloud_step2_load_and_eval.sh.]
- Superseded: the old 60/60 templated deterministic eval was a
  guardrail test on synthetic cases, not model performance. It must
  never be quoted as model accuracy. The 60 synthetic cases now live
  only as data/guardrail_cases.json for guardrail tests.

## Data, honestly labeled

- Policies: simplified faithful subsets of Aetna CPB 0236, Aetna CPB
  0673, and Cigna IP0660 (Crohn indication only), with source URLs in
  data/policies.json. Full policies must be checked by a human.
  Do not soften this. See docs/SIMPLIFIED_VS_COMPLETE_POLICIES.md.
  Cigna caveat: a March 2026 policy update removed several IP0660
  Crohn initial therapy options effective 03/15/2026. Only the
  first pages and the Crohn excerpt were read in detail. The full
  22 pages were NOT read. A human must read all 22 pages and
  re-check the current version before any real use. A simplified
  subset cannot be used for a real submission, because it omits
  rules that can change the answer, its code lists are incomplete,
  and its pathways are models of a policy, not the policy.
  An unsupported code here means not in the subset, not not covered,
  and a supported code here does not prove coverage.
- Eval set: 30 cases in data/eval_cases.json, annotated before any
  model run, not used to optimize the agent. 3 are paraphrased
  published case reports (PMC11475090 CC BY 4.0, PMC7993418 CC BY,
  PMC8891723 CC BY-NC 4.0 non-commercial only). 27 are structured
  test fixtures, clearly labeled, not real patient notes. Gold
  readiness: 5 READY_FOR_HUMAN_REVIEW, 13 NOT_READY,
  12 NEEDS_MANUAL_REVIEW, derived from gold criterion outcomes by the
  deterministic pathway scorer, not by a model.
  Difficult cases are deliberate: contradictions, ambiguous wording,
  negated findings, incomplete conservative treatment (for example
  3 weeks PT, unclear duration), outdated policy versions,
  unsupported claims, incorrect or unsupported codes, exclusions
  fired, age rule failures, and red-flag and locked-knee waiver
  pathways. See data/eval_cases.json categories.
- Difficult case walkthroughs, 3 to 5, pending actual Cloud Shell
  outputs: they will be added here from eval/results_real.json,
  showing where the system succeeds and where it fails, with
  criteria, citations, critic findings, and guardrail outcome per
  case. Until then, no walkthrough is invented here, and no case
  is described as a success or failure of the model.
- False-ready analysis, pending actual run: run
  python scripts/false_ready_report.py eval/results_real.json
  after the Cloud Shell eval. It lists every predicted READY case
  that is gold non-ready, with criteria, citations, and guardrail
  outcome. A zero false-ready claim is allowed only if that run
  actually shows it, with its denominator (gold non-ready cases).
- Limitation: no representative typical prior auth packet (request
  form, imaging report, PT notes, denial letter) was found as a
  legally reusable real set. The PMC vignettes are atypical. Results
  on this set do not prove performance on typical packets.
- No real patient data, no PHI, no MIMIC credentialed data, no
  MTSamples text presented as real. The system is not clinically
  validated, not production-certified, and not ready for real patient
  information. Human review is required for every case.

## Architecture, in one paragraph

FastAPI (src/priorauth/api.py) and Streamlit (app/streamlit_app.py)
call the same ADK pipeline. Intake is Pydantic validated. Retrieval
embeds the case query with Vertex AI and ranks policy chunks by
cosine similarity, or uses BigQuery VECTOR_SEARCH when the table is
loaded. Gemini extracts one structured outcome per criterion, with
exact excerpts required. Deterministic code validation and citation
verification downgrade unsupported claims to missing. The pathway
scorer decides readiness. Gemini drafts only from verified met
criteria, with gaps listed separately. Every run is audit logged with
model, embedding model, token usage, estimated cost, retrieval
method, and tool calls. Retries: the pipeline raises on cloud
failure instead of retrying silently or returning a mock; eval runs
are idempotent because each review gets a new review ID and results
are written per run to eval/results_real.json, never overwritten
without a new filename for a new arm.

## Business value, measured vs hypothetical, kept separate

- Measured (available after Cloud Shell eval): review time per case
  in the demo (latency_ms in eval output) and estimated API cost per
  case. No manual baseline was measured in this build, so no time
  saved figure is claimed. A manual baseline method for a future
  measurement: time a human reviewer working the same 30 cases with
  the policy PDFs open, record per-case minutes, and compare medians.
  Until that is run, time savings are hypothetical, not measured.
- Hypothetical value model (assumptions, not results): if a reviewer
  spends T minutes per case manually and the demo takes D minutes,
  and a clinic reviews N cases per week, weekly time change is
  N times (T minus D). T, N, and any denial or revenue effect are
  inputs a clinic must supply. No staff productivity, denial
  reduction, or financial ROI figure is claimed in this project.
- Plausible value, stated as mechanism not outcome: repetitive policy
  lookup is automated, missing documentation is surfaced before
  submission, and every decision has a citable trail, which supports
  consistent human decisions. Whether that changes outcomes must be
  measured in a real deployment, which this project is not.

## Broader enterprise applications (potential only, not implemented)

The same pattern transfers, and nothing else in this repo implements
these: contract compliance verification (clauses as criteria,
contract text as evidence), billing dispute analysis, shipping claims
documentation (carrier policy as criteria, delivery evidence as
notes), operations policy validation, enterprise knowledge workflows,
and evidence-based exception management. In each, policy retrieval,
structured requirements, evidence matching, independent verification,
audit trails, and human escalation are the reusable parts. Healthcare
remains the only implemented use case.

## Enterprise engineering: implemented vs proposed

- Implemented: modular code, Pydantic schema enforcement, audit
  logging with traceability, versioned policies with current and
  superseded versions, input validation, cost controls (BudgetTracker
  stops at $8, ceiling $10), cleanup scripts, automated tests.
- Proposed, not implemented: authentication and authorization for
  the API, persistent session storage (InMemorySessionService is
  demo only), monitoring and alerting, rate limiting, production
  secrets management, HIPAA-compliant hosting, and clinical validation.
  None of these are claimed as done.
