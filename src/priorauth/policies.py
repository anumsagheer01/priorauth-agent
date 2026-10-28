"""Load and validate policy data from data/policies.json."""

from __future__ import annotations

import json
from pathlib import Path

from priorauth.models import Policy

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def load_policies(data_dir: str | Path | None = None) -> list[Policy]:
    """Load policies.json and validate every policy with Pydantic."""
    path = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
    path = path / "policies.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    policies = raw["policies"] if isinstance(raw, dict) else raw
    return [Policy.model_validate(item) for item in policies]


def get_policy(policies: list[Policy], policy_id: str) -> Policy | None:
    for policy in policies:
        if policy.policy_id == policy_id:
            return policy
    return None


def load_chunks(data_dir: str | Path | None = None) -> list[dict]:
    path = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
    path = path / "policy_chunks.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    return raw["chunks"] if isinstance(raw, dict) else raw


def load_cases(data_dir: str | Path | None = None) -> list[dict]:
    """Load guardrail cases. These are synthetic and are NOT model eval."""
    path = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
    path = path / "guardrail_cases.json"
    if not path.exists():
        path = path.parent / "cases.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    return raw["cases"] if isinstance(raw, dict) else raw


def load_guardrail_cases(data_dir: str | Path | None = None) -> list[dict]:
    return load_cases(data_dir)


def load_eval_cases(data_dir: str | Path | None = None) -> list[dict]:
    """Load the real-text model evaluation set. Annotated before any model run."""
    path = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
    path = path / "eval_cases.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    return raw["cases"] if isinstance(raw, dict) else raw
