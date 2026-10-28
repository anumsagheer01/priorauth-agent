"""Streamlit demo for PriorAuth Agent, real pipeline only.

The UI calls the FastAPI backend at PRIORAUTH_API_URL when it is set
and reachable, otherwise it calls the same real pipeline directly and
says so on screen. It never replays a hardcoded result: every run
shows the live review returned for the note that was submitted.
If GCP credentials are absent, it shows the Cloud Shell sign-in
message and stops, instead of showing a mock result.

The 10 demo steps, in order:
1 intake and procedure, 2 policy and effective date, 3 requirements
extraction, 4 evidence matching per requirement, 5 exact citations
and excerpts, 6 missing, contradictory, and unsupported evidence,
7 critic findings, 8 deterministic readiness, 9 citation-grounded
draft, 10 human review and audit history.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st

from priorauth.models import ClinicalCase
from priorauth.policies import get_policy, load_eval_cases, load_policies

API_URL = os.environ.get("PRIORAUTH_API_URL", "").rstrip("/")

st.set_page_config(page_title="PriorAuth Agent, real pipeline demo", layout="wide")
st.title("PriorAuth Agent: documentation readiness, real pipeline")
st.write("This demo checks whether documentation is ready for human review. "
         "It never approves, denies, or submits a prior authorization. "
         "A human must review every result.")

policies = load_policies()
cases = load_eval_cases()
case_by_id = {c["case_id"]: c for c in cases}

st.header("Step 1: Intake and procedure")
procedure = st.selectbox("Procedure", options=["lumbar_mri", "knee_arthroscopy", "biologic_infusion"],
    format_func=lambda v: {"lumbar_mri": "Lumbar spine MRI", "knee_arthroscopy": "Knee arthroscopy",
                            "biologic_infusion": "Biologic infusion (infliximab, Crohn disease)"}[v])
matching = [p for p in policies if p.procedure == procedure]
policy = st.selectbox("Policy", options=matching, format_func=lambda p: f"{p.policy_id}: {p.title}")
st.header("Step 2: Policy and effective date")
st.write(f"Policy: {policy.policy_id}, payer: {policy.payer} ({policy.payer_type}).")
st.write(f"Current version: {policy.current_version}. Versions: "
         + ", ".join(f"{v.version} effective {v.effective_date} ({v.status})" for v in policy.versions))
st.write(f"Source: {policy.source_url}")
st.write(f"Note: {policy.subset_note}")
st.write("Pathways: " + "; ".join(f"{p.pathway_id}: {p.name}" for p in policy.pathways))

case_options = ["Paste my own note"] + [c["case_id"] for c in cases if c["procedure"] == procedure]
choice = st.selectbox("Evaluation case, or paste a note (test text only, no real patient data)", options=case_options)
if choice == "Paste my own note":
    note = st.text_area("Clinical note (test text only, no real patient data)", height=200)
    dx = st.text_input("Diagnosis codes, comma separated", value=policy.supported_diagnosis_codes[0] if policy.supported_diagnosis_codes else "")
    proc_code = st.text_input("Procedure code", value=policy.procedure_codes[0] if policy.procedure_codes else "")
    age = st.number_input("Patient age", min_value=0, max_value=120, value=40)
    case_id, version = "PASTE-001", policy.current_version
    source_note = "Pasted test note, not a real patient record."
else:
    selected = case_by_id[choice]
    note = st.text_area("Clinical note", value=selected["clinical_note"], height=200)
    dx = st.text_input("Diagnosis codes, comma separated", value=", ".join(selected["diagnosis_codes"]))
    proc_code = st.text_input("Procedure code", value=selected["procedure_code"])
    age = st.number_input("Patient age", min_value=0, max_value=120, value=selected["patient_age"] or 40)
    case_id, version = selected["case_id"], selected["policy_version"]
    source_note = f"Eval case source: {selected['source_type']}, {selected.get('source_id', '')} {selected.get('source_url', '')} license: {selected.get('source_license', '')}"

if st.button("Run real review"):
    payload = {"case_id": case_id, "procedure": procedure, "policy_id": policy.policy_id,
               "policy_version": version, "diagnosis_codes": [c.strip() for c in dx.split(",") if c.strip()],
               "procedure_code": proc_code, "patient_age": int(age), "clinical_note": note}
    result = None
    backend = ""
    if API_URL:
        try:
            import httpx

            resp = httpx.post(f"{API_URL}/reviews", json=payload, timeout=300.0)
            if resp.status_code == 200:
                result, backend = resp.json(), f"FastAPI backend at {API_URL}"
            else:
                st.error(f"FastAPI backend returned {resp.status_code}: {resp.text}")
        except Exception as exc:
            st.warning(f"FastAPI backend at {API_URL} was not reachable ({exc}). Falling back to the same real pipeline in this process.")
    if result is None:
        try:
            from priorauth.adk_agent import run_via_adk
            from priorauth.policies import load_chunks

            out = run_via_adk(ClinicalCase.model_validate(payload), policy, load_chunks())
            result, backend = out.model_dump(), "Real pipeline in this process (same ADK pipeline the API uses)"
        except Exception as exc:
            st.error(f"Real pipeline could not run: {exc}. "
                     "In Cloud Shell, sign in and click Authorize first. No mock result is shown.")
            st.stop()
    st.write(f"Backend used: {backend}")
    st.write(f"Source: {source_note}")
    st.header("Step 3: Requirements extraction")
    for c in policy.criteria:
        st.write(f"- {c.criterion_id} ({c.kind}, {c.section}): {c.text}")
    st.header("Step 4: Evidence matching per requirement")
    st.header("Step 5: Exact citations and excerpts")
    crit_by_id = {c.criterion_id: c for c in policy.criteria}
    for r in result["criterion_results"]:
        st.write(f"**{r['criterion_id']}**: {r['status']}")
        if r.get("citation"):
            st.write(f"  Policy: {r['citation']['policy_id']} version {r['citation']['policy_version']}, section {r['citation']['section']}, {r['citation']['source_url']}")
        for ex in r.get("evidence_excerpts", []):
            st.write(f'  Excerpt: "{ex}"')
        if r.get("notes"):
            st.write(f"  Notes: {r['notes']}")
    st.header("Step 6: Missing, contradictory, and unsupported evidence")
    for gap in result["gaps"]:
        st.write(f"- {gap}")
    if not result["gaps"]:
        st.write("- None recorded.")
    st.header("Step 7: Critic findings")
    for f in result["critic_findings"]:
        st.write(f"- {f}")
    st.header("Step 8: Deterministic readiness")
    st.write(f"Readiness: **{result['readiness']}** (documentation readiness only, not an insurance decision).")
    st.write(f"Policy version current: {result['policy_version_current']}. Codes: {result['code_validation']}.")
    st.header("Step 9: Citation-grounded draft")
    if result.get("draft_letter"):
        st.write(result["draft_letter"]["body"])
        st.write(result["draft_letter"]["disclaimer"])
    st.header("Step 10: Human review and audit history")
    st.write(f"Review ID: {result['review_id']}. Model: {result['model_name']}. Embedding model: {result['embedding_model']}.")
    st.write(f"Retrieval method: {result['retrieval_method']}. Tool calls: {', '.join(result['tool_calls'])}.")
    st.write(f"Latency: {result['latency_ms']:.0f} ms. Estimated cost: ${result['cost_usd_estimated']:.4f}. Token usage: {result['token_usage']}.")
    st.write("Human reviewer action required: verify every statement against the full policy and the complete clinical record before any action is taken.")
    st.json(result["audit_entry"])
