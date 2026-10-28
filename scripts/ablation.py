"""Ablation comparison: full system vs no-citation-verification arm.

This script makes no model calls. It compares two eval output files
produced by evaluate_real.py, one with citation verification on and
one with --no-citation-verification. That keeps the ablation cheap:
the off arm is one extra eval run, not a new experiment design.

Usage:
  python scripts/evaluate_real.py --out eval/results_real.json
  python scripts/evaluate_real.py --no-citation-verification --out eval/results_no_citation_check.json
  python scripts/ablation.py eval/results_real.json eval/results_no_citation_check.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: ablation.py <full_results.json> <ablation_results.json>")
        return 2
    full = json.loads(Path(sys.argv[1]).read_text())
    abl = json.loads(Path(sys.argv[2]).read_text())
    for label, report in (("full_system", full), ("no_citation_verification", abl)):
        m = report["metrics"]
        print(f"{label}: n={m['n_cases']} criterion_accuracy={m['criterion_accuracy']} "
              f"case_accuracy={m['case_readiness_accuracy']} false_ready_rate={m['false_ready_rate']} "
              f"citation_precision={m['citation_precision']} missing_recall={m['missing_evidence_recall']}")
    fm, am = full["metrics"], abl["metrics"]
    print("Delta (full minus ablation):")
    for key in ("criterion_accuracy", "case_readiness_accuracy", "false_ready_rate", "citation_precision", "missing_evidence_recall"):
        if fm[key] is not None and am[key] is not None:
            print(f"  {key}: {round(fm[key] - am[key], 4)}")
    print("Interpretation: if citation precision or false-ready rate worsens "
          "without verification, the verifier earns its place. If nothing "
          "changes, the verifier is not demonstrably helping on this set, "
          "and that must be reported as such.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
