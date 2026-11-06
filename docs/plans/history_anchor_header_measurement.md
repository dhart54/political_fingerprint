# History anchor header measurement fix

## Scope

Local fix on `codex/history-heading-anchor-fix`, based on PR258 head
`224c11465c9a34303e54ecb288120b70bb30097f`. PR258 remains unchanged.
No semantic, publication, database, schema, security, or deployment changes.
No push or merge is authorized for this investigation.

## Reproduced cause

Hosted frontend run 42284216534, attempt 2, failed the final Back navigation in
`frontend-loading-anchors.spec.mjs` with the representative heading 10 CSS pixels
under the sticky header. Repeated local production-build runs reproduced the
same -10 value. Instrumented events established the order:

1. Budd's no-issue navigation header is 45px high, with a 61px scroll margin.
2. Final Back loads Foushee with selected-issue navigation, growing the header to 71px.
3. Section restoration runs before the header ResizeObserver callback and uses the stale 61px margin.
4. Restoration disconnects its observer; the later 87px margin update does not rescroll.

This is a stale layout measurement, not a changed editorial snapshot or evidence
record. No timeout increase, tolerance relaxation, retry, or ignored assertion is used.

## Minimal correction

Measure SiteHeader in a layout effect keyed by representative name and selected
issue. That synchronizes the CSS offset after the relevant React commit and
before history-restoration animation frames. Retain the ResizeObserver for
viewport, zoom, and other later layout changes. No new navigation controller or
scrolling policy is introduced.

The existing rapid Back/Forward test now runs both normally and with header
ResizeObserver delivery withheld for final Back. The latter isolates the
ordering contract instead of depending on a lucky callback schedule. Other
ResizeObservers continue receiving their entries.

## Validation

- New delayed-observer case against the unchanged PR258 production bundle: fails
  with the original -10px occlusion, establishing a negative control.
- Fixed production build: passed, with existing lint warnings only.
- Natural and delayed-observer rapid Back/Forward: 20/20 passed, two workers,
  ten repeats per variant, no retries.
- Entire frontend-loading-anchors browser suite: 28/28 passed, including
  cancellation, absent targets, same-hash reassertion, no-hash native policy,
  narrow widths, zoom and error paths.
- Frontend unit contracts: 319/319 passed.
- Frontend lint: zero errors, nine pre-existing warnings.
- `git diff --check`: passed.

Diagnostics are local scratch only. Full repository/hosted release validation
was not rerun, and the separate presentation border-box issue is outside this
patch. No approval for merge is inferred from these local results.
