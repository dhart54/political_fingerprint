# Independent vote and analysis loading

## Intent, scope and authority

Make validated vote evidence usable while reviewed analysis is pending. The
October 31 approval covers implementation, tests, independent review and a draft
PR. Preserve design, meanings, coverage, scope/identity guards, exact receipts,
source links and navigation. No backend/API, editorial, publication, production,
hosting, caching or pooling changes. Merge and deployment need separate authority.

Sole owner uses existing 4b3c worktree, branch
`codex/independent-vote-analysis-loading`, based on verified remote main
`63b8d982dbcdc9de03b433fab3928bf14ed364f2`. Prior feature branch `e6817b5c`
and ignored audit/release evidence are preserved. Archive SHA remains
`d4cba33cf1e5c47f19fa1a1241f3eb7afafdf57b810edb3ada5142f93805ed84`.
Initial tracked tree/index clean; known unreadable caches unchanged.

Read AGENTS, interpretation principles, operating model, rendered/PR workflows.
This is an existing repository frontend correction, not Sites publication.

## Sequence and definition of done

1. Capture the pending-analysis regression using existing intercepted fixtures.
2. Separate endpoint settlement, preserve inactive-response guards, distinguish
   pending/empty/error analysis in affected consumers and exact-finding links.
3. Validate both arrival orders/failures, scope/member changes, source mismatch,
   receipt state and keyboard/history anchors; inspect desktop/mobile rendering.
4. Inspect scoped diff; independent exact-target review; ordinary commit/push,
   draft PR and terminal exact-head hosted checks. No GitHub approval review.

Expected 5–8 files including focused browser tests and CI test-list addition;
no generated content. Frontend validation only, using existing dependencies and
hermetic fixtures. Release gates belong near draft delivery, not repeated PR244
backend/production observation. Local startup previously hit spawn EPERM; new
implementation/test authority permits a narrowly scoped normal approval request,
not a denial bypass. No installations, credentials or system-wide inventory.

## Decisions and progress

- [x] Verified current main, clean tracked state and prior archive; created branch.
- [x] Regression, implementation and focused validation.
- [x] Desktop/mobile rendered review.
- [ ] Exact-commit independent review and draft delivery with hosted checks (record final results in PR).

Analysis pending must not be displayed as absent, unreviewed or mismatched.
Exact finding selection cannot be applied until its existing hash/identity
contracts pass. Existing meanings and coverage calculations remain authoritative.
Production writes: none. Rollback: ordinary code revert if later integrated.
Current blockers: none in implementation or local validation. Exact-target
independent review and hosted checks remain for draft delivery.

## Implemented behavior and review corrections

Eight intended files: four components, the section-navigation helper, one new
browser suite, its existing CI test-list entry and this plan. Both requests start
in parallel and settle their own state. Valid positions expose receipt fetching
while analysis is pending or failed; valid analysis survives positions failure.
Existing member/scope/source-hash/action guards and inactive-response rejection
remain authoritative. Pending, valid empty, failure and mismatch remain distinct.

A pending exact-finding link does not mislabel the complete ledger as that
finding's selected actions. Its stable complete-record link is immediately usable.
Late analysis preserves receipt filters, disclosures, focus, source links and
viewport position. Navigation observers can finish when receipts extend a short
pending layout, without waiting for analysis or overriding later reader intent.

Independent preliminary review found delayed section restoration, late finding
focus theft, and deliberate receipt navigation suppressed after focus preservation.
Each was reproduced and corrected within scope. The finding view participates in
the navigation intent so explicit view changes and Back restore expected focus.
Broader validation also exposed initial desktop/tablet positioning: an automatic
issue landing must preserve its intended issue, not the changing grid above it.
A production-mode check also exposed an eight-pixel post-commit layout shift for
focused discovery at scroll zero. A single bounded frame reconciliation corrects
that shift and cancels on newer focus, pointer, keyboard, wheel, touch or resize
intent. The viewport assertion remains five pixels; it was not weakened.

## Validation evidence

