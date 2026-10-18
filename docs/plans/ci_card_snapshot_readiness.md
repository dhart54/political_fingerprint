# Milestone Plan: Released-card snapshot readiness

## Intent and outcome

Diagnose the reported frontend failure separately from the merged stdout fix.
If justified, deliver the smallest test/tooling repair, negative checks, and a
draft PR for independent review. No merge is authorized by this follow-up.

## Scope and baseline

- Owner/worktree: existing native-local engineer, `.w/ci-output`.
- New branch: `codex/ci-card-snapshot-readiness`, based on live main
  `485e0319deacfd5badb493a04945c0873099dc71`; clean before switching.
- Preserve merged PR233 and all candidate research/writer ownership. No edits
  to `.w/infra`, `.w/ib`, product code, fixtures, editorial semantics, production
  configuration, publication, deployments, or candidate branches.
- Expected footprint: one browser spec plus this plan; no generated output.
- Targeted validation: deterministic held-response and unavailable-response
  checks, original complete/partial history journeys, then the affected browser
  spec and exact-head hosted frontend lane. Runtime: minutes per stage.

## Exact evidence

- Infrastructure head `d0a3b2586f3128195ba7a1b889a6f0b406ac765e`.
- Backend workflow `39160820528`: success. This does not make the head green.
- Frontend workflow `39160820403`, job `117773562955`: failure, 194 browser
  tests passed and one failed. Expected/actual checkout both match that head.
- Failure: `local-record-filter.spec.mjs:357`, "released finding complete
  response keeps source identity, coverage and history", equality at line 384.
  Initial snapshot expected `[]`; later snapshot contained the six loaded cards.
- Downloaded exact diagnostics artifact `12148976632` through supported GitHub
  CLI into ignored `.tmp/readiness-d0a`; inspected JSON report and trace ZIP.
- Trace `call@2502` starts at 36829.110 ms and returns `[]` at 36854.295 ms.
  Profile fulfillment starts at 36839.880 ms; positions/editorial fulfillments
  start at 36863.355/36863.637 ms. The initial read preceded card data readiness.
  Later `call@2606` returns the loaded cards. The trace establishes the immediate
  snapshot read; the deterministic local reproduction below verifies the boundary.
- Candidate frontend source and frontend workflow have no diff against main.
- The component intentionally renders loading until positions, presentations,
  and card projection resolve. No product defect is established by this trace.

## Sequence and definition of done

- [x] Read applicable instructions/workflows; inspect ownership and exact logs.
- [x] Inspect trace and compare relevant candidate/main source.
- [x] Reproduce with controlled fixture readiness, without sleeps or retries.
- [x] Add readiness to the snapshot boundary while retaining exact equality.
- [x] Prove delayed load succeeds and unavailable data cannot become a baseline.
- [x] Run original complete/partial journeys and full affected spec; inspect diff.
- [x] Prepare the narrowly scoped commit/push and draft-PR review handoff.

The attached draft PR records the pushed head, hosted workflow/job IDs, checkout
identity, and final conclusions. This external validation receipt is maintained
in the PR body to avoid changing the exact head merely to record its results.

Definition of done: supported root cause, proportional repair, original
assertions/proof semantics preserved, meaningful negative checks, clean reviewed
diff, exact-head validation receipt and independent-review handoff. If evidence
does not justify repair, report that result and a bounded validation proposal.

## Decisions, discoveries, and validation

Both added regressions fail with the original immediate snapshot implementation:
the held editorial response produces zero cards instead of six, and the HTTP 503
case resolves an empty snapshot instead of rejecting. This reproduces the test
boundary deterministically against unchanged main product code. The correction
is test-only; no product defect was established.

The six-card expectation is derived from the existing bound candidate fixture,
not from a sampled DOM or new product rule. A shared local snapshot helper uses
condition-based `toHaveCount` before both initial and returned snapshots. The
original id/href/text equality and every journey assertion remain. The 500 ms
option is used only to bound the deliberately unavailable negative case; normal
snapshots retain the existing configured assertion timeout. No test retries or
fixed sleeps are added.

Validation on native Windows/Node 22.16.0:

- Controlled two-test baseline: both fail, exit 1, before the readiness assertion.
- Full affected browser spec with `--workers=2 --retries=0`: 25 passed in 35.8 s,
  including the original complete and partial response history journeys.
- Focused ESLint: passed. Final `git diff --check`: passed.
- Final diff inspected: original snapshot field mapping and equality retained;
  no original assertion, test selection, fixture artifact, or failure exit removed.
- Exact-head hosted production-build/frontend results: see attached draft PR.

## Production, rollback, and blockers

Production writes performed: none. No deployment or candidate integration.
Rollback: revert this test-only engineering commit. No data rollback required.
No scope blocker currently. Final hosted results will be recorded in the draft
PR body so recording them does not create another unvalidated commit.

## Final reconciliation

The supported trace and deterministic reproduction justify a test readiness
repair. Both snapshot reads now require the bound complete list; delayed data
can load and unavailable data cannot become a valid empty baseline. Product
behavior, merged stdout repair, research branches, and semantic/publication
boundaries remain intact. Delivery is a draft PR; independent review precedes
any separately authorized merge. The historical Infrastructure head retains its
failed frontend attribution until its owner integrates and reruns at a new head.
