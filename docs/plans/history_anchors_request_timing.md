# History anchors and request timing

## Intent and outcome
Restore recognized section hashes on browser history traversal without stealing
later user navigation. Add bounded backend timing diagnostics to locate latency
stages without recording identifying data. Interpretation principles were read;
no copy, evidence meaning, counting, or publication contracts change.

## Scope and decision envelope
Approved: controlled reproduction, navigation fix, timing instrumentation, focused
tests/rendered review, independent review, commit/push and one draft PR.
Reserved: merge, manual deployments, production writes, access-log configuration,
pooling/caching/query concurrency, hosting/security, editorial or Health activation.
Expected scope: roughly 10–14 source/test/documentation files; no generated corpus.
Validation starts with focused browser and Python tests, then frontend build and
runtime contract regressions. No load tests.

## Baseline
Clean worktree at main fdd2ce8afa243f63f0f9976532f28b74ead6d955, fetched and verified
2026-10-27. Branch: codex/history-anchors-request-timing. Earlier branches and
ignored receipts preserved. Final main deployment was previously verified live.

## Sequence and definition of done
- [x] Investigate the reported sequence; reproduce a controlled delayed-mount
  history failure, retaining the exact original sequence's reproduction limit.
- [x] Implement generation-scoped restoration; preserve no-hash history, receipt
  ownership, explicit links, reduced motion, focus and measured sticky offsets.
- [x] Add request-local fixed-label timing, safe across sync workers and cancellation.
- [x] Validate delayed loads, rapid history/member/scope navigation and user override.
- [x] Validate privacy, errors, isolation, closure, logging failure and response parity.
- [ ] Inspect rendered behavior/diff, freeze exact tree, independent review.
- [ ] Commit reviewed tree, push draft PR, inspect exact-head hosted checks.

## Timing contract
Monotonic request wall time ends after the final body send; abnormal exits have a
separate aborted label. Connection, execute, fetch and row-conversion durations
are cumulative call time. Composition spans are inclusive and overlap DB work;
they are not additive with those stages or a measurement of TTFB/database CPU.
One bounded fixed-label/duration record per selected request; no identifiers,
URLs, queries, SQL/parameters, bodies, exception strings, environment values,
public timing headers, external collector or persistent storage. Request state
closes once; late workers cannot mutate or emit after closure. Logging failure
cannot change response or exception behavior.

## Discoveries, decisions and corrections
Source inspection found a history restoration gap. Fast Education → Justice → Back
passes baseline in both motion modes after establishing the first anchor. A
controlled Back to a delayed issue-summary after scope remount fails baseline
(target remains outside viewport) and passes with restoration. This establishes
the missing-target restoration defect, not the exact original live causal chain.
Issue selection preserves representative hash but scrolls to issue detail;
popstate changes query state, not anchor intent. Existing receipt guard owns only
receipt anchors. Existing Uvicorn access logs may include paths/query strings;
the new timing guarantee does not cover baseline logs. That privacy risk remains
a separate follow-up; access-log settings will not be changed.

## Validation and progress
- Final targeted Python run: 138 passed, including 18 timing cases, actual
  FastAPI sync-worker context/INFO capture, real-thread cancellation, response
  parity, connection/query cleanup and prior workflow preservation.
- Production build passed. Only pre-existing hook warnings in unrelated
  components remain. No dependency or build-setting changes.
- Final affected production browser run: 113 passed / 1 optional screenshot-only
  test skipped (PASS_A_SCREENSHOT_DIR unset). The new matrix explicitly retains
  desktop/mobile screenshots; both were visually inspected below sticky headers.
- 27 anchor/loading cases cover direct hashes, both motion preferences, Back/
  Forward, delayed profile/positions/presentations/receipts, scope/member remounts,
  rapid superseding navigation, keyboard/wheel/new-section cancellation, same-hash
  activation, native no-hash behavior, 320–1440 widths and CSS zoom to 200%.
- Earlier development run: 95 passed / 4 receipt-retry failures / 1 skipped.
  One failure was independently confirmed with exact-main frontend source copies,
  then feature bytes restored. The prior milestone documents Strict Mode duplicate
  requests in these single-attempt fixtures; canonical production mode passes all
  four. No retry code, fixture weakening or runner configuration change was made.
- The expanded matrix exposed restoration before layout settlement (heading
  occlusion after profile arrival). A route-matched settled/error layout signal
  fixed it without timeout polling or waiting indefinitely on successful receipts.
- Incremental review requested explicit same-hash activation. Added a delegated
  unmodified-click handler; pointer/key cancellation remains intact. The Chromium
  same-hash test also passed before that addition, so no failing reproduction of
  that specific event omission is claimed.
- Existing frontend exact-head CI already includes this browser file. Added one
  bounded offline timing job at exact head; all prior backend job blocks remain
  unchanged. No extra hosted service or permissions beyond contents:read.
Initial git SSH command hit Windows sandbox signal-pipe
restrictions; authorized native fetch succeeded outside sandbox. No production
operations performed. Playwright initially could not spawn inside the sandbox;
the supported escalated run succeeded. The launch failure was not a test result.
The initial normal-motion fixture exposed a separate competing initial scroll;
the test was corrected to establish the starting anchor before issue navigation.

## Rollback, blockers and final reconciliation
Rollback is reverting this feature commit; no data rollback is needed. No current
implementation blocker. Exact staged-tree independent review and draft PR/hosted
checks are pending. Their final identities and outcomes belong in the PR/task
receipt, so reporting alone does not mutate a reviewed tree. No production writes
or manual deployment performed. Existing access-log privacy is follow-up scope.
