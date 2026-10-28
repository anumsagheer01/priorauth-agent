"""Optional cloud adapters. All imports are optional.

Local tests pass without google-adk, without credentials, and without
any network call. Cloud mode was NOT executed in this environment
(see docs/CLOUD_STATUS.md). Do not claim a cloud call succeeded unless
a real Cloud Shell run with verified credentials has recorded it.

No cloud model default exists. The single configuration point
is PRIORAUTH_MODEL and PRIORAUTH_MODEL_LOCATION, read in
priorauth.cloud_clients.CloudConfig, and both must be set
explicitly; an unset value is an empty string, never a model
name. Historical note, clearly labeled: gemini-3.8-flash
returned 404 NOT_FOUND in us-central1 for this project on
2026-10-27. The verified pair for the 2026-10-27 cloud eval
was gemini-3.5-flash at global, data us-central1.
Superseded for Vertex use: gemini-2.5-flash (Vertex retirement date
October 20, 2026, per the October 2026 search summary recorded in
docs/CLOUD_STATUS.md). The local deterministic engine never depends
on any model.
"""

from __future__ import annotations

from dataclasses import dataclass

from priorauth.cloud_clients import CloudConfig

# No CLOUD_MODEL constant: there is no default model. Callers
# that need a model must read CloudConfig().model, which is
# empty when PRIORAUTH_MODEL was not set explicitly.
SUPERSEDED_MODEL = "gemini-2.5-flash"
VERTEX_RETIREMENT_DATE_25 = "2026-10-20"
PROJECT_ID = "delivery-experience-511901"
BIGQUERY_DATASET = "priorauth_agent"

try:  # Optional dependency, listed only in requirements-cloud.txt.
    import google.adk  # type: ignore  # noqa: F401
    HAS_ADK = True
except Exception:  # ImportError or any environment import failure.
    HAS_ADK = False


@dataclass
class CloudStatus:
    adk_available: bool
    model: str
    executed: bool = False
    mode: str = "local"

    def describe(self) -> str:
        if not self.executed:
            return (
                f"Cloud mode not executed. Local mode is active. "
                f"Configured cloud model is {self.model}. "
                f"ADK import available: {self.adk_available}."
            )
        return f"Cloud mode executed with model {self.model}."


def get_cloud_status() -> CloudStatus:
    """Return cloud availability without making any cloud call."""
    return CloudStatus(adk_available=HAS_ADK, model=CloudConfig().model, executed=False, mode="local")


def embed_text_local_fallback(text: str) -> list[float]:
    """Deterministic local fallback embedding, not a Vertex embedding.

    Returns a small normalized vector derived from character counts so
    local code paths that expect a vector can run without credentials.
    It is labeled as a fallback everywhere it is used and is never
    presented as a Vertex AI embedding.
    """
    import math

    vector = [0.0] * 16
    for char in text.lower():
        vector[ord(char) % 16] += 1.0
    norm = math.sqrt(sum(v * v for v in vector)) or 1.0
    return [v / norm for v in vector]


def bigquery_vector_search_sql(
    dataset: str = BIGQUERY_DATASET, project: str = PROJECT_ID
) -> str:
    """Return the VECTOR_SEARCH SQL text for later Cloud Shell use.

    This function only returns SQL text. It does not run a query.
    """
    return f"""-- BigQuery VECTOR_SEARCH example, to run in Cloud Shell only.
-- Dataset: {project}.{dataset}
SELECT base.chunk_id, base.policy_id, base.section
FROM VECTOR_SEARCH(
  TABLE `{project}.{dataset}.policy_chunks`,
  'embedding',
  (SELECT embedding FROM `{project}.{dataset}.policy_chunks` LIMIT 1),
  top_k => 5
);
"""
