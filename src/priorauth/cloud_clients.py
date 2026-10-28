"""Real Google Cloud clients. No mocks, no fallbacks that pretend to be cloud.

If credentials are absent, every function here raises
CloudNotConfigured with a clear message about Cloud Shell sign-in,
instead of returning a fake embedding, a fake model response, or a
precomputed result. That failure is the correct behavior in a local
environment without GCP credentials, and it is tested in
tests/test_cloud_config.py.

There is NO model default in this module, by design. The model
name comes only from the PRIORAUTH_MODEL environment variable,
and the model endpoint only from PRIORAUTH_MODEL_LOCATION, both
read in CloudConfig below. If either is unset, CloudConfig
records an empty string for it, and require_model() raises
before any Gemini call is made, so no call can silently run
an unverified model. Historical note, clearly labeled: on
2026-10-27 gemini-3.8-flash returned 404 NOT_FOUND for
projects/delivery-experience-511901/locations/us-central1/
publishers/google/models/gemini-3.8-flash in Cloud Shell, so
0 of 30 eval cases ran under that name. The verified pair for
the 2026-10-27 cloud eval was gemini-3.5-flash at global, data
us-central1 (see docs/EVAL_RESULTS_2026-10-27.md). That pair
must be re-verified with a minimal live call before any rerun;
it is not a code default. The cloud scripts refuse to run
without PRIORAUTH_MODEL and PRIORAUTH_MODEL_LOCATION set.
The actual model used is recorded in every eval output.

Model endpoint is separate from data location, fixed 2026-10-27:
- Data location is CloudConfig.location, default us-central1.
  BigQuery dataset priorauth_agent and embeddings use it, and
  it does not change when the model endpoint changes.
- Model location is CloudConfig.model_location, from
  PRIORAUTH_MODEL_LOCATION only, with no default. It is used
  only for Gemini generation calls: the ADK Gemini client_kwargs
  location in adk_agent.py and the Vertex init inside
  gemini_generate here. It is never used for BigQuery.
- The verified model endpoint for the 2026-10-27 cloud eval
  was "global" for gemini-3.5-flash, because official
  documentation lists gemini-3.5-flash as supported on global
  and us, not us-central1. Historical note: gemini-3.5-flash
  at us-central1 already returned 404 on 2026-10-27, as did
  gemini-3.8-flash and gemini-3.5-flash-lite in us-central1.
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass, field

# No model default exists. VERIFIED_MODEL_2026_10_27 is a
# documentation constant only: the pair verified by a live
# Cloud Shell call on 2026-10-27. It is NEVER used as a
# fallback. Code must set PRIORAUTH_MODEL explicitly.
VERIFIED_MODEL_2026_10_27 = "gemini-3.5-flash"
VERIFIED_MODEL_LOCATION_2026_10_27 = "global"


class CloudNotConfigured(Exception):
    """Raised when GCP credentials or a required library are absent."""


@dataclass
class CloudConfig:
    project: str = os.environ.get("GOOGLE_CLOUD_PROJECT", "delivery-experience-511901")
    # Data location only: BigQuery dataset and embeddings. Default
    # us-central1, from PRIORAUTH_DATA_LOCATION if set, else
    # GOOGLE_CLOUD_LOCATION for backward compatibility. Changing
    # the model endpoint must never change this field.
    location: str = field(default_factory=lambda: os.environ.get(
        "PRIORAUTH_DATA_LOCATION",
        os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")))
    # Model endpoint only: Gemini generation calls. No default:
    # an empty string means "not set", and require_model()
    # raises before any Gemini call. The verified endpoint for
    # the 2026-10-27 cloud eval was "global" for
    # gemini-3.5-flash; re-verify before any rerun.
    model_location: str = field(default_factory=lambda: os.environ.get("PRIORAUTH_MODEL_LOCATION", ""))
    # default_factory, not a class-time os.environ.get, so that
    # setting PRIORAUTH_MODEL in the environment before constructing
    # a config actually changes the model. This is the single place
    # where the model name is chosen. There is no fallback: an
    # empty string means "not set", and require_model() raises.
    model: str = field(default_factory=lambda: os.environ.get("PRIORAUTH_MODEL", ""))
    embedding_model: str = field(default_factory=lambda: os.environ.get("PRIORAUTH_EMBEDDING_MODEL", "text-embedding-004"))
    dataset: str = os.environ.get("PRIORAUTH_DATASET", "priorauth_agent")
    input_price_per_million: float = float(os.environ.get("PRIORAUTH_INPUT_PRICE_PER_MILLION", "0.75"))
    output_price_per_million: float = float(os.environ.get("PRIORAUTH_OUTPUT_PRICE_PER_MILLION", "3.75"))
    budget_usd: float = float(os.environ.get("PRIORAUTH_BUDGET_USD", "8.0"))


def require_model(config: CloudConfig) -> None:
    """Fail fast if the model pair was not set explicitly.

    Raises RuntimeError if PRIORAUTH_MODEL or
    PRIORAUTH_MODEL_LOCATION was not set. This is what
    prevents a silent run against an unverified model: an
    empty model or endpoint is never passed to Gemini or ADK.
    The verified pair for the 2026-10-27 cloud eval was
    gemini-3.5-flash at global, data us-central1; re-verify
    it with a minimal live call before any rerun.
    """
    if not config.model or not config.model_location:
        raise RuntimeError(
            "PRIORAUTH_MODEL and PRIORAUTH_MODEL_LOCATION must both be "
            "set explicitly before any Gemini call. There is no model "
            "default. The verified pair for the 2026-10-27 cloud eval "
            "was PRIORAUTH_MODEL=gemini-3.5-flash and "
            "PRIORAUTH_MODEL_LOCATION=global (data us-central1); "
            "re-verify that pair with a minimal live call before "
            "any rerun."
        )


def check_credentials() -> dict:
    """Check Application Default Credentials without printing any secret.

    Returns only booleans and the account/project names that the
    credential library itself reports, never a token or key.
    """
    try:
        import google.auth  # type: ignore
    except Exception as exc:
        raise CloudNotConfigured(f"google-auth is not installed: {exc}") from exc
    try:
        credentials, project = google.auth.default()
    except Exception as exc:
        raise CloudNotConfigured(
            "No Application Default Credentials found. Run in Cloud Shell "
            "after signing in as the account owner and clicking Authorize, "
            "or set GOOGLE_APPLICATION_CREDENTIALS to a service account "
            "file you control. No key should ever be pasted in chat. "
            f"Underlying error: {exc}"
        ) from exc
    return {
        "credentials_present": credentials is not None,
        "adc_project": project or "",
        "service_account_email": getattr(credentials, "service_account_email", "") or "",
    }


def init_vertex(config: CloudConfig, location: str | None = None) -> None:
    """Initialize Vertex AI at one explicit location.

    When location is None, the model endpoint
    (config.model_location) is used, because most callers here
    are Gemini generation calls. Callers for embeddings must
    pass config.location explicitly, so embeddings stay at the
    data location and are never silently moved to global.
    Raises CloudNotConfigured on any failure.
    """
    check_credentials()
    try:
        import vertexai  # type: ignore
    except Exception as exc:
        raise CloudNotConfigured(f"vertexai library is not installed: {exc}") from exc
    init_location = location if location is not None else config.model_location
    try:
        vertexai.init(project=config.project, location=init_location)
    except Exception as exc:
        raise CloudNotConfigured(f"Vertex AI init failed for project {config.project} at {init_location}: {exc}") from exc


def embed_texts(texts: list[str], config: CloudConfig) -> list[list[float]]:
    """Return real Vertex embeddings. No local fallback vector is used here.

    The old embed_text_local_fallback in cloud_adapters.py is retained
    only as a historical, clearly labeled helper and is never called
    by the real pipeline or by eval. Calling this function without
    credentials raises CloudNotConfigured.
    """
    # Embeddings stay at the data location, not the model endpoint.
    init_vertex(config, location=config.location)
    try:
        from vertexai.language_models import TextEmbeddingModel  # type: ignore
    except Exception as exc:
        raise CloudNotConfigured(f"TextEmbeddingModel import failed: {exc}") from exc
    model = TextEmbeddingModel.from_pretrained(config.embedding_model)
    embeddings = model.get_embeddings(texts)
    return [list(e.values) for e in embeddings]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity for real embedding vectors."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


def gemini_generate(prompt: str, config: CloudConfig, response_schema: dict | None = None) -> dict:
    """Call Gemini on Vertex and return text plus actual usage metadata.

    The response_schema, when given, is passed as a JSON schema for
    structured output. The caller validates the returned JSON with
    Pydantic or json parsing and must not trust an unparsed model
    string. Token counts come from response.usage_metadata when
    available, and are recorded verbatim in eval output. Cost is
    estimated from those counts and the configured rates, and is
    labeled estimated, not measured billing, because billing is
    reported separately by Google Cloud. Gemini generation uses
    the model endpoint (config.model_location), not the data
    location, so a model supported only on global or us does
    not fail with a us-central1 404 here.
    """
    require_model(config)
    init_vertex(config, location=config.model_location)
    try:
        from vertexai.generative_models import GenerationConfig, GenerativeModel  # type: ignore
    except Exception as exc:
        raise CloudNotConfigured(f"GenerativeModel import failed: {exc}") from exc
    gen_config = None
    if response_schema is not None:
        gen_config = GenerationConfig(response_mime_type="application/json", response_schema=response_schema)
    model = GenerativeModel(config.model, generation_config=gen_config)
    response = model.generate_content(prompt)
    text = ""
    try:
        text = response.text or ""
    except Exception:
        text = ""
    usage = {}
    try:
        meta = response.usage_metadata
        if meta is not None:
            usage = {
                "prompt_token_count": int(getattr(meta, "prompt_token_count", 0) or 0),
                "candidates_token_count": int(getattr(meta, "candidates_token_count", 0) or 0),
                "total_token_count": int(getattr(meta, "total_token_count", 0) or 0),
            }
    except Exception:
        usage = {}
    return {"text": text, "usage": usage, "model": config.model,
            "model_location": config.model_location, "data_location": config.location}


def bigquery_vector_search(query_embedding: list[float], config: CloudConfig, top_k: int = 5) -> list[dict]:
    """Run BigQuery VECTOR_SEARCH. Raises if the table or credentials are absent.

    This is used only when the priorauth_agent.policy_chunks table has
    been loaded with real embeddings in Cloud Shell. It does not fall
    back to keyword search, and it does not invent chunks.
    """
    check_credentials()
    try:
        from google.cloud import bigquery  # type: ignore
    except Exception as exc:
        raise CloudNotConfigured(f"google-cloud-bigquery is not installed: {exc}") from exc
    client = bigquery.Client(project=config.project, location=config.location)
    query = f"""
    SELECT chunk_id, policy_id, policy_version, section, text, source_url,
           distance
    FROM VECTOR_SEARCH(
      TABLE `{config.project}.{config.dataset}.policy_chunks`,
      'embedding',
      (SELECT @query_embedding AS embedding),
      top_k => @top_k,
      distance_type => 'COSINE'
    )
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter("query_embedding", "FLOAT64", query_embedding),
            bigquery.ScalarQueryParameter("top_k", "INT64", top_k),
        ]
    )
    rows = client.query(query, job_config=job_config).result()
    return [dict(row) for row in rows]


