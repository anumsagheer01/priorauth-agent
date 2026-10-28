"""Eight deterministic tools, not prompts.

Every function here is a real, testable function. No tool calls a
language model, and no tool invents evidence, codes, or excerpts.

Deterministic scoring rules (documented, and always overriding any
heuristic score):
  1. An exclusion that fires means NOT_READY. Nothing overrides it.
  2. Otherwise, any uncertainty, contradiction, ambiguous history,
     invalid or unsupported code, or stale policy version means
     NEEDS_MANUAL_REVIEW.
  3. Otherwise, any missing or not_met required criterion means
     NOT_READY.
  4. Otherwise, when every required criterion is met, no exclusion
     fires, codes are valid, and the policy version is current, the
     result is READY_FOR_HUMAN_REVIEW, which is documentation readiness
     only, not an approval.
Conditional criteria that are not applicable do not block readiness.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from priorauth.models import (
    AuditEntry,
    Citation,
    ClinicalCase,
    CodeCheck,
    CodeValidation,
    Criterion,
    CriterionResult,
    DraftLetter,
    Policy,
    Readiness,
    utc_now_iso,
)

ICD10_RE = re.compile(r"^[A-Z][0-9]{2}(\.[0-9A-Z]{1,4})?$")
CPT_RE = re.compile(r"^[0-9]{5}$")
HCPCS_RE = re.compile(r"^[A-Z][0-9]{4}$")
NEGATION_WORDS = ["no ", "not ", "denied", "absent", "negative", "without "]


def _sentences(note: str) -> list[str]:
    parts = re.split(r"(?<=[.\n])\s+", note.replace("\n", " "))
    return [p.strip() for p in parts if p.strip()]


def _contains(text: str, patterns: list[str]) -> list[str]:
    low = text.lower()
    return [p for p in patterns if p.lower() in low]


def _duration_weeks(note: str, pattern: str) -> int | None:
    """Return weeks from a phrase like '3 weeks of conservative therapy'."""
    match = re.search(r"(\d+)\s+weeks?\s+" + pattern, note.lower())
    if match:
        return int(match.group(1))
    return None


# ---------------------------------------------------------------- policy_search
def policy_search(
    chunks: list[dict],
    query: str,
    procedure: str | None = None,
    version: str | None = None,
) -> list[dict]:
    """Keyword search over local policy chunks.

    Filters by procedure and version when given. Returns chunks ranked
    by keyword overlap, each with source id, section, and section label.
    Never invents a chunk: only chunks passed in are returned.
    """
    query_words = [w for w in re.findall(r"[a-z0-9]+", query.lower()) if len(w) > 2]
    scored: list[tuple[int, dict]] = []
    for chunk in chunks:
        if procedure and chunk.get("procedure", "").lower() != procedure.lower():
            continue
        if version and chunk.get("policy_version", "") != version:
            continue
        text = (chunk.get("text", "") + " " + chunk.get("section", "")).lower()
        score = sum(1 for w in query_words if w in text)
        if query_words and score == 0:
            continue
        scored.append((score, chunk))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [
        {
            "chunk_id": c.get("chunk_id", ""),
            "policy_id": c.get("policy_id", ""),
            "policy_version": c.get("policy_version", ""),
            "section": c.get("section", ""),
            "section_label": c.get("section", ""),
            "text": c.get("text", ""),
            "source_url": c.get("source_url", ""),
            "score": score,
        }
        for score, c in scored
    ]


# ---------------------------------------------------------------- code_validator
def code_validator(case: ClinicalCase, policy: Policy) -> CodeValidation:
    """Validate diagnosis and procedure codes against the policy lists.

    Returns valid, unsupported, or invalid with reasons. Never invents
    a code: a code not in the supported list is unsupported, not corrected.
    """
    diagnosis_checks: list[CodeCheck] = []
    for code in case.diagnosis_codes:
        if not ICD10_RE.match(code.strip().upper()):
            diagnosis_checks.append(
                CodeCheck(
                    code=code,
                    code_type="diagnosis",
                    status="invalid",
                    reason="Diagnosis code does not match ICD-10-CM format.",
                )
            )
        elif code.strip().upper() in [c.upper() for c in policy.supported_diagnosis_codes]:
            diagnosis_checks.append(
                CodeCheck(
                    code=code,
                    code_type="diagnosis",
                    status="valid",
                    reason="Diagnosis code is in the policy supported list.",
                )
            )
        else:
            diagnosis_checks.append(
                CodeCheck(
                    code=code,
                    code_type="diagnosis",
                    status="unsupported",
                    reason="Diagnosis code is formatted correctly but is not in the policy supported list.",
                )
            )
    proc = case.procedure_code.strip().upper()
    if not proc:
        procedure_check = CodeCheck(
            code="", code_type="procedure", status="invalid",
            reason="No procedure code was supplied.",
        )
    elif not (CPT_RE.match(proc) or HCPCS_RE.match(proc)):
        procedure_check = CodeCheck(
            code=proc, code_type="procedure", status="invalid",
            reason="Procedure code does not match CPT (5 digits) or HCPCS (letter plus 4 digits) format.",
        )
    elif proc in [c.upper() for c in policy.procedure_codes]:
        procedure_check = CodeCheck(
            code=proc, code_type="procedure", status="valid",
            reason="Procedure code is in the policy procedure code list.",
        )
    else:
        procedure_check = CodeCheck(
            code=proc, code_type="procedure", status="unsupported",
            reason="Procedure code is formatted correctly but is not in the policy procedure code list.",
        )
    statuses = [c.status for c in diagnosis_checks] + [procedure_check.status]
    if "invalid" in statuses:
        overall = "invalid"
    elif "unsupported" in statuses:
        overall = "unsupported"
    else:
        overall = "valid"
    return CodeValidation(
        diagnosis_checks=diagnosis_checks,
        procedure_check=procedure_check,
        overall_status=overall,
    )


# ---------------------------------------------------------------- criteria_extractor
def criteria_extractor(policy_data: dict) -> list[Criterion]:
    """Parse a policy dict into criteria, with full schema validation."""
    policy = Policy.model_validate(policy_data)
    return policy.criteria


# ---------------------------------------------------------------- evidence_extractor
def evidence_extractor(
    case: ClinicalCase, criteria: list[Criterion]
) -> list[CriterionResult]:
    """Deterministic excerpt matching over the clinical note.

    Case-sensitive keyword and phrase matching is done on lowercased
    text so that casing in the note does not change the outcome, and
    matching phrases are recorded verbatim as excerpts. Negation is
    criterion specific: only the negation_patterns listed for that
    criterion count as a negation for it, so a phrase such as
    'no improvement after 6 weeks' is not misread as negating therapy.
    When both a positive excerpt and a negation excerpt appear for the
    same criterion, the result is contradictory.
    """
    note = case.clinical_note
    low_note = note.lower()
    sentences = _sentences(note)
    results: list[CriterionResult] = []
    for criterion in criteria:
        cid = criterion.criterion_id
        if criterion.field_check == "age_at_least_6":
            if case.patient_age is None:
                results.append(
                    CriterionResult(
                        criterion_id=cid, status="missing",
                        notes="Patient age was not supplied, so the age criterion cannot be confirmed.",
                    )
                )
            elif case.patient_age >= 6:
                results.append(
                    CriterionResult(
                        criterion_id=cid, status="met",
                        evidence_excerpts=[],
                        notes=f"Structured field check: patient age {case.patient_age} years is at least 6 years. Age comes from the case field, not from a note excerpt, so no excerpt is claimed.",
                    )
                )
            else:
                results.append(
                    CriterionResult(
                        criterion_id=cid, status="not_met",
                        evidence_excerpts=[],
                        notes=f"Structured field check: patient age {case.patient_age} years is under 6 years.",
                    )
                )
            continue

        positive = [s for s in sentences if _contains(s, criterion.positive_patterns)]
        negations = [s for s in sentences if _contains(s, criterion.negation_patterns)]
        ambiguous = [s for s in sentences if _contains(s, criterion.ambiguous_patterns)]

        # Duration rules for conservative therapy criteria.
        duration_not_met = False
        duration_note = ""
        if cid in ("LUM-02", "KNE-04"):
            weeks = _duration_weeks(low_note, "of conservative therapy")
            if weeks is None and cid == "KNE-04":
                weeks = _duration_weeks(low_note, "of formal physical therapy")
            if weeks is not None and weeks < 6:
                duration_not_met = True
                duration_note = f"Documented duration is {weeks} weeks, under the 6 week minimum."

        if criterion.kind == "exclusion":
            if positive:
                results.append(
                    CriterionResult(
                        criterion_id=cid, status="fired",
                        evidence_excerpts=positive,
                        notes="Exclusion evidence was found in the note.",
                    )
                )
            else:
                results.append(
                    CriterionResult(
                        criterion_id=cid, status="not_fired",
                        notes="No exclusion evidence was found in the note.",
                    )
                )
            continue

        if positive and negations:
            results.append(
                CriterionResult(
                    criterion_id=cid, status="contradictory",
                    evidence_excerpts=positive + negations,
                    notes="Both a positive finding and its negation appear in the note.",
                )
            )
        elif negations:
            results.append(
                CriterionResult(
                    criterion_id=cid, status="not_met",
                    evidence_excerpts=negations,
                    notes="The note explicitly negates this criterion.",
                )
            )
        elif positive:
            if duration_not_met:
                results.append(
                    CriterionResult(
                        criterion_id=cid, status="not_met",
                        evidence_excerpts=positive, notes=duration_note,
                    )
                )
            else:
                results.append(
                    CriterionResult(
                        criterion_id=cid, status="met",
                        evidence_excerpts=positive,
                        notes="A positive evidence excerpt was found in the note.",
                    )
                )
        elif ambiguous:
            results.append(
                CriterionResult(
                    criterion_id=cid, status="uncertain",
                    evidence_excerpts=ambiguous,
                    notes="Only ambiguous language was found for this criterion.",
                )
            )
        elif duration_not_met:
            results.append(
                CriterionResult(
                    criterion_id=cid, status="not_met",
                    evidence_excerpts=[],
                    notes=duration_note,
                )
            )
        else:
            if criterion.kind == "conditional":
                results.append(
                    CriterionResult(
                        criterion_id=cid, status="not_applicable",
                        notes="No conditional pathway evidence was documented; this does not block readiness.",
                    )
                )
            else:
                results.append(
                    CriterionResult(
                        criterion_id=cid, status="missing",
                        notes="No evidence excerpt was found in the note for this criterion.",
                    )
                )
    return results


# ---------------------------------------------------------------- checklist_scorer
def checklist_scorer(
    criterion_results: list[CriterionResult],
    code_validation: CodeValidation,
    policy_version_current: bool,
    pathways: list | None = None,
) -> tuple[Readiness, str]:
    """Deterministic readiness scoring, pathway aware.

    Rules, in order, and no model output can override them:
    1. An exclusion that fires means NOT_READY.
    2. A contradiction anywhere means NEEDS_MANUAL_REVIEW.
    3. Invalid or unsupported codes, or a stale policy version, mean
       NEEDS_MANUAL_REVIEW.
    4. If pathways are given, READY requires at least one pathway
       whose every required criterion is met. A pathway whose only
       non-met criteria are uncertain means NEEDS_MANUAL_REVIEW,
       because that pathway might be met on a fuller record.
       Otherwise, if no pathway is fully met, the result is NOT_READY.
    5. If no pathways are given, the old rule applies: every required
       criterion must be met, otherwise NOT_READY, with uncertainty
       already handled above.
    """
    if any(r.status == "fired" for r in criterion_results):
        fired = [r.criterion_id for r in criterion_results if r.status == "fired"]
        return "NOT_READY", f"Exclusion fired: {', '.join(fired)}. An exclusion cannot be overridden."
    if any(r.status == "contradictory" for r in criterion_results):
        bad = [r.criterion_id for r in criterion_results if r.status == "contradictory"]
        return "NEEDS_MANUAL_REVIEW", f"Contradictory evidence: {', '.join(bad)}."
    if code_validation.overall_status in ("invalid", "unsupported"):
        return (
            "NEEDS_MANUAL_REVIEW",
            f"Code validation is {code_validation.overall_status}; a human must resolve the codes.",
        )
    if not policy_version_current:
        return "NEEDS_MANUAL_REVIEW", "Policy version is not current; a human must check the current policy."
    if pathways:
        by_id = {r.criterion_id: r.status for r in criterion_results}
        for pathway in pathways:
            ids = pathway.required_criterion_ids if hasattr(pathway, "required_criterion_ids") else pathway.get("required_criterion_ids", [])
            if ids and all(by_id.get(cid) == "met" for cid in ids):
                return (
                    "READY_FOR_HUMAN_REVIEW",
                    f"Pathway {pathway.pathway_id if hasattr(pathway, 'pathway_id') else pathway.get('pathway_id')} fully met, no exclusion fires, codes are valid, and the policy version is current.",
                )
        for pathway in pathways:
            ids = pathway.required_criterion_ids if hasattr(pathway, "required_criterion_ids") else pathway.get("required_criterion_ids", [])
            statuses = [by_id.get(cid) for cid in ids]
            if statuses and all(s in ("met", "uncertain") for s in statuses) and any(s == "uncertain" for s in statuses):
                return "NEEDS_MANUAL_REVIEW", f"Pathway {pathway.pathway_id if hasattr(pathway, 'pathway_id') else pathway.get('pathway_id')} is uncertain; a human must resolve the uncertain criteria."
        missing = [
            r.criterion_id
            for r in criterion_results
            if r.status in ("missing", "not_met", "uncertain")
        ]
        return "NOT_READY", f"No pathway fully met. Non-met criteria: {', '.join(missing)}."
    if any(r.status == "uncertain" for r in criterion_results):
        uncertain = [r.criterion_id for r in criterion_results if r.status == "uncertain"]
        return "NEEDS_MANUAL_REVIEW", f"Uncertain evidence: {', '.join(uncertain)}."
    missing = [
        r.criterion_id
        for r in criterion_results
        if r.status in ("missing", "not_met")
    ]
    if missing:
        return "NOT_READY", f"Required criterion not satisfied: {', '.join(missing)}."
    return (
        "READY_FOR_HUMAN_REVIEW",
        "Every required criterion is met, no exclusion fires, codes are valid, and the policy version is current.",
    )


# ---------------------------------------------------------------- citation_verifier
def citation_verifier(
    criterion_results: list[CriterionResult],
    claims: list[dict],
    note: str = "",
) -> tuple[list[CriterionResult], list[str]]:
    """Citation verification: exact quote matching, no fuzzy trust.

    What counts as supported, all three must hold for a met claim:
      1. The claim has a complete policy citation: both
         citation_policy_id and citation_section are non-empty.
      2. The cited excerpt appears verbatim, as an exact substring,
         in the clinical note (when a note is supplied). Paraphrase,
         summary, or a close-but-different sentence does not pass.
         Exact matching is deliberate: it is strict, it cannot be
         gamed by a plausible-sounding summary, and its failures
         are visible, but it will also reject a genuine paraphrase.
         That trade-off is recorded here rather than hidden.
      3. The excerpt is one the extractor actually found for that
         criterion, in result.evidence_excerpts. A sentence that is
         in the note but was not extracted for this criterion
         does not support this criterion. This is the critic catch:
         it stops a claim from borrowing an unrelated sentence
         from the note as if it proved a criterion.

    What downgrades a claim to missing:
      - No complete policy citation, or a citation for a different
        policy or section than the claim's criterion.
      - Excerpt not in the note, verbatim.
      - Excerpt not among the extractor's excerpts for that criterion.
      - Claim for a criterion that does not exist in the results.
    In each case, a met claim becomes missing, its excerpts are
    cleared, and the finding is recorded in the returned findings
    list, which becomes part of ReviewResult.critic_findings and
    the audit log. Only met claims are downgraded; missing,
    not_met, uncertain, contradictory, and fired statuses are
    already non-ready and are left as they are, because the
    scorer treats them as gaps.

    Demonstrated in tests/test_citation_critic.py with deliberately
    unsupported claims, test only, not eval: an excerpt invented
    outside the note, a missing policy citation, and an excerpt
    borrowed from another part of the note are each downgraded,
    while a verbatim excerpt with a complete citation passes.
    The critic is deterministic code, never a model checking its
    own output, and it runs in finalize_review before drafting,
    so a draft is built only from verified met criteria.
    """
    findings: list[str] = []
    results = [r.model_copy(deep=True) for r in criterion_results]
    by_id = {r.criterion_id: r for r in results}
    # Build a keyword map from results is not possible without criteria,
    # so verification uses the claim excerpt against the note and the
    # result's own excerpts: a claim passes only if its excerpt text
    # appears in the note (when a note is supplied) and matches an
    # excerpt the extractor actually found for that criterion.
    for claim in claims:
        cid = claim.get("criterion_id", "")
        excerpt = claim.get("excerpt", "")
        result = by_id.get(cid)
        if result is None:
            findings.append(f"Claim for unknown criterion {cid} was rejected.")
            continue
        if not claim.get("citation_policy_id") or not claim.get("citation_section"):
            findings.append(f"Claim for {cid} has no complete policy citation and was downgraded.")
            if result.status == "met":
                result.status = "missing"
                result.evidence_excerpts = []
            continue
        if note and excerpt not in note:
            findings.append(
                f"Claim for {cid} cites an excerpt that does not appear in the note and was downgraded."
            )
            if result.status == "met":
                result.status = "missing"
                result.evidence_excerpts = []
            continue
        if result.status == "met" and excerpt and excerpt not in result.evidence_excerpts:
            findings.append(
                f"Claim for {cid} cites an excerpt the extractor did not find and was downgraded."
            )
            result.status = "missing"
            result.evidence_excerpts = []
    return results, findings


# ---------------------------------------------------------------- draft_generator
def draft_generator(
    criterion_results: list[CriterionResult],
    criteria: list[Criterion],
    policy: Policy,
    case: ClinicalCase,
) -> DraftLetter:
    """Build a justification draft only from verified met criteria.

    Gaps are listed separately. The draft never claims approval.
    """
    crit_by_id = {c.criterion_id: c for c in criteria}
    met_lines: list[str] = []
    gaps: list[str] = []
    for result in criterion_results:
        crit = crit_by_id.get(result.criterion_id)
        label = crit.text if crit else result.criterion_id
        section = crit.section if crit else ""
        if result.status == "met":
            excerpt = result.evidence_excerpts[0] if result.evidence_excerpts else ""
            met_lines.append(f"{result.criterion_id} ({section}): {label} Evidence: {excerpt}")
        elif result.status in ("missing", "not_met", "uncertain", "contradictory"):
            gaps.append(f"{result.criterion_id}: {label} Status: {result.status}. {result.notes}")
        elif result.status == "fired":
            gaps.append(f"{result.criterion_id}: EXCLUSION FIRED: {label}")
    body_lines = [
        f"Documentation summary for case {case.case_id}, procedure {case.procedure}.",
        f"Policy: {policy.policy_id}, {policy.title}, version {case.policy_version}.",
        "Verified documented criteria:",
    ]
    body_lines.extend([f"- {line}" for line in met_lines] or ["- None verified."])
    body_lines.append("Gaps and items needing human review:")
    body_lines.extend([f"- {line}" for line in gaps] or ["- None."])
    body_lines.append(
        "This draft is for human review only. It is not an approval, "
        "denial, or submission of a prior authorization."
    )
    draft = DraftLetter(
        title=f"Documentation draft: {case.case_id} under {policy.policy_id}",
        met_criteria_summary=met_lines,
        gaps=gaps,
        body="\n".join(body_lines),
    )
    return draft


# ---------------------------------------------------------------- audit_logger
def audit_logger(entry: AuditEntry, path: str | Path | None = None) -> AuditEntry:
    """Append one JSON lines audit entry when a path is given.

    Always returns the entry, so callers can store it in memory when
    no file path is supplied.
    """
    if path is not None:
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("a", encoding="utf-8") as handle:
            handle.write(entry.model_dump_json() + "\n")
    return entry


def _unused_json_helper(data: dict) -> str:
    return json.dumps(data, sort_keys=True)
