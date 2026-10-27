# Milestone plan: expected-commit readiness before Render smoke checks

## Intent and outcome

Make automatic deployment verification tolerate temporary health unavailability
or the previous deployed commit during rollout. A bounded readiness gate precedes
the existing strict eight-request serving-contract check. This changes verification
robustness, not API latency, publication semantics or hosting configuration.

## Scope, baseline and decision envelope

- Base: verified `origin/main` at `3aa57b7af67894c9ec7b872031d0d67ba9cbe36b`.
- Branch: `codex/render-smoke-readiness`; old frontend branch and ignored evidence preserved.
- Expected four files: workflow, existing smoke script/tests, this plan; no generated fan-out.
- Failed automatic smoke `40393234023` timed out on the first health GET after
  30 seconds. Later read-only checks passed on exact main; cause remains unknown.
- Authorized: implementation, focused offline validation, independent frozen-target
  review arranged by controller, commit/push and a separate draft PR.
- Excluded: manual deployment or workflow rerun, hook/secrets/permissions/triggers
  changes, infrastructure/security/DB changes, frontend/Health/Immigration work.
- Stop owned PC-dependent work by 2026-10-26 23:01 UTC; no automatic local resume.

## Implementation sequence and definition of done

1. Preserve exactly one existing deploy-hook invocation and missing-hook read-only behavior.
2. Replace the fixed sleep with opt-in monotonic expected-commit polling: workflow
   deadline 600 seconds, interval 10 seconds, each health attempt capped at 30
   seconds or the remaining deadline. A disposable subprocess bounds DNS/body reads
   as well as socket operations and is killed/reaped on timeout.
3. Persist each readiness attempt, timing and outcome separately from strict success.
4. Run all original strict checks once after readiness; never retry a failed
   publication contract, substitute fixtures or change contract assertions.
5. Validate transient timeout, wrong commit, deadline expiry, late matching response,
   subprocess timeout, CLI guardrails, opt-out behavior and post-readiness failures.
6. Inspect the exact diff, freeze for independent review, then commit/push and draft PR.

## Progress and validation

- [x] Applicable instructions and baseline inspected; new branch created.
- [x] Readiness implementation and workflow integration drafted.
- [x] Offline tests and diff review.
- [ ] Independent frozen-target review.
- [ ] Commit/push and draft PR attached.

Targeted validation is the existing `python -m unittest scripts.tests.test_render_backend_smoke -v`
suite plus focused workflow inspection and `git diff --check`. No production request
is needed for local validation. PR automation retains its existing GET-only check.

The initial sandbox run hit Windows TemporaryDirectory permission errors in both
existing and new tests. Final validation outside the sandbox under the documented
repository workaround: **36 tests passed**, including real offline child-process
import/protocol and timeout termination. `git diff --check` passed. AST comparison
against main confirms all eleven pre-existing strict helpers, including `validate`,
`check_health`, `check_presentations`, `check_justice` and `get_json`, are unchanged.
Workflow diff inspection confirms only removal of the fixed sleep and addition of
the readiness option in the existing nonempty-hook branch.

## Discoveries, decisions and corrections

- `urllib` timeout alone is per socket operation, so a subprocess deadline bounds
  readiness attempts. Process creation/termination overhead may extend observed wall
  time slightly; no new attempt starts or matching response passes after the deadline.
- Readiness is off by default and requires an explicit full expected SHA. The
  missing-hook and pull-request paths therefore retain immediate strict read-only checks.
- Strict transport/contract behavior and all existing authority comparisons remain unchanged.

## Production writes, rollback and blockers

No production writes or deploy-hook invocations performed. Rollback is reverting this
bounded commit after normal review; no data rollback is required. No current blocker.
Live latency/root-cause analysis is outside this milestone.

## Final reconciliation

Pending validation, frozen-target review and draft PR. No merge authorization.
