# Milestone Plan: Frontend Pass A

## Intent

- Immediate task: Replace the stacked representative route with a bounded
  find-representative → overview → issue → reviewed analysis → exact receipts
  journey.
- Larger-goal alignment: Establish the route-ready presentation foundation
  without treating benchmark findings as full representative-level issue
  syntheses.

## Outcome

- User-visible or operational result: A single-scroll, responsive voter journey
  with stable URL state, truthful Congress scope, light issue discovery,
  scope-governed reviewed analysis, and one chronological action ledger.

## Scope And Boundaries

- In scope: deterministic public review-state catalog and read-only adapter;
  primary route/components; public serializer finding roles; focused backend,
  frontend, browser, accessibility, and documentation updates.
- Out of scope: production or publication mutation; new interpretation;
  full-record Foushee Justice authority; episode prose on the live page;
  deferred comparison, preference, alerts, race, and across-Congress tools;
  multi-route redesign; merge or manual deployment.
- Files/systems likely touched: one generated catalog and builder, presentation
  API/serializer/tests, route-ready frontend components/helpers/tests, and Pass A
  plan/design/review documents.

## Decision Envelope

- Codex may decide and execute: component boundaries, non-semantic UI behavior,
  deterministic adapter structure, styling within Option 1.1, test fixture
  structure, and focused documentation.
- Explicit approval required for: production/publication writes, methodology or
  accepted Semantic IR changes, active artifact/registry mutation, merge, or a
  new public route.

## Definition Of Done

- [x] Finder is the only pre-selection primary content and selected state is
  compact, URL-persistent, and truthful about scope.
- [x] Issue discovery, reviewed-sample presentation, optional episode boundary,
  and chronological ledger meet the supplied data contracts without React
  analytical inference.
- [x] Catalog build/check and identity/scope fail-closed behavior are validated.
- [x] Tests/build/browser/accessibility/governance validation recorded.
- [x] Design record and review packet updated.
- [x] Final reconciliation completed.

## Baseline

- Branch/base commit:
  `codex/frontend-pass-a-representative-issue-foundation` from
  `13a51154c3c5dfce38ca717db1f3819b1fef9e23`.
- Production/deployment state, if relevant: one historically active Foushee
  Justice 119th-Congress benchmark-sample presentation; this milestone performs
  no production or publication write.
- Tracked working tree: clean at branch creation.
- Known unrelated untracked artifacts: none reported by `git status --short`.

## Implementation Sequence

1. Build and test the validated, deterministic, non-authorizing public
   review-state catalog and merge it into the existing read-only presentation
   response only on exact identity/scope agreement.
2. Refactor the primary route into independent finder, header, scope, issue,
   analysis, optional episode, navigation, ledger, and receipt components with
   stable URL state.
3. Update contracts and Pass A documentation; run focused through release-level
   validation, rendered inspection, final diff review, commit, push, preview
   inspection, and draft PR.

## Progress Checklist

- [x] Discovery started; required governing documents and current runtime read.
- [x] Implementation
- [x] Validation
- [x] Documentation
- [x] Commit/PR readiness

## Discoveries

- The active presentation artifact already carries compiled proposition
  direction in `compiled_semantic_meaning`; the API can serialize it without
  modifying approved artifact bytes or inferring from wording/order.
- Full-record review validation is reusable through
  `validate_review`; runtime should load only generated public fields rather
  than source review manifests.
- The existing protected-file manifest was authored against canonical LF
  repository bytes while native Windows checkout bytes are CRLF. Exact-byte
  validation therefore failed before the Pass A catalog could be built even
  though the governed text was unchanged.
- The local database contains the production-style representative catalog, so
  fallback search tests must explicitly isolate the fixture path to remain
  deterministic.

## Decisions And Rationale

- Generate the runtime catalog under the backend package so deployed reads do
  not depend on repository documentation paths.
- Keep catalog state non-authorizing and require a separately eligible active
  presentation before analytical copy can render.

## Deviations Or Corrections

- The merged full-record validator now accepts an exact digest first and then,
  for governed text suffixes only, the narrowly canonical CRLF-to-LF
  equivalent. Its contract test uses the same matcher. The stale incident-file
  hash was corrected to the current canonical LF digest; no report wording,
  publication record, or approved presentation bytes changed.
- Search API fallback tests now patch the database lookup boundary instead of
  relying on ambient `DATABASE_URL` state.
- The final screenshot fixture waits for issue/ledger readiness and removes the
  development-only Next.js portal before capture.

## Validation Results

- `python scripts/build_public_review_state_catalog.py --check` — passed.
- `python scripts/run_editorial_pipeline.py validate --tier semantic --json` —
  all seven semantic/schema/full-record/reference/test/governance commands
  passed; the runner required narrow permission to write temporary contract
  fixtures on managed Windows.
- Focused public catalog, presentation API, and profile/search API tests — 62
  passed.
- `node --test frontend/lib/*.test.mjs` — 105 passed.
- `npm run lint --prefix frontend` — passed with eight pre-existing hook
  warnings in deferred components and no errors.
- `npm run build --prefix frontend` — passed; `/` compiled as a static route.
- Cutover smoke — 3 passed. IR presentation — 4 passed. Pass A — 12 passed
  with screenshot capture, then 11 passed and the optional capture test skipped
  in the final no-output regression run.
- Browser coverage passed at 1440, 1024, 390, and 320 pixels, keyboard focus,
  reduced motion, and 200% zoom. In-app browser inspection found no console
  errors or horizontal overflow.
- Documentation governance, full-record terminology, changed JSON parsing, and
  `git diff --check` passed.
- Rendered evidence:
  `C:/Users/Dylan/.codex/visualizations/2026/07/29/019fb04c-a952-77f2-a2df-f7ff9a767a7a/frontend-pass-a-desktop.png`
  and
  `C:/Users/Dylan/.codex/visualizations/2026/07/29/019fb04c-a952-77f2-a2df-f7ff9a767a7a/frontend-pass-a-mobile.png`.

## Production Writes

- Performed: no
- Scope: none
- Expected effects: none
- Actual effects: none

## Rollback Paths

- Revert the cohesive branch commit; no data or publication rollback is needed.

## Blockers

- None.

## Final Reconciliation

- Definition of done satisfied: yes; implementation, trust boundaries,
  rendered behavior, and the final diff were reconciled before publication
  handoff.
- Remaining limitations: the live selector intentionally supplies no policy
  episodes; eight lint warnings remain in deferred pre-Pass-A components.
- Recommended next step: review CI and the Vercel preview, then merge the draft
  PR if those checks remain green.
