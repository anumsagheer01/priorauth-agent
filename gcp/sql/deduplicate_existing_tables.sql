-- Deduplicate priorauth_agent tables after the 2026-10-27 rerun.
--
-- What happened: the first load inserted policies (3) and
-- policy_chunks (7), then failed on cases with "no such field
-- source_type". The second load, after that column was added in
-- Cloud Shell only, inserted the same policies and chunks again,
-- leaving policies 6, policy_chunks 14, and criteria 40 (double
-- the 20 in data/policies.json), while cases reached the correct 30.
--
-- Why this file exists, and why it is NOT run automatically:
-- gcp/load_to_bigquery.py is now idempotent: it queries existing
-- primary keys and skips rows already present, so a rerun adds
-- no further duplicates. Idempotency does NOT remove duplicates
-- that are already in the tables. A fresh eval that relies on
-- BigQuery row counts or VECTOR_SEARCH over policy_chunks must
-- therefore clean the existing tables first, in Cloud Shell,
-- and record row counts before and after.
--
-- How to use it, in Cloud Shell only, project
-- delivery-experience-511901, dataset priorauth_agent:
--   1. Record current counts: SELECT COUNT(*) from each table.
--   2. Run the four CREATE OR REPLACE statements below, one at
--      a time, and record the new counts. Expected clean counts
--      from the repo data files: policies 3, criteria 20,
--      policy_chunks 7, cases 30.
--   3. Only then rerun gcp/load_to_bigquery.py, which will now
--      report "inserted 0 rows, skipped N already present" for
--      every table, confirming no new duplicates.
-- If any count after dedup does not match the expected clean
-- count, stop and report the discrepancy; do not run the eval
-- on tables whose contents do not match the repo data files.
-- This file is never run by gcp/cloud_step2_load_and_eval.sh.

CREATE OR REPLACE TABLE `delivery-experience-511901.priorauth_agent.policies` AS
SELECT * EXCEPT (rn) FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY policy_id ORDER BY policy_id) AS rn
  FROM `delivery-experience-511901.priorauth_agent.policies`
) WHERE rn = 1;

CREATE OR REPLACE TABLE `delivery-experience-511901.priorauth_agent.criteria` AS
SELECT * EXCEPT (rn) FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY policy_id, criterion_id ORDER BY policy_id, criterion_id) AS rn
  FROM `delivery-experience-511901.priorauth_agent.criteria`
) WHERE rn = 1;

CREATE OR REPLACE TABLE `delivery-experience-511901.priorauth_agent.policy_chunks` AS
SELECT * EXCEPT (rn) FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY chunk_id ORDER BY chunk_id) AS rn
  FROM `delivery-experience-511901.priorauth_agent.policy_chunks`
) WHERE rn = 1;

CREATE OR REPLACE TABLE `delivery-experience-511901.priorauth_agent.cases` AS
SELECT * EXCEPT (rn) FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY case_id ORDER BY case_id) AS rn
  FROM `delivery-experience-511901.priorauth_agent.cases`
) WHERE rn = 1;
