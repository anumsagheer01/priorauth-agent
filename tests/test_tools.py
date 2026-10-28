from priorauth.models import ClinicalCase
from priorauth.policies import load_chunks, load_policies
from priorauth.tools import (
    citation_verifier,
    code_validator,
    criteria_extractor,
    evidence_extractor,
    policy_search,
)


def _policies():
    return {p.policy_id: p for p in load_policies()}


def test_policy_search_filters_and_returns_source():
    chunks = load_chunks()
    results = policy_search(chunks, "knee arthroscopy mechanical", procedure="knee_arthroscopy")
    assert results
    assert all(r["procedure"] if "procedure" in r else True for r in results)
    assert results[0]["policy_id"] == "AETNA_CPB_0673"
    assert results[0]["section"]
    assert results[0]["source_url"].startswith("https://")


def test_code_validator_valid_unsupported_invalid():
    policies = _policies()
    policy = policies["AETNA_CPB_0236"]
    base = {"procedure": "lumbar_mri", "policy_id": "AETNA_CPB_0236", "policy_version": "2026",
            "procedure_code": "72148", "clinical_note": "Note."}
    assert code_validator(ClinicalCase(case_id="T1", diagnosis_codes=["M54.16"], **base), policy).overall_status == "valid"
    assert code_validator(ClinicalCase(case_id="T2", diagnosis_codes=["J06.9"], **base), policy).overall_status == "unsupported"
    assert code_validator(ClinicalCase(case_id="T3", diagnosis_codes=["XYZ"], **base), policy).overall_status == "invalid"
    assert code_validator(ClinicalCase(case_id="T4", diagnosis_codes=["M54.16"], procedure_code="99999", procedure="lumbar_mri", policy_id="AETNA_CPB_0236", policy_version="2026", clinical_note="Note."), policy).overall_status == "unsupported"


def test_criteria_extractor_validates():
    policies = load_policies()
    criteria = criteria_extractor(policies[0].model_dump())
    assert criteria
    assert all(c.source_url.startswith("https://") for c in criteria)


def test_evidence_extractor_negation_and_contradiction():
    policies = _policies()
    policy = policies["AETNA_CPB_0236"]
    note_met = "Exam shows radicular pain with motor weakness in the L5 distribution and diminished Achilles reflex."
    results = evidence_extractor(ClinicalCase(case_id="T", procedure="lumbar_mri", policy_id="AETNA_CPB_0236", policy_version="2026", clinical_note=note_met), policy.criteria)
    by_id = {r.criterion_id: r for r in results}
    assert by_id["LUM-01"].status == "met"
    assert by_id["LUM-01"].evidence_excerpts
    note_neg = "Exam shows no radiculopathy, no motor weakness, and no reflex changes."
    results = evidence_extractor(ClinicalCase(case_id="T", procedure="lumbar_mri", policy_id="AETNA_CPB_0236", policy_version="2026", clinical_note=note_neg), policy.criteria)
    assert {r.criterion_id: r for r in results}["LUM-01"].status == "not_met"
    note_both = note_met + " The exam also states no radiculopathy and no motor weakness."
    results = evidence_extractor(ClinicalCase(case_id="T", procedure="lumbar_mri", policy_id="AETNA_CPB_0236", policy_version="2026", clinical_note=note_both), policy.criteria)
    assert {r.criterion_id: r for r in results}["LUM-01"].status == "contradictory"


def test_citation_verifier_downgrades_fake_claim():
    policies = _policies()
    policy = policies["AETNA_CPB_0236"]
    note = "Exam shows radicular pain with motor weakness in the L5 distribution."
    results = evidence_extractor(ClinicalCase(case_id="T", procedure="lumbar_mri", policy_id="AETNA_CPB_0236", policy_version="2026", clinical_note=note), policy.criteria)
    fake_claims = [{"criterion_id": "LUM-01", "excerpt": "A finding that never appears in the note.", "citation_policy_id": "AETNA_CPB_0236", "citation_section": "Lumbar spine MRI criteria"}]
    updated, findings = citation_verifier(results, fake_claims, note=note)
    assert {r.criterion_id: r for r in updated}["LUM-01"].status == "missing"
    assert findings
