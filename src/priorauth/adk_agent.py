"""Google ADK orchestration layer for PriorAuth Agent, genuinely ADK-driven.

Audit finding, 2026-10-27, revision 2.0.0-real as first delivered:
the old run_via_adk built an Agent object, then called run_real_review
directly. The ADK Runner was never called, no ADK tool event was ever
emitted, and the string "adk_agent:priorauth_agent:gemini-3.8-flash"
in tool_calls was not a tool invocation. That version is superseded.
Do not quote it as ADK execution.

Current execution path, the only path FastAPI and evaluate_real.py use:
  api.create_review / evaluate_real.main
    -> adk_agent.run_via_adk (sync wrapper)
    -> adk_agent.run_via_adk_async
      -> build_agent_for_run(case, policy, chunks, config, budget)
           Agent(model=Gemini(...), tools=[FunctionTool(...), ...])
      -> session_service.create_session(app_name="priorauth_agent",
           user_id="priorauth-reviewer", state={case_id, policy_id, procedure})
      -> Runner.run_async(user_id, session_id, new_message=Content)
           Runner yields Event objects. Each event's
           get_function_calls() and get_function_responses() are
           recorded verbatim (summarized) in ReviewResult.adk_tool_events.
           FunctionTool invokes, in the order the model calls them:
             search_policy_chunks, validate_case_codes, extract_evidence
      -> tool outputs from ADK events (not model free text) are taken
         as inputs to deterministic citation_verifier and
         checklist_scorer in real_pipeline.finalize_review
      -> draft_with_gemini, after verification only, recorded as
         draft_generator:gemini_post_verification, NOT as an ADK
         tool event, because drafting is not an ADK tool in this
         design. The audit log distinguishes ADK events from
         post-verification steps.

Model backend, verified against installed google-adk 2.13.0:
- Agent model is a Gemini object, not a bare string, so the backend
  is explicit: Gemini(model=config.model,
  client_kwargs={"vertexai": True, "project": config.project,
  "location": config.model_location}).
- Model endpoint is separate from data location, fixed 2026-10-27:
  config.model_location comes from PRIORAUTH_MODEL_LOCATION
  only, with no default. config.location stays us-central1 for
  BigQuery and embeddings and is never used for the ADK
  Gemini client. The verified pair for the 2026-10-27 cloud
  eval was gemini-3.5-flash at global, data us-central1;
  re-verify that pair with a minimal live call before any
  rerun. The non-ADK gemini_generate path in
  cloud_clients.py also uses config.model_location, while
  embeddings and BigQuery use config.location, so the whole
  Gemini generation path moves with the model endpoint and
  the data path does not move.
- In google/adk/models/google_llm.py, Gemini.supported_models()
  matches r'gemini-.*', and its api_client builds a google.genai
  Client. That client chooses Vertex AI when vertexai=True (see
  google/genai/_api_client.py, GOOGLE_GENAI_USE_VERTEXAI handling,
  and ADK get_gcp_client_defaults in utils/_gcp_metadata.py).
  There is no "vertexai/gemini-..." prefix in ADK 2.13.0 registry
  resolution; the prefix form would go to LiteLLM, not Gemini.
  The plain model string is therefore the value of PRIORAUTH_MODEL,
  read in CloudConfig, the single configuration point. There is
  no default: if PRIORAUTH_MODEL or PRIORAUTH_MODEL_LOCATION is
  unset, require_model() raises before any Gemini call.
  Historical note: gemini-3.8-flash returned 404 NOT_FOUND in
  us-central1 for this project on 2026-10-27. The Vertex backend
  comes from client_kwargs, not from the string. The non-ADK gemini_generate in
  cloud_clients.py uses the separate vertexai GenerativeModel SDK;
  both go to Vertex, and eval output records which path was used
  by recording model name, not by claiming a single SDK.
- Embedding model default is text-embedding-004
  (PRIORAUTH_EMBEDDING_MODEL to change it). Cloud Shell must verify
  004 versus 005 availability and dimension before indexing, and
  must never mix embedding models in one index. That check is in
  gcp/embed_policy_chunks.py --verify-only.

Tool failure handling:
- A tool that hits missing GCP credentials returns
  {"error": "CloudNotConfigured: ..."} instead of raising through
  ADK, so the model sees the failure. After Runner finishes,
  run_via_adk_async re-checks tool responses: a credentials error
  raises CloudNotConfigured to the caller (FastAPI maps it to 503),
  it is never turned into a fabricated outcome.
- Any other tool error, or a required tool the model never called,
  is recorded as a critic finding, the affected criteria are
  treated as missing, and the deterministic scorer therefore
  cannot produce READY_FOR_HUMAN_REVIEW for that case. Missing
  tool output is a system failure, counted as wrong in eval, not
  silently repaired by a separate pipeline.
- Tools are bound to one review at Runner creation time (closure
  over case, policy, chunks, config, budget). The model never
  supplies the clinical note through a tool argument, so it cannot
  fabricate a note by passing one. It supplies only policy_id,
  query, and case_id, which are checked against the bound case
  and policy before any tool work runs.

Deterministic guardrails, unchanged: schema validation, code
validation, citation verbatim checking, pathway scoring, and
blocking READY on missing required evidence, fired exclusion,
invalid or unsupported code, or stale policy, regardless of
model output. Drafting happens only after verification, only
from verified met criteria.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field

from priorauth.cloud_clients import CloudConfig, CloudNotConfigured, check_credentials
from priorauth.models import ClinicalCase, Policy, ReviewResult
from priorauth.policies import load_chunks, load_policies


@dataclass
class _RunContext:
    case: ClinicalCase
    policy: Policy
    chunks: list[dict]
    config: CloudConfig
    budget: object = None
    retrieved: list[dict] | None = None
    retrieval_method: str = ""
    code_validation: object = None
    evidence_results: list | None = None
    evidence_usage: dict | None = None
    tool_trace: list[dict] = field(default_factory=list)


def _truncate(text: str, limit: int = 200) -> str:
    text = str(text or "")
    return text if len(text) <= limit else text[:limit] + "...[truncated]"


def build_gemini_model(config: CloudConfig):
    """Build the ADK Gemini model object with an explicit Vertex backend.

    No API call happens here. Building the object only records the
    model name and client_kwargs. The backend is chosen when ADK
    first uses the model, from vertexai=True plus project/location.
    """
    from google.adk.models import Gemini
    from priorauth.cloud_clients import require_model

    require_model(config)
    return Gemini(
        model=config.model,
        client_kwargs={
            "vertexai": True,
            "project": config.project,
            # Model endpoint only. Never config.location: that is
            # the data location (us-central1), where gemini-3.5-flash
            # and gemini-3.8-flash already returned 404.
            "location": config.model_location,
        },
    )


def _make_tools(ctx: _RunContext):
    """Create FunctionTools bound to one review. See module docstring.

    Each tool function has typed arguments so ADK can generate a
    Gemini function declaration from it. Each tool checks that the
    model-supplied policy_id / case_id matches the bound review
    before doing any work.
    """
    from google.adk.tools import FunctionTool

    def search_policy_chunks(policy_id: str, query: str, top_k: int = 5) -> dict:
        """Retrieve policy chunks with Vertex embeddings for a policy.

        Args:
            policy_id: Policy to search, must match the bound review.
            query: Free-text query, usually derived from the clinical note.
            top_k: Maximum chunks to return.
        Returns:
            Chunk ids, sections, text, scores, and retrieval method,
            or an error dict if credentials are absent or the policy
            does not match the bound review.
        """
        from priorauth.real_pipeline import retrieve_chunks

        if policy_id != ctx.policy.policy_id:
            return {"error": f"Policy mismatch: tool called with {policy_id}, bound review is {ctx.policy.policy_id}", "chunks": []}
        try:
            chunks, method = retrieve_chunks(ctx.case, ctx.policy, ctx.chunks, ctx.config)
        except CloudNotConfigured as exc:
            return {"error": f"CloudNotConfigured: {exc}", "chunks": []}
        except Exception as exc:
            return {"error": f"Retrieval failed: {exc}", "chunks": []}
        ctx.retrieved = chunks
        ctx.retrieval_method = method
        result = {"retrieval_method": method, "chunks": chunks[:top_k]}
        ctx.tool_trace.append({"tool": "search_policy_chunks", "policy_id": policy_id,
                               "query": _truncate(query), "chunk_ids": [c.get("chunk_id", "") for c in result["chunks"]]})
        return result

    search_policy_chunks.__name__ = "search_policy_chunks"

    def validate_case_codes(case_id: str) -> dict:
        """Validate diagnosis and procedure codes deterministically.

        Args:
            case_id: Case to validate, must match the bound review.
        Returns:
            Code validation result, or an error dict on mismatch.
        """
        from priorauth.tools import code_validator

        if case_id != ctx.case.case_id:
            return {"error": f"Case mismatch: tool called with {case_id}, bound review is {ctx.case.case_id}"}
        result = code_validator(ctx.case, ctx.policy)
        ctx.code_validation = result
        ctx.tool_trace.append({"tool": "validate_case_codes", "case_id": case_id,
                               "overall_status": result.overall_status})
        return result.model_dump()

    validate_case_codes.__name__ = "validate_case_codes"

    def extract_evidence(policy_id: str) -> dict:
        """Extract structured criterion outcomes with Gemini.

        Args:
            policy_id: Policy to extract for, must match the bound review.
        Returns:
            Criterion outcomes with statuses and exact excerpts, plus
            token usage, or an error dict if credentials are absent
            or the policy does not match. Excerpts are not trusted
            here; citation_verifier checks them verbatim afterwards.
        """
        from priorauth.real_pipeline import extract_evidence_with_gemini, retrieve_chunks

        if policy_id != ctx.policy.policy_id:
            return {"error": f"Policy mismatch: tool called with {policy_id}, bound review is {ctx.policy.policy_id}"}
        try:
            retrieved = ctx.retrieved
            if retrieved is None:
                retrieved, method = retrieve_chunks(ctx.case, ctx.policy, ctx.chunks, ctx.config)
                ctx.retrieved = retrieved
                ctx.retrieval_method = method
            results, usage = extract_evidence_with_gemini(ctx.case, ctx.policy, retrieved, ctx.config)
        except CloudNotConfigured as exc:
            return {"error": f"CloudNotConfigured: {exc}"}
        except Exception as exc:
            return {"error": f"Evidence extraction failed: {exc}"}
        ctx.evidence_results = results
        ctx.evidence_usage = usage
        outcomes = [{"criterion_id": r.criterion_id, "status": r.status,
                     "evidence_excerpts": r.evidence_excerpts, "notes": r.notes} for r in results]
        ctx.tool_trace.append({"tool": "extract_evidence", "policy_id": policy_id,
                               "outcome_count": len(outcomes),
                               "token_usage": usage})
        return {"criterion_outcomes": outcomes, "token_usage": usage}

    extract_evidence.__name__ = "extract_evidence"

    return [
        FunctionTool(search_policy_chunks),
        FunctionTool(validate_case_codes),
        FunctionTool(extract_evidence),
    ]


def build_agent(config: CloudConfig | None = None, run_context: _RunContext | None = None):
    """Build the ADK agent.

    Without a run context, tools are bound to no case and return an
    error if called; build_agent alone is for inspection and tests,
    not for execution. Execution must use build_agent_for_run and
    run_via_adk_async, which bind tools to a real case and policy
    and drive them through Runner.run_async.
    """
    from google.adk.agents import Agent

    config = config or CloudConfig()
    if run_context is not None:
        tools = _make_tools(run_context)
    else:
        # Inspection-only tools: they refuse to run without a bound review.
        def _unbound(*args, **kwargs):
            return {"error": "Tool called without a bound case review context. Use run_via_adk_async, not build_agent alone, for execution."}

        _unbound.__name__ = "search_policy_chunks"
        from google.adk.tools import FunctionTool

        tools = [FunctionTool(_unbound)]
    agent = Agent(
        name="priorauth_agent",
        model=build_gemini_model(config),
        description="Prior authorization documentation reviewer. It never approves, denies, or submits a prior authorization.",
        instruction=(
            "You review documentation readiness for human review only. "
            "Call search_policy_chunks for the bound policy, then "
            "validate_case_codes for the bound case, then extract_evidence "
            "for the bound policy, in that order, and stop. Do not decide "
            "readiness yourself, do not invent an excerpt, code, duration, "
            "or finding, and do not add clinical claims in your final text. "
            "The deterministic checklist scorer, not you, decides readiness, "
            "and citation verification checks every excerpt verbatim afterwards."
        ),
        tools=tools,
    )
    return agent


def build_agent_for_run(ctx: _RunContext):
    """Build an agent whose tools are bound to one review."""
    return build_agent(config=ctx.config, run_context=ctx)


def build_runner(agent=None, config: CloudConfig | None = None, run_context: _RunContext | None = None):
    """Build an ADK Runner with an in-memory session service.

    InMemorySessionService is correct for this demo and for Cloud Shell
    eval. A production deployment must replace it with a persistent
    session service. That substitution is documented, not claimed.
    """
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService

    if agent is None:
        agent = build_agent_for_run(run_context) if run_context is not None else build_agent(config)
    return Runner(agent=agent, app_name="priorauth_agent", session_service=InMemorySessionService())


def adk_available() -> dict:
    """Report ADK availability and credential presence, no secrets."""
    try:
        from google.adk.agents import Agent  # noqa: F401
        from google.adk.runners import Runner  # noqa: F401

        adk = True
    except Exception:
        adk = False
    try:
        creds = check_credentials()
        present = bool(creds.get("credentials_present"))
    except Exception:
        present = False
    config = CloudConfig()
    return {"adk_available": adk, "credentials_present": present,
            "model": config.model, "embedding_model": config.embedding_model,
            "model_location": config.model_location, "data_location": config.location,
            "model_verification_status": "VERIFIED 2026-10-27: gemini-3.5-flash at global responded OK in a minimal live Cloud Shell call and completed the 30-case cloud eval (data us-central1); re-verify that pair before any rerun. No model default exists: PRIORAUTH_MODEL and PRIORAUTH_MODEL_LOCATION must be set explicitly. Historical note: gemini-3.8-flash, gemini-3.5-flash, and gemini-3.5-flash-lite all returned 404 in us-central1 on 2026-10-27."}


async def run_via_adk_async(
    case: ClinicalCase,
    policy: Policy,
    chunks=None,
    config: CloudConfig | None = None,
    budget=None,
    audit_path=None,
    verify_citations: bool = True,
) -> ReviewResult:
    """Run one review genuinely through ADK Runner. See module docstring."""
    from google.genai import types as genai_types

    from priorauth.cloud_clients import BudgetTracker
    from priorauth.real_pipeline import finalize_review
    from priorauth.tools import code_validator

    config = config or CloudConfig()
    budget = budget or BudgetTracker(budget_usd=config.budget_usd)
    if not adk_available()["credentials_present"]:
        raise CloudNotConfigured(
            "GCP credentials are absent. Run in Cloud Shell after signing in "
            "and clicking Authorize, or set Application Default Credentials. "
            "No mock result is returned."
        )
    ctx = _RunContext(case=case, policy=policy, chunks=chunks if chunks is not None else load_chunks(),
                      config=config, budget=budget)
    agent = build_agent_for_run(ctx)
    runner = build_runner(agent=agent)
    session_id = f"session-{uuid.uuid4().hex[:12]}"
    user_id = "priorauth-reviewer"
    session = await runner.session_service.create_session(
        app_name="priorauth_agent", user_id=user_id,
        state={"case_id": case.case_id, "policy_id": policy.policy_id, "procedure": case.procedure},
        session_id=session_id,
    )
    session_id = session.id
    started = time.perf_counter()
    user_text = (
        f"Review case {case.case_id} for policy {policy.policy_id} version {case.policy_version}, "
        f"procedure {case.procedure}. Call search_policy_chunks with policy_id={policy.policy_id} "
        f"and a query derived from the clinical note, then validate_case_codes with "
        f"case_id={case.case_id}, then extract_evidence with policy_id={policy.policy_id}, "
        "in that order, and stop. Do not decide readiness."
    )
    content = genai_types.Content(role="user", parts=[genai_types.Part(text=user_text)])
    adk_events: list[dict] = []
    tools_invoked: list[str] = []
    final_response = ""
    credentials_error: str | None = None
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        calls = []
        responses = []
        try:
            calls = event.get_function_calls() or []
        except Exception:
            calls = []
        try:
            responses = event.get_function_responses() or []
        except Exception:
            responses = []
        for call in calls:
            name = getattr(call, "name", "") or ""
            if name and name not in tools_invoked:
                tools_invoked.append(name)
        for resp in responses:
            name = getattr(resp, "name", "") or ""
            resp_dict = {}
            try:
                resp_dict = resp.response if isinstance(resp.response, dict) else {"response": str(resp.response)}
            except Exception:
                resp_dict = {}
            if isinstance(resp_dict, dict) and "error" in resp_dict and "CloudNotConfigured" in str(resp_dict.get("error", "")):
                credentials_error = str(resp_dict["error"])
            # Also check the bound tool trace for a credentials error, in
            # case ADK surfaces it differently across versions.
        text_parts = []
        try:
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if getattr(part, "text", None):
                        text_parts.append(part.text)
        except Exception:
            pass
        if text_parts:
            final_response = " ".join(text_parts)
        adk_events.append({
            "author": getattr(event, "author", ""),
            "is_final_response": bool(event.is_final_response()) if hasattr(event, "is_final_response") else False,
            "function_calls": [{"name": getattr(c, "name", ""), "args": _truncate(str(getattr(c, "args", "")))} for c in calls],
            "function_responses": [{"name": getattr(r, "name", ""), "keys": list(resp_dict.keys()) if isinstance(resp_dict, dict) else []} for r in responses],
            "text": _truncate(" ".join(text_parts), 500),
        })
    if credentials_error:
        raise CloudNotConfigured(credentials_error)

    extra_findings: list[str] = []
    if "search_policy_chunks" not in tools_invoked:
        extra_findings.append("ADK did not invoke search_policy_chunks; retrieval is treated as missing, not fabricated.")
    if "validate_case_codes" not in tools_invoked:
        extra_findings.append("ADK did not invoke validate_case_codes; codes are re-validated deterministically below, and the missing tool call is recorded.")
    if "extract_evidence" not in tools_invoked:
        extra_findings.append("ADK did not invoke extract_evidence; all criteria are treated as missing, not met. This is a system failure, counted as wrong in eval, not repaired by a separate pipeline.")

    # Deterministic inputs to finalize_review come from ADK tool outputs
    # when present, and from deterministic recomputation only where a
    # tool output is missing or mismatched. Never from model free text.
    retrieved = ctx.retrieved
    retrieval_method = ctx.retrieval_method
    if retrieved is None:
        # No ADK retrieval happened. Do not invent chunks, and do not
        # silently run a separate retrieval pipeline as if ADK did it.
        # Finalize with empty retrieval; evidence will be missing and
        # the scorer cannot produce READY. The finding above records why.
        retrieved = []
        retrieval_method = "adk_tool_not_invoked"
    if ctx.code_validation is None:
        # Code validation is deterministic, so recomputing it here is
        # not a model decision. Record that the ADK tool did not supply it.
        ctx.code_validation = code_validator(case, policy)
    if ctx.evidence_results is None:
        from priorauth.models import CriterionResult

        evidence_results = [
            CriterionResult(criterion_id=c.criterion_id, status="missing",
                            notes="ADK extract_evidence was not invoked or returned no outcomes; treated as missing, not met.")
            for c in policy.criteria
        ]
        evidence_usage = {"prompt_token_count": 0, "candidates_token_count": 0, "total_token_count": 0}
    else:
        evidence_results = ctx.evidence_results
        evidence_usage = ctx.evidence_usage or {"prompt_token_count": 0, "candidates_token_count": 0, "total_token_count": 0}

    tool_calls = [f"adk:{name}" for name in tools_invoked]
    tool_calls.append("citation_verifier:deterministic_quote_check" if verify_citations else "citation_verifier:disabled_for_ablation")
    tool_calls.append("checklist_scorer:deterministic_pathway_guardrail")
    # finalize_review appends its own citation/scorer/draft entries;
    # to avoid double-counting those names, pass only ADK tool calls
    # and let finalize append the deterministic steps once. Remove
    # the two names just added, finalize will add them.
    tool_calls = [f"adk:{name}" for name in tools_invoked]

    result = finalize_review(
        case, policy, evidence_results, evidence_usage, ctx.code_validation,
        retrieved, retrieval_method, config, budget, audit_path,
        verify_citations=verify_citations,
        tool_calls=tool_calls, started=started,
        adk_session_id=session_id, adk_tool_events=adk_events,
        adk_tools_invoked=tools_invoked, adk_final_response=_truncate(final_response, 1000),
        extra_critic_findings=extra_findings,
    )
    return result


def run_via_adk(case: ClinicalCase, policy: Policy, chunks=None, config: CloudConfig | None = None, **kwargs) -> ReviewResult:
    """Sync wrapper for FastAPI and eval scripts. Runs Runner in a new loop.

    If called from code that already has a running event loop, use
    run_via_adk_async instead; asyncio.run cannot be nested.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(run_via_adk_async(case, policy, chunks, config=config, **kwargs))
    raise RuntimeError("run_via_adk cannot be called from async code; use run_via_adk_async instead.")
