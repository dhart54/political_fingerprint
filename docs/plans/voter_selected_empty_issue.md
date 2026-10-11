# Selected empty issue reliability

Third bounded voter-journey increment: keep a valid selected issue when its current
Congress scope contains zero supplied actions. Base verified main `f494324`, isolated
`.w/ve` / `codex/voter-selected-empty-issue`. Navigation PR203 (`b26679c`) and
type-display PR204 (`7493c0f`) remain on separate frozen heads.

Read repository AGENTS, interpretation principles and execution/rendered workflows.
Rechecked PR193 exact RepresentativeExperience diff and `.w/record-repro` state;
only shared-card import/load hunks, no selection/render ownership conflict. Other
checkouts and PR193 content are untouched.

## Source and outcome

Read-only current API captured Ted Budd profile and 118/119 Justice response
envelopes on 2026-10-11. 119 has 2 exact receipts; 118 has a supplied Justice row
with total_votes=0 and empty evidence. This is a valid empty selected state, not
an API failure or stance. Existing discovery filtering must stay unchanged; the
selected detail should resolve against supplied issue rows before that filtering.
Use the existing issue summary/ledger structure with explicit scope-empty wording,
so header anchors, direct URLs, keyboard use and browser history stay valid.

No new coverage, inference, analytical summary, editorial/ETL/production data,
publication, configuration, merge or manual deployment. Code rollback is a revert.

## Checks

- [x] Verified current responses and separate ownership; source-backed fixture.
- [x] Reproduced pre-fix disappearance; repaired selection and empty ledger copy.
- [x] Keyboard 119->118, Back/Forward, direct URL, focus/anchors and refresh.
- [x] 4 focused browser checks, 28 units, targeted lint and diff review pass.
- [ ] Draft PR and exact-head hosted CI.

## Workstream resume

PR203 hosted frontend: 168 units, 100 browsers, lint/build pass, 8 existing hook
warnings. PR204 local: 44 units, one browser check (both rows/all+119), targeted
lint/diff pass; hosted pending. Parent-message route unavailable (thread not found).
Next isolated increments are API-source access honesty, Education79 same-source
locator preparation only, and fault-injection checks for partial receipt sets.
Massie procedural-label origin remains an upstream evidence-review item.
