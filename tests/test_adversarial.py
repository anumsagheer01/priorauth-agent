"""Adversarial tests: fake claims, exclusions, missing criteria,
stale policies, and unsupported citations must never produce READY.
"""

from priorauth.engine import run_review
from priorauth.models import ClinicalCase, CriterionResult
from priorauth.policies import load_cases, load_policies
from priorauth.tools import checklist_scorer, citation_verifier, code_validator


def _policies():
    return {p.policy_id: p for p in load_policies()}


def test_fake_met_claim_without_excerpt_cannot_be_ready():
    policies = _policies()
    policy = policies["AETNA_CPB_0236"]
    case = ClinicalCase(case_id="ADV-1", procedure="lumbar_mri", policy_id="AETNA_CPB_0236",
                        policy_version="2026", diagnosis_codes=["M54.16"], procedure_code="72148",
                        clinical_note="No relevant findings documented.")
    # Direct citation check: a claim with no real excerpt is downgraded.
    fake_results = [CriterionResult(criterion_id="LUM-01", status="met", evidence_excerpts=[])]
    fake_claims = [{"criterion_id": "LUM-01", "excerpt": "Invented radiculopathy finding.", "citation_policy_id": "AETNA_CPB_0236", "citation_section": "Lumbar spine MRI criteria"}]
    updated, _ = citation_verifier(fake_results, fake_claims, note=case.clinical_note)
    assert updated[0].status == "missing"
    result = run_review(case, policy)
    assert result.readiness != "READY_FOR_HUMAN_REVIEW"


def test_exclusion_firing_cannot_be_overridden():
    policies = _policies()
    policy = policies["AETNA_CPB_0673"]
    results = [
        CriterionResult(criterion_id="KNE-01", status="met", evidence_excerpts=["x"]),
        CriterionResult(criterion_id="KNE-EX-01", status="fired", evidence_excerpts=["Kellgren-Lawrence grade 4"]),
    ]
    case = ClinicalCase(case_id="ADV-2", procedure="knee_arthroscopy", policy_id="AETNA_CPB_0673",
                        policy_version="2024-09-11", diagnosis_codes=["M23.22"], procedure_code="29881",
                        clinical_note="Note.")
    readiness, _ = checklist_scorer(results, code_validator(case, policy), True)
    assert readiness == "NOT_READY"


def test_missing_required_cannot_be_ready():
    policies = _policies()
    policy = policies["AETNA_CPB_0236"]
    case = ClinicalCase(case_id="ADV-3", procedure="lumbar_mri", policy_id="AETNA_CPB_0236",
                        policy_version="2026", diagnosis_codes=["M54.16"], procedure_code="72148",
                        clinical_note="Exam shows radicular pain with motor weakness in the L5 distribution.")
    result = run_review(case, policy)
    assert result.readiness == "NOT_READY"


def test_stale_policy_forces_manual_or_not_ready():
    policies = _policies()
    cases = {c["case_id"]: c for c in load_cases()}
    result = run_review(ClinicalCase.model_validate(cases["BIO-015"]), policies["CIGNA_IP0660"])
    assert result.readiness in ("NEEDS_MANUAL_REVIEW", "NOT_READY")


def test_citation_verifier_downgrades_unsupported_claim():
    policies = _policies()
    policy = policies["AETNA_CPB_0236"]
    note = "Exam shows radicular pain with motor weakness in the L5 distribution."
    results = [CriterionResult(criterion_id="LUM-01", status="met", evidence_excerpts=["Exam shows radicular pain with motor weakness in the L5 distribution."])]
    claims = [{"criterion_id": "LUM-01", "excerpt": "Not in the note at all.", "citation_policy_id": "AETNA_CPB_0236", "citation_section": "Lumbar spine MRI criteria"}]
    updated, findings = citation_verifier(results, claims, note=note)
    assert updated[0].status == "missing"
    assert findings
