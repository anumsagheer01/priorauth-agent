"""API real-mode tests, deterministic by design.

2026-10-27 audit fix: the old tests asserted credentials_present is
False and POST /reviews returns 503 unconditionally. In credentialed
Cloud Shell those assertions failed (200 instead of 503), because the
code path is decided by whether google.auth.default() succeeds in the
process running pytest, not by anything the test set up. These tests
now mock the exact call sites, so they mean the same thing locally
and in Cloud Shell, with no model call.

See also tests/test_adk_no_credentials.py (skip-when-credentialed
pattern, kept for the ADK path) and tests/test_api_credentialed.py
(opt-in only, for the real credentialed path).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from fastapi.testclient import TestClient

import priorauth.adk_agent as adk_agent
import priorauth.api as api_module
from priorauth.api import app
from priorauth.cloud_clients import CloudNotConfigured

client = TestClient(app)


def test_health_reports_real_mode_and_no_credentials_locally(monkeypatch):
    """GET /health reports the mocked adk_available() result verbatim."""
    monkeypatch.setattr(api_module, "adk_available", lambda: {
        "adk_available": True, "credentials_present": False,
        "model": "gemini-3.5-flash", "embedding_model": "text-embedding-004",
    })
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["mode"] == "real_adk_pipeline"
    assert body["credentials_present"] is False


def test_review_without_credentials_fails_clearly_not_mocked(monkeypatch):
    """POST /reviews maps a mocked CloudNotConfigured to 503, no mock result returned."""
    def _raise(*args, **kwargs):
        raise CloudNotConfigured("No GCP credentials: run in Cloud Shell after signing in.")
    monkeypatch.setattr(adk_agent, "run_via_adk", _raise)
    payload = {"case_id": "TEST-001", "procedure": "lumbar_mri", "policy_id": "AETNA_CPB_0236",
               "policy_version": "2026", "diagnosis_codes": ["M54.16"], "procedure_code": "72148",
               "patient_age": 45, "clinical_note": "Test note only."}
    resp = client.post("/reviews", json=payload)
    assert resp.status_code == 503
    assert "credentials" in resp.text.lower()
