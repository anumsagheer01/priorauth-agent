"""False-ready analysis for a real eval output file. No model calls.

Usage:
  python scripts/false_ready_report.py eval/results_real.json

Prints every predicted READY_FOR_HUMAN_REVIEW case whose gold
readiness is not READY, with its criterion results, citations,
critic findings, ADK tools invoked, and guardrail outcome. If there
are none, it prints that fact with the denominator, and it does NOT
claim a zero false-ready rate unless the input file actually shows
that denominator and count. This script must never be run on a
templated or mocked eval file and presented as model performance.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: false_ready_report.py <eval_results.json>")
        return 2
    report = json.loads(Path(sys.argv[1]).read_text())
    rows = report.get("rows", [])
    non_ready = [r for r in rows if r.get("gold_readiness") != "READY_FOR_HUMAN_REVIEW"]
    false_ready = [r for r in rows if r.get("readiness") == "READY_FOR_HUMAN_REVIEW" and r.get("gold_readiness") != "READY_FOR_HUMAN_REVIEW"]
    print(f"Cases evaluated: {len(rows)}")
    print(f"Gold non-ready cases (denominator): {len(non_ready)}")
    print(f"False-ready cases: {len(false_ready)}")
    if non_ready:
        print(f"False-ready rate: {len(false_ready) / len(non_ready):.4f} ({len(false_ready)}/{len(non_ready)})")
    if not false_ready:
        print("No false-ready case in this run. Do not generalize this to other case sets.")
        return 0
    for row in false_ready:
        print(f"\nFALSE READY: {row.get('case_id')} procedure={row.get('procedure')} gold={row.get('gold_readiness')} pred={row.get('readiness')}")
        print(f"  ADK tools invoked: {row.get('adk_tools_invoked', [])}")
        print(f"  ADK session: {row.get('adk_session_id', '')}")
        print(f"  Critic findings: {row.get('critic_findings', [])}")
        print(f"  Gaps reported: {row.get('gaps', [])}")
        for crit in row.get("criterion_results", []):
            print(f"  {crit.get('criterion_id')}: pred={crit.get('status')} gold={row.get('gold_criterion_outcomes', {}).get(crit.get('criterion_id'))} excerpts={crit.get('evidence_excerpts', [])} citation={crit.get('citation', {})}")
        print("  Guardrail outcome: this case reached READY despite gold non-ready, so at least one guardrail, citation check, or criterion judgment failed. Investigate the criterion above where pred is met and gold is not met, missing, or fired, and check whether its excerpt is verbatim in the note and whether its policy citation is complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
