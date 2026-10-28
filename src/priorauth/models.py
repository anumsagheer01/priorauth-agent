"""Pydantic v2 schemas for PriorAuth Agent.

Readiness states describe documentation readiness only, not insurance
decisions. The system never approves, denies, or submits a prior
authorization. A human must review every draft and every case.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

Readiness = Literal["READY_FOR_HUMAN_REVIEW", "NOT_READY", "NEEDS_MANUAL_REVIEW"]
CriterionKind = Literal["required", "conditional", "exclusion"]
CriterionStatus = Literal[
    "met",
    "not_met",
    "uncertain",
    "contradictory",
    "missing",
    "not_applicable",
    "fired",
    "not_fired",
]
CodeStatus = Literal["valid", "unsupported", "invalid"]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class PolicyVersion(BaseModel):
    version: str
    effective_date: str = ""
    status: Literal["current", "superseded"] = "current"
    notes: str = ""


class Criterion(BaseModel):
    criterion_id: str
    text: str
    section: str
    source_policy_id: str
    source_url: str
    kind: CriterionKind
    evidence_keywords: list[str] = Field(default_factory=list)
    positive_patterns: list[str] = Field(default_factory=list)
    negation_patterns: list[str] = Field(default_factory=list)
    ambiguous_patterns: list[str] = Field(default_factory=list)
    field_check: str = ""


class Pathway(BaseModel):
    """One medical necessity pathway.

    A case is medically necessary for documentation readiness only if
    every criterion in at least one pathway is met, no exclusion fires,
    codes are valid, and the policy version is current. This corrects
    the old model, which wrongly required every required criterion in
    a policy at once, even when the real policy says any listed
    criterion or pathway can suffice. Pathways are a simplified faithful
    subset, not the full policy, and a human must check the full policy.
    """

    pathway_id: str
    name: str
    required_criterion_ids: list[str] = Field(default_factory=list)
    description: str = ""


class Policy(BaseModel):
    policy_id: str
    title: str
    payer: str
    payer_type: str = "commercial"
    procedure: str
    source_url: str
    retrieval_date: str = "2026-10-27"
    current_version: str
    versions: list[PolicyVersion] = Field(default_factory=list)
    supported_diagnosis_codes: list[str] = Field(default_factory=list)
    procedure_codes: list[str] = Field(default_factory=list)
    criteria: list[Criterion] = Field(default_factory=list)
    pathways: list[Pathway] = Field(default_factory=list)
    subset_note: str = ""


class ClinicalCase(BaseModel):
    case_id: str
    procedure: str
    policy_id: str
    policy_version: str
    diagnosis_codes: list[str] = Field(default_factory=list)
    procedure_code: str = ""
    patient_age: int | None = None
    clinical_note: str
    gold_readiness: Readiness | None = None
    gold_criterion_outcomes: dict[str, CriterionStatus] = Field(default_factory=dict)
    categories: list[str] = Field(default_factory=list)
    source_type: str = "published"
    source_id: str = ""
    source_url: str = ""
    source_license: str = ""
    annotation_rationale: str = ""
    is_synthetic: bool = False


class Citation(BaseModel):
    policy_id: str
    policy_version: str
    section: str
    source_url: str


class CriterionResult(BaseModel):
    criterion_id: str
    status: CriterionStatus
    evidence_excerpts: list[str] = Field(default_factory=list)
    citation: Citation | None = None
    notes: str = ""


class CodeCheck(BaseModel):
    code: str
    code_type: Literal["diagnosis", "procedure"]
    status: CodeStatus
    reason: str


class CodeValidation(BaseModel):
    diagnosis_checks: list[CodeCheck] = Field(default_factory=list)
    procedure_check: CodeCheck | None = None
    overall_status: CodeStatus = "valid"


class DraftLetter(BaseModel):
    title: str
    met_criteria_summary: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    body: str
    disclaimer: str = (
        "This draft is for human review only. It is not an approval, "
        "denial, or submission of a prior authorization. A human reviewer "
        "must verify every statement against the full policy and the "
        "complete clinical record before any action is taken."
    )


class AuditEntry(BaseModel):
    case_id: str
    policy_id: str
    policy_version: str
    policy_version_current: bool
    criterion_results: list[CriterionResult] = Field(default_factory=list)
    readiness: Readiness
    engine_version: str = "2.0.0-real"
    timestamp: str = Field(default_factory=utc_now_iso)


class ReviewResult(BaseModel):
    review_id: str
    case_id: str
    policy_id: str
    policy_version: str
    policy_version_current: bool
    readiness: Readiness
    criterion_results: list[CriterionResult] = Field(default_factory=list)
    code_validation: CodeValidation | None = None
    gaps: list[str] = Field(default_factory=list)
    critic_findings: list[str] = Field(default_factory=list)
    draft_letter: DraftLetter | None = None
    audit_entry: AuditEntry | None = None
    engine_version: str = "2.0.0-real"
    latency_ms: float = 0.0
    model_name: str = ""
    # Run record: model endpoint and data location are different
    # fields on purpose. model_location is where Gemini was called
    # (approved test endpoint "global" for gemini-3.5-flash, until
    # Cloud Shell verifies it); data_location is where BigQuery
    # and embeddings live (us-central1). Never collapse them into
    # one location field, or a us-central1 404 will be misread
    # as a model problem for every endpoint.
    model_location: str = ""
    data_location: str = ""
    embedding_model: str = ""
    token_usage: dict = Field(default_factory=dict)
    cost_usd_estimated: float = 0.0
    retrieval_method: str = ""
    retrieval_chunks: list[dict] = Field(default_factory=list)
    tool_calls: list[str] = Field(default_factory=list)
    # ADK execution trace. tool_calls above is kept for backward
    # compatibility with eval scripts, but adk_tool_events is the
    # authoritative record: every entry is an event actually yielded
    # by Runner.run_async, with function calls and responses as
    # returned by ADK. An empty list means the Runner did not run,
    # and must never be backfilled with a fabricated trace.
    adk_session_id: str = ""
    adk_tools_invoked: list[str] = Field(default_factory=list)
    adk_tool_events: list[dict] = Field(default_factory=list)
    adk_final_response: str = ""
