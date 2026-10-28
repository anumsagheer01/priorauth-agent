from priorauth.engine import run_review
from priorauth.models import ClinicalCase
from priorauth.policies import load_cases, load_policies


def _policy_map():
    return {p.policy_id: p for p in load_policies()}


def _case(raw):
    return ClinicalCase.model_validate(raw)


def test_fully_documented_case_is_ready():
    policies = _policy_map()
    cases = {c["case_id"]: c for c in load_cases()}
    result = run_review(_case(cases["LUM-001"]), policies["AETNA_CPB_0236"])
    assert result.readiness == "READY_FOR_HUMAN_REVIEW"
    assert result.draft_letter is not None
    assert "not an approval" in result.draft_letter.disclaimer.lower() or "human review only" in result.draft_letter.disclaimer.lower()
    assert result.audit_entry is not None
    assert result.audit_entry.case_id == "LUM-001"


def test_missing_required_is_not_ready():
    policies = _policy_map()
    cases = {c["case_id"]: c for c in load_cases()}
    result = run_review(_case(cases["LUM-005"]), policies["AETNA_CPB_0236"])
    assert result.readiness == "NOT_READY"


def test_stale_policy_is_never_ready():
    policies = _policy_map()
    cases = {c["case_id"]: c for c in load_cases()}
    result = run_review(_case(cases["LUM-015"]), policies["AETNA_CPB_0236"])
    assert result.readiness in ("NEEDS_MANUAL_REVIEW", "NOT_READY")
    assert result.policy_version_current is False


def test_exclusion_cannot_be_overridden():
    policies = _policy_map()
    cases = {c["case_id"]: c for c in load_cases()}
    result = run_review(_case(cases["KNE-007"]), policies["AETNA_CPB_0673"])
    assert result.readiness == "NOT_READY"
    assert any(r.status == "fired" for r in result.criterion_results)


def test_all_three_procedures_run():
    policies = _policy_map()
    cases = {c["case_id"]: c for c in load_cases()}
    for case_id, policy_id in [("LUM-001", "AETNA_CPB_0236"), ("KNE-001", "AETNA_CPB_0673"), ("BIO-001", "CIGNA_IP0660")]:
        result = run_review(_case(cases[case_id]), policies[policy_id])
        assert result.readiness == "READY_FOR_HUMAN_REVIEW"
