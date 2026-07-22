# Milestone Plan: Public Editorial Product Frontend V1

## Intent

- Immediate task: Turn the generic editorial issue experience into a polished, domain-neutral public presentation contract without publishing any pending editorial slice.
- Larger-goal alignment: Prepare the representative issue route to explain reviewed legislative behavior clearly, with receipts, bounded coverage, and safe fallbacks as editorial coverage grows.

## Outcome

- User-visible or operational result: A reader-facing issue summary, coverage model, issue availability language, improved basic-evidence fallback, and exact public-mode review previews that work across complete, mixed, partial, unavailable, and procedural-only records.

## Scope And Boundaries

- In scope: representative issue navigation; editorial selector/presentation/renderer; coverage-state derivation; public copy; basic fallback; review harness; synthetic fixtures; responsive/accessibility tests; documentation and screenshots.
- Out of scope: research claims, vote or episode meaning, inference/candidate selection, real publication status, production registry entries, comparison views, homepage redesign, broad scaling, API/persistence migrations, merge, or manual deployment.
- Files/systems likely touched: `frontend/components`, `frontend/lib`, `frontend/tests`, the guarded golden-render route, `docs/workflows`, `docs/plans`, and `docs/review_packets`.

## Decision Envelope

- Codex may decide and execute: domain-neutral public terminology; layout hierarchy; coverage states derived from supplied structured fields; issue availability wording; synthetic test fixtures; targeted fallback and review-harness improvements; branch, commit, push, and draft PR.
- Explicit approval required for: changing analytical meaning, publishing a real slice, modifying production data or registries, broad redesign, merge, or manual deployment.

## Definition Of Done

- [x] Actual representative-to-editorial/fallback path is documented and public terminology is isolated from review semantics.
- [x] Public presentation handles reviewed conclusion, developing, limited, unavailable, and procedural-only coverage without calculating political conclusions in React.
- [x] Issue navigation and fallback communicate evidence availability in reader language while preserving vote-card progressive disclosure.
- [x] Review mode renders pending data through the exact public adapter/renderer and synthetic fixtures cover all requested public states.
- [x] Real statuses, production registry, inference semantics, and editorial source artifacts remain unchanged.
- [x] Tests/build/rendered validation and forbidden-term scans are recorded.
- [x] Review packet, contract, glossary, and coverage guidance are updated.
- [x] Final reconciliation completed.

## Baseline

- Branch/base commit: `codex/public-editorial-product-frontend-v1` from exact post-PR-#96 `main` SHA `55ab4218b4a7c59d7b5da871b294c17c5096503e`.
- Production/deployment state, if relevant: no real editorial slice is production eligible; automatic draft-PR preview is allowed; merge and manual production deployment are forbidden.
- Tracked working tree: clean isolated worktree at milestone start.
- Known unrelated untracked artifacts: none in the isolated milestone worktree.

## Implementation Sequence

1. Trace the representative route, issue selection, evidence loading, editorial eligibility, fallback, registries, and review harness; inventory public terminology and responsive behavior.
2. Formalize a domain-neutral public view model and coverage-state mapper, then update summary hierarchy, issue availability, fallback, and review previews without changing analytical inputs.
3. Add synthetic state fixtures, forbidden-term/accessibility/responsive regressions, documentation, rendered evidence, and full validation.
4. Reconcile scope and gates, commit intended files, push normally, and open a draft PR without merging.

## Progress Checklist

- [x] Discovery
- [x] Implementation
- [x] Validation
- [x] Documentation
- [x] Commit/PR readiness

## Discoveries

