"""Generate data/cases.json: 60 synthetic cases, 20 per procedure.

Gold labels are assigned here by template intent, before the engine
ever runs. The evaluation script compares engine predictions to these
gold labels; gold labels are never copied from engine output. See
data/labeling_rubric.md for the definitions.

No real patient data is used. Names, dates, and histories are invented
for synthetic cases and are labeled synthetic in the data file.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "cases.json"

LUM_CRITS = ["LUM-01", "LUM-02", "LUM-03", "LUM-EX-01"]
KNE_CRITS = ["KNE-01", "KNE-02", "KNE-03", "KNE-04", "KNE-05", "KNE-EX-01", "KNE-EX-02"]
BIO_CRITS = ["BIO-01", "BIO-02", "BIO-03", "BIO-04", "BIO-05", "BIO-06", "BIO-EX-01", "BIO-EX-02", "BIO-EX-03"]

FIRST = ["Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Jamie", "Sam"]
LAST = ["Patel", "Garcia", "Kim", "Nguyen", "Smith", "Johnson", "Lee", "Brown"]


def lum_gold(**over):
    base = {"LUM-01": "met", "LUM-02": "met", "LUM-03": "not_applicable", "LUM-EX-01": "not_fired"}
    base.update(over)
    return base


def kne_gold(**over):
    base = {
        "KNE-01": "met", "KNE-02": "met", "KNE-03": "met", "KNE-04": "met",
        "KNE-05": "not_applicable", "KNE-EX-01": "not_fired", "KNE-EX-02": "not_fired",
    }
    base.update(over)
    return base


def bio_gold(**over):
    base = {
        "BIO-01": "met", "BIO-02": "met", "BIO-03": "met", "BIO-04": "met",
        "BIO-05": "met", "BIO-06": "met", "BIO-EX-01": "not_fired",
        "BIO-EX-02": "not_fired", "BIO-EX-03": "not_fired",
    }
    base.update(over)
    return base


def lum_note(i, lum01, lum02, extra=""):
    name = f"{FIRST[i % 8]} {LAST[i % 8]}"
    return (
        f"SYNTHETIC CASE. Patient: {name}, age 52. Visit dates: 2026-03-02, 2026-04-10, 2026-05-18. "
        f"History: persistent low back pain for 4 months, with prior visits for back pain and leg symptoms. "
        f"{lum01} {lum02} "
        f"Imaging requested: lumbar spine MRI. Prior therapy: moderate activity, analgesics, NSAIDs, and muscle relaxants as tolerated. "
        f"{extra}"
    ).strip()


def kne_note(i, kne01, kne02, kne03, kne04, extra=""):
    name = f"{FIRST[i % 8]} {LAST[(i + 2) % 8]}"
    return (
        f"SYNTHETIC CASE. Patient: {name}, age 48. Visit dates: 2026-02-14, 2026-03-20, 2026-04-28. "
        f"History: knee pain for 5 months, worse with stairs and prolonged standing. "
        f"{kne01} {kne02} {kne03} {kne04} "
        f"Imaging requested: knee arthroscopy with possible partial meniscectomy. "
        f"{extra}"
    ).strip()


def bio_note(i, bio02, bio03, bio04, bio05, bio06, age=34, extra=""):
    name = f"{FIRST[(i + 1) % 8]} {LAST[(i + 3) % 8]}"
    return (
        f"SYNTHETIC CASE. Patient: {name}, age {age}. Visit dates: 2026-01-12, 2026-02-09, 2026-03-16. "
        f"History: abdominal pain, diarrhea, and weight loss over 8 months, with prior gastroenterology follow-up. "
        f"{bio02} {bio03} {bio04} {bio05} {bio06} "
        f"Treatment requested: infliximab intravenous infusion. "
        f"{extra}"
    ).strip()


LUM01 = "Exam shows radicular pain with motor weakness in the L5 distribution and diminished Achilles reflex."
LUM01B = "Exam documents objective motor weakness in the L5 distribution with reflex changes in the L5 distribution."
LUM02 = "The patient completed 6 weeks of conservative therapy with moderate activity, analgesics, NSAIDs, and muscle relaxants, with no improvement after 6 weeks of conservative therapy."
LUM02B = "The patient completed 8 weeks of conservative therapy with moderate activity, analgesics, NSAIDs, and muscle relaxants, with no improvement after 8 weeks of conservative therapy."
KNE01 = "Patient reports significant knee pain with mechanical symptoms, including knee locking and catching in the knee."
KNE02 = "Imaging grade is Kellgren-Lawrence grade 2, consistent with mild osteoarthritis."
KNE03 = "MRI shows meniscal tear in the medial meniscus."
KNE04 = "The patient completed 6 weeks of formal physical therapy in the past year, confirmed by PT notes."
KNE04B = "The patient completed 8 weeks of formal physical therapy in the past year, confirmed by PT notes."
BIO02 = "Infliximab was prescribed by a gastroenterologist."
BIO03 = "Diagnosis is moderate to severe Crohn disease."
BIO04 = "Planned dosing is 5 mg per kg at weeks 0, 2, and 6, then maintenance dosing every 6 weeks."
BIO05 = "TB screening documented before initiation, with a negative result."
BIO06 = "The patient failed corticosteroids and failed immunomodulators, with documented intolerance to prior therapy."
BIO06B = "The patient has corticosteroid failure documented and immunomodulator failure documented after conventional therapy."

cases = []
n = 0


def add(case_id, procedure, policy_id, version, dx, proc, age, note, gold, gold_crit, cats):
    global n
    n += 1
    cases.append({
        "case_id": case_id, "procedure": procedure, "policy_id": policy_id,
        "policy_version": version, "diagnosis_codes": dx, "procedure_code": proc,
        "patient_age": age, "clinical_note": note, "gold_readiness": gold,
        "gold_criterion_outcomes": gold_crit, "categories": cats,
    })


# ---------------- Lumbar, 20 cases ----------------
for k in range(4):
    i = k
    add(f"LUM-{k+1:03d}", "lumbar_mri", "AETNA_CPB_0236", "2026", ["M54.16"], "72148", 52,
        lum_note(i, LUM01 if k % 2 == 0 else LUM01B, LUM02 if k % 2 == 0 else LUM02B),
        "READY_FOR_HUMAN_REVIEW", lum_gold(), ["fully_documented"])
for k in range(2):
    i = 10 + k
    add(f"LUM-{5+k:03d}", "lumbar_mri", "AETNA_CPB_0236", "2026", ["M54.16"], "72148", 52,
        lum_note(i, LUM01, ""),
        "NOT_READY", lum_gold(**{"LUM-02": "missing"}), ["missing_evidence"])
add("LUM-007", "lumbar_mri", "AETNA_CPB_0236", "2026", ["M54.16"], "72148", 52,
    lum_note(7, LUM01, LUM02, "A lumbar MRI already completed for the same indication is on file, with no new symptoms reported."),
    "NOT_READY", lum_gold(**{"LUM-EX-01": "fired"}), ["exclusion_triggered"])
add("LUM-008", "lumbar_mri", "AETNA_CPB_0236", "2026", ["M54.16"], "72148", 52,
    lum_note(8, LUM01, LUM02, "A lumbar MRI already completed for the same indication is on file, with no new symptoms reported."),
    "NOT_READY", lum_gold(**{"LUM-EX-01": "fired"}), ["exclusion_triggered"])
add("LUM-009", "lumbar_mri", "AETNA_CPB_0236", "2026", ["J06.9"], "72148", 52,
    lum_note(9, LUM01, LUM02), "NEEDS_MANUAL_REVIEW", lum_gold(), ["incorrect_or_unsupported_code"])
add("LUM-010", "lumbar_mri", "AETNA_CPB_0236", "2026", ["XYZ"], "72148", 52,
    lum_note(10, LUM01, LUM02), "NEEDS_MANUAL_REVIEW", lum_gold(), ["incorrect_or_unsupported_code"])
for k in range(2):
    i = 11 + k
    add(f"LUM-{11+k:03d}", "lumbar_mri", "AETNA_CPB_0236", "2026", ["M54.16"], "72148", 52,
        lum_note(i, LUM01, LUM02, "The exam also states no radiculopathy and no motor weakness."),
        "NEEDS_MANUAL_REVIEW", lum_gold(**{"LUM-01": "contradictory"}), ["contradictory_notes"])
for k in range(2):
    i = 13 + k
    add(f"LUM-{13+k:03d}", "lumbar_mri", "AETNA_CPB_0236", "2026", ["M54.16"], "72148", 52,
        lum_note(i, "There is possible radiculopathy, but the exam is unclear.", LUM02),
        "NEEDS_MANUAL_REVIEW", lum_gold(**{"LUM-01": "uncertain"}), ["ambiguous_history"])
for k in range(2):
    i = 15 + k
    add(f"LUM-{15+k:03d}", "lumbar_mri", "AETNA_CPB_0236", "2024", ["M54.16"], "72148", 52,
        lum_note(i, LUM01, LUM02),
        "NEEDS_MANUAL_REVIEW", lum_gold(), ["outdated_policy"])
for k in range(2):
    i = 17 + k
    add(f"LUM-{17+k:03d}", "lumbar_mri", "AETNA_CPB_0236", "2026", ["M54.16"], "72148", 52,
        lum_note(i, LUM01, "The patient completed 3 weeks of conservative therapy with analgesics and NSAIDs."),
        "NOT_READY", lum_gold(**{"LUM-02": "not_met"}), ["incomplete_conservative"])
add("LUM-019", "lumbar_mri", "AETNA_CPB_0236", "2026", ["M54.16"], "72148", 52,
    lum_note(19, "Exam shows no radiculopathy, no motor weakness, and no reflex changes.", LUM02),
    "NOT_READY", lum_gold(**{"LUM-01": "not_met"}), ["negated_findings"])
add("LUM-020", "lumbar_mri", "AETNA_CPB_0236", "2026", ["M54.16"], "72148", 52,
    lum_note(20, "Patient reports back pain radiating down the leg, without a documented neurological exam.", LUM02),
    "NOT_READY", lum_gold(**{"LUM-01": "missing"}), ["insufficient_evidence"])

# ---------------- Knee, 20 cases ----------------
for k in range(4):
    i = k
    add(f"KNE-{k+1:03d}", "knee_arthroscopy", "AETNA_CPB_0673", "2024-09-11", ["M23.22"], "29881", 48,
        kne_note(i, KNE01, KNE02, KNE03, KNE04 if k % 2 == 0 else KNE04B),
        "READY_FOR_HUMAN_REVIEW", kne_gold(), ["fully_documented"])
for k in range(2):
    i = 10 + k
    add(f"KNE-{5+k:03d}", "knee_arthroscopy", "AETNA_CPB_0673", "2024-09-11", ["M23.22"], "29881", 48,
        kne_note(i, KNE01, KNE02, KNE03, ""),
        "NOT_READY", kne_gold(**{"KNE-04": "missing"}), ["missing_evidence"])
add("KNE-007", "knee_arthroscopy", "AETNA_CPB_0673", "2024-09-11", ["M23.22"], "29881", 48,
    kne_note(7, KNE01, "Imaging grade is Kellgren-Lawrence grade 4, consistent with moderate to severe osteoarthritis.", KNE03, KNE04),
    "NOT_READY", kne_gold(**{"KNE-02": "missing", "KNE-EX-01": "fired"}), ["exclusion_triggered"])
add("KNE-008", "knee_arthroscopy", "AETNA_CPB_0673", "2024-09-11", ["M23.22"], "29881", 48,
    kne_note(8, KNE01, KNE02, "", "", "This request is for diagnostic arthroscopy alone without radiologic confirmation."),
    "NOT_READY", kne_gold(**{"KNE-03": "missing", "KNE-04": "missing", "KNE-EX-02": "fired"}), ["exclusion_triggered"])
add("KNE-009", "knee_arthroscopy", "AETNA_CPB_0673", "2024-09-11", ["J06.9"], "29881", 48,
    kne_note(9, KNE01, KNE02, KNE03, KNE04), "NEEDS_MANUAL_REVIEW", kne_gold(), ["incorrect_or_unsupported_code"])
add("KNE-010", "knee_arthroscopy", "AETNA_CPB_0673", "2024-09-11", ["XYZ"], "29881", 48,
    kne_note(10, KNE01, KNE02, KNE03, KNE04), "NEEDS_MANUAL_REVIEW", kne_gold(), ["incorrect_or_unsupported_code"])
for k in range(2):
    i = 11 + k
    add(f"KNE-{11+k:03d}", "knee_arthroscopy", "AETNA_CPB_0673", "2024-09-11", ["M23.22"], "29881", 48,
        kne_note(i, KNE01, KNE02, KNE03, KNE04, "The exam also states no mechanical symptoms and no locking."),
        "NEEDS_MANUAL_REVIEW", kne_gold(**{"KNE-01": "contradictory"}), ["contradictory_notes"])
for k in range(2):
    i = 13 + k
    add(f"KNE-{13+k:03d}", "knee_arthroscopy", "AETNA_CPB_0673", "2024-09-11", ["M23.22"], "29881", 48,
        kne_note(i, KNE01, KNE02, KNE03, "The patient had some physical therapy, with unclear duration of physical therapy."),
        "NEEDS_MANUAL_REVIEW", kne_gold(**{"KNE-04": "uncertain"}), ["ambiguous_history"])
for k in range(2):
    i = 15 + k
    add(f"KNE-{15+k:03d}", "knee_arthroscopy", "AETNA_CPB_0673", "2023", ["M23.22"], "29881", 48,
        kne_note(i, KNE01, KNE02, KNE03, KNE04),
        "NEEDS_MANUAL_REVIEW", kne_gold(), ["outdated_policy"])
for k in range(2):
    i = 17 + k
    add(f"KNE-{17+k:03d}", "knee_arthroscopy", "AETNA_CPB_0673", "2024-09-11", ["M23.22"], "29881", 48,
        kne_note(i, KNE01, KNE02, KNE03, "The patient completed 4 weeks of formal physical therapy in the past year."),
        "NOT_READY", kne_gold(**{"KNE-04": "not_met"}), ["incomplete_conservative"])
add("KNE-019", "knee_arthroscopy", "AETNA_CPB_0673", "2024-09-11", ["M23.22"], "29881", 48,
    kne_note(19, KNE01, KNE02, "MRI shows no meniscal tear on MRI and no loose body on imaging.", KNE04),
    "NOT_READY", kne_gold(**{"KNE-03": "not_met"}), ["negated_findings"])
add("KNE-020", "knee_arthroscopy", "AETNA_CPB_0673", "2024-09-11", ["M23.22"], "29881", 48,
    kne_note(20, "Patient reports knee pain and occasional discomfort.", KNE02, KNE03, KNE04),
    "NOT_READY", kne_gold(**{"KNE-01": "missing"}), ["insufficient_evidence"])

# ---------------- Biologic, 20 cases ----------------
for k in range(4):
    i = k
    add(f"BIO-{k+1:03d}", "biologic_infusion", "CIGNA_IP0660", "2026", ["K50.00"], "J1745", 34,
        bio_note(i, BIO02, BIO03, BIO04, BIO05, BIO06 if k % 2 == 0 else BIO06B),
        "READY_FOR_HUMAN_REVIEW", bio_gold(), ["fully_documented"])
for k in range(2):
    i = 10 + k
    add(f"BIO-{5+k:03d}", "biologic_infusion", "CIGNA_IP0660", "2026", ["K50.00"], "J1745", 34,
        bio_note(i, BIO02, BIO03, BIO04, "", BIO06),
        "NOT_READY", bio_gold(**{"BIO-05": "missing"}), ["missing_evidence"])
add("BIO-007", "biologic_infusion", "CIGNA_IP0660", "2026", ["K50.00"], "J1745", 34,
    bio_note(7, BIO02, BIO03, BIO04, BIO05, BIO06, extra="Patient has active serious infection requiring antibiotics."),
    "NOT_READY", bio_gold(**{"BIO-EX-01": "fired"}), ["exclusion_triggered"])
add("BIO-008", "biologic_infusion", "CIGNA_IP0660", "2026", ["K50.00"], "J1745", 34,
    bio_note(8, BIO02, BIO03, BIO04, BIO05, BIO06, extra="Patient has untreated latent tuberculosis."),
    "NOT_READY", bio_gold(**{"BIO-EX-02": "fired"}), ["exclusion_triggered"])
add("BIO-009", "biologic_infusion", "CIGNA_IP0660", "2026", ["J06.9"], "J1745", 34,
    bio_note(9, BIO02, BIO03, BIO04, BIO05, BIO06), "NEEDS_MANUAL_REVIEW", bio_gold(), ["incorrect_or_unsupported_code"])
add("BIO-010", "biologic_infusion", "CIGNA_IP0660", "2026", ["XYZ"], "J1745", 34,
    bio_note(10, BIO02, BIO03, BIO04, BIO05, BIO06), "NEEDS_MANUAL_REVIEW", bio_gold(), ["incorrect_or_unsupported_code"])
for k in range(2):
    i = 11 + k
    add(f"BIO-{11+k:03d}", "biologic_infusion", "CIGNA_IP0660", "2026", ["K50.00"], "J1745", 34,
        bio_note(i, BIO02, BIO03, BIO04, BIO05, BIO06, extra="The note also states mild Crohn disease."),
        "NEEDS_MANUAL_REVIEW", bio_gold(**{"BIO-03": "contradictory"}), ["contradictory_notes"])
for k in range(2):
    i = 13 + k
    add(f"BIO-{13+k:03d}", "biologic_infusion", "CIGNA_IP0660", "2026", ["K50.00"], "J1745", 34,
        bio_note(i, BIO02, BIO03, BIO04, BIO05, "Prior therapy history unclear, with unclear prior therapy history."),
        "NEEDS_MANUAL_REVIEW", bio_gold(**{"BIO-06": "uncertain"}), ["ambiguous_history"])
add("BIO-015", "biologic_infusion", "CIGNA_IP0660", "2024", ["K50.00"], "J1745", 34,
    bio_note(15, BIO02, BIO03, BIO04, BIO05, BIO06),
    "NEEDS_MANUAL_REVIEW", bio_gold(), ["outdated_policy"])
for k in range(2):
    i = 16 + k
    add(f"BIO-{16+k:03d}", "biologic_infusion", "CIGNA_IP0660", "2026", ["K50.00"], "J1745", 34,
        bio_note(i, BIO02, BIO03, BIO04, BIO05, "Patient tried corticosteroids briefly, with no documented failure, intolerance, or contraindication."),
        "NOT_READY", bio_gold(**{"BIO-06": "missing"}), ["incomplete_conservative"])
add("BIO-018", "biologic_infusion", "CIGNA_IP0660", "2026", ["K50.00"], "J1745", 34,
    bio_note(18, "No gastroenterologist prescribed this medication, and no gastroenterology input is documented.", BIO03, BIO04, BIO05, BIO06),
    "NOT_READY", bio_gold(**{"BIO-02": "not_met"}), ["negated_findings"])
add("BIO-019", "biologic_infusion", "CIGNA_IP0660", "2026", ["K50.00"], "J1745", 34,
    bio_note(19, BIO02, "Patient has Crohn disease, without a documented severity grade.", BIO04, BIO05, BIO06),
    "NOT_READY", bio_gold(**{"BIO-03": "missing"}), ["insufficient_evidence"])
add("BIO-020", "biologic_infusion", "CIGNA_IP0660", "2026", ["K50.00"], "J1745", 34,
    bio_note(20, BIO02, "Patient has Crohn disease, with severity not clearly documented in this note.", BIO04, BIO05, BIO06),
    "NOT_READY", bio_gold(**{"BIO-03": "missing"}), ["insufficient_evidence"])

OUT.write_text(json.dumps({"cases": cases, "note": "All cases are synthetic. No real patient data, no PHI."}, indent=2), encoding="utf-8")
print(f"Wrote {len(cases)} cases to {OUT}")
from collections import Counter
print("By procedure:", Counter(c['procedure'] for c in cases))
print("By category:", Counter(cat for c in cases for cat in c['categories']))
print("By gold:", Counter(c['gold_readiness'] for c in cases))
