# GCS layout, metadata only

Bucket name used in gcp/setup.sh: priorauth-agent-metadata-511901.
If that name is taken, use a new clear name with the same prefix and
record the actual name in docs/CLOUD_STATUS.md. Do not reuse a
Delivery Experience bucket.

Layout:
- gs://<bucket>/policies/policies.json (structured metadata only)
- gs://<bucket>/policies/policy_chunks.json (paraphrased chunks only)
- gs://<bucket>/cases/cases.json (synthetic cases only, no PHI)
- gs://<bucket>/eval/evaluation.json (eval outputs)

No policy PDFs, no proprietary CPT sets, no real patient data, no
secrets, and no credentials are stored in GCS.
