"""Recompute reported evaluation metrics from raw eval files, if present.

Usage:
  python scripts/recompute_metrics.py [--evidence-dir DIR]

Default evidence directory: evidence/cloud_eval_2026-10-27/raw/ relative
to the repo root, falling back to evidence/cloud_eval_2026-10-27/ if
the raw files are not in raw/.

This script NEVER invents metrics. If a required raw file is
absent, it reports that file as unavailable and exits with code 2.
If a file is present, it recomputes metrics from that file's rows
using scripts/eval_metrics.py, compares each recomputed value to
the metrics embedded in the same file, and reports any mismatch.
A mismatch is reported, never silently adjusted, and causes a
non-zero exit code.

Raw files expected, unchanged, in evidence/cloud_eval_2026-10-27/raw/:
  results_real.json, results_baseline.json,
  results_no_citation_check.json (from Cloud Shell at
  ~/pa_final4/priorauth-agent/eval/, via the user upload),
  results_baseline_corrected.json (corrected baseline rerun,
  2026-10-27, from Cloud Shell at
  ~/pa_baseline_rerun/priorauth-agent/eval/, via a later user
  upload, copied byte-for-byte, 116872 bytes, SHA-256
  ed13f335aff8b1452a8419b39b33e1fa63e35a31710f18d115caff1d60986ff9).
Each file is expected to be a report object with "rows" (a list)
and "metrics" (a dict), as produced by scripts/evaluate_real.py
and scripts/baseline.py. If a file has a different shape, that
is reported as a mismatch, not worked around by guessing.

Reported values, for reference only, are printed at the end for
comparison with the recomputed values, but the pass/fail
comparison is against the metrics embedded in each raw file
itself, because those are the values that must agree with the rows.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

REQUIRED = [
    "results_real.json",
    "results_baseline.json",
    "results_no_citation_check.json",
    "results_baseline_corrected.json",
]

# Reported values, from the raw files' embedded metrics, 2026-10-27.
# These are NOT a substitute for raw files. They are printed only
# so a reader can see what the recomputation should agree with
# when raw files are present.
REPORTED = {
    "results_real.json": {
        "criterion_correct": 171, "criterion_total": 200,
        "case_correct": 28, "n_cases": 30,
        "false_ready": 0, "non_ready_total": 25,
        "missing_caught": 12, "missing_total": 14,
        "citation_good": 89, "citation_total": 89,
    },
    "results_baseline.json": {
        "criterion_correct": 14, "criterion_total": 200,
        "case_correct": 13, "n_cases": 30,
        "false_ready": 11, "non_ready_total": 25,
        "missing_caught": 14, "missing_total": 14,
        "citation_good": 0, "citation_total": 0,
    },
    "results_no_citation_check.json": {
        "criterion_correct": 173, "criterion_total": 200,
        "case_correct": 28, "n_cases": 30,
        "false_ready": 0, "non_ready_total": 25,
        "missing_caught": 12, "missing_total": 14,
        "citation_good": 90, "citation_total": 90,
    },
    "results_baseline_corrected.json": {
        "criterion_correct": 176, "criterion_total": 200,
        "case_correct": 8, "n_cases": 30,
        "false_ready": 18, "non_ready_total": 25,
        "missing_caught": 13, "missing_total": 14,
        "citation_good": 90, "citation_total": 99,
    },
}

COMPARE_KEYS = [
    "n_cases", "criterion_correct", "criterion_total",
    "criterion_accuracy", "case_correct", "case_readiness_accuracy",
    "false_ready", "non_ready_total", "false_ready_rate",
    "missing_caught", "missing_total", "missing_evidence_recall",
    "citation_good", "citation_total", "citation_precision",
    "retrieval_hits", "retrieval_recall_proxy",
    "latency_ms_p50", "latency_ms_p95", "latency_ms_mean",
    "cost_usd_total_estimated", "cost_usd_mean_per_case",
]


def load_compute_metrics(script_dir: Path):
    path = script_dir / "eval_metrics.py"
    spec = importlib.util.spec_from_file_location("priorauth_eval_metrics", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.compute_metrics


def close(a, b, tol=0.001):
    if a is None or b is None:
        return a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) <= tol
    return a == b


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--evidence-dir", default=None,
        help="Directory containing the raw eval JSON files. "
             "Default: evidence/cloud_eval_2026-10-27/ under the repo root.")
    args = parser.parse_args(argv)
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
    if args.evidence_dir:
        evidence_dir = Path(args.evidence_dir)
    else:
        # Raw files live in the raw/ subdirectory since the 2026-10-27
        # user upload; fall back to the parent evidence directory only
        # if raw/ does not contain the required files.
        raw_dir = repo_root / "evidence" / "cloud_eval_2026-10-27" / "raw"
        parent_dir = repo_root / "evidence" / "cloud_eval_2026-10-27"
        evidence_dir = raw_dir if all((raw_dir / n).is_file() for n in REQUIRED) else parent_dir

    missing = [name for name in REQUIRED if not (evidence_dir / name).is_file()]
    if missing:
        print("RAW FILES UNAVAILABLE: the following required raw eval files are not present:")
        for name in missing:
            print(f"  missing: {evidence_dir / name}")
        print("No metrics were recomputed and none are invented here.")
        print("Download the originals from Cloud Shell at ~/pa_final4/priorauth-agent/eval/,")
        print("verify their sizes, scan them for credentials, place them unchanged in the")
        print("evidence directory, and run this script again.")
        return 2

    compute_metrics = load_compute_metrics(script_dir)
    overall_ok = True
    for name in REQUIRED:
        path = evidence_dir / name
        try:
            report = json.loads(path.read_text())
        except Exception as exc:  # noqa: BLE001 - report, do not hide
            print(f"{name}: FAILED to parse JSON: {exc}")
            overall_ok = False
            continue
        rows = report.get("rows") if isinstance(report, dict) else None
        embedded = report.get("metrics") if isinstance(report, dict) else None
        if not isinstance(rows, list) or not rows:
            print(f"{name}: MISMATCH: rows are missing or empty, cannot recompute.")
            overall_ok = False
            continue
        if not isinstance(embedded, dict):
            print(f"{name}: MISMATCH: embedded metrics are missing, cannot compare.")
            overall_ok = False
            continue
        try:
            recomputed = compute_metrics(rows)
        except Exception as exc:  # noqa: BLE001 - report, do not hide
            print(f"{name}: FAILED to recompute metrics: {exc}")
            overall_ok = False
            continue
        mismatches = []
        for key in COMPARE_KEYS:
            if key in embedded and not close(recomputed.get(key), embedded.get(key)):
                mismatches.append(f"{key}: recomputed={recomputed.get(key)} embedded={embedded.get(key)}")
        # By-procedure breakdown must also agree exactly.
        emb_proc = embedded.get("by_procedure") or {}
        rec_proc = recomputed.get("by_procedure") or {}
        if emb_proc and rec_proc != emb_proc:
            mismatches.append(f"by_procedure: recomputed={rec_proc} embedded={emb_proc}")
        # Failures list must agree exactly when both are present.
        emb_fail = embedded.get("failures")
        rec_fail = recomputed.get("failures")
        if emb_fail is not None and rec_fail is not None and rec_fail != emb_fail:
            mismatches.append(f"failures: recomputed={rec_fail} embedded={emb_fail}")
        # Token totals are NOT in COMPARE_KEYS, but they must be checked
        # separately: the as-run baseline embedded token total is 0/0,
        # while its rows sum to prompt 12020 / candidates 4874 (known
        # old-code bug, documented in
        # docs/RAW_VERIFICATION_AND_RECOMPUTATION_2026-10-27.md).
        # Report it here rather than hiding it behind an OK.
        emb_tokens = embedded.get("token_usage_total") or {}
        rec_tokens = recomputed.get("token_usage_total") or {}
        for tok_key in ("prompt", "output"):
            if tok_key in emb_tokens and not close(rec_tokens.get(tok_key), emb_tokens.get(tok_key)):
                mismatches.append(
                    f"token_usage_total.{tok_key}: recomputed={rec_tokens.get(tok_key)} "
                    f"embedded={emb_tokens.get(tok_key)} (known baseline token bug; see recomputation doc)"
                )
        completed = report.get("cases_completed", len(rows))
        attempted = report.get("cases_attempted", len(rows))
        not_completed = report.get("cases_not_completed")
        print(f"{name}: rows={len(rows)} attempted={attempted} completed={completed} not_completed={not_completed}")
        if mismatches:
            overall_ok = False
            print(f"{name}: MISMATCHES ({len(mismatches)}):")
            for line in mismatches:
                print(f"  {line}")
        else:
            print(f"{name}: OK, recomputed metrics match embedded metrics.")
        print(f"{name}: reported reference: {REPORTED[name]}")
    if overall_ok:
        print("RESULT: all present files recompute cleanly against their embedded metrics.")
        return 0
    print("RESULT: mismatches found. They are reported above and were NOT silently adjusted.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
