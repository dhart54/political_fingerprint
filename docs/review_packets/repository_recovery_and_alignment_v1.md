# Repository Recovery and Canonical Root Alignment V1

Date: 2026-07-24
Production writes: none
Merge, deployment, publication, promotion: not authorized and not performed

## Outcome

The dirty root checkout was preserved through a validated external recovery package, recovery branch, and named stash. All five registered child worktrees were moved outside the repository with `git worktree move`. The repository root was then safely switched to `main` and fast-forwarded to exact `origin/main` `3d0ffb252c54fb8b93e58fbd4724724ec40a2790` before the scoped milestone branch was created.

No unpreserved state was discarded. No reset-hard, clean, forced checkout, raw worktree move, worktree remove, broad deletion, blanket review-bundle ignore, merge, deployment, publication change, or production-data operation occurred.

## Recovery package

Path:

```text
C:\Users\Dylan\Documents\Data Science\political_fingerprint-recovery\2026-07-24-root-38ad159
```

Recovery references:

- original root branch: `codex/foushee-justice-public-safety-gold-v1`;
- original root commit: `38ad15999f4bfcea85c8777f25da816888750942`;
- recovery branch: `codex/recovery-root-20260724-38ad159`;
- named stash: `repository-recovery-alignment-v1 root preservation 2026-07-24`;
- detached validation worktree: `C:\Users\Dylan\Documents\Data Science\political_fingerprint-recovery\validation-root-38ad159`.

Package contents:

- `root-tracked.patch`;
- `root-status-porcelain-v2.txt`;
- `worktree-list-porcelain.txt`;
- `branch-and-commit-metadata.txt`;
- `sha256.json`;
- `RESTORE.md`;
- copied chamber filtering audit;
- all 19 files from `review_bundle_frontend_data_grounding/`;
- Repository and Documentation Hygiene Audit V1 Markdown and JSON.

Validation:

- `git apply --check` passed in the clean detached recovery worktree;
- 19 source bundle files matched 19 copied files;
- chamber audit source and copied SHA-256 matched;
- both chamber-audit references into the copied bundle resolved;
- all 27 entries in `sha256.json` existed and matched;
- `sha256.json` SHA-256: `C99397D930ED57A28B80FBF8F070C0C02856692B0DA00C9332E249A20F9FFF8A`.

Critical recovery hashes:

| File | SHA-256 |
| --- | --- |
| `root-tracked.patch` | `4E202611C0D87AA8A998DF3A4256D6C5B28499E2F94425448D9861098AC57E65` |
| `root-status-porcelain-v2.txt` | `A47957168EA893C81FBE40C63579327BA3DC47A3C398746BDC592F643A73557D` |
| `worktree-list-porcelain.txt` | `1AC8FBD717FF81ED4CD086D55EA45F4B41A6BE7204C3F242482A5C77E0EC1286` |
| copied chamber audit | `9DFC4743592275DF2FDB3E599D8E115310B981A110CB02E36E2408556500E910` |
| hygiene audit Markdown | `F960596CE4570C3EE62FD18CF3F351C804596DCACDA923547268CA3C4ACAAD11` |
| hygiene audit JSON | `E25E2B7BB8B7DB9190A10025FFC000D02EC8DCC6EEF4D9271D9CAFB8BD87282B` |
| restoration instructions | `001F62C0AA2C55645C768B57668710DA44B7CD6ECA2E60456CC3D33A781CADA9` |

The JSON companion records all 27 package-file hashes.

## Cleanup performed

Exactly the approved allowlist was removed:

- `docs/.gitkeep`;
- `_codex_worktrees/blind-editorial-pipeline-validation-v1/frontend/test-results/.last-run.json`;
- `_codex_worktrees/public-editorial-product-frontend-v1/frontend/test-results/.last-run.json`;
- `_codex_worktrees/blind-editorial-pipeline-validation-v1/backend/tests/_data_inventory_cases/`.

Nothing else was deleted.

## Before and after worktree locations

| Branch or purpose | Before | After |
| --- | --- | --- |
| Blind editorial validation | `C:\Users\Dylan\Documents\Data Science\political_fingerprint\_codex_worktrees\blind-editorial-pipeline-validation-v1` | `C:\Users\Dylan\Documents\Data Science\political_fingerprint-worktrees\blind-editorial-pipeline-validation-v1` |
| Cross-issue generality | `C:\Users\Dylan\Documents\Data Science\political_fingerprint\_codex_worktrees\cross-issue-editorial-generality-v1` | `C:\Users\Dylan\Documents\Data Science\political_fingerprint-worktrees\cross-issue-editorial-generality-v1` |
| Editorial artifact persistence | `C:\Users\Dylan\Documents\Data Science\political_fingerprint\_codex_worktrees\editorial-artifact-persistence-v1` | `C:\Users\Dylan\Documents\Data Science\political_fingerprint-worktrees\editorial-artifact-persistence-v1` |
| Justice cross-member validation | `C:\Users\Dylan\Documents\Data Science\political_fingerprint\_codex_worktrees\justice-cross-member-validation-v1` | `C:\Users\Dylan\Documents\Data Science\political_fingerprint-worktrees\justice-cross-member-validation-v1` |
| Former dedicated `main` checkout | `C:\Users\Dylan\Documents\Data Science\political_fingerprint\_codex_worktrees\public-editorial-product-frontend-v1` | `C:\Users\Dylan\Documents\Data Science\political_fingerprint-worktrees\main` |

