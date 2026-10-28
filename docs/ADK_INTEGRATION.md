# Google ADK integration: exact Runner and tool invocation path

## Audit finding, stated plainly

First delivered revision 2.0.0-real was NOT genuinely ADK-driven,
even though its README and docs said "real ADK pipeline".

Evidence, in the old code:
- src/priorauth/adk_agent.py, old run_via_adk: it called
  build_agent(config), then called run_real_review(case, policy, ...)
  directly. It never called Runner, never created a session, and
  never read an ADK Event.
- Old tool_calls was a fabricated-looking string:
  "adk_agent:priorauth_agent:gemini-3.8-flash" plus the pipeline's
  own tool names. That string was not a tool invocation, and it
  must never be quoted as one.
- Old tools search_policy_chunks and validate_case_codes were plain
  Python functions listed in Agent(tools=[...]), but ADK never
  invoked them, because Runner.run_async was never called.
- FastAPI and evaluate_real.py called run_via_adk, so they inherited
  the same flaw: the agent object existed, the pipeline ran beside it.

This document describes the fixed path. If any future change reverts
to building an agent and then calling run_real_review directly,
that change reintroduces the flaw, and the tests in
tests/test_adk_agent.py are designed to catch it by checking that
run_via_adk_async source calls Runner.run_async, create_session,
get_function_calls, and get_function_responses, and does not call
run_real_review.

## Fixed execution path, file by file

Entry points, both use the same path:
- src/priorauth/api.py, create_review: calls
  adk_agent.run_via_adk(case, policy, _CHUNKS). If credentials are
  absent, run_via_adk raises CloudNotConfigured, and FastAPI maps
  it to HTTP 503. It never falls back to a mock.
- scripts/evaluate_real.py, main: calls adk_agent.run_via_adk for
  every eval case, with the same budget tracker and the same
  verify_citations flag (False only for the ablation arm).

Sync wrapper:
- src/priorauth/adk_agent.py, run_via_adk(case, policy, chunks,
  config, **kwargs): if no event loop is running, it calls
  asyncio.run(run_via_adk_async(...)). If a loop is already running,
  it raises and tells the caller to use run_via_adk_async, because
  asyncio.run cannot be nested. FastAPI endpoints in this repo are
  sync, and eval scripts are sync, so the wrapper is the normal path.

Async execution, the authoritative path:
- src/priorauth/adk_agent.py, run_via_adk_async(case, policy, chunks,
  config, budget, audit_path, verify_citations):
  1. Check credentials with adk_available(). If absent, raise
     CloudNotConfigured. No mock result is returned.
  2. Build a _RunContext(case, policy, chunks, config, budget).
     This object holds the bound review. The model never supplies
     the clinical note through a tool argument, so it cannot
     fabricate a note by passing one.
  3. Build the agent with build_agent_for_run(ctx), which calls
     build_agent(config, run_context=ctx).
  4. Build a Runner with build_runner(agent=agent):
     Runner(agent=agent, app_name="priorauth_agent",
     session_service=InMemorySessionService()).
     InMemorySessionService is demo and Cloud Shell eval only.
     Production must replace it with a persistent session service.
     That substitution is documented in docs/REAL_SYSTEM.md, not claimed.
  5. Create a session, awaited, because InMemorySessionService.
     create_session is async in google-adk 2.13.0:
       session = await runner.session_service.create_session(
           app_name="priorauth_agent", user_id="priorauth-reviewer",
           state={"case_id": case.case_id, "policy_id": policy.policy_id,
                  "procedure": case.procedure},
           session_id=f"session-{uuid4 hex[:12]}")
     The session id is recorded in ReviewResult.adk_session_id.
     Session state holds only ids, not the full note or chunks.
  6. Build the user message:
       Content(role="user", parts=[Part(text=...)])
     from google.genai.types. The text names the case id, policy id,
     policy version, and procedure, and instructs the model to call
     search_policy_chunks, then validate_case_codes, then
     extract_evidence, in that order, and stop, without deciding
     readiness itself.
  7. Drive the agent:
       async for event in runner.run_async(
           user_id="priorauth-reviewer", session_id=session.id,
           new_message=content):
     For every event, record:
       - event.author
       - event.is_final_response()
       - event.get_function_calls(): each call name and args summary
       - event.get_function_responses(): each response name and keys
       - final response text, truncated to 1000 characters
     These records go, summarized, into ReviewResult.adk_tool_events,
     with names in ReviewResult.adk_tools_invoked. An empty
     adk_tool_events list means the Runner did not run, and it must
     never be backfilled.
  8. Check tool responses for a credentials error. If any tool
     response contains CloudNotConfigured, raise CloudNotConfigured.
     Any other missing tool is recorded as a critic finding, and
     its criteria are treated as missing, not met. See "Tool failure"
     below.
  9. Take deterministic inputs from ADK tool outputs, not from model
     free text:
       - retrieved chunks and retrieval method from the
         search_policy_chunks tool output, stored in _RunContext.
       - code validation from the validate_case_codes tool output,
         or, if that tool was not invoked, from a deterministic
         recomputation with code_validator, recorded as such.
         Recomputing a deterministic check is not a model decision.
       - evidence outcomes and token usage from the extract_evidence
         tool output. If that tool was not invoked, every criterion
         is treated as missing, not met, and the case cannot be READY.
     Then call real_pipeline.finalize_review, which runs
     citation_verifier, checklist_scorer, and draft_with_gemini
     after verification only. Drafting is recorded as
     draft_generator:gemini_post_verification, NOT as an ADK tool
     event, because drafting is not an ADK tool in this design.
     The audit log distinguishes ADK events from post-verification
     steps, and ReviewResult.tool_calls is populated from actual
     ADK tool names plus the deterministic step names that
     finalize_review appends, not from a fabricated list.

