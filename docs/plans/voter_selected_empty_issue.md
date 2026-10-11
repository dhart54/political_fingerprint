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
- [x] Draft PR205 at cc06995: hosted 168 units / 96 browser checks, lint/build and
  required backend checks pass.

## Narrow independent-review correction

Parent review found that the newly reachable zero-row summary cell still claimed
"Vote receipts remain available". The new direct118 assertion reproduced that
contradiction against the reviewed head. Make only the no-interpretation coverage
description conditional on actual supplied receipt rows. Reviewed accounting and
summary ready/unavailable distinctions remain unchanged; nonempty unreviewed119
retains the existing availability description.

- [x] Add zero-row presence/contradiction assertions to both existing Budd checks
  and nonempty119 fallback assertion before scope switch.
- [x] Both focused browser checks pass (scope/history/refresh plus direct URL);
  targeted lint and diff checks pass.
- [ ] Fresh exact-head hosted checks.
PR205 remains uncleared for merge; parent must independently review its fresh head.
PR203/204/206 now have explicit clean-merge integration authority; keep their
reviewed feature heads unchanged. PR207/208 remain isolated drafts with hosted
checks passed; no activation or merge authority for them.

## Workstream resume

PR203 hosted frontend: 168 units, 100 browsers, lint/build pass, 8 existing hook
warnings. PR204 local: 44 units, one browser check (both rows/all+119), targeted
lint/diff pass; hosted pending. Parent-message route unavailable (thread not found).
Next isolated increments are API-source access honesty, Education79 same-source
locator preparation only, and fault-injection checks for partial receipt sets.
Massie procedural-label origin remains an upstream evidence-review item.
