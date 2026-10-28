"""429 handling and idempotent BigQuery load. No cloud call, no model call.

Regression tests for the 2026-10-27 full eval abort: a 429
RESOURCE_EXHAUSTED aborted evaluate_real.py with no
results_real.json written, and a BigQuery rerun duplicated
policies (6 instead of 3) and policy_chunks (14 instead of 7).
"""

import json
import sys
import types
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gcp"))

import evaluate_real
from priorauth.cloud_clients import BudgetTracker, CloudConfig
from priorauth.models import CriterionResult, ReviewResult
from rate_limit import call_with_429_retry, is_rate_limit_error


class _ResourceExhausted(Exception):
    pass


def test_is_rate_limit_error_detects_429_forms_and_rejects_other_errors():
    assert is_rate_limit_error(_ResourceExhausted("429 RESOURCE_EXHAUSTED"))
    assert is_rate_limit_error(Exception("google.api_core.exceptions.ResourceExhausted: 429"))
    coded = Exception("quota exceeded")
    coded.code = 429
    assert is_rate_limit_error(coded)
    assert not is_rate_limit_error(ValueError("not a quota error"))
    assert not is_rate_limit_error(Exception("404 NOT_FOUND"))


def test_call_with_429_retry_retries_bounded_times_with_backoff():
    sleeps = []
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise _ResourceExhausted("429 RESOURCE_EXHAUSTED")
        return "ok"

    assert call_with_429_retry(flaky, sleep_fn=sleeps.append) == "ok"
    assert calls["n"] == 3
    assert sleeps == [10.0, 20.0]


def test_call_with_429_retry_exhausts_after_four_attempts():
    sleeps = []
    calls = {"n": 0}

    def always_429():
        calls["n"] += 1
        raise _ResourceExhausted("429 RESOURCE_EXHAUSTED")

    try:
        call_with_429_retry(always_429, sleep_fn=sleeps.append)
    except _ResourceExhausted:
        pass
    else:  # pragma: no cover - the retry must not swallow the error
        raise AssertionError("expected the 429 to be re-raised after retries")
    assert calls["n"] == 4
    assert sleeps == [10.0, 20.0, 40.0]


def _raw_case(case_id, gold):
    return {"case_id": case_id, "procedure": "lumbar_mri", "policy_id": "P1",
            "policy_version": "v1", "clinical_note": "evidence here",
            "gold_readiness": gold, "gold_criterion_outcomes": {"c1": "met" if gold == "READY_FOR_HUMAN_REVIEW" else "missing"},
            "retrieval_keywords": [], "categories": [], "source_type": "test"}


def _fake_result(case_id, gold):
    status = "met" if gold == "READY_FOR_HUMAN_REVIEW" else "missing"
    excerpts = ["evidence here"] if status == "met" else []
    return ReviewResult(review_id="r1", case_id=case_id, policy_id="P1",
                        policy_version="v1", policy_version_current=True,
                        readiness=gold,
                        criterion_results=[CriterionResult(criterion_id="c1", status=status,
                                                           evidence_excerpts=excerpts)],
                        latency_ms=100.0, cost_usd_estimated=0.01,
                        adk_tools_invoked=["search_policy_chunks"],
                        adk_session_id="session-test")


