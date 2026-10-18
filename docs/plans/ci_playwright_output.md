# Milestone Plan: Playwright CI subprocess output

## Intent and outcome

Repair the repeated accepted M14G/public-receipt runner crash while preserving
every assertion, failure status, and proof boundary. Deliver a feature-branch
commit and draft PR for independent review; do not merge.

## Scope, boundaries, and decision envelope

- Owner: this native-local engineering chat (`hostId=local`,
  `projectId=local-9f0a954bc56e7ae25eac9d04e83f5d7d`).
- Implement only in `.w/ci-output`, branch `codex/ci-playwright-output`.
- Expected footprint: 3–6 runner/test/workflow/plan files, no generated artifacts.
- Validation: focused subprocess negative tests, exact affected browser command,
  then exact-head hosted CI. Expected runtime: minutes per stage.
- No civic/editorial semantics, fixtures, publication state, production writes,
  configuration, secrets, deployment, or candidate-branch implementation.
- Infrastructure `.w/infra`, Immigration `.w/ib`, and unrelated root work remain
  owned by their existing writers. No checkout, edits, or interruption there.

## Baseline

- Live main fetched: `af6cd6d78d6944d64a68a92653066c4c1625f96b`.
- Root checkout contains unrelated tracked changes; preserved in place.
- Existing worktrees and supported app task metadata inspected before creation.
- Batch35 run `39153212986`, job `117750968065`, checkout
  `fffdb8ca4c0b4772380930ae290405e1ee7f3493`: 215 shared candidate tests pass;
  subsequent accepted regression step fails at Playwright `coreBundle.js:9515`
  (`stdout += data.toString()`, `RangeError: Invalid string length`, Node 20.20.2).
- Batch36 run `39155333254`, job `117757274641`, checkout
  `82dad47ec1713681be59cda9801d186f2796b719`: 217 shared candidate tests pass;
  same later crash. Neither candidate head is green; later steps are skipped.
- Logs read through supported GitHub CLI and saved outside the worktree.
- Both candidate heads have identical Playwright config, lockfile, package file,
  and public-record browser spec to main. No candidate-only code needed so far.

## Sequence and progress

- [x] Inspect instructions, ownership, live main, and exact failed logs.
- [x] Trace the failing subprocess and reproduce the smallest bounded case.
- [x] Repair the runner boundary and add meaningful negative failure tests.
- [x] Validate affected behavior and inspect final diff.
- [x] Prepare and review the scoped commit/feature-branch push for a draft PR.

The attached draft PR and final chat receipt record the final pushed SHA and
hosted workflow/job conclusions. These external run results are maintained in
the PR body so recording them does not create a new, unvalidated Git head.

## Definition of done

Root cause demonstrated; bounded runner repair with negative tests; existing
assertions and failure semantics preserved; intended diff reviewed; committed
head pushed; draft PR explains candidate applicability and exact validation.
Independent parent review remains a merge prerequisite.

## Discoveries and decisions

- Repository root AGENTS and operating, planning, milestone, PR, and rendered
  validation workflows read. No scoped AGENTS applies to the runner files.
- Initial sandbox prevents Git metadata writes and network; approved native
  escalation works. This is an environment boundary, not a product failure.
- Installed lockfile-pinned Playwright 1.61.1. Its `gitCommitInfoPlugin` enables
  diff capture on GitHub Actions by default, runs `git diff <PR base> HEAD`,
  and only applies its 100 KB limit after `spawnAsync` buffers all stdout.
- Streaming batch35's diff against fetched main produced 570,768,610 bytes,
  exceeding V8's 536,870,888-character string limit. The stream-count command
  completed normally without retaining the diff. Installed source and exact
  stack location explain the pre-test crash; no giant in-memory replay needed.
- Use the supported [`captureGitInfo` setting](https://playwright.dev/docs/api/class-testconfig#test-config-capture-git-info)
  with `commit: true, diff: false`. This removes optional report enrichment and
  its implicit fetch, retaining actual commit metadata, CI identity checks,
  all existing test selection/assertions, status propagation, and proof gates.
- The CLI canary imports the real repository config. A finite 1 MiB fake diff
  makes the regression deterministic without requiring hundreds of MB. Only
  diff/fetch children are substituted; commit capture and Playwright assertions
  run unchanged. Both tests fail on the original config, observing diff/fetch.
- Scope remains four files: config, CLI contract tests, existing CI invocation,
  and this plan. No dependency update or product/runtime behavior change.

## Validation results

- Native Windows, Node 22.16.0: two new CLI boundary tests red before repair,
  green after; deliberate assertion failure retains exit 1 and failed result.
- Affected frontend contracts: 48 passed, zero skipped.
- Focused ESLint on config and new tests: passed.
- Original `playwright test tests/public-record-integrity.spec.mjs` (CI mode,
  one worker, zero retries): 2 passed; real local dev server/browser lifecycle.
- M14G site-integration builder `--check`: passed.
- M14G acceptance builder `--check`: passed.
- Four original backend regression files: 80 passed.
- Windows `core.autocrlf=true` initially broke frozen byte checks. Five verified
  clean receipt files were temporarily readied with their exact HEAD blob
  bytes; no artifact content changed. Restore original checkout line endings
  after validation. No repository configuration change.
- Exact-head hosted Node20/Linux results: see the attached draft PR's validation
  receipt, including workflow/job IDs and actual checkout SHA.

## Production writes and rollback

Production writes performed: none. Rollback is reverting the scoped engineering
commit; no data or editorial rollback is needed.

## Blockers, deviations, and final reconciliation

No scope blocker. Original candidate runs remain failed; this branch's checks
cannot establish those candidate heads as green. Candidate writers must later
integrate the reviewed fix and rerun all gates at their new exact heads.
Implementation and local proof are complete. The final diff contains the four
intended engineering files, with no receipt artifacts, dependency changes, or
production effects. The attached draft PR is the delivery and live hosted
validation addendum. Independent review remains required before merge; this
milestone authorizes no merge or candidate-branch integration.
