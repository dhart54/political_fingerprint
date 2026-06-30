# Milestone Plan: Fallback Static Loading Copy Cleanup

## Intent

- Immediate task: clean stale loading, static, fallback, and sample/default copy so the first visible frontend state matches the current plain-English voting-record interpreter direction.
- Larger-goal alignment: make Political Fingerprint immediately read as clear interpretation with receipts, not a stale methodology dashboard.

## Outcome

- User-visible or operational result: initial, loading, fallback, and sample states avoid stale movement language and misleading placeholder counts while preserving evidence access.

## Scope And Boundaries

- In scope: frontend loading/static/no-data/no-JS fallback copy, hero/stat fallback values, default/sample official labeling, targeted stale-label tests, rendered/static validation, review packet.
- Out of scope: backend/data/schema/methodology changes, Record Across methodology changes, broad redesign, production writes, token/config changes.
- Files/systems likely touched: `frontend/`, `docs/review_packets/`, this active plan.

## Decision Envelope

- Codex may decide and execute: replacing stale fallback labels with neutral or approved labels, hiding or neutralizing misleading fallback stats, adding focused tests, opening a focused PR.
- Explicit approval required for: product semantics changes, backend/data changes, production writes, broad redesign, merge/deployment actions if ambiguity appears.

## Definition Of Done

- [x] Required stale-term audit completed and findings classified.
- [x] Stale visible loading/static/fallback copy fixed without methodology or semantics changes.
- [x] Focused tests added or updated where practical.
- [x] Rendered/static validation completed or limitations documented.
- [x] Required commands pass: `npm run lint`, `npm run build`, `node --test lib\*.test.mjs`, `.next\static` internal-token scan with no matches.
- [x] Review packet updated.
- [x] Final reconciliation completed.
- [x] Focused PR opened and ready for review unless a true stop condition is reached.

## Baseline

- Branch/base commit: `codex/fallback-copy-cleanup` from `main` aligned with `origin/main`.
- Production/deployment state, if relevant: no production writes authorized or planned.
- Tracked working tree: clean at start.
- Known unrelated untracked artifacts: `docs/review_packets/chamber_filtering_data_integrity_audit.md`, `review_bundle_frontend_data_grounding/`.

## Implementation Sequence

1. Audit required frontend terms and classify matches.
2. Change only stale visible loading/static/fallback surfaces.
3. Add/update focused tests where practical.
4. Run required tests/build/static scan.
5. Perform local production-build rendered/static validation.
6. Create review packet and reconcile the plan.
7. Commit intended files and open PR.

## Progress Checklist

- [x] Discovery
- [x] Implementation
- [x] Validation
- [x] Documentation
- [x] Commit/PR readiness

## Discoveries

- Interpretation principles consulted before implementation; copy must avoid unsupported cross-time movement claims such as change, drift, steady, or trend.
- Required audit classification:
  - Stale visible loading/static/fallback copy changed: `frontend/app/page.js` hard-coded hero stat fallbacks (`548`, `8`, `--`) and unlabeled default Aaron Bean profile state.
  - Valid ready-state copy left unchanged: `ProfileQuickRead` uses `Strongest evidence`, `Coverage`, and `Record read`; `source links` remains a loaded metadata label; issue overview `sample` language is bounded evidence copy.
  - Valid historical/test fixture copy left unchanged: issue overview test fixture copy and Record Across Congresses source-link tests.
  - Unrelated/internal left unchanged: config `export default`, React status values such as `loading`, fallback variable names, internal `fetchDrift` API wrapper and dormant drift component copy, comparison control text.
  - Out of scope: broad removal of old drift-related components not rendered in the current first-page flow.

## Decisions And Rationale

- Prefer approved labels `Strongest evidence`, `Coverage`, and `Record read` for top-summary fallback labels where labels remain visible.
- Hide numeric hero stats until coverage metadata is available rather than hard-coding potentially inaccurate values.
- Mark the default Aaron Bean profile as a sample until the user selects an official through ZIP lookup, comparison, or search.

## Deviations Or Corrections

- Initial broad `.next` stale-copy scan also searched framework/server bundles and produced irrelevant matches. Narrowed static inspection to `.next/server/app/index.html`, the useful first-paint artifact.
- Local Record Across Congresses rendered validation could not be completed because the Next proxy requires `INTERNAL_API_TOKEN`; token/config changes are out of scope. The required static token scan and Record Across tests passed.

## Validation Results

- `node --test lib\*.test.mjs`: passed, 56 tests.
- `npm run lint`: passed with 8 existing React hook dependency warnings.
- `npm run build`: passed with the same 8 warnings.
- `rg -n "INTERNAL_API_TOKEN|X-Internal-API-Token|/internal/record-across-congresses" .next\static`: no matches.
- Static HTML stale-copy scan on `.next/server/app/index.html`: no matches for `Best read`, `Change`, `Steady mix`, `8 roll calls`, `-- source links`, or `548 legislators`.
- Rendered desktop production build with fixture backend: stale top-summary/fallback strings absent, sample/default handling clear, issue evidence rendered, no page-level horizontal overflow, no token/header/internal-route text visible.
- Rendered 390x844 mobile production build with fixture backend: stale strings absent, issue evidence rendered, no misleading stat placeholders, no page-level horizontal overflow.

## Production Writes

- Performed: no
- Scope: not authorized.
- Expected effects: none.
- Actual effects: none.

## Rollback Paths

- Revert the focused frontend, test, plan, and review-packet commit for this branch.

## Blockers

- None.

## Final Reconciliation

- Definition of done satisfied: yes; PR #61 is open and ready for review.
- Remaining limitations: local Record Across Congresses rendering requires internal token configuration; lint/build warnings pre-existed and are unrelated.
- Recommended next step: review PR #61.
