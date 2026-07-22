# Justice Inference Framework Validation V1

## Result

The corrected framework produces six bounded candidates across seven members from one shared five-episode set without an exact seven-action decision table or prewritten paragraph catalog. Foushee and Adams resolve equivalently; Aderholt, Massie, Bishop, García, and Moskowitz resolve to distinct evidence-backed candidates. Existing PR #95 dossiers and Foushee factual artifacts are unchanged.

## Corrected architecture

The shared contract declares expected substantive rolls, controls, episode IDs, and episode-to-roll mappings. The overlay derives coverage and one trajectory per episode. Justice-specific action interpretations emit member-independent atomic themes. A domain-neutral evaluator selects candidates from theme repetition, conflicts, complete episode coverage, and mechanism diversity, then adds the member name to structured synthesis.

No caller-supplied coverage status is trusted. Omission keeps denominators at seven substantive rolls and five episodes. Present, Not Voting, and missing actions emit no support/opposition evidence. Unknown, duplicate, or mismatched identifiers fail closed.

## Generalization evidence

- All 128 complete Yes/No combinations evaluate without a vector template; the results include the six substantive candidate families plus a mixed fallback.
- An unselected complete action structure produces a meaningful candidate, and two different structures can select the same candidate.
- Identical actions produce equivalent decision evidence regardless of identity or party metadata.
- Changing one action changes themes only in its episode; removing a load-bearing action removes the affected candidate.
- Inverse actions emit competing themes.
- The three fentanyl stages count as one episode.
- Present and Not Voting remain excluded from support/opposition.
- Source scans cover the actual evaluator and find no selected IDs, member names, party branches, exact-vector selector, or paragraph-by-vector catalog.

The selected review profiles continue through the same frontend selector, adapter, `EditorialIssueExperience`, source presentation, and eligibility gates. All generated artifacts remain `human_approval_pending`, `not_promoted`, and `production_eligible: false`; the production registry is unchanged.

## Remaining limits

This is a seven-member, five-episode review sample. It validates architecture and bounded behavior, not national validity, motive, ideology, future behavior, or a comprehensive Justice philosophy. Candidate copy still requires human editorial approval.
