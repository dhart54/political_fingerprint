# Voter receipt type display

Second bounded voter-reliability increment, independent of routing PR203 (`b26679c`).
Base: verified main `f494324`; worktree `.w/vt`; branch
`codex/voter-receipt-type-display`. Root/Immigration/other checkouts untouched.
Read repository AGENTS and interpretation, operating, rendered and PR workflows.
PR193 has no diff in the touched presentation helper or tests.

## Outcome and boundaries

Current public API and recorded release snapshot agree: reviewed Environment
`house:119:1:112` / `114` supply accepted top-level
`final_passage_or_suspension_passage` and retain raw `vote_context.vote_type=rule`.
Read-only official Clerk XML for both says `On Passage`. Backend reviewed overlays
preserve raw context while adding accepted display fields. UI preferred raw context.

Only reviewed display labels now prefer a nonempty accepted type. Unreviewed or
missing accepted types retain raw fallback. No interpretation, filtering, status,
accounting, source URL, member vote, ETL, accepted artifact or publication changes.
No production write, merge or manual deployment; parent owns integration.

## Validation and reconciliation

- [x] Source-backed discovery and pre-fix unit failure (`Rule` instead of passage).
- [x] Minimal presentation-only repair with immutable input/filter checks.
- [x] 44 focused units pass; targeted lint and diff check pass.
- [ ] Focused rendered checks, commit/push, draft PR and exact-head hosted CI.

Browser checks cover both exact rows in all/119 scope, keyboard anchor focus,
accepted label, unchanged Nay attribution/status and exact official vote URLs.
Initial browser expectation incorrectly said Yea; corrected to recorded Nay.
Full release validation delegated to existing exact-head hosted frontend lane.
Rollback is a code revert; production writes: none.

## Workstream resume

PR203 navigation head remains unchanged. Separate `.w/ve` starts the confirmed Budd
119 Justice -> empty 118 selected-state fix; PR193 hunks checked (card projection
import/load only, outside selection/empty-state changes). Further authorized work:
API-source access honesty; isolated Education79 same-source locator preparation;
fault-injection validation of incomplete exact receipt sets. Production publication
and source identity changes remain forbidden. Parent-message route returned thread
not found; preserve durable state and continue without retries.
