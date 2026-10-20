# Finder request reliability

## Intent and envelope

Make held ZIP/name searches understandable and cancellable without extra traffic.
One implementation owner in `codex/finder-request-reliability`, isolated `.w/fr`.
Change RepresentativeFinder, optional signal forwarding in the two API helpers,
finder browser tests and short evidence only. No page.js/RepresentativeExperience
loaders, interpretation, publication, production writes, timeout/retry, keepalive,
hosting/configuration, manual deploy or merge. Independent review/merge belong to
the parent. Rollback is a scoped code revert.

## Baseline and ownership

Remote main verified 2026-10-14 as `af6cd6d78d6944d64a68a92653066c4c1625f96b`
(PR228 receipt retry). New worktree started clean at that SHA. Root, `.w/ib`,
`.w/rr`, `.w/cvp` and PR193 are preserved. PR193 head `a1ea3035` file list and
local diff exclude all three finder target files. Open PR inventory has no active
finder implementation; PR209 is historical combined validation.

Read AGENTS, operating model, milestone/plan, development, local preview,
rendered-validation, PR workflows and interpretation principles; supplemented by
PR199's Dot operating brief. No `.agents/skills` exists in the current checkout,
root, inspected ancestor directories or user `.agents` location. Neutral elapsed
time guidance will make no diagnosis of cold starts or service availability.

## Sequence and definition of done

- [x] Reproduce held ZIP/name requests on unchanged production build; capture.
- [x] Add synchronous pending identity guard, per-request AbortController,
  sequence guard, slow guidance timer and lifecycle cleanup; preserve inputs.
- [x] Exercise duplicate, cancel/resubmit, eventual completion, stale callbacks,
  superseding/invalid search, Close, selection, unmount/history and keyboard/reflow.
- [x] Run all frontend units, lint, production build and applicable CI browser lane.
- [ ] Inspect diff/captures; commit/push scoped feature branch and draft PR;
  verify fresh exact-head CI and hand off for independent review.

## Validation and discoveries

On unchanged main's production build, both ZIP and name requests held for 15
simulated seconds kept the same loading message, offered no Cancel and forwarded
no signal. Three identical submissions issued three GETs. Controlled routes were
then released and eventual results rendered. This is not a live incident claim.

The final implementation shows neutral guidance after eight seconds, with no
timeout/retry or traffic. A synchronous mode/query guard suppresses identical
pending submissions (name queries use the existing trim). Different and invalid
submissions invalidate the sequence, clear the timer and abort the previous
controller. Cancel preserves both inputs and returns focus to the active input;
an explicit resubmission starts a new request. Close/selection/unmount clean up.
Obsolete finally callbacks cannot release the newer pending guard.

Node 22.16.0 / locked Next 15.5.12: 279/279 units pass; lint and production build
pass with eight pre-existing hook warnings in untouched components. Final focused
production-build browser suite passes 48/48; the full applicable frontend CI lane
passes 213/213, zero skips/flakes. Tests combine real AbortError transport checks
with intentionally abort-ignoring transport to challenge retained sequence guards,
including forced obsolete timer callbacks during newer loading and ready states.
Held searches still use one GET after repeated submits and 68 simulated seconds;
eventual success works. Inputs, URL/history, ZIP qualifications, 404 versus 503,
empty name versus transport failure, official links, keyboard, selection and
history isolation are preserved. Widths 320/390/768/1440 fit without overflow.

Visually inspected desktop/narrow guidance, focus outline, cancelled and completed
ZIP/name captures. [Structured evidence](../review_packets/finder_request_reliability/verification.json)
binds normalized code hashes, actual report stats, baseline observations and six
hashed [captures](../review_packets/finder_request_reliability/). Raw local reports
and broader captures remain under ignored `.local/finder-reliability/` and
`frontend/test-results/`. Browser ARIA/keyboard assertions do not constitute
assistive-technology or physical-device testing.

Initial sandbox GitHub/SSH access failed; build and unit workers hit `spawn EPERM`.
Escalated same-command execution succeeded. A reporter argument needed PowerShell
quoting. Four initial focus assertions used programmatic focus after pointer input;
corrected them to traverse with Tab and expanded narrow checks before the final
passing suites. No application correction beyond the authorized finder/API scope,
automatic-review denial, production write, merge or manual deploy occurred.

## Initial handoff at 701d89fe

Implementation and local validation are complete; final diff contains the three
authorized frontend files, this plan and bounded evidence. Root/reserved tracked
work is unchanged. No product blocker remains. Commit/push/draft PR and fresh
exact-head hosted CI are the next steps; their result will be recorded in the PR
and task handoff. Independent review and merge remain reserved to the parent.

## Independent review correction: asynchronous completion focus

The first draft head `701d89fef38d25d4459c4ab1b658de13b52ea7ad` passed its
recorded local and hosted gates (279 units / 213 browsers), but independent review
found an omitted focus assertion. On that unchanged production build, keyboard
focus on Cancel followed by successful ZIP completion fell to `BODY` when Cancel
disappeared. The added assertion fails before correction; its JSON attachment
records `{ "tag": "BODY", "id": "" }`. This is a confirmed regression in the
new control, not an unrelated baseline finding.

Add a Cancel button ref. Existing completion cleanup restores the submitted
search input only when the request still owns the pending identity/sequence and
Cancel is the active element, immediately before the settled render removes it.
Moved focus remains where the reader placed it; obsolete completion cleanup
cannot restore an old input or move focus from a newer Cancel. Explicit Cancel,
Close, superseding/invalid search and unmount retain their existing guards.
No API, result, qualification, error, input, URL/history or selection change.

- [x] Reproduce loss of focus at exact first draft head before changing runtime.
- [x] Implement the scoped focus correction and regression coverage.
- [x] 279 units, lint (eight existing warnings), production build and 68 finder
  checks pass, including 16 success/network/503/empty/404 focus ownership cases,
  four cross-mode superseded success/error cases and all eight slow-search success
  checks with focus asserted after completion at 320/390/768/1440.
- [x] Full applicable production browser lane passes 233/233, zero skips/flakes.
  Inspected completion/error focus captures at 390/1440; refreshed evidence binds
  final code, actual report stats, eight captures and the before/after focus
  observations. All eight held-success cases report the correct active input.
- [ ] Commit/push same draft PR and verify fresh exact-head CI; no merge.

Local correction is complete with no blocker. Same draft PR remains held for
independent review. Hosted results for the correction head will be recorded on
the PR and in the task handoff rather than inferred from the first draft's CI.
