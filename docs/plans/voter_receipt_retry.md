# Recover exact vote receipts after transport failure

## Intent and envelope

Restore access to the current issue's receipts through an explicit retry. Preserve
finding/source/scope URLs, history, exact action identity, ordering, qualifications,
links and established filters. No profile loading, global timeout, architecture,
interpretation, publication, schema/security, credentials or production writes.
One implementation owner; independent review and merge belong to the parent.

## Baseline and ownership

Live main verified 2026-10-14: `9337ed516621875709f6bb33ca4f9fb20c4ef2b7`.
New branch `codex/voter-receipt-retry`, isolated `.w/rr` worktree. Root checkout,
`.w/ib`, `.w/cvp` and PR193 remain untouched. No active overlapping task found.
Open PR209's record-card-release overlap is historical validation: current main
already includes newer focus/navigation tests, preserved here. No `.agents/skills`
directory exists in this checkout or the inspected ancestor skill locations.
Read root AGENTS, operating model, interpretation principles, development,
rendered-validation and PR workflows; supplemented with PR199's operating brief.

## Reproduction

Before implementation, intercept only receipt transport with 503 and network
failure. On the unchanged local development build, the unavailable alert persists
after transport recovery and revisiting the same finding receipt link: zero rows,
zero retry controls, no additional receipt requests. Initial Strict Mode effects
make two requests; neither returning link adds another. Desktop 1440 and narrow
390 captures plus JSON are retained under ignored `.local/receipt-retry/`.
This is a controlled reproduction, not a claim of a live service incident.

## Sequence and definition of done

- [x] Verify live main and ownership; create isolated worktree; reproduce defect.
- [x] Add current-context retry, synchronous duplicate guard, lifecycle stale
  response guard, status/error announcements and focus recovery.
- [x] Exercise 503/network recovery, repeated activation/failure, navigation,
  unmount, identity rejection and legitimate empty responses.
- [x] Compare successful baseline and recovered exact records/journey; inspect
  keyboard, desktop/narrow captures against a production build.
- [x] Run full frontend units/lint/build and relevant release browser lane.
- [ ] Inspect final diff; commit/push; draft PR and fresh exact-head CI.

## Decisions and validation

Retry reuses the established receipt request/identity contract. Context changes
and unmount invalidate earlier responses through effect cleanup. The request
guard is set before rerender so repeated activation cannot queue retries. Keep
the retry control focusable with `aria-disabled` while pending; on success move
focus from that disappearing control to the record/finding only when it still
owns focus. Preserve selected exact-action requests across retry.

A blocking keyboard challenge found the ledger's ordinary arrival effect still
took focus when a reader moved away during linked-receipt retry. Add a one-use
`focusOnArrival` option in `ChronologicalActionLedger.js`, supplied only by retry
completion. Receipt resolution/filtering still runs; later explicit navigation
retains ordinary focus. This small additional component change is required by
the authorized safe-focus outcome; no architecture or interpretation change.

Local Node 22.16.0 / locked Next 15.5.12: 279 unit contracts pass. Lint and final
production build pass with eight pre-existing hook warnings in untouched files.
An initial production browser run passed 195 checks; the strengthened linked
focus challenge then reproduced a failure and received the bounded correction.
Final full-lane verification passes: 195/195 checks, zero skips/flakes, including
14 retry checks against the final production build. The four 503/network cases
at widths 390/1440 compare ordered action IDs, expanded receipt text/qualifications,
source links, finding text, filter states and unchanged request URL/history.
Retry preserves focus on a moved-to control and later Back/Forward restores
normal ledger focus. Screenshots were visually inspected for accessible control
placement and readable reflow. [Structured verification](../review_packets/receipt_retry/verification.json)
retains normalized code hashes, actual report stats, parity observations and six
hashed [captures](../review_packets/receipt_retry/). Fixtures intercept local read URLs;
production data and services are never written. Browser ARIA/keyboard assertions
do not constitute assistive-technology or physical-device testing.

Initial sandbox checks could not access SSH/GitHub and could not create the Git
ref or spawn npm install helpers. Approved escalations completed read-only remote
checks, isolated worktree creation and cached locked dependency installation.
No automatic-review denial received. No production write, merge or manual deploy.

## Rollback and final reconciliation

Rollback is a scoped code revert. Validation and draft-PR evidence will be recorded
on this branch and its draft PR. Local implementation/validation is complete;
commit/push/draft PR and hosted exact-head CI remain the next steps. No product
blocker remains. Independent review and merge are reserved to the parent.