The former dedicated `main` worktree is detached at `88d6f3446f54b07735e084cbc958c1614b190fab` so the root can own `main`. It retains its referenced review bundle.

The recovery validation worktree is registered outside the repository at:

```text
C:\Users\Dylan\Documents\Data Science\political_fingerprint-recovery\validation-root-38ad159
```

After `git worktree repair`, no registered worktree remains beneath the repository root.

## Referenced review evidence

Before moving the two worktrees containing referenced screenshots, all assets were inventoried and hashed:

- blind editorial validation: 4 screenshots;
- public editorial frontend validation: 15 screenshots.

After moving, all 19 files existed at the same worktree-relative paths and retained their exact hashes. The bundles were moved with their registered worktrees; no reference rewrite or external review-archive move was required.

The older `review_bundle_frontend_data_grounding/` and chamber audit were preserved in the external recovery package and named stash. They were not restored into the canonical root because they are not part of this tracked PR scope.

## Repository changes

- Added narrow ignore rules for external worktrees, Playwright output, named pytest temp roots, and the Windows venv.
- Did not ignore review bundles, `.local/`, `backend/data_sources/`, reports, source manifests, rollback SQL, or editorial artifacts.
- Repaired five machine-specific README links.
- Added `docs/README.md` as an authority and retention index.
- Added the non-negotiable autonomy and failure-handling contract to `docs/workflows/editorial-standardization-pipeline.md`.
- Added the mandatory workflow pointer to `AGENTS.md`.
- Added the living milestone plan and both hygiene/recovery review packets.
- Preserved the four route terms without changing publication or editorial meaning:
  - `standard_generation_pass`;
  - `sampled_audit_candidate`;
  - `human_exception_required`;
  - `blocked`.

## Files and areas explicitly left untouched

- `.local/`;
- `backend/data_sources/`;
- all ACL-inaccessible pytest temp directories;
- every review screenshot bundle;
- all completed plans pending a later archive decision;
- all legacy authority documents pending human semantic reconciliation;
- tracked generated JSON/Markdown reports;
- source manifests;
- rollback SQL;
- committed editorial artifacts;
- publication, benchmark, and production registry status;
- production data, schema state, services, deployments, and secrets;
- original dirty source state preserved by the recovery package and stash.

## Root alignment

Alignment gate result:

- remote `main` remained `3d0ffb252c54fb8b93e58fbd4724724ec40a2790`;
- root switched safely to `main`;
- local `main` fast-forwarded from `88d6f3446f54b07735e084cbc958c1614b190fab`;
- root `HEAD` and `origin/main` matched exactly before milestone branch creation;
- root status was clean;
- migration `backend/migrations/0016_editorial_artifact_persistence.sql` was present;
- editorial artifact modules were present;
- `docs/workflows/editorial-standardization-pipeline.md` was present;
- the frontend production editorial registry was frozen and empty.

Final delivery branch:

```text
codex/repository-recovery-alignment-v1
```

The exact final commit is reported by Git and the draft PR after commit creation; it cannot be embedded self-referentially in the commit that contains this packet.

## Validation results

| Validation | Result |
| --- | --- |
| Recovery `git apply --check` | passed |
| Recovery package hashes | 27/27 passed |
| Chamber audit bundle references | 2/2 resolved |
| Moved review assets | 19/19 hashes preserved |
| `git worktree repair` and registry inspection | passed |
| `git fsck --no-dangling --no-progress` | passed |
| Repository-relative Markdown link scan | 230 files, 0 failures |
| Documentation authority/workflow contract assertion | passed |
| Frontend editorial workflow tests | 49 passed |
| Backend Economy editorial documentation tests | 15 passed |
| Production registry assertion | frozen and empty |
| Required migration/artifact/workflow files | present |
| `git diff --check` | passed |

The raw `node scripts/build_editorial_standardization_validation.mjs --check` command failed because the Windows checkout contains CRLF report files while the builder creates LF strings and compares raw bytes. A read-only rerun that normalized only those two report inputs to LF passed: `Editorial standardization validation artifacts are deterministic and current.` No report was regenerated or modified.

## Limitations and retained recovery state

- The detached patch-validation worktree remains registered because this milestone prohibited `git worktree remove`.
- ACL-inaccessible pytest temp directories remain untouched and may still emit status warnings until a later approved cleanup.
- The named stash remains available as an additional local recovery layer.
- The external recovery package and moved worktrees are not part of the repository diff or PR.

## Final reconciliation

The approved low-risk recovery and alignment scope is complete. Broader documentation archival and legacy-authority consolidation remain explicitly deferred. No production or publication boundary changed.
