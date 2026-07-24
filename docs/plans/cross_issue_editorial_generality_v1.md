# Milestone Plan: Cross-Issue Editorial Generality V1

## Intent

- Immediate task: test whether the existing issue-neutral editorial pipeline can model one non-Justice, non-Economy House issue domain once and reuse it across two deterministically selected members.
- Larger-goal alignment: validate the next generality boundary after PR #99 without member-specific prose, domain-specific synthesis logic, exhaustive member review, or production publication.

## Outcome

- User-visible or operational result: either a review-only Health & Social validation packet with six actions, five episodes, two member slices, all 64 complete vectors, property/regression results, and guarded renderer anchors, or a precise fail-closed exception report.

## Scope And Boundaries

- In scope: one 119th-Congress House domain; exactly six substantive actions; five episodes; two action-structure-selected members; shared dossiers and traits; existing composer and validator; one generalized correction pass at most; review-only rendering and draft PR.
- Out of scope: Justice, Economy, Senate actions, ingestion, production writes, registry promotion, ZIP changes, frontend redesign, member-specific or exact-vector prose, merge, and manual deployment.
- Files/systems likely touched: `backend/app/summaries`, a focused build script and tests, `docs/editorial/cross_issue_editorial_generality_v1`, `docs/review_packets`, guarded frontend review data/anchors, and focused Node/render tests.

## Decision Envelope

- Codex may decide and execute: deterministic candidate scoring, official-source collection, existing-contract trait values, episode mapping, member selection by action structure, review-only artifacts, generalized tests, and draft PR creation.
- Explicit approval required for: production writes, publication promotion, registry inclusion, schema/product-semantics changes, merge, or deployment.

## Definition Of Done

- [x] Domain selection is deterministic, locked, and fail-closed with no eligible domain.
- [x] The source/action/episode inventory and exclusion reasons are preserved.
- [x] Downstream member, vector, and property work is explicitly not authorized after the Part I stop.
- [x] Renderer anchors and rendered inspection are explicitly not applicable after the Part I stop.
- [x] Backend, frontend, validator, mutation, lint, build/type, drift, leak, registry, and diff gates are recorded.
- [x] All real artifacts remain `human_approval_pending`, `not_promoted`, and `productionEligible: false`; production registry remains empty.
- [x] Review packet and final reconciliation are complete; the blocked result is ready for its draft PR.

## Baseline

- Branch/base commit: `codex/cross-issue-editorial-generality-v1` at `88d6f3446f54b07735e084cbc958c1614b190fab`.
- Production/deployment state, if relevant: review-only milestone; no production mutation or manual deployment authorized.
- Tracked working tree: clean isolated worktree; local `main` and `origin/main` verified at the required commit after fetch.
- Known unrelated untracked artifacts: preserved in other worktrees; none in this isolated worktree.

## Implementation Sequence

1. Complete repository/source inventory and freeze deterministic domain and action/episode selection.
2. Build one shared evidence/trait packet; obtain complete authoritative member vectors and lock two members.
3. Generate first member outputs and all-vector/property results through existing generic synthesis.
4. Apply at most one generalized correction if required, then run full regression and rendered validation.
5. Reconcile artifacts, commit intentional files, push, and open a draft PR without merge/deploy.

## Progress Checklist

- [x] Discovery
- [x] Implementation
- [x] Validation
- [x] Documentation
- [x] Commit/PR readiness

## Discoveries

- Startup gate passed: PR #99 merged at the required commit and `origin/main` had not advanced.
- The original checkout contains unrelated work, so this milestone uses a separate clean worktree.
- Initial benchmark inventory: Health & Social has six substantive House actions; National Security has twelve actions dominated by stages of one package plus one independent bill; Education has only two substantive House actions; Environment and Immigration have one each; Infrastructure is Senate/procedural-only in the benchmark.
- The broader stored packet inventory does not cure the benchmark gap. Native House evidence yields: Education three substantive actions/three single-action episodes; Health two/two; Environment one/one; Immigration one/one; Infrastructure zero; National Security many actions but only two parent-measure episodes.
- Five Health-stratum benchmark rows retain other stored primary-domain identities: Justice roll 131, Economy rolls 182/281/285, and National Security roll 262. They cannot be repurposed to manufacture a new Health ontology.

## Decisions And Rationale

- Interpretation boundary: syntheses describe the reviewed legislative choices and policy mechanisms, never motive, ideology, character, or voting advice.
- Domain result: none. Health & Social was the provisional benchmark-count leader, but the native-domain/source audit disqualified it. National Security fails the independent-episode gate.
- Stable domain tie-breaker: descending eligibility, then total structured score, then canonical domain ID ascending.

## Deviations Or Corrections

- The provisional Health direction was withdrawn before any domain lock, member synthesis, or public conclusion. This is discovery correction, not a synthesis correction pass.

## Validation Results

- Startup: fetched `origin`; `main == origin/main == 88d6f3446f54b07735e084cbc958c1614b190fab`; PR #99 state `MERGED`.
- Domain artifact drift check: pass.
- Focused selection tests: `7 passed`; RTK reported no collection, native `python -m pytest` retry passed. Two pytest cache warnings are local filesystem limitations, not product failures.
- Focused selection + proposition/property + benchmark tests: `42 passed`.
- Frontend Node suite: `136 passed`; this includes four semantic references, all 48 rules, and all 32 malformed mutations.
- Blind and Justice generators: deterministic. Existing editorial-standardization report drifted at the starting commit; it was not regenerated because that would be an unrelated baseline artifact change.
- ESLint: pass with eight pre-existing hook warnings.
- Next production build: compiled and completed type validation, then failed during page-data collection with `Cannot find module for page: /_document`.
- Rendered suite using a temporary dependency junction: 11 passed, 1 failed, 12 skipped. The failure followed a Next dev-server React client-manifest path error; no new renderer was created after the Part I stop.
- Full backend suite: 680 passed, 14 failed, 41 errors. Failures were outside this selection change: inaccessible shared pytest temp state, missing ignored Senate XML/source files, and a pre-existing pinned ZIP manifest checksum mismatch.

## Production Writes

- Performed: no
- Scope: none authorized.
- Expected effects: none.
- Actual effects: none.

## Rollback Paths

- All milestone changes are isolated on the milestone branch/worktree and remain removable by dropping that worktree/branch after review; no production rollback is needed.

## Blockers

- Hard stop reached: no candidate domain meets the action-count, episode-count, and multi-action-episode gates simultaneously.

## Final Reconciliation

- Definition of done satisfied: the Part I blocked-result definition is satisfied and ready for draft-PR delivery.
- Remaining limitations: cross-issue synthesis remains untested because no eligible evidence set exists inside the milestone envelope.
- Recommended next step: run one additional bounded domain validation only after a qualifying native House evidence set exists; do not expand this milestone to create it.
