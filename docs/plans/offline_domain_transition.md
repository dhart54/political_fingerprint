# Offline four-to-five domain transition proof

## Intent, authority, and outcome

Deliver synthetic unit tests, mocked ordinary-route browser regressions, and this
release-order plan as a validated draft PR. Dylan explicitly approved the offline
assignment on 2026-10-19. No merge, publication, activation, production write,
runtime/manifest change, configuration change, or manual deployment is authorized.

This proves existing serving boundaries before a separately authorized release;
it cannot approve a real candidate or manufacture a production binding.

## Baseline and scope

- Supported host/project: `local`, `local-9f0a954bc56e7ae25eac9d04e83f5d7d`.
- Fresh main/base: `36fb94f24f42e2c60954acaaaed559fcc872de89`.
- Separate worktree `.w/domain-transition`, branch
  `codex/offline-domain-transition`; existing engineering work preserved.
- Infrastructure `.w/infra` and Immigration `.w/ib` remain independently owned.
- Checked-in serving fixture: four reviewed domains (Education, Environment,
  Justice, National Security), six selected entries, historical roots 245/239/251/248.
  This is a repository-contract baseline, not a live production preflight.
- Expected scope: one test-only fixture module, one unit test file, additions to
  the already-enumerated release browser spec, and this plan. No generated output.
- Read root instructions, interpretation principles, operating/planning,
  editorial-standardization, milestone, PR, and rendered-validation workflows.
  No additional directory instruction applies to these test files.
- Reuse Education locator tests' complete-source hashing, both scopes, rollback,
  mocked public interfaces, and independent summary/receipt fallback patterns.

## Contract and readiness limits

`projectRecordCard` verifies all eight domain slots, the exact reviewed set,
member/scope, complete presentation hashes (including provenance), coverage
bindings, and selected findings. Preserve these checks unchanged.

The synthetic fifth domain uses an existing receipts-only Economy slot with
explicit TEST ONLY labels and synthetic provenance. It is neither Infrastructure
candidate content nor accepted/publication-eligible evidence. Six existing
selections remain unchanged; no fifth-domain finding is selected or approved.

| Manifest argument | Mocked serving payload | Expected overview |
| --- | --- | --- |
| M4 | P4 | ready, six entries |
| M4 | P5 | withheld: source_mismatch |
| M5 | P4 | withheld: incomplete |
| M5 | P5 | ready in projector unit test only |

M5 is an in-memory synthetic test argument, never a runtime artifact. The ordinary
route statically imports `recordCardContent.json`; it cannot serve M5/P5 readiness
without a separately authorized manifest/runtime binding. Browser tests therefore
prove M4/P4, staging without serving changes, M4/P5 withholding, fallback access,
P4 restoration, and stale-response isolation. They do not claim a browser M5
deployment. The UI hash check also does not prove database registry ownership,
approval, persistence, backend selection, or production rollback correctness.

## Prospective release and rollback order (not execution authority)

1. Before any future release, obtain the actual candidate acceptance/publication
   authority, sealed graph/roots, exact full-response hashes for 119/all, intended
   member, and approved target manifest. Capture complete current registry rows
   and serving/manifest bytes; validate bounded owned-state rollback separately.
2. Stage immutable artifacts without selecting them. Verify P4/M4 remains exact;
   mere artifact persistence must not be treated as activation or M5 readiness.
3. Gate the release on a reviewed target binding and explicit handling of the
   intermediate mismatch. Neither update order preserves overview availability
   under the existing exact-set contract: M4/P5 and M5/P4 both withhold it. A
   zero-gap compatibility design is a separate runtime/product decision.
4. After separate authorization, change only the bounded reviewed pair, observe
   exact API member/scope/source hashes and the selected overview plus issue
   summaries/receipts, and stop on mismatch. These tests supply no write command.
