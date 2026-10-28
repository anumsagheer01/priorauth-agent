# Labeling rubric, synthetic cases only

Gold labels were assigned by template intent when cases were generated,
before the engine ever ran. Gold labels are never copied from engine
output. If the engine disagrees with gold, that is an engine failure to
report, not a label to change after the fact, unless the template itself
was demonstrably mislabeled and the correction is documented.

## Readiness labels, documentation readiness only

- READY_FOR_HUMAN_REVIEW: every required criterion has a positive
  excerpt, no exclusion fires, codes are valid, and the policy version
  is current. This is not an approval, denial, or submission.
- NOT_READY: a required criterion is missing or not met, or an
  exclusion fires.
- NEEDS_MANUAL_REVIEW: evidence is uncertain or contradictory, history
  is ambiguous, a code is invalid or unsupported, or the policy version
  is stale, and no exclusion already forces NOT_READY.

## Criterion outcomes

- met: a positive pattern excerpt is present, with no negation excerpt
  for the same criterion.
- not_met: an explicit negation excerpt is present, or a documented
  duration is under the required minimum.
- missing: no positive, negation, or ambiguous excerpt is present.
- uncertain: only ambiguous language is present.
- contradictory: both a positive excerpt and a negation excerpt are present.
- not_applicable: a conditional pathway is not documented; this never blocks.
- fired / not_fired: exclusions only.

## Categories

fully_documented, missing_evidence, exclusion_triggered,
incorrect_or_unsupported_code, contradictory_notes, ambiguous_history,
outdated_policy, incomplete_conservative, negated_findings,
insufficient_evidence. See scripts/generate_cases.py for how each
template maps to gold labels.
