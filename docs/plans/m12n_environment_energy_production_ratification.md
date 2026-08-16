# Milestone Plan: M12N Environment & Energy Production Ratification

## Intent

- Immediate task: bind the accepted M12N preparation to the exact deployed post-PR157 runtime and fresh production state, then publish an unaccepted/unsealed activation-ratification candidate.
- Larger-goal alignment: preserve the separation between reviewed publication preparation, independent activation ratification, and any later mechanical production activation.

## Outcome

- User-visible or operational result: one draft PR containing production-specific evidence and a non-authorizing prospective authority subject; Environment & Energy remains inactive.

## Scope And Boundaries

- In scope: guarded PR157 merge verification, exact runtime deployment proof, read-only production preflight, deterministic evidence regeneration, disposable PostgreSQL proof, ratification candidate, validation, and one draft PR.
- Out of scope: production dry-run/apply/rollback, registry mutation, persistence, accepted or sealed authority, Environment activation, runtime-source changes, PR merge, and all protected ZIPs.
- Files/systems likely touched: governed Environment publication-activation evidence, ratification validator/tests, current-state documentation, and this plan. Runtime-manifest files must remain unchanged.

## Decision Envelope

- Codex may decide and execute: truthful production-specific binding regeneration and mechanical validation corrections that do not alter runtime or civic semantics.
- Explicit approval required for: positive authority sealing, production database writes, activation, rollback, runtime corrections, deployment configuration/secrets, and ratification PR merge.

## Definition Of Done

- [x] Exact deployed commit and runtime manifest proven.
- [x] Fresh read-only production state matches the accepted 5/149/161/2 baseline and issue boundaries.
- [ ] Finalized 1/3/2/1 additive write set passes disposable apply, rejection, idempotency, and rollback proof (hosted PostgreSQL pending).
- [x] Immutable accepted=false/sealed=false ratification candidate validates and grants no authority.
- [x] Tests/build/validation recorded.
- [x] Review packet or final documentation updated.
- [ ] Exact-head hosted checks obtained on one draft PR.
- [ ] Final reconciliation completed.

## Baseline

- Branch/base commit: `codex/m12n-environment-energy-production-ratification` from `79d49f3e613e7914e4dc81d2f3b6a348cf80fafc`.
- Production/deployment state: `/health` reports exact post-PR157 main; production data still requires fresh read-only verification.
- Tracked working tree: clean isolated linked worktree.
- Known unrelated artifacts: original checkout contains historical Windows EOL noise and user-owned ZIPs; neither is touched.

## Implementation Sequence

1. Capture and validate fresh runtime and production-state evidence.
2. Regenerate the preparation/write-set/rollback package and construct the unaccepted ratification candidate.
3. Run disposable PostgreSQL, deterministic, regression, diff, and frozen-file validation.
4. Commit intended files, push, open one draft PR, obtain exact-head hosted checks, and stop.

## Progress Checklist

- [x] Discovery
- [x] Implementation
- [ ] Validation
- [x] Documentation
- [ ] Commit/PR readiness

## Discoveries

- PR157 merged as `79d49f3e613e7914e4dc81d2f3b6a348cf80fafc`; production `/health` reports that exact commit.
- The post-merge Render workflow deployed successfully but its smoke assertion failed on a historical Justice `artifact_id` expectation; the fresh milestone validator will establish the governed current identities.
- Fresh production state remained exactly `5 / 149 / 161 / 2` with fingerprint `b22908fb081fa3dcefbb2e7326b0619b9f95fecc1bbebc76e783628dceddb0eb`; Environment rows remain absent.
- Fresh runtime proof subject is `5b3d0df5464ba386d7cefe8bac3738650552e6a050955bcf5c9e5f18d582a3fc`; fresh preflight subject is `59f282ebd0888360669a4b1568a25b201ed552598cda661b40976a05d6932ab8`.
- Final preparation authority subject is `891256c341e8b4c97949559fb6a6016f926451a8aec7af15084b2d6212c31077`; final write-set subject is `b4a3a446ffb125459db63be746535b13663baa28c6c029eae32d7dfa99db9f98`.
- The ratification candidate is immutable, unaccepted, and unsealed; prospective subject digest is `725571c3319511f1f4debab25b63b842fd4fd7458056d828a2aaa06e4d88b49f`.

## Decisions And Rationale

- Use a clean linked worktree to avoid altering the original checkout's historical EOL noise or user-owned artifacts.
- Freeze every reviewed-runtime-manifest source on this branch; any required runtime change is a stop condition.

## Deviations Or Corrections

- Initial linked-worktree paths exceeded Windows path limits; repository-local `core.longpaths` and a short `.w/r` path resolved checkout without changing content.
- Two historical validators still exceeded the linked-worktree path ceiling for one frozen source; both passed unchanged from the shorter original checkout. No historical artifact was rewritten.

## Validation Results

- All 15 M12 validators passed; M12B/C passed from the shorter original checkout due the documented Windows path-length condition.
- Focused M12N/M11N suite: 40 passed.
- Editorial presentations API suite with read-only profile environment: 48 passed.
- Candidate validator, deterministic build check, JSON parse, Ruff lint/format, compileall, and `git diff --check`: passed.
- Frozen reviewed-runtime files, M11N governed artifacts, and accepted M12L/M12M governed artifacts: no Git diff.
- Disposable PostgreSQL proof is configured against the finalized governed write set and awaits hosted execution.

## Production Writes

- Performed: no.
- Scope: read-only production health and database preflight only.
- Expected effects: none.
- Actual effects: none; `/health` deployment and production preflight were read-only.

## Rollback Paths

- The prospective Environment-only rollback contract will be regenerated and proven solely in disposable PostgreSQL; no production rollback is authorized.

## Blockers

- Exact-head hosted CI and its disposable PostgreSQL proof remain pending until the draft PR is opened.

## Final Reconciliation

- Definition of done satisfied: pending.
- Remaining limitations: pending.
- Recommended next step: independent ratification of the exact prospective authority subject only.
