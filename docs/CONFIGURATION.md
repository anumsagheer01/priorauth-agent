# Configuration, verified end to end (issue-3 fix, 2026-10-27)

## Required environment variables for any cloud rerun

There is no model default in code. If either of the first two
variables is unset, `require_model()` in
`src/priorauth/cloud_clients.py` raises before any Gemini call,
and the cloud scripts (`gcp/cloud_step2_load_and_eval.sh`,
`gcp/deploy_cloudrun.sh`) refuse to run.

| Variable | Required value for a rerun | Read by |
| --- | --- | --- |
| `PRIORAUTH_MODEL` | `gemini-3.5-flash` (verified 2026-10-27; re-verify with a minimal live call first) | `CloudConfig.model` |
| `PRIORAUTH_MODEL_LOCATION` | `global` (verified endpoint for the pair above) | `CloudConfig.model_location`, ADK Gemini client and `gemini_generate` only |
| `GOOGLE_CLOUD_PROJECT` | `delivery-experience-511901` | `CloudConfig.project` |
| `PRIORAUTH_DATA_LOCATION` | `us-central1` | `CloudConfig.location`, BigQuery and embeddings only |
| `PRIORAUTH_DATASET` | `priorauth_agent` | `CloudConfig.dataset`, BigQuery table names |
| `PRIORAUTH_EMBEDDING_MODEL` | `text-embedding-004` (dimension 768, verified) | `CloudConfig.embedding_model` |

Optional, with the defaults the code actually uses:
`GOOGLE_CLOUD_LOCATION` (fallback for data location only, default
`us-central1`), `PRIORAUTH_INPUT_PRICE_PER_MILLION` (default
0.75), `PRIORAUTH_OUTPUT_PRICE_PER_MILLION` (default 3.75),
`PRIORAUTH_BUDGET_USD` (default 8.0, the eval stop rule),
`PRIORAUTH_API_URL` (Streamlit only, FastAPI backend URL).

## Variables that are NOT read by the runtime code

`PRIORAUTH_PROJECT`, `PRIORAUTH_LOCATION`, and
`BIGQUERY_DATASET` are not read by `CloudConfig` or by the
FastAPI app. They were removed from
`gcp/cloud_step2_load_and_eval.sh` in the issue-3 fix, and
`gcp/deploy_cloudrun.sh` already documented their removal.
Do not set them expecting an effect; set the variables in
the table above instead.

## Cross-file verification, issue-3 fix

- `.env.example`: matches the table above exactly.
- `gcp/cloudrun.yaml`: service `priorauth-agent-demo`,
  region is set by the deploy command (`us-central1`), port
  8000, env names match `CloudConfig` exactly. This YAML is
  a record, not the deploy path: `gcp/deploy_cloudrun.sh`
  deploys with `--source .` and its own `--set-env-vars`,
  which take precedence. Keep service name, region, port,
  and env names identical in both files.
- `gcp/deploy_cloudrun.sh`: requires `PRIORAUTH_MODEL` and
  `PRIORAUTH_MODEL_LOCATION` to be set, deploys FastAPI only
  on port 8000, memory 1Gi, max 1 instance, with the env
  names in the table above. Deployment FAILED on 2026-10-27
  on IAM permissions; no URL, screenshot, or deployed review
  exists, and no IAM change was made in this fix.
- `gcp/cloud_step2_load_and_eval.sh`: requires
  `PRIORAUTH_MODEL` and `PRIORAUTH_MODEL_LOCATION` to be
  set, sets data location to `us-central1` and dataset to
  `priorauth_agent`, verifies the embedding model before
  indexing, and runs the eval, baseline, and ablation.
  Its example model comment was corrected from
  gemini-3.5-flash-lite to the verified gemini-3.5-flash
  at global.
- `Dockerfile`: FastAPI only on port 8000, installs both
  `requirements.txt` and `requirements-cloud.txt`, copies
  `src`, `data`, and `app`, sets `PYTHONPATH=/app/src`.
  Streamlit is not started by this container; run it
  separately with `PRIORAUTH_API_URL` set to the service URL.
- `src/priorauth/cloud_clients.py`: model and model
  location have no default (empty string means unset);
  `require_model()` raises if either is unset.
  `gemini_generate` calls `require_model()` before any
  Vertex call. Embeddings always use the data location,
  never the model location. Historical note:
  gemini-3.8-flash returned 404 in us-central1 for this
  project on 2026-10-27 and is not a default anywhere
  in the current code.

## Final verified results (for reference, not configuration)

Full system, 30/30 cases, gemini-3.5-flash at global, data
us-central1: criterion 171/200, case readiness 28/30,
false-ready 0/25, missing-evidence recall 12/14, citation
89/89, latency p50 28.8 s, p95 62.2 s, cost $0.0784
(script estimate). Original as-run baseline, 30/30,
SUPERSEDED BY CORRECTED BASELINE RERUN 2026-10-27 (prompt flaw found in the audit):
criterion 14/200, case 13/30, false-ready 11/25. No-citation
ablation, 30/30: criterion 173/200, case 28/30, delta
criterion -0.01; citation verification did NOT
demonstrably help on this set. Pilot, n=3 only, is not
full performance. Deployment FAILED on IAM. Cap restored
to $10; console delta about $4.29 vs script estimate
about $0.22, gap unresolved. The original 60/60 result is
a templated guardrail test, never model performance.


## Addendum: corrected baseline rerun, 2026-10-27

Any "SUPERSEDED PENDING RERUN" label in this document is superseded by
the corrected baseline rerun on 2026-10-27: criterion 176/200, case
8/30, false-ready 18/25, missing recall 13/14, latency p50 10.9 s,
p95 14.5 s, cost $0.0463. The original baseline (14/200, 13/30, 11/25)
remains superseded history only. The corrected baseline raw JSON file IS now included locally, unchanged, in the GitHub pack at evidence/cloud_eval_2026-10-27/raw/results_baseline_corrected.json (116,872 bytes, SHA-256 ed13f335aff8b1452a8419b39b33e1fa63e35a31710f18d115caff1d60986ff9); see corrected_baseline_summary_2026-10-27.md.
