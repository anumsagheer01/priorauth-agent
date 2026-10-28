# Simplified faithful subsets vs complete medical policies

Read this before using any output of this project for a real case.
This section is not boilerplate. It is the single most important
limit of the system.

## The short version

Every policy in this project is a simplified, faithful subset of a
public medical policy. It is NOT the complete policy. It must NOT
be used to decide, approve, deny, submit, or advise on a real prior
authorization. A human must read the full, current policy before
any real submission. The system output is documentation readiness
only: READY_FOR_HUMAN_REVIEW, NOT_READY, or NEEDS_MANUAL_REVIEW,
and even READY means "ready for a human to review against the full
policy", not "approved".

## What was actually read, policy by policy

- Aetna Clinical Policy Bulletin 0236, lumbar spine MRI, commercial.
  Source: https://www.aetna.com/cpb/medical/data/200_299/0236.html
  Retrieved 2026-10-27. Encoded subset: persistent pain with
  radiculopathy plus at least 6 weeks conservative therapy, and
  the red-flag pathway as a separate pathway, not as a shortcut
  to approval. What was not encoded: the full policy text, every
  qualifying condition and imaging indication, every code list,
  every exception, every age, imaging, and documentation rule,
  and every update after retrieval. Aetna commercial policy is
  not a Medicare NCD. There is no Medicare NCD for lumbar spine
  MRI; coverage is via MAC LCDs, for example LCD L34220, which
  uses at least 4 weeks conservative therapy for non-red-flag
  cases, versus Aetna 6 weeks. Encoding the Aetna rule as a
  Medicare rule would be wrong, and this project does not do that.
- Aetna Clinical Policy Bulletin 0673, knee arthroscopy, commercial.
  Source: https://www.aetna.com/cpb/medical/data/600_699/0673.html
  Retrieved 2026-10-27. Encoded subset: significant pain plus
  mechanical symptoms, Kellgren-Lawrence grade 0-2 ceiling,
  radiologic confirmation, at least 6 weeks formal physical
  therapy, and a locked bucket-handle waiver pathway that still
  requires human review of the full policy. What was not encoded:
  the full policy text, every qualifying condition, every
  exclusion, every code list, and every update after retrieval.
- Cigna Coverage Policy IP0660, infliximab intravenous products,
  inflammatory conditions, Crohn disease modeled only.
  Source: https://v.static.cigna.com/assets/chcp/pdf/coveragePolicies/pharmacy/ip_0660_coveragepositioncriteria_inflammatory_conditions_infliximab_intravenous_products_pa.pdf
  Effective 2026-03-15 on page 1, retrieved 2026-10-27. This is
  the weakest coverage of the three policies, and it is stated
  plainly here: only the first pages and the Crohn excerpt were
  read in detail, a March 2026 update removed several Crohn
  initial-therapy options, and the full 22 pages were NOT read.
  Encoded subset: Crohn initial-therapy steps BIO-01 through
  BIO-06, as a simplified subset, with HCPCS J1745 for the modeled
  product and Q5103 flagged as a different product code, not
  silently substituted. What was not encoded: the remaining
  pages, other inflammatory conditions, every step-therapy rule,
  every code list, every age and dosing rule, and every update
  after retrieval. A human must read all 22 pages before any real
  use of the biologic pathway, and must re-check the current
  version, because a policy effective in March 2026 may not be
  the version in force when a case is reviewed.

No policy PDF is redistributed in this repo. Policy chunks are
short paraphrases with source links and retrieval instructions,
not verbatim reproduction. Supported code lists are simplified
subsets, not exhaustive policy code lists. ICD-10-CM references
are policy-supported lists only, for example M54.16, M51.16,
M17.0, K50.90, and they must not be treated as a complete coding
guide.

## Why a simplified subset cannot be used for a real submission

- A simplified subset omits rules that can change the answer.
  A criterion this subset calls met can still fail under a rule
  the subset does not encode, and a criterion this subset calls
  missing can be satisfied by documentation the subset does not
  describe.
- A policy version changes. This repo records a version string
  and a stale-policy guardrail, but it cannot know about an
  update that happened after the retrieval date, or about a
  payer-specific amendment that applies to a particular plan.
- A code list is incomplete. An unsupported code in this system
  means "not in the simplified subset", not "not covered by the
  payer", and a supported code in this system does not prove
  coverage, because coverage also depends on plan, benefit,
  medical necessity, and documentation rules outside the subset.
- A pathway is a model of the policy, not the policy. The lumbar
  red-flag pathway, the knee locked bucket-handle waiver, and the
  biologic step pathways are useful for documentation readiness,
  and they are dangerous if they are read as approval rules.
  The knee waiver in particular is flagged human-must-check in
  the data itself, because the subset does not encode the full
  waiver conditions.

## What the system does about this, and what it does not do

What it does:
- It labels the data as simplified subsets in data/policies.json,
  in README, and in docs/REAL_SYSTEM.md, not only in this file.
- It checks policy version currency against the recorded current
  version, and downgrades readiness when the version is stale.
- It requires a policy citation, section, and version for every
  supported criterion, and downgrades unsupported claims to
  missing through citation_verifier.
- It returns NEEDS_MANUAL_REVIEW when evidence is ambiguous,
  contradictory, or incomplete, rather than forcing a READY or
  NOT_READY answer it cannot support.

What it does not do, and must not be claimed to do:
- It does not read the full current policy at review time.
- It does not verify plan-specific benefits, member eligibility,
  or payer-specific amendments.
- It does not validate codes against the complete payer code list.
- It does not approve, deny, submit, or recommend a clinical
  decision, and it must not be described as clinically validated,
  production-certified, or ready for use with real patient
  information.

## Difficult cases, and why they are included

The 30-case eval set is deliberately hard, not representative
of a typical prior auth packet, because a typical packet was not
available as a legally reusable real set. It includes ambiguous
wording, missing evidence, contradictions, explicit negations,
incomplete conservative treatment (for example 3 weeks of
physical therapy, or an unclear duration), outdated policy
versions, unsupported claims, incorrect or unsupported codes,
exclusions fired, age rule failures, and red-flag and locked-knee
waiver pathways. Three cases are paraphrased published case
reports, clearly labeled with source and license, and the other
27 are structured test fixtures, clearly labeled, not real
patient notes. Results on this set will show where the system
succeeds and where it fails on hard cases. They will not prove
performance on typical packets, and they must not be quoted as
if they do.

Walkthroughs of 3 to 5 difficult cases will be added to the
final docs from actual Cloud Shell run outputs, once available.
Until then, they are labeled pending in docs/REAL_SYSTEM.md and
in the study notes, and they are not invented here.
