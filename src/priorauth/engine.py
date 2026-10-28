"""Review engine: intake, retrieval, extraction, scoring, verification,
pre-check, draft, and audit, in that order.

The engine is local and deterministic. It never calls a model, never
approves, denies, or submits a prior authorization, and never invents
evidence. Cloud adapters are optional and are not used here.
"""

from __future__ import annotations

import time
import uuid
from pathlib import Path

from priorauth.models import (
    AuditEntry,
    Citation,
    ClinicalCase,
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
    evidence_extractor,
)


def run_review(
    case: ClinicalCase,
    policy: Policy,
    policy_version_current: bool = True,
    audit_path: str | Path | None = None,
) -> ReviewResult:
    """Run the full review workflow and return a ReviewResult."""
    started = time.perf_counter()
    review_id = f"REV-{uuid.uuid4().hex[:12]}"

    # Step 1: intake validation. A case with no note or no codes is
    # still reviewed, but the gaps are recorded, not hidden.
    critic_findings: list[str] = []
    if not case.clinical_note.strip():
        critic_findings.append("Clinical note is empty; all required criteria will be missing.")
    if not case.diagnosis_codes:
        critic_findings.append("No diagnosis codes were supplied.")

    # Step 2: policy retrieval is represented by the policy object the
    # caller loaded from data/policies.json. Version currency is an
    # explicit input so a stale version can never be silently treated
    # as current.
    if case.policy_version != policy.current_version:
        policy_version_current = False

    # Step 3: criteria extraction is the policy criteria themselves,
    # already validated by Pydantic on load.
    criteria = policy.criteria

    # Step 4: evidence matching.
    results = evidence_extractor(case, criteria)

    # Attach citations to met and fired results.
    for result in results:
        crit = next((c for c in criteria if c.criterion_id == result.criterion_id), None)
        if crit is not None:
            result.citation = Citation(
                policy_id=policy.policy_id,
                policy_version=case.policy_version,
                section=crit.section,
                source_url=crit.source_url,
            )

    # Step 5: code validation, then deterministic scoring.
    code_validation = code_validator(case, policy)

    # Step 6: citation verification. Claims are built only from the
    # extractor's own excerpts, so a fake claim with no excerpt cannot
    # pass: see tests/test_adversarial.py for the direct test.
    claims = []
    for result in results:
        if result.status == "met" and result.evidence_excerpts:
            claims.append(
                {
                    "criterion_id": result.criterion_id,
                    "excerpt": result.evidence_excerpts[0],
                    "citation_policy_id": policy.policy_id,
                    "citation_section": result.citation.section if result.citation else "",
                }
            )
    results, citation_findings = citation_verifier(results, claims, note=case.clinical_note)
    critic_findings.extend(citation_findings)

    # Step 7: final pre-check with the deterministic scorer. This
    # overrides any heuristic: there is no heuristic score in this
    # engine, so the scorer output is the readiness output.
    readiness, rationale = checklist_scorer(results, code_validation, policy_version_current, pathways=policy.pathways)
    critic_findings.append(f"Pre-check: {rationale}")

    gaps: list[str] = []
    for result in results:
        if result.status in ("missing", "not_met", "uncertain", "contradictory"):
            gaps.append(f"{result.criterion_id}: {result.status} ({result.notes})")
        elif result.status == "fired":
            gaps.append(f"{result.criterion_id}: exclusion fired")
    if code_validation.overall_status != "valid":
        gaps.append(f"Code validation: {code_validation.overall_status}.")
    if not policy_version_current:
        gaps.append("Policy version is not current.")

    # Step 8: draft generation, only from verified met criteria.
    draft = draft_generator(results, criteria, policy, case)

    # Step 9: audit logging.
    audit = AuditEntry(
        case_id=case.case_id,
        policy_id=policy.policy_id,
        policy_version=case.policy_version,
        policy_version_current=policy_version_current,
        criterion_results=results,
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
        criterion_results=results,
        code_validation=code_validation,
        gaps=gaps,
        critic_findings=critic_findings,
        draft_letter=draft,
        audit_entry=audit,
        latency_ms=latency_ms,
    )