- Startup gate passed after local `main` was explicitly fast-forwarded: local and remote `main` both resolve to `55ab4218b4a7c59d7b5da871b294c17c5096503e`.
- PR #96 is merged; its final head and `origin/main` have identical trees.
- The production route already had a pure selection/adapter boundary, but the adapter exposed review-oriented synthesis wording and the React surface mixed the public experience with review labeling.
- The previous basic fallback combined interpreted vote counts into broader prose. That exceeded the safe public fallback contract when no eligible editorial slice exists.
- The readiness grid appeared before the selected issue result and pushed the conclusion below the fold. Moving the full grid below the selected evidence preserves navigation while restoring conclusion-first hierarchy.

## Decisions And Rationale

- Interpretation boundary: lead with the supplied evidence-grounded conclusion, keep party alignment as secondary voting context, and consolidate sample limits below the finding rather than repeating defensive caveats.
- Public React will consume reader-facing concepts only; internal inference codes, candidate IDs, workflow states, and publication gates remain in selectors, adapters, data, or isolated review chrome.
- Coverage counts describe the reviewed sample and never act as a political score or a claim that incomplete coverage means no position.
- `reviewed_conclusion`, `developing_record`, and `limited_evidence` derive only from supplied inference state, expected records, and independent-episode coverage. The fallback uses separate `no_editorial_coverage` and `procedural_context_only` states and never creates a political finding.
- Public evidence-strength terms are centralized in `editorialIssuePublicPresentation.mjs`; review metadata is isolated as `reviewContext`, and review labels remain outside elements marked as public surfaces.
- Issue availability uses three reader terms: `Reviewed analysis`, `Vote evidence`, and `Limited record`.
- Real pending slices continue through the exact selector, adapter, and renderer in review mode. Synthetic production-eligible and partial-coverage fixtures exercise public behavior without changing any real publication signal.

## Deviations Or Corrections

- Initial rendered review showed the issue-readiness grid dominating the top of the evidence panel. It was moved below the selected issue experience and the compact jump navigation was kept above it.
- One local development request returned a transient 500 while source files were hot-reloading; the final clean 17-case Playwright run and production build passed.

## Validation Results

- Frontend Node suite: 108 passed (`node --test --test-concurrency=1 lib/*.test.mjs`).
- Responsive/accessibility golden-render suite: 17 passed at wide desktop, laptop, tablet, and 390 px mobile widths, including keyboard disclosure, single-parent expansion, overflow, public-term, source-grouping, navigation, production-gate, and screenshot cases.
- Focused backend/content/inference suite: 42 passed across Economy editorial gold, Economy staged website, Justice & Public Safety editorial gold, Justice cross-member validation, and generic editorial inference. The suites include deterministic builder `--check` assertions.
- ESLint: passed with zero errors and eight pre-existing React hook warnings.
- Production build/type validation: passed with the same eight pre-existing warnings.
- `git diff --check`: passed; only normal LF-to-CRLF notices were emitted.
- Production-registry and editorial-source diff: empty against `origin/main`.
- Runtime genericity scan: no member names, selected-member IDs, roll-number conditionals, candidate IDs, or party conditionals in the changed editorial runtime path. Existing domain catalogs in `profileNarrative.mjs` remain unchanged in purpose.
- Visual review: conclusion-first desktop, 390 px mobile, outer review-harness separation, developing, fallback, procedural-only, grouped-source, and production-gate states reviewed. Fifteen screenshots are in the untracked local review bundle.

## Production Writes

- Performed: no
- Scope: none authorized.
- Expected effects: none.
- Actual effects: none.

## Rollback Paths

- All changes are isolated on the milestone branch and can be reverted by commit; no data or production rollback is required.

## Blockers

- None after startup reconciliation.

## Final Reconciliation

- Definition of done satisfied: yes. The milestone changes only the generic frontend contract, fixtures, tests, and documentation.
- Remaining limitations: real editorial slices remain pending and production-ineligible; human editorial approval, benchmark promotion, publication, merge, deployment, and user comprehension sessions remain outside this milestone.
- Recommended next step: review the draft PR and automatic preview using `docs/review_packets/public_editorial_product_frontend_v1.md`; do not merge or publish until the separate governance decisions are made.
