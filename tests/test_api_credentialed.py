"""Credentialed API integration tests. Opt-in only, never in the default gate.

These tests make a real Vertex call, so they must NOT run by default
and must NOT run in the cloud test gate. They skip unless BOTH:
- PRIORAUTH_RUN_CREDENTIALED_TESTS=1, and
- adk_available()["credentials_present"] is True.

They also require PRIORAUTH_MODEL and PRIORAUTH_MODEL_LOCATION to be
set to a Cloud Shell-verified pair (verified 2026-10-27:
gemini-3.5-flash at global, data us-central1). They never use the
a model default, which does not exist. If those conditions are not met,
the test skips with a clear reason instead of failing or calling a
wrong model.
"""
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest
from fastapi.testclient import TestClient

from priorauth.adk_agent import adk_available
from priorauth.api import app

client = TestClient(app)


def _credentialed_or_skip():
    if os.environ.get("PRIORAUTH_RUN_CREDENTIALED_TESTS") != "1":
        pytest.skip("Credentialed test: set PRIORAUTH_RUN_CREDENTIALED_TESTS=1 to run.")
    if not adk_available()["credentials_present"]:
        pytest.skip("Credentialed test: no GCP credentials present.")
    if not os.environ.get("PRIORAUTH_MODEL") or not os.environ.get("PRIORAUTH_MODEL_LOCATION"):
        pytest.skip("Credentialed test: set PRIORAUTH_MODEL and PRIORAUTH_MODEL_LOCATION to a verified pair.")


def test_health_reports_credentials_present_when_credentialed():
    _credentialed_or_skip()
    body = client.get("/health").json()
    assert body["mode"] == "real_adk_pipeline"
    assert body["credentials_present"] is True
