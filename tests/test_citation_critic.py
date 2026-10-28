"""Demonstrable citation critic catches. Test only, not eval results.

Each test constructs a deliberately unsupported claim and asserts
citation_verifier downgrades it to missing. No model call happens.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from priorauth.models import Citation, CriterionResult
from priorauth.tools import citation_verifier


def _result(status="met", excerpts=None):
    return CriterionResult(
        criterion_id="LUM-01", status=status,
        evidence_excerpts=excerpts or ["Patient completed 6 weeks of conservative therapy."],
        citation=Citation(policy_id="AETNA_CPB_0236", policy_version="2026", section="Lumbar", source_url="https://example.test/policy"),
    )


def test_unsupported_excerpt_not_in_note_is_downgraded():
    note = "Patient reports back pain. No therapy history is documented."
    results, findings = citation_verifier(
        [_result()], [{"criterion_id": "LUM-01", "excerpt": "Patient completed 6 weeks of conservative therapy.",
                      "citation_policy_id": "AETNA_CPB_0236", "citation_section": "Lumbar"}], note=note)
    assert results[0].status == "missing"
    assert results[0].evidence_excerpts == []
    assert any("does not appear in the note" in f for f in findings)


def test_missing_policy_citation_is_downgraded():
    note = "Patient completed 6 weeks of conservative therapy."
    results, findings = citation_verifier(
        [_result()], [{"criterion_id": "LUM-01", "excerpt": "Patient completed 6 weeks of conservative therapy.",
                      "citation_policy_id": "", "citation_section": ""}], note=note)
    assert results[0].status == "missing"
    assert any("no complete policy citation" in f for f in findings)


def test_excerpt_not_found_by_extractor_is_downgraded():
    note = "Patient completed 6 weeks of conservative therapy. Patient also ran a marathon."
    results, findings = citation_verifier(
        [_result()], [{"criterion_id": "LUM-01", "excerpt": "Patient also ran a marathon.",
                      "citation_policy_id": "AETNA_CPB_0236", "citation_section": "Lumbar"}], note=note)
    # Excerpt is in the note, but it is not an excerpt the extractor
    # found for this criterion, so it must not be used to support met.
    assert results[0].status == "missing"
    assert any("extractor did not find" in f for f in findings)


def test_supported_excerpt_is_not_downgraded():
    note = "Patient completed 6 weeks of conservative therapy."
    results, findings = citation_verifier(
        [_result()], [{"criterion_id": "LUM-01", "excerpt": "Patient completed 6 weeks of conservative therapy.",
                      "citation_policy_id": "AETNA_CPB_0236", "citation_section": "Lumbar"}], note=note)
    assert results[0].status == "met"
    assert findings == []
