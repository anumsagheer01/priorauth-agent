"""Evaluate the local deterministic engine over data/cases.json.

Writes eval/results/evaluation.json, eval/results/evaluation.md, and
eval/results/failure_analysis.md. All metrics come from this run only.
Latency is measured locally with time.perf_counter. Cloud cost is a
modeled estimate only, with formula and inputs shown, never a measured
cloud cost, because no cloud call is made in this run.
"""

from __future__ import annotations

import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from priorauth.engine import run_review  # noqa: E402
from priorauth.models import ClinicalCase  # noqa: E402
from priorauth.policies import get_policy, load_cases, load_policies  # noqa: E402

# Modeled cloud cost inputs, not measured. See gcp/cost_estimation.md.
# Formula: modeled_cost_per_case = input_tokens * input_rate + output_tokens * output_rate
# Inputs used here: 1500 input tokens per case, 500 output tokens per case.
MODELED_INPUT_TOKENS = 1500
MODELED_OUTPUT_TOKENS = 500
MODELED_INPUT_RATE_PER_1K = 0.00030
MODELED_OUTPUT_RATE_PER_1K = 0.00250
MODELED_COST_PER_CASE = (
    MODELED_INPUT_TOKENS / 1000 * MODELED_INPUT_RATE_PER_1K
    + MODELED_OUTPUT_TOKENS / 1000 * MODELED_OUTPUT_RATE_PER_1K
)


