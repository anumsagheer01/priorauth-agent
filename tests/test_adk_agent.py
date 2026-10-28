import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import inspect

from priorauth.adk_agent import adk_available, build_agent, build_agent_for_run, run_via_adk, _RunContext
from priorauth.cloud_clients import CloudConfig, require_model
from priorauth.models import ClinicalCase
from priorauth.policies import load_policies


def _sample():
    policies = {p.policy_id: p for p in load_policies()}
    policy = policies["AETNA_CPB_0236"]
    case = ClinicalCase(case_id="TEST-ADK-001", procedure=policy.procedure, policy_id=policy.policy_id,
                        policy_version=policy.current_version, diagnosis_codes=["M54.16"],
                        procedure_code="72148", patient_age=45, clinical_note="Test note only.")
    return case, policy


def test_build_agent_has_model_and_tools(monkeypatch):
    # No model default: the verified pair must be set explicitly.
    monkeypatch.setenv("PRIORAUTH_MODEL", "gemini-3.5-flash")
    monkeypatch.setenv("PRIORAUTH_MODEL_LOCATION", "global")
    agent = build_agent()
    assert agent.name == "priorauth_agent"
    # ADK 2.13.0: model is a Gemini object, not a bare string. The
    # backend is Vertex because client_kwargs sets vertexai=True.
    # This test checks wiring, not availability. Historical note:
    # gemini-3.8-flash returned 404 in us-central1 on 2026-10-27,
    # so no test here may present it as verified or as a default.
    model = agent.model
    model_name = getattr(model, "model", None) or str(model)
    assert model_name == "gemini-3.5-flash", f"Unexpected ADK model: {model_name!r}"
    client_kwargs = getattr(model, "client_kwargs", None) or {}
    assert client_kwargs.get("vertexai") is True
    assert client_kwargs.get("project") == "delivery-experience-511901"
    # Model endpoint, not data location: the ADK Gemini client must
    # use config.model_location ("global" for the verified pair),
    # never the us-central1 data location, where the 3.5 and 3.8
    # Flash models historically 404'd.
    assert client_kwargs.get("location") == "global"
    assert client_kwargs.get("location") == CloudConfig().model_location


def test_model_name_is_configurable_in_one_place(monkeypatch):
    # PRIORAUTH_MODEL is the single configuration point, read in
    # CloudConfig. Setting it must change the config and the ADK
    # agent model, with no model call and no file edit.
    monkeypatch.setenv("PRIORAUTH_MODEL", "test-model-from-env-only")
    monkeypatch.setenv("PRIORAUTH_MODEL_LOCATION", "global")
    config = CloudConfig()
    assert config.model == "test-model-from-env-only"
    agent = build_agent(config=config)
    model_name = getattr(agent.model, "model", None) or str(agent.model)
    assert model_name == "test-model-from-env-only"


def test_build_agent_for_run_registers_three_tools(monkeypatch):
    monkeypatch.setenv("PRIORAUTH_MODEL", "gemini-3.5-flash")
    monkeypatch.setenv("PRIORAUTH_MODEL_LOCATION", "global")
    case, policy = _sample()
    ctx = _RunContext(case=case, policy=policy, chunks=[], config=CloudConfig())
    agent = build_agent_for_run(ctx)
    names = [t.name for t in agent.tools]
    assert names == ["search_policy_chunks", "validate_case_codes", "extract_evidence"], names


def test_pipeline_entry_point_routes_through_adk_runner():
    # Static proof, no model call: run_via_adk must call
    # run_via_adk_async, which must call Runner.run_async. Check
    # source, not a mocked run, because no credentials exist locally.
    source = inspect.getsource(run_via_adk)
    assert "run_via_adk_async" in source
    async_source = inspect.getsource(__import__("priorauth.adk_agent", fromlist=["run_via_adk_async"]).run_via_adk_async)
    assert "runner.run_async" in async_source
    assert "create_session" in async_source
    assert "get_function_calls" in async_source
    assert "get_function_responses" in async_source
    # Old flaw must be gone: run_via_adk must not call run_real_review
    # directly as its execution path.
    assert "run_real_review" not in async_source


def test_adk_available_reports_facts_not_secrets():
    info = adk_available()
    assert info["adk_available"] is True
    assert "credentials_present" in info
    assert "token" not in str(info).lower()


# NOTE: the no-credentials test was moved, not deleted, to
# tests/test_adk_no_credentials.py. It must not run in the cloud
# gate, because in credentialed Cloud Shell it would make a real
# Vertex call instead of failing with CloudNotConfigured, and
# set -euo pipefail
# would stop the script before any eval. See that file for the
# explicit skip mechanism and the local-only run command.