## Tool registration, exact names and signatures

Tools are registered as FunctionTool objects, not as plain functions
in a list, in src/priorauth/adk_agent.py, _make_tools(ctx):

- search_policy_chunks(policy_id: str, query: str, top_k: int = 5) -> dict
  Calls real_pipeline.retrieve_chunks with the bound case and
  policy, using Vertex embeddings or BigQuery VECTOR_SEARCH.
  Returns chunk ids, sections, text, scores, and retrieval method.
  Checks policy_id against the bound policy first; on mismatch it
  returns an error dict, not a chunk from another policy.
- validate_case_codes(case_id: str) -> dict
  Calls tools.code_validator with the bound case and policy.
  Deterministic, no model call. Checks case_id against the bound
  case first.
- extract_evidence(policy_id: str) -> dict
  Calls real_pipeline.extract_evidence_with_gemini with the bound
  case, policy, and retrieved chunks. Returns criterion outcomes
  with statuses, exact excerpts, notes, and token usage. Excerpts
  are not trusted here; citation_verifier checks them verbatim
  afterwards, and unsupported claims are downgraded to missing.

Tools are bound to one review by closure over _RunContext at
Runner creation time. That is intentional: it prevents the model
from supplying a different clinical note, different codes, or a
different policy through tool arguments. The model supplies only
policy_id, query, and case_id, each checked against the bound review.

build_agent() without a run context is for inspection and tests
only. Its single tool returns an error if called, because it has
no bound case. Execution must use build_agent_for_run and
run_via_adk_async. Any code path that calls build_agent() and then
runs a separate pipeline is the old flaw, restated.

## Model endpoint separate from data location, fixed 2026-10-27

This fix is local only. No cloud call was made in this VM, and
no global call is claimed as successful here.

- Data location: CloudConfig.location, default us-central1.
  It is used for BigQuery dataset priorauth_agent and for
  embeddings (text-embedding-004, dimension 768, verified in
  us-central1). It comes from PRIORAUTH_DATA_LOCATION if set,
  else GOOGLE_CLOUD_LOCATION for backward compatibility.
- Model location: CloudConfig.model_location, from
  PRIORAUTH_MODEL_LOCATION, default "global". It is used only
  for Gemini generation calls: the ADK Gemini client_kwargs
  location, and the Vertex init inside gemini_generate in
  cloud_clients.py. It is never used for BigQuery.
- Why they differ: gemini-3.5-flash, gemini-3.5-flash-lite,
  and gemini-3.8-flash all returned 404 in us-central1 for
  this project on 2026-10-27. On 2026-10-27 the user approved
  testing the global endpoint now, and confirmed from Google
  official documentation that gemini-3.5-flash is listed as
  supported on global and us, not us-central1. "global" as a
  default is therefore the approved test endpoint, not a
  verification. gemini-3.5-flash at global is a documented
  candidate only until a minimal live call succeeds in Cloud
  Shell at global.
- Run record: every ReviewResult and every eval report now
  carries model_name, model_location, and data_location as
  separate fields. A result that reports only one location
  is incomplete for this project, because the model endpoint
  and the data location are different by design.
- Cloud Shell must set, before any verification call:
    export PRIORAUTH_MODEL=gemini-3.5-flash
    export PRIORAUTH_MODEL_LOCATION=global
  The model name above is the documented candidate for the
  global test, not a verified name. If the minimal live call
  at global fails, stop and report the exact error. Do not
  raise the spending cap until configuration and model
  availability checks are complete; if the cap then blocks
  the call, raise it temporarily to $50 under the $10
  incremental budget and $8 stop rule, and restore it to
  $10 after cloud execution, even on failure.

## Model and embedding strings, verified against installed ADK 2.13.0

- Agent model object: google.adk.models.Gemini, constructed as
  Gemini(model=config.model, client_kwargs={"vertexai": True,
  "project": config.project, "location": config.model_location}).
