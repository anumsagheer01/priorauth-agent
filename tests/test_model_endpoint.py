"""Model endpoint is separate from data location. No model call.

PRIORAUTH_MODEL_LOCATION controls only Gemini generation calls:
the ADK Gemini client_kwargs location, and the Vertex init inside
gemini_generate. PRIORAUTH_DATA_LOCATION / GOOGLE_CLOUD_LOCATION
controls BigQuery and embeddings, and stays us-central1 by default.
A test that collapses them would reintroduce the us-central1 404
for gemini-3.5-flash. Historical note: gemini-3.8-flash also
returned 404 in us-central1 on 2026-10-27 and is not a default.
The verified pair is gemini-3.5-flash at global, data us-central1.
"""
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import priorauth.cloud_clients as cc
from priorauth.adk_agent import build_agent, build_gemini_model
from priorauth.cloud_clients import CloudConfig, require_model


def test_model_and_data_locations_can_differ(monkeypatch):
    monkeypatch.setenv("PRIORAUTH_DATA_LOCATION", "us-central1")
    monkeypatch.setenv("PRIORAUTH_MODEL_LOCATION", "global")
    monkeypatch.setenv("PRIORAUTH_MODEL", "gemini-3.5-flash")
    config = CloudConfig()
    assert config.location == "us-central1"
    assert config.model_location == "global"
    assert config.location != config.model_location
    agent = build_agent(config=config)
    client_kwargs = getattr(agent.model, "client_kwargs", None) or {}
    assert client_kwargs.get("location") == "global"
    assert client_kwargs.get("vertexai") is True
    assert client_kwargs.get("project") == "delivery-experience-511901"
    model = build_gemini_model(config)
    assert getattr(model, "model", None) == "gemini-3.5-flash"


def test_no_model_default_requires_explicit_pair(monkeypatch):
    # There is no model or model-location default. Unset values
    # are empty strings, and require_model() must raise before
    # any Gemini call, so no call can silently use an unverified
    # model. This is the regression test for the removed
    # gemini-3.8-flash default.
    monkeypatch.delenv("PRIORAUTH_MODEL", raising=False)
    monkeypatch.delenv("PRIORAUTH_MODEL_LOCATION", raising=False)
    monkeypatch.delenv("PRIORAUTH_DATA_LOCATION", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_LOCATION", raising=False)
    config = CloudConfig()
    assert config.model == ""
    assert config.model_location == ""
    assert config.location == "us-central1"
    import pytest

    with pytest.raises(RuntimeError, match="PRIORAUTH_MODEL"):
        require_model(config)
    with pytest.raises(RuntimeError, match="PRIORAUTH_MODEL"):
        build_gemini_model(config)


def test_explicit_verified_pair_is_accepted(monkeypatch):
    monkeypatch.setenv("PRIORAUTH_MODEL", "gemini-3.5-flash")
    monkeypatch.setenv("PRIORAUTH_MODEL_LOCATION", "global")
    config = CloudConfig()
    assert config.model == "gemini-3.5-flash"
    assert config.model_location == "global"
    require_model(config)


def test_gemini_generate_uses_model_location_and_embeddings_use_data_location(monkeypatch):
    """Route check with stubbed Vertex SDK, no network, no credentials.

    check_credentials is stubbed to present, so the only thing under
    test is which location each caller passes to vertexai.init.
    """
    monkeypatch.setenv("PRIORAUTH_DATA_LOCATION", "us-central1")
    monkeypatch.setenv("PRIORAUTH_MODEL_LOCATION", "global")
    monkeypatch.setenv("PRIORAUTH_MODEL", "gemini-3.5-flash")
    monkeypatch.setattr(cc, "check_credentials", lambda: {"credentials_present": True})

    init_locations = []
    vertexai = types.ModuleType("vertexai")
    vertexai.init = lambda project, location: init_locations.append(location)
    generative = types.ModuleType("vertexai.generative_models")

    class _GenConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class _Response:
        text = "ok"
        usage_metadata = None

    class _GenerativeModel:
        def __init__(self, model, generation_config=None):
            self.model = model

        def generate_content(self, prompt):
            return _Response()

    generative.GenerationConfig = _GenConfig
    generative.GenerativeModel = _GenerativeModel
    language = types.ModuleType("vertexai.language_models")

    class _Embedding:
        def __init__(self, values):
            self.values = values

    class _TextEmbeddingModel:
        @staticmethod
        def from_pretrained(name):
            class _M:
                def get_embeddings(self, texts):
                    return [_Embedding([0.1, 0.2]) for _ in texts]

            return _M()

    language.TextEmbeddingModel = _TextEmbeddingModel
    monkeypatch.setitem(sys.modules, "vertexai", vertexai)
    monkeypatch.setitem(sys.modules, "vertexai.generative_models", generative)
    monkeypatch.setitem(sys.modules, "vertexai.language_models", language)

    config = CloudConfig()
    result = cc.gemini_generate("Say OK.", config)
    assert result["model_location"] == "global"
    assert result["data_location"] == "us-central1"
    assert init_locations[-1] == "global"
    vectors = cc.embed_texts(["probe"], config)
    assert vectors == [[0.1, 0.2]]
    assert init_locations[-1] == "us-central1"
