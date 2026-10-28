"""No-credentials ADK test, local only, NOT part of the cloud gate.

Why this file exists, stated plainly:
On 2026-10-27 the cloud script ran tests/test_adk_agent.py in
credentialed Cloud Shell. The no-credentials test in that file
expects CloudNotConfigured, but with real credentials present it
instead proceeds to a real Vertex call, which then failed with
404 for the unverified model name, and the script stopped under
set -euo pipefail before any eval case ran.

This test is therefore NOT deleted and NOT mocked. It is moved
here, with an explicit environment check, so that:
- Locally, with no credentials, it runs and must pass.
- In Cloud Shell, with credentials, it SKIPS, with a clear reason,
  instead of failing or making a model call as a test.
- The cloud script runs only tests/test_adk_agent.py and
  tests/test_citation_critic.py, never this file.

Run locally (no credentials, no model call):
  PYTHONPATH=src python3 -m pytest tests/test_adk_no_credentials.py -q
Run the cloud gate (credentialed, no model call in tests):
  PYTHONPATH=src python3 -m pytest tests/test_adk_agent.py tests/test_citation_critic.py -q
Do not add this file to gcp/cloud_step2_load_and_eval.sh.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from priorauth.adk_agent import adk_available, run_via_adk
from priorauth.models import ClinicalCase
from priorauth.policies import load_policies


def test_run_via_adk_without_credentials_fails_clearly_not_mocked():
    if adk_available()["credentials_present"]:
        pytest.skip(
            "Credentialed environment: a no-credentials test cannot "
            "pass here, because run_via_adk would make a real Vertex "
            "call instead of raising CloudNotConfigured. This test "
            "is local-only by design; the cloud gate must not run it."
        )
    policies = {p.policy_id: p for p in load_policies()}
    policy = policies["AETNA_CPB_0236"]
    case = ClinicalCase(
        case_id="TEST-ADK-001", procedure=policy.procedure,
        policy_id=policy.policy_id, policy_version=policy.current_version,
        diagnosis_codes=["M54.16"], procedure_code="72148",
        patient_age=45, clinical_note="Test note only.",
    )
    try:
        run_via_adk(case, policy, [])
    except Exception as exc:
        # It must fail with a credentials error, not return a result.
        # The message legitimately says "No mock result is returned",
        # so the check is on the exception type and the credentials
        # wording, not on the absence of the word mock.
        assert type(exc).__name__ == "CloudNotConfigured"
        assert "credentials" in str(exc).lower()
    else:
        raise AssertionError("Expected a credentials failure locally, not a result")
