# Review Packet: Public Editorial Product Frontend V1

## Review focus

This milestone converts the generic editorial issue experience into a public product contract while leaving every real editorial slice unpublished.

Review the representative route for:

- conclusion-first hierarchy and plain-language evidence strength;
- explicit reviewed-period, vote, episode, Not Voting, Present, and missing-record coverage;
- safe developing, limited, no-editorial, and procedural-only states;
- issue availability labels that distinguish reviewed analysis, vote evidence, and a limited record;
- progressively disclosed vote context and official receipts;
- separation between outer review chrome and the exact public renderer;
- keyboard operation and layouts from 390 px through wide desktop.

## Governance checks

- Real publication statuses are unchanged.
- `frontend/lib/editorialIssueProductionSlices.mjs` remains unchanged and contains no newly eligible slice.
- Editorial source artifacts, vote meanings, inference levels, candidate selection, and source mappings are unchanged.
- The public adapter translates supplied structured analysis; React does not calculate political conclusions.
- Synthetic fixtures are confined to the guarded review route and tests.

## Render matrix

The local review bundle captures strong repeated, selective/conditional, contested, developing, Not Voting, basic fallback, procedural-only, mixed navigation, expanded vote, arguments/context, grouped sources, mobile summary, mobile expanded vote, outer review harness, and production-mode pending fallback states.

Expected local directory:

`review_bundle_public_editorial_product_frontend_v1/screenshots/`

## Validation record

- Frontend unit tests: 108 passed.
- Responsive/accessibility Playwright checks: 17 passed.
- Focused civic/editorial backend regressions: 42 passed.
- ESLint: passed with zero errors and eight pre-existing React hook warnings.
- Production build and type validation: passed.
- Deterministic editorial builders: covered by the focused regression suite and their `--check` tests.
- Production-registry isolation, forbidden public terminology, runtime genericity, and diff hygiene: recorded in the active milestone plan.
