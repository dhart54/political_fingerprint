# M11M National Security Site Integration

## Intent and larger-goal alignment

Build a production-shaped, publication-inactive site integration candidate for Valerie Foushee's accepted 119th-Congress National Security & Foreign Policy record. This is the first of three independent gates: site integration candidate, production/publication activation candidate, and live verification.

## Outcome

The existing representative journey can render the 18 exact M11L wording items through the established issue-summary and vote-receipt experience when an explicit local review flag is enabled. Default runtime selection remains unchanged and fail-closed.

## Scope and boundaries

- Base: `55dd4a2e05bdd3d61a328793b8349a952df000d6`.
- Reuse the current presentation API shape, selected-issue route, and display-only frontend.
- Add generic support for synthesis and notable-choice sections.
- Preserve the M11L wording byte-for-byte at the field level.
- Keep H.R. 8800 / `house:119:2:278` blocked and out of every finding.
- Keep publication, production persistence, database writes, deployment, and live activation false.
- Do not inspect or modify either protected user-owned ZIP.

## Decision envelope

The milestone may add an inactive candidate compiler, validator, opt-in preview transport, generic UI rendering, tests, fixtures, and review evidence. It may not weaken active-publication selection or alter accepted M11A-M11L/Justice artifacts.

## Definition of done

- Deterministic candidate binds the exact M11L authority, implementation, and parity identities.
- All 18 wording items map to governed semantic inputs and supporting action IDs.
- The real frontend path renders overview, syntheses, patterns, trajectory, notable choices, limitations, and vote navigation.
- Scope 119 and all behave as bounded; other scopes fail closed.
- Default publication API remains receipts-only for National Security.
- Backend, frontend, accessibility, responsive, regression, deterministic regeneration, formatting, and artifact validation pass.
- Draft PR is opened and work stops for independent review.

## Baseline

- Justice is the sole publication-active production reference.
- National Security M11L wording is canonical internally but not public or production-selectable.
- Existing public selector only accepts active, approved, production-eligible database rows.
- Existing frontend already consumes generic presentation payloads but has no synthesis/notable-choice sections.

## Implementation sequence and progress

- [x] Verify exact base and protected-ZIP boundaries.
- [x] Inspect Justice compiler, selector, API, and selected-issue frontend seams.
- [x] Add deterministic M11M candidate compiler/validator and governed artifacts.
- [x] Add opt-in, fail-closed preview transport without changing active selection.
- [x] Extend generic frontend sections and evidence navigation.
- [x] Add backend/frontend/adversarial tests and render packet.
- [x] Run required validation and inspect diff.
- [x] Commit, push, open draft PR, and stop.

## Discoveries and decisions

- The existing active selector is deliberately coupled to publication controls. M11M will not pass inactive data through that selector or relax its gates.
- M11L contains exactly 18 items: one overview, two syntheses, eight repeated patterns, one trajectory, and six notable choices.
- The accepted public compiler predates synthesis-card and notable-choice display sections. A bounded generic presentation-candidate compiler is required; it will project accepted wording only and perform no semantic inference.
- Preview transport will require both an exact request token and a server-side opt-in flag. Production defaults remain off.
- `docs/interpretation_principles.md` was read before UI/copy work. Direction is sourced only from accepted wording metadata; raw Yea/Nay never creates an analytical label.

## Deviations and corrections

- The initial production-shaped API preview exposed only the 31 precomputed National Security rows. The bounded preview transport now replaces the 119th-Congress domain slice with all 82 governed M11M rows while retaining non-119 evidence in `all` scope.
- The selected-finding strip previously defaulted a directionless finding to `mixed`. It now uses the neutral `bounded` fallback, so the accepted Ukraine wording and four receipt links never create an unauthorized public Mixed/± label.
- The blocked H.R. 8800 test control initially used `not_voting`; it now preserves the official `nay` action while remaining source-blocked, uninterpreted, non-counting, and excluded from every analytical finding.

## Validation results

- Deterministic M11M regeneration/check: passed; 18 wording items, 32 uniquely mapped actions/episodes, 82 preview evidence rows, one blocked control.
- M11A-M11M backend regressions: 177 passed.
- Justice/API regressions: 190 passed; one base-existing stale assertion remains (`applied_production_active` expected versus the accepted base value `full_record_applied_production_active_read_only_verified`).
- Semantic IR validator and unit regression: passed (12 accepted references, 4 accepted held-out references; 26 tests).
- Full frontend Node unit regression: 132 passed.
- M11M plus accepted frontend/production-evidence Playwright regressions: 36 passed, 2 capture-only tests skipped; dedicated M11M capture: 1 passed.
- Responsive review at 1440, 1024, 390, and 320 CSS pixels plus 200 percent zoom: passed with no horizontal overflow; five screenshots regenerated and visually inspected.
- Next.js production build: passed with eight pre-existing React hook warnings and no errors.
- Ruff check/format, Python compilation, JSON parsing, and `git diff --check`: passed.

## Production writes performed

None. No database, publication, deployment, or production write is authorized.

## Rollback

Revert the M11M branch commit. Since preview transport is opt-in and no persistence occurs, rollback requires no data or publication action.

## Blockers

None.

## Final reconciliation

The candidate provides the requested real-route review experience behind two exact opt-ins, retains the active publication selector unchanged, preserves the accepted M11L text and upstream identities, and keeps H.R. 8800 outside all analysis. No database, publication, production, deployment, or live-site state changed. Draft PR #145 is the independent human-review stop.