5. Rollback manifest first: M5/P5 -> M4/P5 (withheld) -> M4/P4 (ready).
   Rollback serving selection first: M5/P5 -> M5/P4 (withheld) -> M4/P4 (ready).
   Verify complete P4/M4 restoration and idempotent reads; keep staged immutable
   artifacts inactive rather than deleting historical evidence. Real rollback
   must retain the existing owned-state/drift checks and its approved envelope.

## Sequence and definition of done

- [x] Verify metadata, fresh main, ownership, contracts, and Education patterns.
- [x] Add reusable synthetic fixture and matrix/negative/rollback unit tests.
- [x] Add mocked-route transition and stale-response browser regressions.
- [x] Run scoped units, browser spec, lint, and inspect intended diff.
- [x] Prepare scoped commit/push and the draft-PR independent-review handoff.

Done means all requested reversible tests and limits are reviewable and validated,
with no production binding invented. Hosted results belong in the draft PR body
so recording them does not create another unvalidated Git head.

## Validation, discoveries, and final reconciliation

- Synthetic unit suite: 36 passed; focused card/Education/synthetic units: 117
  passed. Root/hash/member/scope mutations reject without altering runtime code.
- Browser staging/extra-domain/selection-rollback journeys pass in both scopes,
  with identical independent Justice summaries and opened receipt source links.
- Initial stale-test harness corrections: hold every matching initial request
  (development effect replay can send more than one), and recognize canonical
  `all` navigation with the omitted scope parameter. Neither requires a product
  change, timing sleep, test retry, or relaxed serving guard.
- Matching target readiness is representable in the unchanged projector;
  browser target readiness remains outside this scope. Full browser validation
  and exact-head hosted gates are recorded in the draft PR receipt.
- Local production build: passed (existing unrelated hook-dependency warnings).
- Canonical production-server browser command below: 46 passed in 36.7 s,
  including all four new cases and the existing Education rollback suite.
- Dev-server comparison: 42 passed, four pre-existing first-request receipt-retry
  cases failed; the same cases pass in production mode. No old assertion or
  runtime behavior was changed to accommodate development effect replay.
- Focused ESLint and `git diff --check`: passed. Final scope: four intended
  test/documentation files; runtime code, runtime manifest, checked-in source
  snapshots, publication controls, and CI configuration have no diff.

Reproduce from the repository root (PowerShell):

```powershell
npm ci --prefix frontend --no-audit --no-fund
node --test frontend/lib/domainTransition.test.mjs frontend/lib/recordCard.test.mjs frontend/lib/education79CardCompatibility.test.mjs
Set-Location frontend
$env:NEXT_PUBLIC_API_BASE_URL = 'http://localhost:8000'
$env:ENABLE_ZIP_LOOKUP_STATE_FIXTURE = '1'
$env:ENABLE_M6_REVIEW_FIXTURE = '1'
$env:ENABLE_RECORD_CARD_REVIEW = '1'
$env:NEXT_TELEMETRY_DISABLED = '1'
npm run build
$env:CI = 'true'
$env:PLAYWRIGHT_PRODUCTION_BUILD = '1'
npx --no-install playwright test tests/record-card-release.spec.mjs tests/education79-card-compatibility.spec.mjs --workers=2 --retries=0
npx --no-install eslint lib/domainTransition.test.mjs tests/fixtures/domain-transition.mjs tests/record-card-release.spec.mjs
```

The draft PR is the final exact-head CI addendum and review packet. These tests
establish the requested synthetic serving/projection behavior; they do not
establish real-candidate acceptance, target-browser M5 readiness, persistence,
or production rollback. Both rollback orders have an explicitly withheld
intermediate overview, with existing issue summaries/receipts independently
available in the mocked browser proof. No runtime decision was absorbed.

## Production effects, rollback, and blockers

Production/database writes: none. No candidate integration, schema/security,
secrets, configuration, publication, or deployment changes. Engineering rollback
is reverting the test-only commit. No implementation blocker; real transition
authority, release bindings, and zero-gap compatibility remain separate decisions.
