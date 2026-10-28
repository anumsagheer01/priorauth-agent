"""FastAPI app for PriorAuth Agent, real pipeline mode.

Endpoints: GET /health, GET /policies, GET /policies/{policy_id},
GET /eval-cases, POST /reviews, GET /reviews/{review_id}.
POST /reviews runs the real ADK pipeline (adk_agent.run_via_adk).
If GCP credentials are absent it returns 503 with a clear message:
run in Cloud Shell after signing in and clicking Authorize. It never
falls back to a mock, and it never approves, denies, or submits a
prior authorization. Reviews are stored in memory only.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from priorauth.adk_agent import adk_available
from priorauth.cloud_clients import CloudNotConfigured
from priorauth.models import ClinicalCase, ReviewResult
from priorauth.policies import get_policy, load_chunks, load_eval_cases, load_policies

app = FastAPI(title="PriorAuth Agent", version="2.0.0-real")
_POLICIES = load_policies()
_CHUNKS = load_chunks()
_REVIEWS: dict[str, ReviewResult] = {}


class HealthResponse(BaseModel):
    status: str
    mode: str
    engine_version: str
    adk_available: bool
    credentials_present: bool
    model: str
    embedding_model: str


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    info = adk_available()
    return HealthResponse(status="ok", mode="real_adk_pipeline", engine_version="2.0.0-real",
                          adk_available=info["adk_available"], credentials_present=info["credentials_present"],
                          model=info["model"], embedding_model=info["embedding_model"])


@app.get("/policies")
def list_policies() -> list[dict]:
    return [p.model_dump() for p in _POLICIES]


@app.get("/policies/{policy_id}")
def get_policy_endpoint(policy_id: str) -> dict:
    policy = get_policy(_POLICIES, policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail=f"Unknown policy: {policy_id}")
    return policy.model_dump()


@app.get("/eval-cases")
def list_eval_cases() -> list[dict]:
    return load_eval_cases()


@app.post("/reviews", response_model=ReviewResult)
def create_review(case: ClinicalCase) -> ReviewResult:
    from priorauth.adk_agent import run_via_adk

    policy = get_policy(_POLICIES, case.policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail=f"Unknown policy: {case.policy_id}")
    if case.procedure != policy.procedure:
        raise HTTPException(status_code=400,
            detail=f"Procedure {case.procedure} does not match policy procedure {policy.procedure}.")
    try:
        result = run_via_adk(case, policy, _CHUNKS)
    except CloudNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    _REVIEWS[result.review_id] = result
    return result


@app.get("/reviews/{review_id}", response_model=ReviewResult)
def get_review(review_id: str) -> ReviewResult:
    result = _REVIEWS.get(review_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Unknown review: {review_id}")
    return result
