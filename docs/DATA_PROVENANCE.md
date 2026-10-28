# Data provenance, retrieval date 2026-10-27

No policy PDFs are redistributed here, and no proprietary CPT code
sets are redistributed. Policy chunks in data/policy_chunks.json are
short paraphrases with source links and retrieval instructions. Check
the full policy at its source URL before relying on any criterion.

## 1. Lumbar spine MRI, commercial payer

- Aetna Clinical Policy Bulletin 0236, Magnetic Resonance Imaging
  (MRI) and Computed Tomography (CT) of the Spine.
- URL: https://www.aetna.com/cpb/medical/data/200_299/0236.html
- Key criteria used: persistent back pain with radiculopathy evidenced
  by pain plus objective motor or reflex changes in the specific nerve
  root distribution, and no improvement after 6 weeks of conservative
  therapy (moderate activity, analgesics, NSAIDs, muscle relaxants);
  red flag pathways such as rapidly progressing neurological deficit,
  major motor weakness, suspected infection, tumor, fracture, or
  cauda equina compression.
- Important distinction: there is no Medicare National Coverage
  Determination for lumbar spine MRI. Coverage is via MAC Local
  Coverage Determinations. Do NOT present this Aetna commercial policy
  as a Medicare NCD.

## 2. Knee arthroscopy, commercial payer

- Aetna Clinical Policy Bulletin 0673, Osteoarthritis of the Knee:
  Selected Treatments.
- URL: https://www.aetna.com/cpb/medical/data/600_699/0673.html
- Last review shown in the archived copy 09/11/2024, originally
  effective 09/26/2003.
- Key criteria used: arthroscopic knee surgery with or without partial
  meniscectomy or meniscal repair for significant knee pain plus
  mechanical symptoms and no more than mild osteoarthritis
  (Kellgren-Lawrence 0, 1, or 2, or modified Outerbridge Grade 0, 1,
  or 2), with radiologic confirmation (X-ray for loose bodies, MRI for
  meniscal tears or loose bodies), and failure of conservative therapy
  defined as at least 6 weeks of formal physical therapy in the past
  year, confirmed by PT notes or claims history. Conservative therapy
  can be waived if the knee is locked due to a displaced bucket handle
  tear. Exclusion: moderate to severe osteoarthritis (KL 3 or 4,
  Outerbridge III or IV) for debridement, and diagnostic arthroscopy
  alone is generally not covered without radiologically proven pathology.

## 3. Biologic infusion, commercial payer, Crohn disease modeled

- Cigna Coverage Policy IP0660, Inflammatory Conditions, Infliximab
  Intravenous Products Prior Authorization Policy.
- URL: https://v.static.cigna.com/assets/chcp/pdf/coveragePolicies/pharmacy/ip_0660_coveragepositioncriteria_inflammatory_conditions_infliximab_intravenous_products_pa.pdf
- Modeled indication: Crohn disease. This is a simplified faithful
  subset, not a verbatim reproduction. The full policy must be checked.
- Key criteria used for initial therapy: patient age at least 6 years,
  medication prescribed by or in consultation with a gastroenterologist,
  moderate to severe Crohn disease diagnosis, initial dosing up to 5 mg
  per kg IV at weeks 0, 2, and 6 then no more frequently than every 6
  weeks, TB screening documented before initiation, and prior
  conventional therapy failure, intolerance, or contraindication
  documented (corticosteroids, immunomodulators, or other conventional
  therapy) unless the case is a continuation case with at least 6 months
  established therapy and objective or symptomatic response.
- Exclusions: active serious infection, untreated latent TB, known
  hypersensitivity to infliximab, and a diagnosis not in policy scope.

## Outdated fixtures

Each policy in data/policies.json includes a superseded version
(lumbar 2024, knee 2023, biologic 2024), clearly labeled as outdated,
so stale policy cases can be tested. Cases using those versions are
stale by design.

## Codes

ICD-10-CM and HCPCS references used here are public references and
procedure names as they appear in public policies. Supported code lists
in data/policies.json are simplified subsets for the modeled criteria,
not exhaustive policy code lists. The code validator never invents a code.

## Cases

All cases in data/cases.json are synthetic, labeled synthetic, with no
real patient data and no PHI. See data/labeling_rubric.md.
