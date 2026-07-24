# Milestone Plan: Golden Render Validation Harness V1

## Intent

- Immediate task: add a deterministic rendered validation path for golden profile and issue-read surfaces.
- Larger-goal alignment: make future public-copy, theme, fallback, and profile-read work safer without relying on ZIP lookup, Vercel preview access, or production smoke.

## Outcome

- User-visible or operational result: local/CI validation can render known golden representative states from fixtures and assert public-copy safety, receipt access, and mobile/desktop layout behavior.

## Scope And Boundaries

- In scope: gated fixture route, fixture data, minimal component fixture seams, focused rendered tests, source-level tests where useful, and documentation.
- Out of scope: backend/schema/data changes, vote interpretation/readiness/support semantics, production data writes, Vercel configuration changes, ZIP lookup dependency, and new product copy behavior.
- Files/systems likely touched: `frontend/app/`, `frontend/components/`, `frontend/lib/`, `frontend/tests/`, `frontend/package.json`, `docs/plans/`, `docs/review_packets/`.

## Decision Envelope

- Codex may decide and execute: route name, fixture module shape, minimal component prop seams, Playwright script/config names, and focused assertion wording.
- Explicit approval required for: production writes, secrets/config changes, backend/schema changes, or any interpretation/counting/readiness semantic change.

## Definition Of Done

- [x] Fixture route is server-side gated by `ENABLE_GOLDEN_RENDER_FIXTURE=1`.
- [x] Fixture route renders profile summary, issue cards, expanded issue reads, receipts/full list/drawers, and Record Across surface or safe fallback.
- [x] Golden fixtures cover Valerie-like dominant/mixed reads, limited one-sided reads, and unsafe raw strings.
- [x] Rendered validation covers desktop and `390x844` mobile overflow and visible internal-token/route safety.
- [x] Existing source validation is preserved.
- [x] Tests/build/validation recorded.
- [x] Review packet or final documentation updated.
- [x] Focused draft PR opened.
- [x] Final reconciliation completed.

## Baseline

- Branch/base commit: `codex/golden-render-validation-harness-v1` from `main` at PR #69 merge commit `c7db4c43d86aae1b6ae0f2f1c5821bde14215fc3`.
- Production/deployment state, if relevant: PR #69 production smoke passed; no production write is authorized.
- Tracked working tree: clean at branch start.
- Known unrelated untracked artifacts: `docs/review_packets/chamber_filtering_data_integrity_audit.md`, `review_bundle_frontend_data_grounding/`.

## Implementation Sequence

1. Confirm Playwright dependency/browser setup is feasible.
2. Add fixture data and gated test-only route.
3. Add minimal fixture/prefetched data seams to existing components.
4. Add rendered Playwright test and source tests.
5. Run existing and new validation.
6. Document harness and open focused draft PR.

## Progress Checklist

- [x] Discovery
- [x] Implementation
- [x] Validation
- [x] Documentation
- [x] Commit/PR readiness

## Discoveries

- Checkpoint selected a gated fixture route with focused Playwright validation as the smallest reliable strategy.
- Current components fetch internally, so small fixture-data props are needed to avoid ZIP/API/network dependencies.
- `@playwright/test` was added as a direct dev dependency and Chromium browser setup succeeded.

## Decisions And Rationale

- Keep the route out of normal product navigation and gate it server-side with `ENABLE_GOLDEN_RENDER_FIXTURE=1`.
- Reuse existing product components rather than duplicating UI markup, so rendered checks exercise the profile/card/read/receipt bridge.
- Keep raw unsafe strings inside fixture receipts to prove top-level copy stays safe while detail surfaces remain inspectable.
- Add opt-in fixture props to profile, issue, and Record Across components while preserving production fetch behavior by default.

## Deviations Or Corrections

- `npm run test:golden-render` cannot launch Playwright inside the managed sandbox (`spawn EPERM`), so the exact command was rerun with approved escalation. The rendered validation passed after the browser/server process was allowed to spawn.

## Validation Results

- `node --test lib\goldenRenderFixture.test.mjs lib\profileNarrative.test.mjs lib\issueOverview.test.mjs`: passed, 30/30.
- `node --test lib\*.test.mjs`: passed, 75/75.
- `npm run lint`: passed with existing React hook dependency warnings; no errors.
- `npm run build`: passed with the same hook dependency warnings; gated fixture route built as a dynamic server-rendered route.
- `rg -n "INTERNAL_API_TOKEN|X-Internal-API-Token|/internal/record-across-congresses" .next\static`: no matches.
- `npm run test:golden-render`: passed, 2/2 after Playwright/Chromium setup and approved browser/server spawn.

## Production Writes

- Performed: no
- Scope: none.
- Expected effects: none.
- Actual effects: none.

## Rollback Paths

- Revert the scoped fixture route, component seams, tests, and docs from this branch.

## Blockers

- None.

## Final Reconciliation

- Definition of done satisfied: yes. Draft PR: https://github.com/dhart54/political_fingerprint/pull/70.
- Remaining limitations: the route is local/CI-only and requires `ENABLE_GOLDEN_RENDER_FIXTURE=1`; it does not replace production smoke for deployed user data. The rendered test currently covers Chromium desktop and `390x844` mobile sizing, not every browser engine. `npm install` reported 2 audit findings in the existing dependency tree after adding Playwright; no audit remediation was in scope.
- Recommended next step: review PR #70 and wait for hosted checks.