Local evidence is retained under `.tmp/independent-loading/` (ignored).
All browser APIs are intercepted using existing immutable source snapshots;
there are no production calls, SQL probes, installs or live latency claims.

- Baseline pending-analysis test failed before implementation: receipts were
  withheld by the coupled request. Both preliminary navigation regressions and
  the deliberate-receipt regression also failed before their corrections.
- Initial browser selector mistakes were corrected without weakening assertions.
  A first broad production-mode run passed 135, skipped one optional screenshot
  case, and exposed two initial anchor failures, subsequently corrected.
- Final focused development-mode run: 62/62 passed, comprising 35 new loading
  cases and 27 existing anchor cases (`settled-layout-dev.log`).
- All 319 unit contracts passed (`units-sequential.log`). An overlapping earlier
  unit run lost its temporary canary when the browser runner reset test-results;
  sequential execution resolved that runner-output collision.
- Lint passes with eight existing unrelated hook warnings (`lint-settled.log`).
- An earlier production build compiled but failed generated `_not-found`
  prerendering after development output reuse. Preserving the old generated
  cache and building fresh passed without source changes (`build-fresh.log`).
  The final build likewise uses a fresh generated directory.
- Rendered evidence inspected at 320, 390 and 1440 widths: pending analysis is
  distinguished, receipts remain usable, filtering and an open receipt survive
  late analysis, readable official/XML links persist, and no horizontal overflow.

Final production build passed (`build-settled.log`). Final broad production-mode
browser run passed 141 with one optional screenshot test skipped (142 total,
`production-browser-settled.log`). All 35 new loading cases passed. Current
screenshots are preserved under `screenshots-final/` and were visually inspected.
The exact frozen independent review and hosted CI results will be recorded with
actual terminal outcomes in the draft PR and ignored evidence. This plan records
the pre-commit checkpoint; final delivery status belongs to the PR evidence.
No backend, editorial meaning, readiness, coverage, publication or production
configuration changed. Merge/deployment remain outside this milestone.


## Hosted correction after the first freeze

PR247's first frontend run checked out `caecbb0c` exactly, passed units/lint/build
and 262 browser cases, but failed the existing empty-scope keyboard navigation
case. The downloaded trace archive matches hosted SHA-256
`2223eff9bd5adb98ab62c9f32246995bb373777319b6f8cbb659561ad824729a`.
The trace shows the URL still at `#issue-summary` after the attempted Vote record
activation: an older queued section restoration reclaimed focus between focusing
the new header link and pressing Enter. Five ordinary local repeats passed;
a deterministic delayed-position regression reproduced the focus loss.

The keyboard correction makes section restoration cancel on focus entering an
interactive control, matching its existing pointer and keyboard cancellation.
Programmatic section-heading focus remains non-interactive and does not cancel
restoration. The new regression keeps the header link focused through settlement,
then checks explicit Enter activation, the receipt hash and receipt-heading focus.
A parallel development rerun also reproduced the eight-pixel discovery shift.
Geometry capture established that the card can grow from 1112 to 1120 pixels
after the fixed follow-up frame has finished. The successor replaces that timing
assumption with a ResizeObserver limited to the current card/issue layout. It
reconciles actual size changes and disconnects on reader interaction, invalid
anchor/route, subsequent analysis settlement or unmount. No timing tolerance was
relaxed. Both regressions passed all eight parallel repetitions after correction.

The new suite now contains 37 loading/navigation cases. This successor changes
only RepresentativeExperience, the existing helper, test suite and plan; all
original scope boundaries hold.
The first run's failure remains recorded; final exact-head results belong in PR247.


Successor local validation: production build, lint (same eight existing warnings)
and all 319 units passed. The complete hosted browser selection passed all 264
cases locally (`production-browser-successor.log`). One additional focused
production-mode cancellation test then passed (`reader-cancellation.log`), bringing
the final selection to 265 cases. That test disables optional native anchoring
on its isolated test page, confirms that later card growth is compensated, then
moves keyboard focus and proves subsequent growth does not restore the old anchor.
Final captures are retained under `screenshots-successor/`. No test assertions
were relaxed; the two failed hosted/local regressions remain in the evidence.
