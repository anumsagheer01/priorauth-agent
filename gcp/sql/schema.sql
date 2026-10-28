-- BigQuery schema, project delivery-experience-511901, dataset priorauth_agent.
-- Run in Cloud Shell only, after the user approves the consolidated estimate.
CREATE SCHEMA IF NOT EXISTS `delivery-experience-511901.priorauth_agent`;

CREATE TABLE IF NOT EXISTS `delivery-experience-511901.priorauth_agent.policies` (
  policy_id STRING NOT NULL,
  title STRING,
  payer STRING,
  procedure STRING,
  source_url STRING,
  retrieval_date DATE,
  current_version STRING
);

CREATE TABLE IF NOT EXISTS `delivery-experience-511901.priorauth_agent.policy_chunks` (
  chunk_id STRING NOT NULL,
  policy_id STRING,
  policy_version STRING,
  section STRING,
  text STRING,
  source_url STRING,
  embedding ARRAY<FLOAT64>
);

CREATE TABLE IF NOT EXISTS `delivery-experience-511901.priorauth_agent.criteria` (
  criterion_id STRING NOT NULL,
  policy_id STRING,
  text STRING,
  section STRING,
  kind STRING
);

CREATE TABLE IF NOT EXISTS `delivery-experience-511901.priorauth_agent.cases` (
  case_id STRING NOT NULL,
  procedure STRING,
  policy_id STRING,
  policy_version STRING,
  diagnosis_codes ARRAY<STRING>,
  procedure_code STRING,
  clinical_note STRING,
  gold_readiness STRING,
  -- Added 2026-10-27 after a Cloud Shell load failed with
  -- "no such field source_type": load_to_bigquery.py inserts
  -- source_type for every case, so the schema must define it.
  -- The column was previously added in Cloud Shell only; it
  -- now agrees with the loader in this repo, so a fresh
  -- dataset creation does not repeat that failure.
  source_type STRING
);

CREATE TABLE IF NOT EXISTS `delivery-experience-511901.priorauth_agent.reviews` (
  review_id STRING NOT NULL,
  case_id STRING,
  policy_id STRING,
  policy_version STRING,
  readiness STRING,
  engine_version STRING,
  created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `delivery-experience-511901.priorauth_agent.audit_log` (
  case_id STRING,
  policy_id STRING,
  policy_version STRING,
  readiness STRING,
  engine_version STRING,
  created_at TIMESTAMP
);

-- VECTOR_SEARCH notes: policy_chunks.embedding is an ARRAY<FLOAT64>
-- placeholder for a future Vertex embedding load. In BigQuery, use a
-- native VECTOR column type at load time if your region supports it,
-- and use VECTOR_SEARCH over that column. Local mode does not use
-- VECTOR_SEARCH; it uses deterministic keyword search in tools.py.
-- Example, to run only after embeddings are loaded:
-- SELECT chunk_id FROM VECTOR_SEARCH(
--   TABLE `delivery-experience-511901.priorauth_agent.policy_chunks`,
--   'embedding', (SELECT embedding FROM `delivery-experience-511901.priorauth_agent.policy_chunks` LIMIT 1),
--   top_k => 5);