def estimate_cost_usd(usage: dict, config: CloudConfig) -> float:
    """Estimate cost from actual token counts and configured rates."""
    prompt = float(usage.get("prompt_token_count", 0) or 0)
    candidates = float(usage.get("candidates_token_count", 0) or 0)
    return (prompt / 1_000_000.0 * config.input_price_per_million) + (
        candidates / 1_000_000.0 * config.output_price_per_million
    )


@dataclass
class BudgetTracker:
    """Track estimated spend and abort before the ceiling is crossed."""

    budget_usd: float = 8.0
    spent_usd_estimated: float = 0.0
    calls: list[dict] = field(default_factory=list)

    @property
    def spent(self) -> float:
        """Alias used by eval scripts. The authoritative field is
        spent_usd_estimated; this property exists so eval scripts do
        not crash with AttributeError after the first case, a bug
        found in the ADK audit. Do not add a second counter."""
        return float(self.spent_usd_estimated)

    def add(self, cost_usd: float, label: str) -> None:
        self.spent_usd_estimated += float(cost_usd)
        self.calls.append({"label": label, "cost_usd_estimated": float(cost_usd)})
        if self.spent_usd_estimated > self.budget_usd:
            raise RuntimeError(
                f"Budget stop: estimated spend {self.spent_usd_estimated:.4f} USD "
                f"exceeds the {self.budget_usd:.2f} USD stop rule. Aborting before further calls."
            )
