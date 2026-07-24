# Repository Recovery and Canonical Root Alignment V1

## Milestone intent

Preserve the dirty root checkout in a validated external recovery package, perform only the approved low-risk hygiene actions, move registered child worktrees outside the repository, align the root to exact `origin/main`, and deliver the scoped repository documentation changes in a draft PR.

## Larger-goal alignment

This milestone restores a trustworthy canonical checkout and makes documentation authority and retention discoverable without changing civic, editorial, publication, deployment, or production-data semantics.

## User-visible or operational outcome

- The repository root becomes a clean checkout based on canonical `main`.
- Registered child worktrees live in the external sibling worktree root.
- The old dirty state remains recoverable by patch, hashes, copied unique evidence, and a recovery branch.
- Narrow ignore and documentation contracts prevent recurrence.

## Scope and boundaries

In scope: the exact recovery package, recovery ref, four cleanup targets, narrow ignore rules, five README links, `docs/README.md`, the editorial autonomy/failure-handling contract, its AGENTS pointer, worktree moves, root alignment, validation, review packet, commit, push, and draft PR.

Out of scope: broader plan archival, legacy-authority consolidation, review-bundle deletion, merge, deployment, publication, promotion, production data, schema changes, and product/editorial meaning changes.

## Decision envelope

- Use no reset-hard, clean, forced checkout, raw worktree move, worktree remove, or broad deletion.
- Stop on any failed recovery, hash, reference, worktree-integrity, remote-main, or preservation gate.
- Preserve the route terms `standard_generation_pass`, `sampled_audit_candidate`, `human_exception_required`, and `blocked`.
- Do not change publication or editorial status.

## Definition of done

- [x] Baseline and remote `main` match the approved commits.
- [x] Recovery package and recovery branch exist.
- [x] Binary patch applies cleanly at the recovery commit.
- [x] Copied unique evidence, hashes, and references validate.
- [x] Only the four approved cleanup targets are removed.
- [x] Narrow ignores and five README links are correct.
- [x] Documentation authority index and editorial contract are complete.
- [x] Referenced review evidence remains resolvable after worktree moves.
- [x] No registered child worktree remains under the repository root.
- [x] Root is safely aligned to exact `origin/main`.
- [x] Required migrations, workflow, and empty production registry are verified.
- [x] Documentation and editorial workflow validation passes.
- [x] Review packet and JSON companion are complete.
- [ ] Intended tracked files only are committed and pushed in a draft PR.

## Current baseline

- Approved remote and local `origin/main`: `3d0ffb252c54fb8b93e58fbd4724724ec40a2790`.
- Original root branch and commit: `codex/foushee-justice-public-safety-gold-v1` at `38ad15999f4bfcea85c8777f25da816888750942`.
- Recovery branch: `codex/recovery-root-20260724-38ad159`.
- Recovery package: `C:\Users\Dylan\Documents\Data Science\political_fingerprint-recovery\2026-07-24-root-38ad159`.
- Detached patch-validation worktree: `C:\Users\Dylan\Documents\Data Science\political_fingerprint-recovery\validation-root-38ad159`.

## Implementation sequence

1. Validate baseline and governing contracts.
2. Build and validate recovery package.
3. Perform exact cleanup allowlist.
4. Add scoped repository documentation changes.
5. Inventory and preserve referenced worktree evidence.
6. Move registered children with `git worktree move`.
7. Preserve root state in Git and external recovery, then align root.
8. Reconcile intended changes on a milestone branch from canonical main.
9. Validate, document, commit, push, and open a draft PR.

## Progress checklist

- [x] Read-only baseline inspection.
- [x] Remote-main check without fetch.
- [x] Child tracked-clean checks.
- [x] Recovery package creation.
- [x] Patch, hash, and reference validation.
- [x] Approved automatic cleanup.
- [x] Repository documentation changes.
- [x] Worktree relocation.
- [x] Root alignment.
- [x] Tests and documentation validation.
- [ ] Draft PR.

## Discoveries

- The first patch-generation command used an invalid PowerShell argument shape; it created no patch and no later phase started. The exact patch command was corrected, and the resulting 153,148-byte patch passed `git apply --check`.
- The recovery package contains 27 hashed files excluding its self-referential SHA manifest.
- The dedicated validation worktree is detached outside the repository because `git worktree remove` is prohibited by this milestone.
- The raw editorial standardization `--check` compares LF generator output to CRLF working-tree files and fails on this Windows checkout. A read-only check that normalizes only those two report inputs to LF passes, proving the committed semantic content is current; no generated artifact was changed.

## Decisions and rationale

- Keep all referenced screenshot bundles with their worktrees during relocation so their repository-relative validation paths remain resolvable inside each checkout.
- Use Git worktree commands exclusively for registered checkout relocation.
- Preserve root state in both the external package and Git before changing the root branch.

## Deviations and corrections

- Patch generation was retried once after Git rejected an empty output argument. No cleanup, branch switch, worktree move, or root alignment occurred before the corrected patch passed.

## Validation results

- Recovery patch apply check: passed.
- Bundle copy: 19 source files and 19 destination files; zero mismatches.
- Chamber audit copy SHA-256: matched.
- Chamber bundle references: both resolved.
- Recovery manifest: 27 entries, zero missing files, zero hash failures.
- Worktree relocation: five registered children moved; no child remains under the root; 19/19 referenced screenshots retained their pre-move hashes.
- Root alignment: clean `main` reached exact `origin/main` `3d0ffb252c54fb8b93e58fbd4724724ec40a2790` before the milestone branch was created.
- Markdown links: 230 tracked and intended Markdown files scanned; zero missing or repository-absolute local targets.
- Documentation contract: passed.
- Frontend editorial workflow tests: 49 passed.
- Backend Economy editorial documentation contract: 15 passed.
- Production editorial registry: frozen and empty.
- Editorial standardization drift: raw Windows check failed on CRLF/LF byte comparison; LF-normalized deterministic check passed.
- `git diff --check`: passed.
- Worktree list and `git fsck --no-dangling --no-progress`: passed.

## Production writes performed

None authorized or performed.

## Rollback paths

- External recovery package with binary patch, copied untracked evidence, metadata, hashes, and restoration instructions.
- Recovery branch at the original root commit.
- Detached clean validation worktree at the recovery commit.

## Blockers

None currently. Any mandatory stop condition will be recorded here and halt the milestone.

## Final reconciliation

Recovery, cleanup, documentation, worktree relocation, canonical-root alignment, and validation are complete. Commit, push, and draft-PR delivery remain; their final identifiers cannot be embedded in the commit that creates them and will be reconciled in a follow-up plan update on the same branch.
