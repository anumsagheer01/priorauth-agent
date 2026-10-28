"""Baseline prompt regression test. No cloud call, no model call.

2026-10-27 audit: the baseline prompt used for the 2026-10-27 run
did not include the policy criterion list or the status vocabulary,
so exact-match scoring defaulted ID-mismatched criteria to "missing"
and produced 14/200 criterion accuracy. The corrected prompt must
include every criterion ID and the status list, while still making
only one call and using no verifier or scorer.
"""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import baseline
from priorauth.cloud_clients import BudgetTracker, CloudConfig
from priorauth.policies import load_eval_cases, load_policies


def test_baseline_prompt_includes_criterion_ids_and_status_vocabulary(tmp_path):
    policies = {p.policy_id: p for p in load_policies()}
    raw = [c for c in load_eval_cases() if c["policy_id"] == "AETNA_CPB_0236"][0]
    policy = policies["AETNA_CPB_0236"]
    captured = {}

    def fake_generate(prompt, config, response_schema=None):
        captured["prompt"] = prompt
        outcomes = [{"criterion_id": c.criterion_id, "status": "missing", "evidence_excerpts": []}
                    for c in policy.criteria]
        return {"text": json.dumps({"readiness": "NOT_READY", "criterion_outcomes": outcomes}),
                "usage": {"prompt_token_count": 10, "candidates_token_count": 5},
                "model": config.model}

    report = baseline.run_baseline(
        [raw], policies, [], CloudConfig(), BudgetTracker(budget_usd=8.0),
        generate_fn=fake_generate,
        retrieve_fn=lambda case, pol, chunks, cfg: ([{"chunk_id": "CH-1", "section": "test", "text": "chunk"}], "test"),
        sleep_fn=lambda s: None, case_delay_seconds=0,
        out_path=tmp_path / "results_baseline.json")
    prompt = captured["prompt"]
    for crit in policy.criteria:
        assert crit.criterion_id in prompt
        assert crit.text[:20] in prompt
    assert "met, not_met, uncertain, contradictory, missing, not_applicable, fired, not_fired" in prompt
    assert report["cases_completed"] == 1
    # Token reporting fix: baseline raw usage keys must now be summed, not 0/0.
    assert report["metrics"]["token_usage_total"] == {"prompt": 10, "output": 5}
