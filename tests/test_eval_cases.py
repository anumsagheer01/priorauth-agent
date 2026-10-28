import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from priorauth.models import ClinicalCase
from priorauth.policies import load_eval_cases, load_policies
from priorauth.tools import checklist_scorer, code_validator

POLICIES = {p.policy_id: p for p in load_policies()}


def test_eval_set_size_and_coverage():
    cases = load_eval_cases()
    assert len(cases) == 30
    procs = {c["procedure"] for c in cases}
    assert procs == {"lumbar_mri", "knee_arthroscopy", "biologic_infusion"}
    assert sum(1 for c in cases if c["procedure"] == "lumbar_mri") == 10
    assert sum(1 for c in cases if c["source_type"] == "published_case_report") == 3


def test_gold_readiness_matches_deterministic_scorer():
    for raw in load_eval_cases():
        case = ClinicalCase.model_validate({k: v for k, v in raw.items() if k in ClinicalCase.model_fields})
        pol = POLICIES[case.policy_id]
        from priorauth.models import CriterionResult
        results = [CriterionResult(criterion_id=k, status=v) for k, v in raw["gold_criterion_outcomes"].items()]
        readiness, _ = checklist_scorer(results, code_validator(case, pol), case.policy_version == pol.current_version, pathways=pol.pathways)
        assert readiness == raw["gold_readiness"], raw["case_id"]


def test_no_em_dash_in_eval_notes():
    for raw in load_eval_cases():
        assert "\u2014" not in raw["clinical_note"], raw["case_id"]


def test_no_overlap_with_guardrail_ids():
    from priorauth.policies import load_guardrail_cases
    guard = {c["case_id"] for c in load_guardrail_cases()}
    assert not (guard & {c["case_id"] for c in load_eval_cases()})
