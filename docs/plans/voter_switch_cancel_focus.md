# Explicit representative finder Close focus

## Scope and baseline

Restore focus to the existing Switch representative button only when the reader explicitly closes its finder. Preserve selection focus, URL/history, pending-request isolation and all six released cards. No modal redesign, Escape behavior, shared-card semantics, evidence/publication/configuration changes, production writes, merge or manual deployment.

Owner branch `codex/voter-switch-cancel-focus` in isolated `.w/vc` starts at verified remote main `34a39fc5432d14e4d7c61f7d8a14184e3caa8cd3`. Existing unrelated worktrees remain untouched. Root AGENTS/workflows read; no .agents or scoped frontend AGENTS exists.

PR193 remains reserved at `a1ea3035606d6b47987dea5606513a2d5e6ad71e`. Exact page.js changes concern reviewDataSource, shared route/query/effect dependencies and banner; they do not overlap Switch/Close callbacks or imports. Its original owner task “Build Record at a glance card” is archived and research paused, no current callback writer found in task inventory or local writer locks. Existing original worktree is tracked clean; no edits or conflict resolution there.

## Implementation and validation

- Capture the actual Switch trigger when it opens the finder.
- Explicit Close closes the finder and synchronously focuses the connected trigger. Avoid deferred focus that could race later reader actions.
- Keep selection and history callbacks, request-sequence protection and route content untouched.
- Reproduce failure before correction at desktop/narrow widths. Fixture regression compares six card identities/links/text, member, URL/history and finding routes; extend existing pending success/error and 320/390/1440 keyboard cases.
- Run focused browsers first, then the established full frontend release gate once the diff is coherent. Review exact diff and deliver a draft PR with exact-head hosted CI for independent review. No merge authority.

## Progress

Ownership resolved; isolated branch created and dependencies installed. Live read-only diagnosis showed BODY after Close and next Tab skipping Switch. Local baseline failed focus assertions in five existing cases (320/390/1440 and pending success/error). Both new released-card regressions failed the same focus assertion at 390/1440 after correcting an initial test selector that read the article ID instead of its nested finding link.

After the bounded callback fix, all nine focused Chromium tests passed (9.8 seconds, no retries/skips), including selection focus and Back/Forward with pending lookups. Lint passed with eight existing unrelated Hook dependency warnings. Exact diff reviewed: one runtime file, two already CI-covered browser suites and this plan. No data or semantic files changed.

The established full release gate will run in exact-head hosted frontend CI on the draft PR: all units, lint, production build, ten browser suites and screenshot exports. This avoids duplicating the complete release run locally. Exact-head results and independent-review readiness will be recorded in the PR and retained owner evidence.

## Production and rollback

Production writes: zero. Code rollback is revert of this bounded feature commit if later integrated. No implementation blocker; draft PR and hosted validation are next, then independent review. No merge before that review.