def main() -> int:
    policies = load_policies()
    cases = load_cases()
    out_dir = ROOT / "eval" / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    audit_path = out_dir / "audit.jsonl"
    if audit_path.exists():
        audit_path.unlink()

    confusion: Counter = Counter()
    criterion_total = 0
    criterion_correct = 0
    citation_total = 0
    citation_correct = 0
    false_ready = 0
    gold_non_ready = 0
    missing_gold = 0
    missing_found = 0
    latencies: list[float] = []
    by_procedure: dict[str, dict] = {}
    failures: list[dict] = []
    failure_categories: Counter = Counter()

    for raw in cases:
        policy = get_policy(policies, raw["policy_id"])
        if policy is None:
            continue
        case = ClinicalCase.model_validate(raw)
        result = run_review(case, policy, audit_path=audit_path)
        latencies.append(result.latency_ms)
        gold = raw["gold_readiness"]
        confusion[(gold, result.readiness)] += 1
        if gold != "READY_FOR_HUMAN_REVIEW":
            gold_non_ready += 1
            if result.readiness == "READY_FOR_HUMAN_REVIEW":
                false_ready += 1
        pred_by_id = {r.criterion_id: r.status for r in result.criterion_results}
        case_failed = False
        for crit_id, gold_status in raw["gold_criterion_outcomes"].items():
            criterion_total += 1
            if pred_by_id.get(crit_id) == gold_status:
                criterion_correct += 1
            else:
                case_failed = True
            if gold_status in ("missing", "not_met"):
                missing_gold += 1
                if pred_by_id.get(crit_id) in ("missing", "not_met"):
                    missing_found += 1
        # Citation precision: for every met prediction, is there a real
        # excerpt from the note? Engine claims are built from excerpts,
        # so this checks that invariant on the full run.
        for item in result.criterion_results:
            # Citation precision is over note-excerpt claims only. BIO-01
            # is a structured field check (age), not a note excerpt, so
            # it is excluded from this denominator by design.
            if item.status == "met" and item.criterion_id != "BIO-01":
                citation_total += 1
                if item.evidence_excerpts and all(e in case.clinical_note for e in item.evidence_excerpts):
                    citation_correct += 1
        proc = by_procedure.setdefault(raw["procedure"], {"total": 0, "correct": 0})
        proc["total"] += 1
        if result.readiness == gold:
            proc["correct"] += 1
        if result.readiness != gold or case_failed:
            failure_categories[raw["categories"][0]] += 1
            failures.append({
                "case_id": raw["case_id"],
                "procedure": raw["procedure"],
                "categories": raw["categories"],
                "gold_readiness": gold,
                "predicted_readiness": result.readiness,
                "gold_criterion_outcomes": raw["gold_criterion_outcomes"],
                "predicted_criterion_outcomes": pred_by_id,
                "gaps": result.gaps,
            })

    total = sum(confusion.values())
    case_correct = sum(v for (g, p), v in confusion.items() if g == p)
    metrics = {
        "total_cases": total,
        "criterion_accuracy": {
            "correct": criterion_correct, "total": criterion_total,
            "value": criterion_correct / criterion_total if criterion_total else 0.0,
        },
        "citation_precision": {
            "correct": citation_correct, "total": citation_total,
            "value": citation_correct / citation_total if citation_total else 0.0,
        },
        "false_ready_rate": {
            "false_ready_count": false_ready, "gold_non_ready_total": gold_non_ready,
            "value": false_ready / gold_non_ready if gold_non_ready else 0.0,
        },
        "missing_evidence_recall": {
            "found": missing_found, "gold_missing_total": missing_gold,
            "value": missing_found / missing_gold if missing_gold else 0.0,
        },
        "case_level_accuracy": {
            "correct": case_correct, "total": total,
            "value": case_correct / total if total else 0.0,
        },
        "confusion_counts": {f"gold={g},predicted={p}": v for (g, p), v in sorted(confusion.items())},
        "latency_ms": {
            "mean": statistics.mean(latencies) if latencies else 0.0,
            "median": statistics.median(latencies) if latencies else 0.0,
            "min": min(latencies) if latencies else 0.0,
            "max": max(latencies) if latencies else 0.0,
        },
        "modeled_cloud_cost_per_case_usd": MODELED_COST_PER_CASE,
        "modeled_cloud_cost_formula": (
            f"({MODELED_INPUT_TOKENS} / 1000 * {MODELED_INPUT_RATE_PER_1K}) "
            f"+ ({MODELED_OUTPUT_TOKENS} / 1000 * {MODELED_OUTPUT_RATE_PER_1K}) "
            f"= {MODELED_COST_PER_CASE:.6f} USD per case. Modeled estimate only, not measured."
        ),
        "performance_by_procedure": {
            proc: {"correct": v["correct"], "total": v["total"],
                   "accuracy": v["correct"] / v["total"] if v["total"] else 0.0}
            for proc, v in sorted(by_procedure.items())
        },
        "failure_categories": dict(failure_categories),
        "failure_case_ids": [f["case_id"] for f in failures],
        "engine": "local deterministic engine only, no model call, no cloud call",
    }
    (out_dir / "evaluation.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    md_lines = [
        "# Evaluation results (local deterministic engine only)",
        "",
        f"Total cases: {metrics['total_cases']}",
        f"Criterion-level accuracy: {criterion_correct} / {criterion_total} = {metrics['criterion_accuracy']['value']:.4f}",
        f"Citation precision: {citation_correct} / {citation_total} = {metrics['citation_precision']['value']:.4f}",
        f"False-ready rate: {false_ready} / {gold_non_ready} = {metrics['false_ready_rate']['value']:.4f} (cases predicted READY that are gold NOT_READY or NEEDS_MANUAL_REVIEW, divided by all gold non-ready cases)",
        f"Missing-evidence recall: {missing_found} / {missing_gold} = {metrics['missing_evidence_recall']['value']:.4f}",
        f"Case-level readiness accuracy: {case_correct} / {total} = {metrics['case_level_accuracy']['value']:.4f}",
        "",
        "Confusion counts (gold, predicted):",
    ]
    for key, value in sorted(metrics["confusion_counts"].items()):
        md_lines.append(f"- {key}: {value}")
    md_lines.extend([
        "",
        f"Latency per case in milliseconds, measured locally: mean {metrics['latency_ms']['mean']:.2f}, median {metrics['latency_ms']['median']:.2f}, min {metrics['latency_ms']['min']:.2f}, max {metrics['latency_ms']['max']:.2f}.",
        f"Estimated cloud cost per case, modeled estimate only: {metrics['modeled_cloud_cost_formula']}",
        "",
        "Performance by procedure:",
    ])
    for proc, v in sorted(metrics["performance_by_procedure"].items()):
        md_lines.append(f"- {proc}: {v['correct']} / {v['total']} = {v['accuracy']:.4f}")
    md_lines.extend(["", "Failure categories (counts and example case ids):"])
    for cat, count in sorted(failure_categories.items()):
        examples = [f["case_id"] for f in failures if f["categories"][0] == cat][:5]
        md_lines.append(f"- {cat}: {count}, examples: {', '.join(examples)}")
    (out_dir / "evaluation.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    fa_lines = [
        "# Failure analysis",
        "",
        "This analysis is tied to real failing case ids from the evaluation run above. "
        "Categories discussed: ambiguous language, missing evidence, contradictions, "
        "retrieval errors, stale policies, and unsupported citations.",
        "",
    ]
    if not failures:
        fa_lines.append("No failures were recorded in this run: every case matched its gold readiness label and every gold criterion outcome.")
    else:
        for item in failures[:30]:
            mismatches = [
                f"{cid}: gold {gold} vs predicted {item['predicted_criterion_outcomes'].get(cid)}"
                for cid, gold in item["gold_criterion_outcomes"].items()
                if item["predicted_criterion_outcomes"].get(cid) != gold
            ]
            fa_lines.append(f"## {item['case_id']} ({item['procedure']}, categories: {', '.join(item['categories'])})")
            fa_lines.append(f"Gold readiness: {item['gold_readiness']}. Predicted: {item['predicted_readiness']}.")
            if mismatches:
                fa_lines.append(f"Criterion mismatches: {'; '.join(mismatches)}.")
            else:
                fa_lines.append("Criterion outcomes matched; the readiness difference comes from the deterministic scorer rules (for example stale policy or code validation).")
            if item["gaps"]:
                fa_lines.append(f"Engine gaps: {'; '.join(item['gaps'])}.")
            fa_lines.append("")
        fa_lines.extend([
            "## Cross-cutting notes",
            "- Ambiguous language: cases with vague history are scored NEEDS_MANUAL_REVIEW by design, not guessed as met.",
            "- Missing evidence: a criterion with no excerpt is missing, never inferred from a related sentence.",
            "- Contradictions: both a finding and its negation for the same criterion produce contradictory, not met.",
            "- Retrieval errors: the local engine searches only local policy chunks; a missing chunk cannot create evidence.",
            "- Stale policies: a non-current version forces NEEDS_MANUAL_REVIEW when no exclusion or missing criterion already applies, and never produces READY.",
            "- Unsupported citations: the citation verifier downgrades any claim whose excerpt does not appear in the note.",
        ])
    (out_dir / "failure_analysis.md").write_text("\n".join(fa_lines), encoding="utf-8")
    print(f"Total: {total}. Criterion accuracy: {criterion_correct}/{criterion_total}. "
          f"Case accuracy: {case_correct}/{total}. False-ready: {false_ready}/{gold_non_ready}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
