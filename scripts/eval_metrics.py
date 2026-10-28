"""Shared, deterministic metric formulas for PriorAuth eval outputs.

Every metric shows its denominator. Nothing here calls a model.
Formulas:
- criterion accuracy: correct criterion outcomes / total gold criterion outcomes.
- case readiness accuracy: cases where predicted readiness equals gold readiness / cases.
- false-ready rate: gold NOT READY or NEEDS_MANUAL_REVIEW cases predicted
  READY_FOR_HUMAN_REVIEW / all gold non-ready cases. A false ready is
  the most dangerous error, so it is reported separately.
- missing-evidence recall: gold missing criteria the model also called
  missing, uncertain, or not_met (that is, did not call met) / gold missing criteria.
  Calling a missing criterion met is the failure this measures.
- citation precision: predicted met claims whose excerpt appears verbatim
  in the note / all predicted met claims with an excerpt.
- retrieval recall: cases where at least one retrieved chunk contains a
  gold retrieval keyword / cases. This is a weak, documented proxy, not
  a claim about chunk-level gold labels, because no chunk-level gold
  set exists for these cases.
Latency: p50 and p95 from the per-case latency_ms values.
Cost: sum of estimated USD from API usage metadata, plus per-case mean.
"""

from __future__ import annotations

import statistics


def _pct(num: int, den: int) -> float | None:
    return round(num / den, 4) if den else None


def compute_metrics(rows: list[dict]) -> dict:
    crit_correct = crit_total = 0
    case_correct = 0
    false_ready = non_ready = 0
    missing_caught = missing_total = 0
    cite_good = cite_total = 0
    retrieval_hit = 0
    latencies: list[float] = []
    costs: list[float] = []
    tokens = {"prompt": 0, "output": 0}
    by_procedure: dict[str, dict] = {}
    failures: list[dict] = []
    for row in rows:
        gold = row["gold_criterion_outcomes"]
        pred = {r["criterion_id"]: r["status"] for r in row["criterion_results"]}
        for cid, g in gold.items():
            crit_total += 1
            if pred.get(cid) == g:
                crit_correct += 1
            elif g == "missing" and pred.get(cid) == "met":
                failures.append({"case_id": row["case_id"], "criterion_id": cid,
                                 "gold": g, "predicted": pred.get(cid), "kind": "missing_called_met"})
            if g == "missing":
                missing_total += 1
                if pred.get(cid) in ("missing", "uncertain", "not_met"):
                    missing_caught += 1
        if row["readiness"] == row["gold_readiness"]:
            case_correct += 1
        elif row["gold_readiness"] != "READY_FOR_HUMAN_REVIEW" and row["readiness"] == "READY_FOR_HUMAN_REVIEW":
            false_ready += 1
            failures.append({"case_id": row["case_id"], "gold": row["gold_readiness"],
                             "predicted": row["readiness"], "kind": "false_ready"})
        elif row["readiness"] != row["gold_readiness"]:
            failures.append({"case_id": row["case_id"], "gold": row["gold_readiness"],
                             "predicted": row["readiness"], "kind": "readiness_mismatch"})
        if row["gold_readiness"] != "READY_FOR_HUMAN_REVIEW":
            non_ready += 1
        for r in row["criterion_results"]:
            if r["status"] == "met":
                for ex in r.get("evidence_excerpts", []):
                    cite_total += 1
                    if ex and ex in row["clinical_note"]:
                        cite_good += 1
        keywords = [k.lower() for k in row.get("retrieval_keywords", [])]
        if any(k in (c.get("text", "") or "").lower() for c in row.get("retrieval_chunks", []) for k in keywords):
            retrieval_hit += 1
        latencies.append(float(row.get("latency_ms", 0.0)))
        costs.append(float(row.get("cost_usd_estimated", 0.0)))
        usage = row.get("token_usage", {})
        # Baseline rows store raw Gemini usage (prompt_token_count / candidates_token_count); full-system rows store
        # evidence_*/draft_* keys. Sum both, without double-counting a row that carries both sets.
        # (2026-10-27 audit fix: the 2026-10-27 baseline token total was 0/0 because only evidence_*/draft_* keys were summed.)
        if usage.get("evidence_prompt_token_count") or usage.get("draft_prompt_token_count"):
            tokens["prompt"] += int(usage.get("evidence_prompt_token_count", 0) or 0) + int(usage.get("draft_prompt_token_count", 0) or 0)
            tokens["output"] += int(usage.get("evidence_candidates_token_count", 0) or 0) + int(usage.get("draft_candidates_token_count", 0) or 0)
        else:
            tokens["prompt"] += int(usage.get("prompt_token_count", 0) or 0)
            tokens["output"] += int(usage.get("candidates_token_count", 0) or 0)
        proc = row["procedure"]
        slot = by_procedure.setdefault(proc, {"cases": 0, "case_correct": 0, "crit_correct": 0, "crit_total": 0})
        slot["cases"] += 1
        slot["case_correct"] += int(row["readiness"] == row["gold_readiness"])
        for cid, g in gold.items():
            slot["crit_total"] += 1
            slot["crit_correct"] += int(pred.get(cid) == g)
    latencies_sorted = sorted(latencies)
    p50 = latencies_sorted[len(latencies_sorted) // 2] if latencies_sorted else 0.0
    p95 = latencies_sorted[int(len(latencies_sorted) * 0.95)] if latencies_sorted else 0.0
    for proc, slot in by_procedure.items():
        slot["case_accuracy"] = _pct(slot["case_correct"], slot["cases"])
        slot["criterion_accuracy"] = _pct(slot["crit_correct"], slot["crit_total"])
    return {
        "n_cases": len(rows),
        "criterion_accuracy": _pct(crit_correct, crit_total),
        "criterion_correct": crit_correct, "criterion_total": crit_total,
        "case_readiness_accuracy": _pct(case_correct, len(rows)),
        "case_correct": case_correct,
        "false_ready_rate": _pct(false_ready, non_ready),
        "false_ready": false_ready, "non_ready_total": non_ready,
        "missing_evidence_recall": _pct(missing_caught, missing_total),
        "missing_caught": missing_caught, "missing_total": missing_total,
        "citation_precision": _pct(cite_good, cite_total),
        "citation_good": cite_good, "citation_total": cite_total,
        "retrieval_recall_proxy": _pct(retrieval_hit, len(rows)),
        "retrieval_hits": retrieval_hit,
        "latency_ms_p50": round(p50, 1), "latency_ms_p95": round(p95, 1),
        "latency_ms_mean": round(statistics.mean(latencies), 1) if latencies else 0.0,
        "cost_usd_total_estimated": round(sum(costs), 4),
        "cost_usd_mean_per_case": round(statistics.mean(costs), 4) if costs else 0.0,
        "token_usage_total": tokens,
        "by_procedure": by_procedure,
        "failures": failures,
    }
