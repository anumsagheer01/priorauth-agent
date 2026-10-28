# Architecture

ASCII diagram:

```
User note / synthetic case
        |
        v
FastAPI POST /reviews  OR  Streamlit demo  OR  scripts/evaluate.py
        |
        v
engine.run_review(case, policy)
  1. Intake validation
  2. Policy retrieval (local data/policies.json, Pydantic validated)
  3. Criteria extraction (policy criteria, no model call)
  4. Evidence extraction (deterministic phrase matching, negation,
     contradiction, duration checks, structured age check)
  5. Code validation (ICD-10-CM format, supported list, CPT/HCPCS)
  6. Citation verification (excerpt must appear in the note)
  7. Deterministic checklist scoring (see src/priorauth/tools.py)
  8. Draft generation (only from verified met criteria, gaps listed)
  9. Audit logging (JSON lines, case, policy, version, results, state)
        |
        v
ReviewResult: readiness, criterion results with citations and
exact excerpts, gaps, critic findings, draft letter, audit entry
```

Why more than basic RAG: basic RAG retrieves text and asks a model to
decide, which can invent excerpts and flip a decision silently. This
system retrieves only local paraphrased chunks, then applies a
deterministic checklist whose rules override any score, verifies every
citation against the actual note, and blocks READY on any exclusion,
missing criterion, bad code, contradiction, ambiguity, or stale policy.
The model, if ever enabled in cloud mode, would only draft or
summarize inside those guardrails, never decide readiness alone.
