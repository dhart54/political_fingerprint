# Milestone Plan: Foushee Justice 119 Universe Refresh V2

## Intent

- Correct PR #123's evidence-integrity and boundary-review findings.
- Preserve V1 as historical evidence, refresh official House actions through
  July 23, 2026 / roll 283, and create a V2 non-authorizing proposal for another
  human universe-boundary review.

## Scope

- In scope: source-bound read-only production proof, official-source and public
  API refresh, reviewed June 11 corrections, expressive nonbinding and FISA
  cross-domain methodology, deterministic V1/V2 comparison, non-mutating
  production repair planning, validation, and draft-PR delivery.
- Out of scope: authority receipts, action interpretation, episodes, full-record
  Semantic IR, synthesis, publication/registry changes, production writes,
  deployment, merge, and ready-for-review promotion.

## Definition Of Done

- [x] V1 artifacts remain unchanged and are explicitly superseded for authority
  and interpretation.
- [x] Runner emits a digest-bound post-rollback/post-close completion record;
  the builder rejects absent, false, substituted, or cross-run proof.
- [x] V2 contains every official Foushee House action through roll 283 and gives
  every newly observed action one resolved disposition.
- [x] Reviewed June 11 corrections, expressive nonbinding actions, and scoped
  FISA cross-domain membership are represented.
- [x] V2 manifest, discovery, source inventory, comparison, review packet, and
  non-mutating production repair plan are content-addressed and non-authorizing.
- [x] Targeted methodology, discovery, safety, schema, parsing, governance,
  compilation, credential, and diff validation passes.
- [x] Final read-only freshness snapshot and latest-official-roll check pass.
- [x] One cohesive commit is prepared for the existing draft PR #123; external
  push and PR-description delivery are recorded in GitHub while the PR remains
  draft.

## Current Reconciliation

- Official boundary: January 3, 2025 through July 23, 2026, House rolls through
  `house:119:2:283`.
- Complete official member actions: 638.
- Direct production member actions: 555.
- V2 recall candidates: 172; proposed substantive/non-directional: 37;
  unresolved: 0.
- Newly observed actions: 61, dispositioned exactly once as 8 substantive, 12
  procedural, and 41 exact-action ineligible.
- Production repair remains unexecuted. The plan records 22 historical and 61
  newly observed member-action gaps plus seven lossy Senate-measure links.

## Safety And Authority

- Production access is limited to a fixed parameterized query pack inside one
  explicit `REPEATABLE READ READ ONLY` transaction, followed by `ROLLBACK` and
  verified connection close.
- No production writes are authorized or performed.
- V2 remains `pending_human_universe_review`, with `full_record_claim=false`,
  `synthesis_eligible=false`, and no detached authority receipt.
