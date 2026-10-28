## MEASURED CLOUD COSTS, 2026-10-27 (supersedes the modeled plan below as the cost record)

Full system script estimate: $0.0784 total, $0.0026 per case (30 cases). Baseline: $0.0273. No-citation arm: $0.0751. Pilot: $0.0081. Attempt script total about $0.22. Console Vertex delta about $4.29 (about $28.76 to about $33.05), below the $8 stop and $10 ceiling, with the attribution gap UNRESOLVED (console lag and other Vertex usage during the day are possible but unproven). The modeled figures below ($7.11 plan total, $0.00170 per case) were a pre-run modeled plan using superseded pricing assumptions and must NOT be quoted as measured costs.

# Cost estimation, modeled estimates only

All costs here are modeled estimates, not measured costs. No cloud
call was made in this local build, so no measured cloud cost exists
to report. Third-party pricing pages are not official Google pricing.
The consolidated estimate presented to the user must be rechecked
against official Google Cloud pricing at approval time.

## Ceiling and stop rule

- Hard ceiling for PriorAuth: $10 total additional spend.
- Stop rule: stop at $8. Do not exceed $10 under any circumstances.
- Scope: existing project delivery-experience-511901 only, dataset
  priorauth_agent, one metadata bucket, temporary Cloud Run for
  screenshots only, then delete that service.

## Modeled formula, per case, local eval script

Modeled cost per case = (input tokens / 1000 * input rate) +
(output tokens / 1000 * output rate)

Inputs used in scripts/evaluate.py, modeled only:
- Input tokens per case: 1500
- Output tokens per case: 500
- Input rate: $0.00030 per 1000 tokens, modeled input
- Output rate: $0.00250 per 1000 tokens, modeled input
- Result: (1500 / 1000 * 0.00030) + (500 / 1000 * 0.00250) = $0.00170 per case

For 60 cases, modeled model cost = 60 * $0.00170 = $0.102.
For a 200 case cloud eval, modeled model cost = 200 * $0.00170 = $0.34.

## Modeled plan total, inside the ceiling

| Item | Modeled estimate |
| --- | --- |
| Model calls for a 60 case cloud eval | $0.11 |
| BigQuery small synthetic tables, storage and queries | $1.00 |
| GCS metadata bucket, small files | $1.00 |
| Cloud Run temporary deployment, short-lived, screenshots only | $2.00 |
| Buffer for retries and verification | $3.00 |
| Modeled total | $7.11 |

$7.11 is inside the $10 ceiling and under the $8 stop rule only if
actual usage is tracked and work stops at $8. If official pricing at
approval time pushes the modeled total over $10, cut in this order:
first, reduce the cloud eval case count; second, skip the temporary
Cloud Run deployment and use local screenshots only if a verified
browser session is available; third, skip Vertex embeddings and use
local chunk search only. Do not cut the $8 stop rule.

## What is not included

Billing, budget, cap, IAM, and quota changes are not authorized and
are not costed here. Delivery Experience resources are untouched.
No policy PDFs are stored in GCS, only metadata and paraphrased chunks.