- Model string, single configuration point: PRIORAUTH_MODEL,
  read in CloudConfig. The built-in fallback "gemini-3.8-flash"
  is UNVERIFIED and FAILED in Cloud Shell on 2026-10-27 with
  404 NOT_FOUND in us-central1 for this project, so 0 of 30
  cases ran in the final attempt. Do not use it for a rerun
  unless Cloud Shell first re-verifies it. The cloud script
  now refuses to run without PRIORAUTH_MODEL set. See
  docs/MODEL_CANDIDATES.md for candidates and verification.
  ADK itself does not settle availability: in google-adk 2.13.0,
  Gemini.supported_models() matches gemini-.*, so any gemini-
  string builds an object and the server decides at call time.
  There is no "vertexai/gemini-..." prefix in ADK 2.13.0 registry
  resolution; Gemini.supported_models() in
  google/adk/models/google_llm.py matches r'gemini-.*', and its
  api_client builds a google.genai Client. That client chooses
  Vertex AI when vertexai=True (see google/genai/_api_client.py,
  GOOGLE_GENAI_USE_VERTEXAI handling, and ADK
  utils/_gcp_metadata.py, get_gcp_client_defaults). The Vertex
  backend therefore comes from client_kwargs, not from the string.
  The separate, non-ADK gemini_generate in cloud_clients.py uses
  the vertexai GenerativeModel SDK; both go to Vertex, and eval
  output records the model name, not a claim of a single SDK.
- Embedding model, default: "text-embedding-004", from
  PRIORAUTH_EMBEDDING_MODEL. Verified in Cloud Shell on
  2026-10-27: text-embedding-004, dimension 768. Do not mix
  embedding models in one index. That check is in
  gcp/embed_policy_chunks.py --verify-only, and in
  gcp/cloud_step2_load_and_eval.sh.
- gemini-2.5-flash remains superseded for Vertex use, with the
  Vertex retirement date recorded as 2026-10-20 in docs/CLOUD_STATUS.md.
  Final availability must be rechecked in Cloud Shell before any
  paid call, because model listings change.

## Tool failure handling

- Credentials error in any tool response: raise CloudNotConfigured
  after Runner finishes. FastAPI maps it to 503. Eval scripts exit
  without writing a fabricated result for that case.
- Other tool error, or a required tool never called: record a
  critic finding, treat affected criteria as missing, and let the
  deterministic scorer decide. A case with a missing tool cannot
  become READY_FOR_HUMAN_REVIEW, because at least one required
  criterion will be missing in every pathway. In eval, that case
  counts as wrong if its gold readiness is READY, and as a system
  failure to investigate, not as a silently repaired run.
- Tool argument mismatch (policy_id or case_id does not match the
  bound review): tool returns an error dict, no work is done for
  the wrong policy or case, and the mismatch is recorded.
- Runner or session failure before any tool call: no ReviewResult
  is fabricated. The error propagates, and the eval run stops for
  that case with the error recorded, not with a precomputed outcome.

## Trace example, structure only, not a real trace

No model run has occurred in this VM, so the trace below is a
structure example only. It must never be presented as a real
execution trace. A real trace will have the same fields, filled
from actual Runner events, in eval/results_real.json rows under
adk_tool_events, adk_tools_invoked, and adk_session_id.

```
adk_session_id: "session-9f3a2b1c4d5e"
adk_tools_invoked: ["search_policy_chunks", "validate_case_codes", "extract_evidence"]
adk_tool_events: [
  {"author": "priorauth_agent", "is_final_response": false,
   "function_calls": [{"name": "search_policy_chunks", "args": "{'policy_id': 'AETNA_CPB_0236', 'query': '...', 'top_k': 5}"}],
   "function_responses": [], "text": ""},
  {"author": "priorauth_agent", "is_final_response": false,
   "function_calls": [], "function_responses": [{"name": "search_policy_chunks", "keys": ["retrieval_method", "chunks"]}], "text": ""},
  {"author": "priorauth_agent", "is_final_response": false,
   "function_calls": [{"name": "validate_case_codes", "args": "{'case_id': 'EVAL-LUM-01'}"}],
   "function_responses": [], "text": ""},
  {"author": "priorauth_agent", "is_final_response": false,
   "function_calls": [{"name": "extract_evidence", "args": "{'policy_id': 'AETNA_CPB_0236'}"}],
   "function_responses": [], "text": ""},
  {"author": "priorauth_agent", "is_final_response": true,
   "function_calls": [], "function_responses": [{"name": "extract_evidence", "keys": ["criterion_outcomes", "token_usage"]}],
   "text": "Tool calls complete. Readiness is decided by the deterministic scorer, not by this text."}
]
```

## What is NOT an ADK tool, by design

- citation_verifier: deterministic, in tools.py, run after ADK
  events, in finalize_review. It must never be a chat model
  decision, because a model checking its own citations is not
  independent verification.
- checklist_scorer: deterministic pathway guardrail, in tools.py,
  run after ADK events, in finalize_review. It decides readiness.
- draft_with_gemini: Gemini call after verification only, from
  verified met criteria, in finalize_review. It is recorded as a
  post-verification step, not as an ADK tool event.
- code_validator recomputation when the ADK validate tool was
  not invoked: deterministic, recorded as such, not a model decision.

This separation is the point of the design: ADK drives retrieval,
validation, and evidence extraction, and deterministic code decides
safety-critical outcomes. Reversing that separation, by letting a
model decide readiness or verify its own citations, would be a
design failure, not an improvement.
