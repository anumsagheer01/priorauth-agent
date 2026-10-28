"""Simple RAG baseline, for comparison with the structured agent workflow.

The baseline does one Gemini call per case: retrieve chunks with
Vertex embeddings, then ask directly for readiness, with no structured
criterion schema enforcement, no deterministic citation verification,
and no pathway scorer. It is intentionally weaker, so the comparison
tests whether the structured workflow improves reliability, rather
than assuming it does. Run in Cloud Shell only; exits without
credentials. Output format matches evaluate_real.py metrics.

CORRECTED 2026-10-27 AUDIT, rerun in the cloud 2026-10-27 (see corrected baseline summary): the prompt
used for the 2026-10-27 baseline run (14/200 criterion, 13/30 case,
11/25 false-ready) did NOT include the policy criterion list or the
status vocabulary, so the model could not reliably emit the criterion
IDs and status strings that exact-match scoring requires, and any
ID mismatch defaulted to "missing". That as-run baseline number must
NOT be quoted as the model's criterion-judgment accuracy. The prompt
below now includes the same criterion list (ID, kind, section, text)
and status semantics as the full system, so a future rerun isolates
the value of structured extraction plus deterministic guardrails.
Until that rerun, the 2026-10-27 baseline comparison is a flawed
comparison for criterion accuracy, although its case-level weakness
(single unstructured readiness guess, no pathway rule, no exclusion
block, no code check) remains a legitimate structured-vs-unstructured
difference. See docs/BASELINE_VALIDATION_2026-10-27.md.

429 handling, added after the 2026-10-27 full eval aborted on a
429 RESOURCE_EXHAUSTED with no output: a case that hits a 429 is
retried a bounded number of times (3 retries, 10s / 20s / 40s
backoff, see scripts/rate_limit.py), never in a tight loop. If it
still fails, it is recorded in not_completed_cases, the remaining
cases still run, and partial results are written with explicit
cases_attempted / cases_completed / cases_not_completed, so a
partial report can never be read as a full 30-case result.
Exit code 0 means a report was written, not that every case
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
from priorauth.cloud_clients import BudgetTracker, CloudConfig, estimate_cost_usd, gemini_generate  # noqa: E402
from priorauth.models import ClinicalCase  # noqa: E402
from priorauth.policies import get_policy, load_chunks, load_eval_cases, load_policies  # noqa: E402
from priorauth.real_pipeline import retrieve_chunks  # noqa: E402
from rate_limit import call_with_429_retry, is_rate_limit_error  # noqa: E402

SCHEMA = {"type": "object", "properties": {
    "readiness": {"type": "string"},
    "criterion_outcomes": {"type": "array", "items": {"type": "object", "properties": {
        "criterion_id": {"type": "string"}, "status": {"type": "string"},
        "evidence_excerpts": {"type": "array", "items": {"type": "string"}}},
        "required": ["criterion_id", "status"]}}},
    "required": ["readiness", "criterion_outcomes"]}


def _write_report(report: dict, out: Path) -> None:
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(report, indent=1))


def run_baseline(cases, policies, chunks, config, budget,
                 generate_fn=None, retrieve_fn=None,
                 sleep_fn=time.sleep, case_delay_seconds: float | None = None,
                 out_path: Path | None = None) -> dict:
    """Run the baseline with bounded 429 handling. See module docstring.

    generate_fn / retrieve_fn are injectable for tests (defaults:
    gemini_generate / retrieve_chunks). sleep_fn is injectable so
    tests never wait for real backoff delays.
    """
    if generate_fn is None:
        generate_fn = gemini_generate
    if retrieve_fn is None:
        retrieve_fn = retrieve_chunks
    if case_delay_seconds is None:
        case_delay_seconds = float(os.environ.get("PRIORAUTH_EVAL_CASE_DELAY_SECONDS", "5"))
    rows = []
    failed = []
    report: dict = {}

    def _one_case(raw):
        case = ClinicalCase.model_validate({k: v for k, v in raw.items() if k in ClinicalCase.model_fields})
        policy = policies[case.policy_id]
        started = time.perf_counter()
        retrieved, method = retrieve_fn(case, policy, chunks, config)
        chunk_text = "\n".join(
            f"- {c.get('chunk_id', '')} {c.get('section', '')}: {c.get('text', '')}" for c in retrieved)
        criteria_text = "\n".join(
            f"{c.criterion_id} ({getattr(c, 'kind', '')}, section {getattr(c, 'section', '')}): {getattr(c, 'text', '')}"
            for c in policy.criteria)
        prompt = (f"Policy {policy.policy_id}: {policy.title}. Retrieved chunks:\n{chunk_text}\n\n"
                  f"Criteria (give one outcome per listed criterion ID):\n{criteria_text}\n\n"
                  f"Patient age field: {case.patient_age}\n"
                  f"Diagnosis codes: {', '.join(case.diagnosis_codes)}\n"
                  f"Procedure code: {case.procedure_code}\n\n"
                  f"Clinical note:\n{case.clinical_note}\n\n"
                  "Use only these statuses: met, not_met, uncertain, contradictory, missing, not_applicable, fired, not_fired. "
                  "Exclusion criteria use fired or not_fired only. If the note does not state it, use missing, not not_met, "
                  "unless the note explicitly negates it. If language is ambiguous, use uncertain. "
                  "Decide documentation readiness directly: READY_FOR_HUMAN_REVIEW, NOT_READY, or NEEDS_MANUAL_REVIEW, "
                  "and give one status per criterion, using the criterion IDs above. Return JSON only. "
                  "This baseline still has no citation verification, no code validation, and no pathway scorer, "
                  "so its readiness is a direct model guess, not a scored pathway outcome.")
        result = generate_fn(prompt, config, response_schema=SCHEMA)
        cost = estimate_cost_usd(result["usage"], config)
        budget.add(cost, f"baseline:{case.case_id}")
        parsed = json.loads(result["text"])
        pred = {o["criterion_id"]: o["status"] for o in parsed.get("criterion_outcomes", [])}
        crit = [{"criterion_id": c.criterion_id, "status": pred.get(c.criterion_id, "missing"),
                 "evidence_excerpts": next((o.get("evidence_excerpts", []) for o in parsed.get("criterion_outcomes", []) if o["criterion_id"] == c.criterion_id), [])}
                for c in policy.criteria]
        row = {"case_id": case.case_id, "procedure": case.procedure,
               "readiness": parsed.get("readiness", "NEEDS_MANUAL_REVIEW"),
               "gold_readiness": raw["gold_readiness"],
               "gold_criterion_outcomes": raw["gold_criterion_outcomes"],
               "criterion_results": crit, "clinical_note": case.clinical_note,
               "retrieval_keywords": raw.get("retrieval_keywords", []),
               "retrieval_chunks": retrieved,
               "latency_ms": (time.perf_counter() - started) * 1000.0,
               "cost_usd_estimated": cost,
               "token_usage": {**result["usage"], "evidence_prompt_token_count": result["usage"].get("prompt_token_count", 0), "evidence_candidates_token_count": result["usage"].get("candidates_token_count", 0)}, "retrieval_method": method}
        print(f"{case.case_id}: baseline pred={row['readiness']} gold={raw['gold_readiness']}", flush=True)
        return row

    try:
        for index, raw in enumerate(cases):
            try:
                rows.append(call_with_429_retry(lambda raw=raw: _one_case(raw), sleep_fn=sleep_fn))
            except Exception as exc:  # noqa: BLE001 - recorded below if 429
                if not is_rate_limit_error(exc):
                    raise
                case_id = raw.get("case_id", f"case-{index}")
                failed.append({"case_id": case_id, "status": "not_completed",
                               "reason": "rate_limit_429_after_bounded_retry",
                               "error": str(exc)[:500]})
                print(f"{case_id}: NOT_COMPLETED rate_limit_429_after_bounded_retry", flush=True)
            report = {"model": config.model, "model_location": config.model_location,
                      "data_location": config.location,
                      "method": "single_call_rag_baseline_no_verifier_no_scorer",
                      "budget_spent_usd_estimated": round(budget.spent, 4),
                      "cases_attempted": len(cases),
                      "cases_completed": len(rows),
                      "cases_not_completed": len(failed),
                      "not_completed_cases": failed,
                      "metrics_denominator_note": "Metrics are computed over completed cases only. cases_completed is the denominator for case-level metrics; see metrics for criterion-level denominators. A partial report is not a full-run result.",
                      "metrics": compute_metrics(rows), "rows": rows}
            if out_path is not None:
                _write_report(report, out_path)
            if index < len(cases) - 1 and case_delay_seconds:
                sleep_fn(case_delay_seconds)
    finally:
        if out_path is not None and report:
            _write_report(report, out_path)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--out", default="eval/results_baseline.json")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    policies = {p.policy_id: p for p in load_policies()}
    chunks = load_chunks()
    cases = load_eval_cases()[: args.limit]
    config = CloudConfig()
    budget = BudgetTracker(budget_usd=config.budget_usd)
    out = root / args.out
    report = run_baseline(cases, policies, chunks, config, budget, out_path=out)
    print(json.dumps(report["metrics"], indent=1))
    if report["cases_not_completed"]:
        print(f"WARNING: {report['cases_not_completed']} of {report['cases_attempted']} cases "
              f"not completed (see not_completed_cases). This is a partial report, not a full run.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
