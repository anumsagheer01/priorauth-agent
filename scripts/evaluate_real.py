"""Real eval: run the ADK pipeline on data/eval_cases.json in Cloud Shell.

Usage (Cloud Shell, project delivery-experience-511901):
  cd priorauth-agent
  python scripts/evaluate_real.py --limit 30 --out eval/results_real.json
  python scripts/evaluate_real.py --limit 10 --no-citation-verification --out eval/results_no_citation_check.json

Stops at the $8 budget via BudgetTracker. Never invents a result: if
credentials are absent, it exits with an error and writes nothing.
The eval set was annotated before any model run and was not used to
optimize the agent.

429 handling, added after the 2026-10-27 full run aborted on a
429 RESOURCE_EXHAUSTED with no results_real.json written:
- A case that hits a 429 is retried a bounded number of times
  (3 retries, 10s / 20s / 40s backoff, see scripts/rate_limit.py),
  never in a tight loop and never indefinitely.
- If it still fails, it is recorded in not_completed_cases with
  its error, the remaining cases still run, and partial results
  are written. Metrics are computed over completed cases only,
  and the report states cases_attempted, cases_completed, and
  cases_not_completed, so a partial report can never be read
  as a full 30-case result.
- The report is also rewritten after every case, so a later
  fatal error (for example a budget stop) does not destroy the
  partial output already produced.
- Exit code 0 means a report was written, not that every case
  completed. Check cases_not_completed in the report.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from eval_metrics import compute_metrics  # noqa: E402
from priorauth.adk_agent import run_via_adk  # noqa: E402
from priorauth.cloud_clients import BudgetTracker, CloudConfig  # noqa: E402
from priorauth.models import ClinicalCase  # noqa: E402
from priorauth.policies import get_policy, load_chunks, load_eval_cases, load_policies  # noqa: E402
from rate_limit import call_with_429_retry, is_rate_limit_error  # noqa: E402


def _write_report(report: dict, out: Path) -> None:
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(report, indent=1))


def _build_report(rows: list[dict], failed: list[dict], attempted: int,
                   config: CloudConfig, budget: BudgetTracker,
                   citation_verification: bool) -> dict:
    # ADK execution proof, summarized from actual Runner events, not
    # from a fabricated tool list. If a case has no ADK tool events,
    # that is a failure to record, not a reason to backfill one.
    tool_counts: dict[str, int] = {}
    sessions: list[str] = []
    for row in rows:
        for name in row.get("adk_tools_invoked", []):
            tool_counts[name] = tool_counts.get(name, 0) + 1
        if row.get("adk_session_id"):
            sessions.append(row["adk_session_id"])
    return {"model": config.model, "model_location": config.model_location,
            "data_location": config.location, "embedding_model": config.embedding_model,
            "citation_verification": citation_verification,
            "budget_spent_usd_estimated": round(budget.spent, 4),
            "adk_tool_call_counts": tool_counts,
            "adk_sessions": sessions,
            "adk_execution_note": "adk_tool_events in each row are events actually yielded by Runner.run_async. A row with empty adk_tool_events did not run through ADK and must not be presented as an ADK result.",
            "cases_attempted": attempted,
            "cases_completed": len(rows),
            "cases_not_completed": len(failed),
            "not_completed_cases": failed,
            "metrics_denominator_note": "Metrics are computed over completed cases only. cases_completed is the denominator for case-level metrics; see metrics for criterion-level denominators. A partial report is not a full-run result.",
            "metrics": compute_metrics(rows), "rows": rows}


def run_eval(cases, policies, chunks, config, budget, verify_citations: bool = True,
             runner=None, sleep_fn=time.sleep, case_delay_seconds: float | None = None,
             out_path: Path | None = None) -> dict:
    """Run cases through the ADK pipeline with bounded 429 handling.

    runner is injectable for tests (default: run_via_adk). sleep_fn
    is injectable so tests never wait for real backoff delays.
    case_delay_seconds defaults to PRIORAUTH_EVAL_CASE_DELAY_SECONDS
    or 5 seconds: a small pause between cases, on top of retry
    backoff, so a quota error is not immediately re-triggered by
    the next case. Non-429 errors still propagate, but only after
    the partial report has been written to out_path, if given.
    """
    if runner is None:
        runner = run_via_adk
    if case_delay_seconds is None:
        case_delay_seconds = float(os.environ.get("PRIORAUTH_EVAL_CASE_DELAY_SECONDS", "5"))
    rows: list[dict] = []
    failed: list[dict] = []
    report: dict = {}
    try:
        for index, raw in enumerate(cases):
            case = ClinicalCase.model_validate({k: v for k, v in raw.items() if k in ClinicalCase.model_fields})
            try:
                result = call_with_429_retry(
                    lambda: runner(case, policies[case.policy_id], chunks, config=config,
                                   budget=budget, verify_citations=verify_citations),
                    sleep_fn=sleep_fn)
            except Exception as exc:  # noqa: BLE001 - recorded below if 429
                if not is_rate_limit_error(exc):
                    raise
                failed.append({"case_id": case.case_id, "status": "not_completed",
                               "reason": "rate_limit_429_after_bounded_retry",
                               "error": str(exc)[:500]})
                print(f"{case.case_id}: NOT_COMPLETED rate_limit_429_after_bounded_retry", flush=True)
            else:
                row = result.model_dump()
                row.update({"gold_readiness": raw["gold_readiness"],
                            "gold_criterion_outcomes": raw["gold_criterion_outcomes"],
                            "procedure": case.procedure,
                            "clinical_note": case.clinical_note,
                            "retrieval_keywords": raw.get("retrieval_keywords", []),
                            "categories": raw.get("categories", []),
                            "source_type": raw.get("source_type", "")})
                rows.append(row)
                print(f"{case.case_id}: pred={result.readiness} gold={raw['gold_readiness']} "
                      f"adk_tools={result.adk_tools_invoked} latency_ms={result.latency_ms:.0f} cost=${result.cost_usd_estimated:.4f} "
                      f"budget_spent=${budget.spent:.4f}", flush=True)
            report = _build_report(rows, failed, len(cases), config, budget, verify_citations)
            if out_path is not None:
                _write_report(report, out_path)
            if index < len(cases) - 1 and case_delay_seconds:
                sleep_fn(case_delay_seconds)
    finally:
        # If a non-429 fatal error aborted the loop, the last
        # report built above (if any) is still written, so the
        # partial output is not lost with the exception.
        if out_path is not None and report:
            _write_report(report, out_path)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--out", default="eval/results_real.json")
    parser.add_argument("--no-citation-verification", action="store_true",
                        help="Ablation arm only. Do not report this as the full system.")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    policies = {p.policy_id: p for p in load_policies()}
    chunks = load_chunks()
    cases = load_eval_cases()[: args.limit]
    config = CloudConfig()
    budget = BudgetTracker(budget_usd=config.budget_usd)
    out = root / args.out
    report = run_eval(cases, policies, chunks, config, budget,
                      verify_citations=not args.no_citation_verification,
                      out_path=out)
    print(json.dumps(report["metrics"], indent=1))
    if report["cases_not_completed"]:
        print(f"WARNING: {report['cases_not_completed']} of {report['cases_attempted']} cases "
              f"not completed (see not_completed_cases). This is a partial report, not a full run.", file=sys.stderr)
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
