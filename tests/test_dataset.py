import subprocess
import sys
from collections import Counter
from pathlib import Path

from priorauth.policies import load_cases, load_policies

ROOT = Path(__file__).resolve().parents[1]


def test_dataset_shape():
    cases = load_cases()
    assert len(cases) >= 50
    assert len({c["case_id"] for c in cases}) == len(cases)
    counts = Counter(c["procedure"] for c in cases)
    assert set(counts) == {"lumbar_mri", "knee_arthroscopy", "biologic_infusion"}
    assert all(v >= 15 for v in counts.values())
    cats = {cat for c in cases for cat in c["categories"]}
    required = {"fully_documented", "missing_evidence", "exclusion_triggered",
                "incorrect_or_unsupported_code", "contradictory_notes", "ambiguous_history",
                "outdated_policy", "incomplete_conservative", "negated_findings", "insufficient_evidence"}
    assert required.issubset(cats), f"Missing categories: {required - cats}"


def test_gold_outcomes_cover_all_criteria():
    policies = {p.policy_id: {c.criterion_id for c in p.criteria} for p in load_policies()}
    for case in load_cases():
        assert case["gold_readiness"] in ("READY_FOR_HUMAN_REVIEW", "NOT_READY", "NEEDS_MANUAL_REVIEW")
        assert set(case["gold_criterion_outcomes"]) == policies[case["policy_id"]]
        assert case["diagnosis_codes"] and case["procedure_code"]


def test_validate_dataset_script_passes():
    result = subprocess.run([sys.executable, "scripts/validate_dataset.py"], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
