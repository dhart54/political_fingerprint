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
- First expansion: two compact groups, "What changed" and "Impact and outcome."
- Deeper detail: side-by-side attributed arguments, approved two-minute detail, consolidated important context, and a grouped `Official sources (N)` disclosure.

Only one parent record opens at a time. Closing a parent also resets its deeper
disclosures. The same two first-level groups and competing arguments stack on
mobile.

The two controls (rolls 263 and 180) use a separate context-only presentation
and remain excluded from substantive pattern counting. Roll 310 remains `Not
Voting`. The six substantive votes continue to represent four policy episodes.

## Rendered review

- Wide desktop: reviewed at 1440 x 1000.
- Desktop/laptop: reviewed at 1280 x 720 and 1024 x 768.
- Tablet: reviewed at 768 x 1024.
- Mobile: reviewed at 390 x 844 with no horizontal overflow.
- H.R. 3944 dollar figures remain absent from collapsed cards and appear only after expansion.
- H.Con.Res. 14 states that the resolution created a framework for later legislation and did not itself change taxes or benefits.
- Roll 310 reads as a non-vote, and rolls 281/285 and 50/100 remain separate stage-specific cards.
- The deeper layer attributes arguments to institutional advocates and does not present them as Foushee's motive.

## Issue-level synthesis

The final primary issue read is:

> In this sample, Foushee voted against specific proposals involving government
> funding, frameworks for later tax-and-spending legislation, military
> construction and veterans programs, and SBA loan eligibility. The six
> substantive votes represent four policy episodes. They reveal several
> specific voting patterns, but this sample is not yet broad enough to establish
> one overarching Economy & Taxes philosophy.

The visible patterns are:

- opposition at both stages of the 2025 government-funding episode;
- opposition at both stages of the FY2025-FY2034 budget-framework episode;
- opposition to the House military-construction and veterans funding proposal;
- opposition to immigration-status restrictions on SBA-backed business loans.

Party alignment appears only afterward as secondary `Voting context`, with an
adjacent motive and repeated-stage boundary.

The presentation helper encodes three inference levels: recorded action,
bounded voting pattern, and broader political philosophy. The third level is
permitted when supported by enough independent episodes, mechanisms, time,
contrary evidence, and a published theme definition. This slice remains at the
bounded-pattern level.

## Wording reconciliation

No approved vote-interpretation field was altered. The issue-level synthesis,
pattern statements, voting-context boundary, and inference-ladder contract are
new presentation copy authorized by the rendered-review brief. Existing
argument, detail, lifecycle, and caveat fields remain unchanged internally;
the public UI consolidates overlapping boundaries into `Important context`.

Source URLs and claim/source mappings are unchanged. Public source records now
carry a human-readable name, locator, and purpose group; canonical URLs are
deduplicated, and internal source IDs remain excluded.

The final terminology pass changes only public labels: `Prior baseline` becomes
`Before this vote`; `Mechanism` becomes `Change at stake`; `Affected` becomes
`Who it affected`; `Scale or timing` becomes `Scale and timing`; `Next` becomes
`Outcome`; and `Who, when, and what happened` becomes `Impact and outcome`.

## Validation

- Backend staged-content, editorial-gold, manual-interpretation, and benchmark regressions: 52 passed.
- Frontend Node tests: 88 passed.
- Playwright desktop/laptop/tablet/mobile rendered regressions: 5 passed in the focused run.
- Deterministic content generator `--check`: passed.
- ESLint: passed with eight pre-existing React hook warnings and zero errors.
- Production frontend build, including type validation: passed.

Eight local review captures cover the issue summary, bounded patterns, voting
context, collapsed record, first expansion, competing arguments, important
context, grouped sources, a context-only record, and mobile rendering. They are
stored outside the repository in the scoped Codex visualization folder.

## Human review gates

The draft preview is intended for rendered comprehension review. It does not
assign `human_approved` or `gold_benchmark`, and it is not authorization to
merge or deploy to production.
