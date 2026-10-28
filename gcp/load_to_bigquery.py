"""Load policies, criteria, chunks, and eval cases into priorauth_agent.

Uses only the dataset created in Cloud Step 1. Run from Cloud Shell.
Tables come from gcp/sql/schema.sql. This script inserts JSON rows
with the BigQuery client; it never touches Delivery Experience tables.

Idempotency, added after the 2026-10-27 rerun duplicated rows:
the first load inserted policies (3) and policy_chunks (7), then
failed on cases with "no such field source_type", because
schema.sql did not yet define that column. The second load,
after the column was added in Cloud Shell only, inserted the
same policies and chunks again, giving policies 6 and
policy_chunks 14 (and criteria 40, double the 20 in
data/policies.json), while cases reached the correct 30.
A rerun must therefore never blindly insert again.

Fix: before inserting into a table, query its existing primary
keys and skip rows already present. Primary keys:
- policies: policy_id
- criteria: (policy_id, criterion_id)
- policy_chunks: chunk_id
- cases: case_id
Rows already present are skipped and counted, not re-inserted,
so a rerun is safe and the counts stay at 3 / 20 / 7 / 30.
Existing rows are never updated by this script: if a row's
content changed in the repo, delete it explicitly in BigQuery
first, then rerun. That delete step is documented, not silent,
because silently replacing rows would hide a data change.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

ROOT = Path(__file__).resolve().parents[1]
PROJECT = "delivery-experience-511901"
DATASET = "delivery-experience-511901.priorauth_agent"

PRIMARY_KEYS = {
    "policies": ["policy_id"],
    "criteria": ["policy_id", "criterion_id"],
    "policy_chunks": ["chunk_id"],
    "cases": ["case_id"],
}


def _key(row: dict, table: str) -> tuple:
    return tuple(str(row.get(col, "")) for col in PRIMARY_KEYS[table])


def _row_key(row, table: str) -> tuple:
    """Read a primary key from a BigQuery Row or a plain dict."""
    values = []
    for col in PRIMARY_KEYS[table]:
        try:
            values.append(str(row[col]))
        except Exception:
            values.append(str(getattr(row, col, "")))
    return tuple(values)


def existing_keys(client, dataset: str, table: str) -> set:
    """Return the set of primary keys already in a table."""
    cols = ", ".join(PRIMARY_KEYS[table])
    query = f"SELECT {cols} FROM `{dataset}.{table}`"
    return {_row_key(row, table) for row in client.query(query).result()}


def load(client, dataset: str, table: str, rows: list[dict]) -> int:
    """Insert only rows whose primary key is not already present.

    Returns the number of rows inserted. Rows skipped as already
    present are reported, not silently dropped: the caller prints
    both counts, so a rerun's output shows exactly what changed.
    """
    if not rows:
        print(f"{table}: 0 rows to load")
        return 0
    already = existing_keys(client, dataset, table)
    new_rows = [r for r in rows if _key(r, table) not in already]
    if not new_rows:
        print(f"{table}: inserted 0 rows, skipped {len(rows)} already present")
        return 0
    errors = client.insert_rows_json(f"{dataset}.{table}", new_rows)
    if errors:
        raise RuntimeError(f"Insert into {table} failed: {errors}")
    print(f"{table}: inserted {len(new_rows)} rows, skipped {len(rows) - len(new_rows)} already present")
    return len(new_rows)


def build_rows() -> dict:
    """Build the row sets from the repo data files, no cloud call."""
    policies = json.loads((ROOT / "data" / "policies.json").read_text())["policies"]
    chunks = json.loads((ROOT / "data" / "policy_chunks.json").read_text())
    chunks = chunks["chunks"] if isinstance(chunks, dict) else chunks
    cases = json.loads((ROOT / "data" / "eval_cases.json").read_text())["cases"]
    return {
        "policies": [{"policy_id": p["policy_id"], "title": p["title"], "payer": p["payer"],
                      "procedure": p["procedure"], "source_url": p["source_url"],
                      "current_version": p["current_version"]} for p in policies],
        "criteria": [{"policy_id": p["policy_id"], "criterion_id": c["criterion_id"],
                      "text": c["text"], "section": c["section"], "kind": c["kind"]}
                     for p in policies for c in p["criteria"]],
        "policy_chunks": [{"chunk_id": c.get("chunk_id", ""), "policy_id": c.get("policy_id", ""),
                           "section": c.get("section", ""), "text": c.get("text", "")} for c in chunks],
        "cases": [{"case_id": c["case_id"], "procedure": c["procedure"], "policy_id": c["policy_id"],
                   "policy_version": c["policy_version"], "clinical_note": c["clinical_note"],
                   "gold_readiness": c["gold_readiness"], "source_type": c["source_type"]} for c in cases],
    }


def main(client=None) -> int:
    if client is None:
        from google.cloud import bigquery

        client = bigquery.Client(project=PROJECT, location="us-central1")
    for table, rows in build_rows().items():
        load(client, DATASET, table, rows)
    print("Load complete. Embeddings are a separate step (embed_policy_chunks.py).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
