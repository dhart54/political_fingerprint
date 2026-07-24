# Episode-first editorial product v1 review packet

## Outcome

The review-mode rich editorial surface now leads with one bounded issue conclusion and groups detailed action receipts inside policy episodes. The default hierarchy is conclusion, evidence label, compact coverage, structured findings, featured episodes, collapsed complete record, and secondary context.

The three reviewed slices remain pending, unpromoted, and production-ineligible. No production registry, vote fact, source URL, approval status, benchmark status, or recorded action changed.

## Reviewed slices

- Foushee — Economy & Taxes: six substantive actions grouped into four authoritative episodes, with one separate Not Voting action and two context controls.
- Foushee — Justice & Public Safety: seven substantive actions grouped into five episodes, including one three-action fentanyl trajectory, plus six procedural controls.
- Massie — Justice & Public Safety: the same neutral action and episode evidence with a Massie action overlay and a policy-mechanism divide synthesis.

## Evidence and civic-integrity checks

- Justice legislative facts, arguments, caveats, and source locators are neutralized before member overlays are applied.
- Tests exercise every shared Justice action with Yea, Nay, Not Voting, and not-yet-serving overlays and reject inherited cohort names or opposite actions.
- Yea, Nay, Present, Not Voting, not yet serving, no longer serving, and missing evidence remain distinct. Only Yea and Nay are analytically eligible.
- Cross-Congress policy-family fixtures keep 118th- and 119th-Congress episodes separate.
- Procedural and context-only actions remain non-counting; Not Voting remains outside support/opposition.

## Rendered review

The local golden-render fixture was reviewed at 1440 px, 768 px, and 390 px. The rich surface showed no page or component horizontal overflow, one title within `data-public-surface`, zero open disclosures by default, four Economy featured episodes, and five Justice featured episodes. Episode expansion exposed the common episode explanation and nested action receipts; action expansion preserved mechanism, affected groups, scale/timing, outcome, stage-specific arguments, neutral debate boundary, and official sources.

Rendered inspection found and corrected two defects before the final gate:

1. Economy action chips initially followed source-array order rather than the authoritative episode timeline.
2. Justice procedural source locators initially retained Foushee's name in Massie's complete record.

## Validation

- `python -m pytest backend/tests/test_editorial_member_overlay.py -q`: 13 passed.
- `python -m pytest backend/tests/test_justice_cross_member_validation.py backend/tests/test_valerie_foushee_justice_public_safety_editorial_gold_v1.py backend/tests/test_valerie_foushee_economy_editorial_gold_v2.py -q -p no:cacheprovider`: 33 passed.
- `node --test frontend/lib/*.test.mjs`: 120 passed across the complete frontend library test suite.
- `npm run build`: passed; pre-existing hook warnings remain outside this milestone.
- `npm run test:golden-render`: 8 passed, 12 skipped. Eleven skipped cases encode the superseded vote-first/flat-card contract; replacement episode-first hierarchy, disclosure, and responsive tests pass. The screenshot-capture test remains intentionally opt-in.

## Publication boundary

This milestone changes review presentation and contracts only. Human editorial approval, gold-benchmark promotion, real-slice production eligibility, production registry inclusion, merge, and manual deployment remain separate and were not performed.
