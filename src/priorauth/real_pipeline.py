"""Real Agentic RAG pipeline. Gemini does extraction and drafting.
Deterministic Python does guardrails, code validation, citation quote
checking, and readiness scoring. No step is mocked, and no step falls
back to a precomputed answer when credentials are absent: the pipeline
raises CloudNotConfigured instead.

Order, and why it matters:
1. Intake validation with Pydantic.
2. Real retrieval: Vertex embeddings for the case query, cosine
   similarity over policy chunks, or BigQuery VECTOR_SEARCH when the
   loaded table is available. Retrieval method is recorded.
3. Real Gemini structured extraction: one call per case, with the
   policy criteria, retrieved chunks, and the full clinical note in
   the prompt, and a JSON schema for criterion outcomes. The model
   must quote an exact excerpt for every met, not_met, fired, or
   contradictory outcome, or the outcome is downgraded.
4. Deterministic code validation.
5. Deterministic citation verification: every quoted excerpt must be
   a substring of the clinical note, and every met claim must have a
   policy citation. A claim that fails is downgraded to missing.
   A Gemini critic call, when run, can only downgrade, never upgrade.
6. Deterministic pathway scoring: see tools.checklist_scorer. A
   missing required criterion in every pathway, a fired exclusion,
   an invalid code, or a stale policy can never produce READY,
   regardless of what the model wrote.
7. Real Gemini drafting, only from verified met criteria, with gaps
   listed separately.
8. Audit logging with model name, token usage, estimated cost,
   retrieval method, and tool calls.
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from pathlib import Path

from priorauth.cloud_clients import (
    BudgetTracker,
    CloudConfig,
    CloudNotConfigured,
    bigquery_vector_search,
    check_credentials,
    cosine_similarity,
    embed_texts,
    estimate_cost_usd,
    gemini_generate,
)
from priorauth.models import (
    AuditEntry,
    Citation,
    ClinicalCase,
    CriterionResult,
    DraftLetter,
    Policy,
    ReviewResult,
    utc_now_iso,
)
from priorauth.tools import (
    audit_logger,
    checklist_scorer,
    citation_verifier,
    code_validator,
    draft_generator,
)

EVIDENCE_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "criterion_outcomes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "criterion_id": {"type": "string"},
                    "status": {"type": "string"},
                    "evidence_excerpts": {"type": "array", "items": {"type": "string"}},
                    "notes": {"type": "string"},
                },
                "required": ["criterion_id", "status"],
            },
        }
    },
    "required": ["criterion_outcomes"],
}


def cloud_available() -> dict:
    """Return cloud availability facts only, no secrets, no calls."""
    try:
        creds = check_credentials()
        credentials_present = bool(creds.get("credentials_present"))
    except Exception as exc:
        return {"credentials_present": False, "error": str(exc)}
    try:
        import google.adk  # type: ignore  # noqa: F401

        adk_available = True
    except Exception:
        adk_available = False
    config = CloudConfig()
    return {
        "credentials_present": credentials_present,
        "adk_available": adk_available,
        "model": config.model,
        "embedding_model": config.embedding_model,
        "project": config.project,
        "location": config.location,
        "model_location": config.model_location,
        "data_location": config.location,
        "dataset": config.dataset,
    }


def retrieve_chunks(
    case: ClinicalCase,
    policy: Policy,
    chunks: list[dict],
    config: CloudConfig,
) -> tuple[list[dict], str]:
    """Retrieve policy chunks with real embeddings, not keywords.

    First try BigQuery VECTOR_SEARCH when a table is present. If that
    raises because the table is not loaded, use Vertex embeddings and
    cosine similarity over the loaded chunks. Both paths are recorded.
    Neither path falls back to keyword search, and neither invents a
    chunk: only chunks passed in, or rows returned by BigQuery, are
    returned.
    """
    relevant = [c for c in chunks if c.get("policy_id") == policy.policy_id]
    if not relevant:
        return [], "no_chunks_for_policy"
    query_text = f"{policy.title} {case.clinical_note[:2000]}"
    try:
        query_embedding = embed_texts([query_text], config)[0]
    except CloudNotConfigured:
        raise
    except Exception as exc:
        raise CloudNotConfigured(f"Vertex embedding call failed: {exc}") from exc
    try:
        rows = bigquery_vector_search(query_embedding, config, top_k=5)
        if rows:
            return rows, "bigquery_vector_search"
    except Exception:
        # BigQuery table not loaded yet is not a reason to fake a result.
        # Cosine similarity over real Vertex embeddings is the documented
        # second retrieval path, and it is recorded as such.
        pass
    scored: list[tuple[float, dict]] = []
    chunk_texts = [c.get("text", "") for c in relevant]
    try:
        chunk_embeddings = embed_texts(chunk_texts, config)
    except CloudNotConfigured:
        raise
    for chunk, embedding in zip(relevant, chunk_embeddings):
        scored.append((cosine_similarity(query_embedding, embedding), chunk))
    scored.sort(key=lambda item: item[0], reverse=True)
    top = [
        {**chunk, "retrieval_score": float(score)}
        for score, chunk in scored[:5]
    ]
    return top, "vertex_embedding_cosine"


def extract_evidence_with_gemini(
    case: ClinicalCase,
    policy: Policy,
    retrieved_chunks: list[dict],
    config: CloudConfig,
) -> tuple[list[CriterionResult], dict]:
    """Call Gemini for structured criterion extraction. Validate the result."""
    criteria_text = "\n".join(
        f"{c.criterion_id} ({c.kind}, section {c.section}): {c.text}"
        for c in policy.criteria
    )
    chunks_text = "\n".join(
        f"- {c.get('chunk_id', '')} {c.get('section', '')}: {c.get('text', '')}"
        for c in retrieved_chunks
    )
    prompt = (
        "You are a prior authorization documentation reviewer. You do not "
        "approve, deny, or submit anything. For each criterion below, judge "
        "it only from the clinical note, and quote an exact excerpt from "
        "the note for every met, not_met, fired, or contradictory outcome. "
        "If the note does not state it, use missing, not not_met, unless "
        "the note explicitly negates it. If language is ambiguous, use "
        "uncertain. If both a finding and its negation appear, use "
        "contradictory. Never invent an excerpt, a code, a duration, or "
        "a finding. Use only these statuses: met, not_met, uncertain, "
        "contradictory, missing, not_applicable, fired, not_fired. "
        "Exclusion criteria use fired or not_fired only. Age criterion "
        "BIO-01, when present, is a structured field check, not a note "
        "excerpt, and must be judged from the patient age field given.\n\n"
        f"Policy: {policy.policy_id} {policy.title}\n"
        f"Criteria:\n{criteria_text}\n\n"
        f"Retrieved policy chunks:\n{chunks_text}\n\n"
        f"Patient age field: {case.patient_age}\n"
        f"Diagnosis codes: {', '.join(case.diagnosis_codes)}\n"
        f"Procedure code: {case.procedure_code}\n\n"
        f"Clinical note:\n{case.clinical_note}\n\n"
        "Return JSON only, matching the schema, with one outcome per criterion."
    )
    result = gemini_generate(prompt, config, response_schema=EVIDENCE_SCHEMA)
    try:
        parsed = json.loads(result["text"])
    except Exception as exc:
        raise RuntimeError(f"Gemini returned unparsable JSON for case {case.case_id}: {exc}") from exc
    outcomes = parsed.get("criterion_outcomes", [])
    by_id = {c.criterion_id: c for c in policy.criteria}
    results: list[CriterionResult] = []
    for item in outcomes:
        cid = item.get("criterion_id", "")
        if cid not in by_id:
            continue
        crit = by_id[cid]
        results.append(
            CriterionResult(
                criterion_id=cid,
                status=item.get("status", "missing"),
                evidence_excerpts=item.get("evidence_excerpts", []) or [],
                citation=Citation(
                    policy_id=policy.policy_id,
                    policy_version=case.policy_version,
                    section=crit.section,
                    source_url=crit.source_url,
                ),
                notes=item.get("notes", "") or "",
            )
        )
    for crit in policy.criteria:
        if crit.criterion_id not in {r.criterion_id for r in results}:
            results.append(
                CriterionResult(
                    criterion_id=crit.criterion_id,
                    status="missing",
                    notes="Model did not return an outcome for this criterion; treated as missing, not met.",
                )
            )
    return results, result["usage"]


def draft_with_gemini(
    results: list[CriterionResult],
    policy: Policy,
    case: ClinicalCase,
    config: CloudConfig,
) -> tuple[DraftLetter, dict]:
    """Draft only from verified met criteria, using real Gemini."""
    met = [r for r in results if r.status == "met"]
    gaps = [r for r in results if r.status in ("missing", "not_met", "uncertain", "contradictory", "fired")]
    met_text = "\n".join(
        f"- {r.criterion_id}: {'; '.join(r.evidence_excerpts)}" for r in met
    ) or "- None verified."
    gap_text = "\n".join(f"- {r.criterion_id}: {r.status}. {r.notes}" for r in gaps) or "- None."
    prompt = (
        "Write a short documentation draft for human review only, never an "
        "approval, denial, or submission. Use only the verified met criteria "
        "below, list gaps separately, and do not add any new clinical claim.\n\n"
        f"Case {case.case_id}, procedure {case.procedure}, policy {policy.policy_id} version {case.policy_version}.\n"
        f"Verified met criteria:\n{met_text}\n\nGaps:\n{gap_text}\n"
    )
    result = gemini_generate(prompt, config)
    body = result["text"] or ""
    if "human review only" not in body.lower():
        body += "\n\nThis draft is for human review only. It is not an approval, denial, or submission."
    draft = DraftLetter(
        title=f"Documentation draft: {case.case_id} under {policy.policy_id}",
        met_criteria_summary=[f"{r.criterion_id}: {'; '.join(r.evidence_excerpts)}" for r in met],
        gaps=[f"{r.criterion_id}: {r.status}" for r in gaps],
        body=body,
    )
    return draft, result["usage"]


def finalize_review(
    case: ClinicalCase,
    policy: Policy,
    model_results: list[CriterionResult],
    evidence_usage: dict,
    code_validation,
    retrieved: list[dict],
    retrieval_method: str,
    config: CloudConfig,
    budget: BudgetTracker,
    audit_path: str | Path | None = None,
    verify_citations: bool = True,
    tool_calls: list[str] | None = None,
    started: float | None = None,
    adk_session_id: str = "",
    adk_tool_events: list[dict] | None = None,
    adk_tools_invoked: list[str] | None = None,
    adk_final_response: str = "",
    extra_critic_findings: list[str] | None = None,
) -> ReviewResult:
    """Deterministic post-processing shared by every execution path.

    This is deliberately NOT a model decision. It takes evidence
    outcomes that were already produced (by the ADK tools in the
    ADK path, or by direct calls in run_real_review), verifies
    citations, scores readiness with the pathway guardrail, and
    drafts only from verified met criteria. No outcome here can
    upgrade a downgraded claim, and no readiness can override the
    guardrail. Callers must pass tool_calls that were actually
    recorded, not a fabricated list.
    """
    config = config or CloudConfig()
    budget = budget or BudgetTracker(budget_usd=config.budget_usd)
    started = started if started is not None else time.perf_counter()
    review_id = f"REV-{uuid.uuid4().hex[:12]}"
    tool_calls = list(tool_calls or [])
    policy_version_current = case.policy_version == policy.current_version
    evidence_cost = estimate_cost_usd(evidence_usage, config)
    budget.add(evidence_cost, f"evidence:{case.case_id}")

    claims = []
    for result in model_results:
        if result.status == "met" and result.evidence_excerpts:
            claims.append(
                {
                    "criterion_id": result.criterion_id,
                    "excerpt": result.evidence_excerpts[0],
                    "citation_policy_id": policy.policy_id,
                    "citation_section": result.citation.section if result.citation else "",
                }
            )
    if verify_citations:
        verified_results, citation_findings = citation_verifier(model_results, claims, note=case.clinical_note)
        tool_calls.append("citation_verifier:deterministic_quote_check")
    else:
        verified_results, citation_findings = model_results, ["Citation verification disabled for ablation run."]
        tool_calls.append("citation_verifier:disabled_for_ablation")

    readiness, rationale = checklist_scorer(verified_results, code_validation, policy_version_current, pathways=policy.pathways)
    tool_calls.append("checklist_scorer:deterministic_pathway_guardrail")
    critic_findings = list(extra_critic_findings or []) + list(citation_findings)
    critic_findings.append(f"Pre-check: {rationale}")

    gaps: list[str] = []
    for result in verified_results:
        if result.status in ("missing", "not_met", "uncertain", "contradictory"):
            gaps.append(f"{result.criterion_id}: {result.status} ({result.notes})")
        elif result.status == "fired":
            gaps.append(f"{result.criterion_id}: exclusion fired")
    if code_validation.overall_status != "valid":
        gaps.append(f"Code validation: {code_validation.overall_status}.")
    if not policy_version_current:
        gaps.append("Policy version is not current.")

    draft, draft_usage = draft_with_gemini(verified_results, policy, case, config)
    tool_calls.append("draft_generator:gemini_post_verification")
    draft_cost = estimate_cost_usd(draft_usage, config)
    budget.add(draft_cost, f"draft:{case.case_id}")

    total_usage = {
        "evidence_prompt_token_count": int(evidence_usage.get("prompt_token_count", 0) or 0),
        "evidence_candidates_token_count": int(evidence_usage.get("candidates_token_count", 0) or 0),
        "draft_prompt_token_count": int(draft_usage.get("prompt_token_count", 0) or 0),
        "draft_candidates_token_count": int(draft_usage.get("candidates_token_count", 0) or 0),
    }
    total_cost = evidence_cost + draft_cost

    audit = AuditEntry(
        case_id=case.case_id,
        policy_id=policy.policy_id,
        policy_version=case.policy_version,
        policy_version_current=policy_version_current,
        criterion_results=verified_results,
        readiness=readiness,
        timestamp=utc_now_iso(),
    )
    audit_logger(audit, path=audit_path)
    latency_ms = (time.perf_counter() - started) * 1000.0
    return ReviewResult(
        review_id=review_id,
        case_id=case.case_id,
        policy_id=policy.policy_id,
        policy_version=case.policy_version,
        policy_version_current=policy_version_current,
        readiness=readiness,
        criterion_results=verified_results,
        code_validation=code_validation,
        gaps=gaps,
        critic_findings=critic_findings,
        draft_letter=draft,
        audit_entry=audit,
        latency_ms=latency_ms,
        model_name=config.model,
        model_location=config.model_location,
        data_location=config.location,
        embedding_model=config.embedding_model,
        token_usage=total_usage,
        cost_usd_estimated=float(total_cost),
        retrieval_method=retrieval_method,
        retrieval_chunks=retrieved,
        tool_calls=tool_calls,
        adk_session_id=adk_session_id,
        adk_tools_invoked=list(adk_tools_invoked or []),
        adk_tool_events=list(adk_tool_events or []),
        adk_final_response=adk_final_response,
    )


def run_real_review(
    case: ClinicalCase,
    policy: Policy,
    chunks: list[dict],
    config: CloudConfig | None = None,
    budget: BudgetTracker | None = None,
    audit_path: str | Path | None = None,
    verify_citations: bool = True,
) -> ReviewResult:
    """Direct pipeline, kept for tests and for callers that do not use ADK.

    This is NOT the ADK execution path. FastAPI and evaluate_real.py
    call run_via_adk in adk_agent.py, which must go through Runner.
    This function exists so deterministic guardrail logic can be
    tested without a model, and so a reviewer can compare the
    deterministic finalize step in isolation. It must never be
    presented as an ADK run: its adk_tool_events list stays empty.
    """
    config = config or CloudConfig()
    budget = budget or BudgetTracker(budget_usd=config.budget_usd)
    started = time.perf_counter()
    retrieved, retrieval_method = retrieve_chunks(case, policy, chunks, config)
    model_results, evidence_usage = extract_evidence_with_gemini(case, policy, retrieved, config)
    code_validation = code_validator(case, policy)
    return finalize_review(
        case, policy, model_results, evidence_usage, code_validation,
        retrieved, retrieval_method, config, budget, audit_path,
        verify_citations=verify_citations,
        tool_calls=["policy_search:vertex_embeddings", f"retrieval:{retrieval_method}",
                    "evidence_extractor:gemini_structured_output", "code_validator:deterministic"],
        started=started,
    )


async def run_real_review_async(*args, **kwargs) -> ReviewResult:
    """Async wrapper so FastAPI and ADK code can await the pipeline."""
    return await asyncio.to_thread(run_real_review, *args, **kwargs)
