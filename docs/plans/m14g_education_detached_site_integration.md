# M14G: Education detached site-integration preview

## Intent and stopping point

Render the human-approved Foushee Education & Workforce wording through the
existing Selected Issue Experience V1.1, backed by the exact reviewed 17-action
ledger and current V2 receipt semantics. Produce deterministic review artifacts
and real desktop/mobile screenshots, open a draft PR, and stop for independent
product review.

## Scope and non-scope

- Exact baseline: `50777a5fd1ce84763e6a294db25578639aa5dce7`.
- Isolated branch: `codex/m14g-education-detached-preview`.
- Add one preview-only router, one explicit preview token, focused tests and
  validator/builder support, review artifacts/screenshots, and exact-head CI.
- Preserve the existing Selected Issue Experience components, M13 artifacts,
  M14A-M14F accepted inputs, shared corpora, publication state, and other issue
  domains byte-for-byte.
- No database or production write, publication, activation, deployment, merge,
  or human acceptance authority.

## Implementation sequence and definition of done

1. Pin M14F wording/authority, M14D ledger/authority, and V2 core/projection via
   the promotion manifest.
2. Compile one overview, two repeated patterns, one notable choice, no synthesis
   or trajectory, six finding-supporting actions, and seven retained limitations.
3. Project exactly 17 governed receipts from V2, including Not Voting and rich
   H.R. 5408 regressions, through `/preview/m14g/...` endpoints gated by both
   server opt-in and the M14G token. Keep the M13N runtime manifest byte-exact.
4. Commit the final runtime and candidate as the capture head, then generate the
   review package, screenshot manifest, and four real-application captures from
   that exact commit. Bind every capture to the capture head.
5. Run focused and inherited regressions, inspect the bounded diff, open a draft
   PR, and verify `m14g-exact-head` at the exact PR head.

## Validation and review boundary

- Focused Python and frontend token tests plus deterministic artifact checking.
- M14A-M14F regression suites/builders and a bounded scope guard.
- Frontend build and real backend/frontend Playwright capture at desktop and
  phone widths.
- Review confirms default/public behavior is unchanged and the three protected
  UI files remain byte-identical.

## Closure checks

- Require an exact 40-character capture commit that is an ancestor of the final
  review head.
- Permit only the four screenshots, screenshot manifest, and review package to
  differ after the capture commit; runtime and candidate code therefore remain
  identical to the code actually rendered.
- Require exact governed GovInfo locators for EO 14251, EO 14168, and 20 U.S.C.
  §1094, with source-type-specific public labels and no generic landing links.
- Final stopping point remains a green draft PR for independent product review;
  merge, deployment, publication, activation, and production writes are out of
  scope.