def test_eval_continues_after_429_and_writes_partial_denominators(tmp_path):
    attempts = {}

    def fake_runner(case, policy, chunks, config=None, budget=None, verify_citations=True):
        attempts[case.case_id] = attempts.get(case.case_id, 0) + 1
        if case.case_id == "A" and attempts[case.case_id] == 1:
            raise _ResourceExhausted("429 RESOURCE_EXHAUSTED")
        if case.case_id == "C":
            raise _ResourceExhausted("429 RESOURCE_EXHAUSTED")
        gold = {"A": "READY_FOR_HUMAN_REVIEW", "B": "NOT_READY"}[case.case_id]
        return _fake_result(case.case_id, gold)

    cases = [_raw_case("A", "READY_FOR_HUMAN_REVIEW"),
             _raw_case("B", "NOT_READY"),
             _raw_case("C", "NOT_READY")]
    sleeps = []
    out = tmp_path / "results_real.json"
    report = evaluate_real.run_eval(cases, {"P1": object()}, [], CloudConfig(),
                                    BudgetTracker(budget_usd=8.0),
                                    runner=fake_runner, sleep_fn=sleeps.append,
                                    case_delay_seconds=0, out_path=out)
    # A retried once and succeeded, B succeeded, C failed after retries.
    assert attempts == {"A": 2, "B": 1, "C": 4}
    assert report["cases_attempted"] == 3
    assert report["cases_completed"] == 2
    assert report["cases_not_completed"] == 1
    assert [r["case_id"] for r in report["rows"]] == ["A", "B"]
    assert report["not_completed_cases"][0]["case_id"] == "C"
    assert report["not_completed_cases"][0]["reason"] == "rate_limit_429_after_bounded_retry"
    # Metrics are over completed cases only, never over attempted ones.
    assert report["metrics"]["n_cases"] == 2
    assert report["metrics"]["case_correct"] == 2
    assert out.exists()
    assert json.loads(out.read_text())["cases_not_completed"] == 1


def test_baseline_retries_a_429_and_completes(tmp_path):
    policy = SimpleNamespace(policy_id="P1", title="t",
                             criteria=[SimpleNamespace(criterion_id="c1")])
    calls = {"n": 0}

    def fake_generate(prompt, config, response_schema=None):
        calls["n"] += 1
        if calls["n"] == 1:
            raise _ResourceExhausted("429 RESOURCE_EXHAUSTED")
        return {"text": json.dumps({"readiness": "READY_FOR_HUMAN_REVIEW",
                                     "criterion_outcomes": [{"criterion_id": "c1", "status": "met",
                                                             "evidence_excerpts": ["evidence here"]}]}),
                "usage": {"prompt_token_count": 10, "candidates_token_count": 5}}

    import baseline

    report = baseline.run_baseline(
        [_raw_case("A", "READY_FOR_HUMAN_REVIEW")], {"P1": policy}, [],
        CloudConfig(), BudgetTracker(budget_usd=8.0),
        generate_fn=fake_generate,
        retrieve_fn=lambda case, pol, chunks, cfg: ([], "test"),
        sleep_fn=lambda s: None, case_delay_seconds=0,
        out_path=tmp_path / "results_baseline.json")
    assert calls["n"] == 2
    assert report["cases_completed"] == 1
    assert report["cases_not_completed"] == 0
    assert report["rows"][0]["readiness"] == "READY_FOR_HUMAN_REVIEW"


class _FakeQueryJob:
    def __init__(self, rows):
        self._rows = rows

    def result(self):
        return self._rows


class _FakeBigQueryClient:
    """Stub BigQuery client whose stored rows persist across loads."""

    def __init__(self):
        self.stored = {"policies": [], "criteria": [], "policy_chunks": [], "cases": []}
        self.insert_calls = []

    def query(self, sql):
        for table in self.stored:
            if f".{table}" in sql:
                return _FakeQueryJob(list(self.stored[table]))
        raise AssertionError(f"unexpected query: {sql}")

    def insert_rows_json(self, table, rows):
        name = table.split(".")[-1]
        self.stored[name].extend(rows)
        self.insert_calls.append((name, len(rows)))
        return []


def test_second_load_does_not_duplicate_rows():
    import load_to_bigquery

    client = _FakeBigQueryClient()
    assert load_to_bigquery.main(client) == 0
    first = {t: len(rows) for t, rows in client.stored.items()}
    assert first == {"policies": 3, "criteria": 20, "policy_chunks": 7, "cases": 30}
    assert load_to_bigquery.main(client) == 0
    second = {t: len(rows) for t, rows in client.stored.items()}
    # A rerun must not duplicate the 2026-10-27 failure mode:
    # policies 6 and policy_chunks 14 after two loads.
    assert second == first
    assert sum(n for _, n in client.insert_calls) == 60


def test_schema_cases_table_includes_source_type():
    schema = (Path(__file__).resolve().parents[1] / "gcp" / "sql" / "schema.sql").read_text()
    cases_block = schema.split("priorauth_agent.cases")[1].split("CREATE TABLE")[0]
    assert "source_type STRING" in cases_block
