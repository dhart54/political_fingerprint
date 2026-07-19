# Valerie Foushee Economy & Taxes staged website V2

## Review target

This draft preview projects the approved proposed fields from
`docs/editorial/valerie_foushee_economy_gold_v2/review_packet.json` at
`db7eb324136866c360a68a2f996e91907eb3d76d` into the existing representative
evidence flow. It remains limited to Valerie P. Foushee (`F000477`), Economy &
Taxes, the 119th Congress, and the nine reviewed roll calls.

All candidate and human-review statuses remain `human_approval_pending`. The
preview does not change persistence, API, counting, alignment, readiness, or
production data.

## Progressive disclosure

- Collapsed: approved 10-second headline, practical choice, and member action/result.
- First expansion: prior baseline, mechanism, affected people/programs/businesses/agencies, scale or timing, and what happened next.
- Deeper detail: approved two-minute detail, attributed institutional supporter and opponent arguments, argument-evidence boundary, later history, caveats, and human-readable official-source links.

The two controls (rolls 263 and 180) use a separate context-only presentation
and remain excluded from substantive pattern counting. Roll 310 remains `Not
Voting`. The six substantive votes continue to represent four policy episodes.

## Rendered review

- Desktop: reviewed at 1280 x 900.
- Mobile: reviewed at 390 x 844 with no horizontal overflow.
- H.R. 3944 dollar figures remain absent from collapsed cards and appear only after expansion.
- H.Con.Res. 14 states that the resolution created a framework for later legislation and did not itself change taxes or benefits.
- Roll 310 reads as a non-vote, and rolls 281/285 and 50/100 remain separate stage-specific cards.
- The deeper layer attributes arguments to institutional advocates and does not present them as Foushee's motive.

## Wording reconciliation

No approved interpretation field was altered. The implementation adds only
presentation labels and introductory navigation copy. Internal source locators
for the House Clerk are normalized to the reader-facing phrase "member vote and
roll-call totals"; source URLs and claim/source mappings are unchanged.

## Validation

- Backend staged-content, editorial-gold, manual-interpretation, and benchmark regressions: 52 passed.
- Frontend Node tests: 86 passed.
- Playwright desktop/mobile rendered regressions: 4 passed.
- Deterministic content generator `--check`: passed.
- ESLint: passed with eight pre-existing React hook warnings and zero errors.
- Production frontend build, including type validation: passed.

## Human review gates

The draft preview is intended for rendered comprehension review. It does not
assign `human_approved` or `gold_benchmark`, and it is not authorization to
merge or deploy to production.
