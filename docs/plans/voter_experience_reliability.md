# Voter-experience reliability workstream

## Intent and scope

Own reversible fixes for verified defects in the existing voter journey so readers
can reliably reach exact vote receipts and sources. Each increment owns one
reviewable outcome. No product/interpretation redesign, editorial approval,
publication, production data/configuration writes, merge or manual deployment.
Commit/push and draft PR preparation are authorized; parent owns integration.

## Baseline and ownership

2026-10-11: verified remote main `f494324f03514291e7f767b5f8a857515fe656a0`
(PR202 merged), isolated `.w/vr`, branch `codex/voter-receipt-navigation`.
Root unrelated work, Immigration `.w/ib`, completed `.w/rf` and `.w/fci` preserved.
No `.agents/skills` or scoped frontend AGENTS exists in this checkout.
Read root AGENTS, interpretation principles, operating model, rendered validation,
PR workflow and planning convention. Rendering must preserve established meaning.

PR193 exact head `a1ea3035606d6b47987dea5606513a2d5e6ad71e`: inspected
its page.js diff and local `.w/record-repro` state (only untracked shutdown deadline).
Its HomePage review-data/path/banner hunks do not overlap SiteHeader or call props.
No PR193 edits, conflict resolution or shared-card content work is included.

## Increment 1: sticky Vote record navigation

Confirmed live defect: Foushee War Powers detail at all scope changes only the hash
to `#vote-record`; the ledger is hidden until `view=receipts`. The finding CTA works.
Use its established `recordCardUrl` and `followRecordLink` contracts in SiteHeader,
retaining representative, issue, scope, finding and source. Full issue routes keep
their existing native anchor. Expected change: page.js, focused released routing
tests and this checkpoint; no evidence or publication output changes.

Definition of done: reproduce baseline failure, validate exact action sets,
mouse/keyboard, focus, refresh and Back/Forward; check full reviewed, receipts-only
and sparse states; inspect diff; deliver a coherent draft PR with exact-head CI.

- [x] Verified main and isolated branch; inspected ownership/overlap.
- [x] Added focused browser regression on existing CI-covered released-card suite.
- [x] Captured baseline failure and repaired header props/link.
- [x] Focused local validation and exact implementation diff review.
- [ ] Commit/push and draft PR.
- [ ] Exact-head hosted frontend validation.

## Next authorized increment

Environment receipts `house:119:1:112` and `house:119:1:114`: accepted top-level
vote_type is `final_passage_or_suspension_passage`, raw vote_context says `rule`,
UI currently displays Rule. Parent verified official Clerk says On Passage.
Diagnose current serving/fixture contract and fix deterministic display precedence
only in a separate increment, preserving filtering, interpretation and ETL.

Source substitutions remain unauthorized pending exact artifact/version evidence:
Security assistance `house:119:2:264` api.congress.gov amendment URL returns 403;
Education `house:119:1:79` GovInfo CREC details reports content unavailable.

Third confirmed increment: Ted Budd 119 Justice (2 receipts) -> 118 leaves the
selected issue in the URL but filters its zero-evidence row out before detail
selection. Direct 118 URL loses the selected detail and header targets. Diagnose
a source-neutral selected empty state with valid anchors, keyboard/focus,
direct URL and history regressions. Inspect PR193 RepresentativeExperience hunks
before edits; no shared-card work may be overwritten.

## Validation and deviations

Locked dependencies installed from offline cache in this worktree (322 packages).
Initial sandboxed npm child-process spawn hit EPERM; authorized elevated install
succeeded. No other worktree dependencies were changed.
Supported send_message_to_thread to delegated source ID returned thread not found;
work continues with this readable checkpoint rather than messaging retries.
Baseline regression failed because header href was only `#vote-record` while the
working CTA included finding/source/view. After repair: 6 focused Chromium tests
passed (26.3s), including all 6 entries x 2 scopes x 2 surfaces and recorded sparse
Senate Education (1 receipt). 29 focused units passed (127.7ms). Sandboxed default
unit process isolation hit EPERM; in-process Node test isolation succeeded.
No local full build/suite duplicated; exact-head hosted CI owns release checks.

## Production writes, rollback and reconciliation

Production writes: none. Rollback: revert the bounded code commit if integrated.
Current implementation/CI results and PR identity are recorded as work completes.
Next step after each PR is independent review plus the next verified scoped defect;
do not stack overlapping edits on a head under review or invent a fix quota.
