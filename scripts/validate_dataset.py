"""Validate data/cases.json against data/policies.json.

Checks: every case has a gold readiness label, every criterion has an
expected outcome, no duplicate case ids, code fields present, and
counts by procedure and by category. Exits non-zero on any failure.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    policies = json.loads((ROOT / "data" / "policies.json").read_text())["policies"]
    crit_by_policy = {p["policy_id"]: {c["criterion_id"] for c in p["criteria"]} for p in policies}
    cases = json.loads((ROOT / "data" / "cases.json").read_text())["cases"]
    errors: list[str] = []
    seen: set[str] = set()
    for case in cases:
        cid = case.get("case_id", "")
        if cid in seen:
            errors.append(f"Duplicate case id: {cid}")
        seen.add(cid)
        if not case.get("gold_readiness"):
            errors.append(f"Case {cid} has no gold readiness label.")
        if not case.get("diagnosis_codes"):
            errors.append(f"Case {cid} has no diagnosis codes.")
        if not case.get("procedure_code"):
            errors.append(f"Case {cid} has no procedure code.")
        if not case.get("clinical_note"):
            errors.append(f"Case {cid} has no clinical note.")
        expected = crit_by_policy.get(case.get("policy_id", ""), set())
        actual = set(case.get("gold_criterion_outcomes", {}).keys())
        if expected != actual:
            errors.append(f"Case {cid} criterion outcomes mismatch: missing {sorted(expected - actual)}, extra {sorted(actual - expected)}.")
        if not case.get("categories"):
            errors.append(f"Case {cid} has no category tags.")
    print(f"Total cases: {len(cases)}")
    print("By procedure:", dict(Counter(c["procedure"] for c in cases)))
    print("By category:", dict(Counter(cat for c in cases for cat in c["categories"])))
    print("By gold readiness:", dict(Counter(c["gold_readiness"] for c in cases)))
    if errors:
        print("ERRORS:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Dataset validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
