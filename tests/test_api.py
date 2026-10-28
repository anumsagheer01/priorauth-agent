"""API tests for the real pipeline API. Deterministic by design.

2026-10-27 audit fix: the old test_post_review_without_credentials_is_503
asserted an environment property (this machine has no ADC credentials)
as if it were a code property. In credentialed Cloud Shell it therefore
failed with 200 instead of 503, contributing to the cloud gate result
43 passed / 3 failed / 1 skipped. These tests now mock the exact call
site, so they pass or fail for the same reason in every environment,
with no model call and no dependence on ADC.

The credentialed path is tested separately in
tests/test_api_credentialed.py, which skips unless explicitly opted in.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from fastapi.testclient import TestClient

import priorauth.adk_agent as adk_agent
from priorauth.api import app
from priorauth.cloud_clients import CloudNotConfigured

client = TestClient(app)


def test_health():
    body = client.get("/health").json()
    assert body["mode"] == "real_adk_pipeline"
    assert body["engine_version"] == "2.0.0-real"


def test_policies_and_eval_case_endpoints():
    assert len(client.get("/policies").json()) == 3
    assert client.get("/policies/AETNA_CPB_0236").status_code == 200
    assert client.get("/policies/UNKNOWN").status_code == 404
    cases = client.get("/eval-cases").json()
    assert len(cases) == 30
    assert cases[0]["case_id"].startswith("EVAL-")


def test_post_review_without_credentials_is_503(monkeypatch):
    """POST /reviews maps CloudNotConfigured to 503, mocked, no ADC dependence."""
    def _raise(*args, **kwargs):
        raise CloudNotConfigured("No GCP credentials: run in Cloud Shell after signing in.")
    monkeypatch.setattr(adk_agent, "run_via_adk", _raise)
    payload = {"case_id": "TEST-001", "procedure": "lumbar_mri", "policy_id": "AETNA_CPB_0236",
               "policy_version": "2026", "diagnosis_codes": ["M54.16"], "procedure_code": "72148",
               "patient_age": 45, "clinical_note": "Test note only."}
    resp = client.post("/reviews", json=payload)
    assert resp.status_code == 503
    assert "credentials" in resp.text.lower()
