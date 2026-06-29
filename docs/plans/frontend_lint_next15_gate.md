# Milestone Plan: Frontend Lint Next 15 Gate

## Intent

- Immediate task: make `frontend` `npm run lint` non-interactive and suitable as a repeatable validation gate.
- Larger-goal alignment: restore a CI-quality frontend safety check before additional UI and product work continues.

## Outcome

- User-visible or operational result: `npm run lint` runs a configured Next 15-compatible ESLint command, exits `0` on pass, exits non-zero on lint failures, and does not open the Next migration/setup prompt.

## Scope And Boundaries

- In scope: frontend package scripts, ESLint/Next lint config if needed, targeted low-risk lint fixes only if required, validation note in a review packet.
- Out of scope: product feature work, UI changes, backend changes unless strictly required by shared tooling, schema/migrations, evidence/data changes, production writes.
- Files/systems likely touched: `frontend/package.json`, frontend ESLint config files if present or needed, `docs/review_packets/`, this active plan.

## Decision Envelope

- Codex may decide and execute: the exact non-interactive ESLint command after repo inspection; smallest compatible config changes; low-risk direct lint fixes needed for the gate.
- Explicit approval required for: broad product-code churn, changes outside frontend tooling, production writes, schema or product semantics changes.

## Definition Of Done

- [x] `npm run lint` is non-interactive, Next 15-compatible, and passing from `frontend`.
- [x] `npm run build` passes from `frontend`.
- [x] `node --test lib\*.test.mjs` passes from `frontend`.
- [x] Record Across Congresses static scan is clean.
- [x] Tests/build/validation recorded.
- [x] Review packet updated or created.
- [x] Final reconciliation completed.

## Baseline

- Branch/base commit: `codex/frontend-lint-next15-gate` from `main` at `d809039fa0e139390dc11451eff6e6b1676ec6fa`.
- Production/deployment state, if relevant: no production deployment required or authorized.
- Tracked working tree: clean at branch creation.
- Known unrelated untracked artifacts: `docs/review_packets/chamber_filtering_data_integrity_audit.md`; `review_bundle_frontend_data_grounding/`.

## Implementation Sequence

1. Inspect frontend package scripts, dependency versions, and ESLint/Next config.
2. Reproduce or confirm the current lint behavior, then choose the smallest Next 15-compatible lint command/config change.
3. Implement scoped tooling changes and any directly required low-risk lint fixes.
4. Run required validation: lint, build, targeted tests, static scan.
5. Document results in a review packet and reconcile final scope.

## Progress Checklist

- [x] Discovery
- [x] Implementation
- [x] Validation
- [x] Documentation
- [x] Commit/PR readiness

## Discoveries

- `frontend/package.json` used `next lint`; no frontend ESLint config existed.
- Neither `eslint` nor `eslint-config-next` was listed as an explicit frontend dev dependency before this milestone.
- Direct ESLint invocation found 1 error and 8 warnings on first run; the error was a low-risk JSX apostrophe escape.

## Decisions And Rationale

- Use `eslint .` for `npm run lint` because it is non-interactive, CI-safe, and matches the current Next guidance to use ESLint directly after `next lint` removal.
- Add `frontend/eslint.config.mjs` using `FlatCompat` with `next/core-web-vitals` because the installed Next 15 ESLint config exposes the shared config through the classic config shape.
- Leave existing hook dependency warnings unchanged because resolving them may require behavior-sensitive effect changes outside a tooling-only milestone.

## Deviations Or Corrections

- Initial dependency install selected the latest `eslint-config-next`; corrected to align the config package with the installed Next 15 line.
- Regenerated package metadata after noticing the first install refreshed more dependency metadata than needed.

## Validation Results

- `npm run lint`: passed, exit `0`; non-interactive `eslint .`; 0 errors and 8 existing hook dependency warnings.
- `npm run build`: passed; Next 15.5.12 production build completed with the same 8 hook warnings.
- `node --test lib\*.test.mjs`: passed, 55/55 tests; existing Node module-type warning emitted.
- `rg -n "INTERNAL_API_TOKEN|X-Internal-API-Token|/internal/record-across-congresses" .next\static`: clean, no matches; `rg` exit `1` indicates no matches.

## Production Writes

- Performed: no
- Scope: none
- Expected effects: none
- Actual effects: none

## Rollback Paths

- Revert the frontend lint script/config changes and the review packet/plan updates from this branch.

## Blockers

- None currently.

## Final Reconciliation

- Definition of done satisfied: yes. `npm run lint` is now a non-interactive `eslint .` gate and all required validation passed.
- Remaining limitations: 8 existing hook dependency warnings remain non-failing; targeted Node tests still emit the existing module-type warning; package audit still reports 2 dependency vulnerabilities outside this milestone.
- Recommended next step: open the PR for review and merge after checks are green.
