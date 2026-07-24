# Milestone Plan: Documentation Governance Cleanup V1

## Intent

- Immediate task: Archive only clearly completed execution plans, clarify active and unresolved plan status, repair navigation, add deterministic governance checks, and prepare a section-level legacy-authority reconciliation.
- Larger-goal alignment: Reduce documentation clutter while preserving provenance and preventing obsolete execution records from operating as current instructions.

## Outcome

- User-visible or operational result: Repository documentation exposes one current plan, visibly retains ambiguous plans for human resolution, separates immutable historical execution records, and fails deterministically when plan navigation or repository-relative links drift.

## Scope And Boundaries

- In scope: Plan classification and safe archival, documentation indexes and links, a narrow checker and focused tests if needed, Markdown and JSON review receipts, and non-destructive legacy-authority analysis.
- Out of scope: Application/database/schema changes, civic or product semantic changes, production writes, review-packet/editorial/source-manifest moves, commissioning-domain work, merge, deployment, publication, promotion, or approval.
- Files/systems likely touched: `docs/README.md`, `docs/plans/**`, current navigational documentation, `scripts/`, checker tests if required, and `docs/review_packets/documentation_governance_cleanup_v1.{md,json}`.

## Decision Envelope

- Codex may decide and execute: Move only revalidated `archive` candidates that have terminal evidence and no unsafe dependency; repair current navigation; add archive/index notices; implement a narrow deterministic checker; create review receipts; commit, push, and open a draft PR.
- Explicit approval required for: Any civic/product-semantics decision, ambiguous authority resolution, production effect, destructive action, merge, deployment, publication, promotion, or editorial approval.

## Definition Of Done

- [x] Every audit-listed plan candidate has an evidence-backed final routing decision.
- [x] Every `archive_confirmed` plan is moved with safe references repaired; ambiguous plans remain in place and are visibly routed.
- [x] `docs/README.md`, `docs/plans/README.md`, and `docs/plans/archive/2026/README.md` identify current, unresolved, and historical plan authority accurately.
- [x] Legacy authority documents have section-level classifications without destructive consolidation.
- [x] Deterministic documentation governance and Markdown-link validation pass.
- [x] Required Markdown and JSON review receipts are complete.
- [x] Tests/build/validation recorded.
- [x] Review packet or final documentation updated.
- [x] Final reconciliation completed.

## Baseline

- Branch/base commit: `codex/documentation-governance-cleanup-v1` from exact `origin/main` `98029d77ad43f7e877eb545b25d9b6878e71cb1a` after `git fetch origin`.
- Production/deployment state, if relevant: No production action authorized; static frontend production editorial registry verified frozen and empty.
- Tracked working tree: Clean before branch creation; root `HEAD` equaled `origin/main`.
- Known unrelated untracked artifacts: Root-local ignored/test/cache directories remain untouched. All registered child worktrees are external to the root.

## Implementation Sequence

1. Revalidate audit classifications, references, terminal evidence, recovery state, and unresolved plan status.
2. Move safe completed plans and repair only current navigational references.
3. Add active/unresolved/archive indexes and deterministic governance validation.
4. Classify legacy authority sections and create complete Markdown/JSON receipts.
5. Run required validation, reconcile the plan, commit, push, and open the authorized draft PR.

## Progress Checklist

- [x] Discovery
- [x] Implementation
- [x] Validation
- [x] Documentation
- [x] Commit/PR readiness

## Discoveries

- Preflight confirmed root `HEAD` and fetched `origin/main` at `98029d77ad43f7e877eb545b25d9b6878e71cb1a`.
- The external recovery package, recovery branch, named preservation stash, and detached validation worktree remain present.
- Registered child worktrees are outside the repository root; the static production registry exports an empty frozen array.
- Forty-one audit candidates had zero unchecked items, documented terminal reconciliations, and no live consumer, so they were archived.
- `zip_source_metadata_ambiguity_payload_v1.md` is terminal but remains at its original path because a backend report builder consumes it.
- Three review receipts retain moved plans' old paths as historical literals; changing them would rewrite provenance rather than repair navigation.

## Decisions And Rationale

- Treat the audit JSON as the candidate manifest, but require current terminal-state and dependency evidence before any move.
- Leave provenance literals unchanged when they record historical paths rather than provide navigation.
- Route all four audit-listed incomplete plans as `retain_unresolved` / completed-but-unreconciled pending human terminal-status decisions.
- Do not add banners to legacy authority files; the section-level proposal is safer because some technical rules may remain unique.

## Deviations Or Corrections

- One automatic candidate was retained as `blocked_reference_dependency`; this is required failure behavior, not a scope reduction.

## Validation Results

- Preflight: clean root, exact fetched `origin/main`, recovery assets present, external worktree layout intact, and production registry empty.
- `origin/main` refetch: unchanged at `98029d77ad43f7e877eb545b25d9b6878e71cb1a`.
- Documentation governance / repository-relative Markdown links: passed.
- Checker syntax compilation and JSON receipt parse: passed.
- Machine-specific navigational-link search: zero.
- Old-path search: 41 moved paths checked; zero unexpected references.
- Unresolved-plan proof: four unresolved plans and the builder-dependent blocked plan remain at original paths.
- Protected deletion proof: zero deletions.
- Worktrees: seven registered paths exist; zero child worktrees beneath root.
- Production registry: frozen and empty.
- `git diff --check`: passed.
- Application builds: intentionally not run because application behavior did not change.

## Production Writes

- Performed: no
- Scope: None authorized.
- Expected effects: None.
- Actual effects: None.

## Rollback Paths

- Before commit, reverse scoped file moves/edits only after resolving exact targets; after commit, revert the milestone commit. Recovery assets and external worktrees are not part of this branch.

## Blockers

- No active blocker. One completed plan remains intentionally blocked from archival by its report-builder dependency.

## Final Reconciliation

- Definition of done satisfied: Yes. Implementation, validation, scoped commit `0cd6f73`, branch push, and draft PR #103 are complete.
- Remaining limitations: Four plans still need human terminal-status reconciliation; one completed plan cannot move while code pins its path; legacy technical/product authority decisions remain deliberately unresolved.
- Recommended next step: Review draft PR #103, then make the exact human decisions listed in the review packet before any legacy consolidation.
