# Milestone Plan: Episode-first editorial product v1

## Intent

- Immediate task: Replace the review-mode vote-first editorial surface with a bounded episode-first hierarchy and a member-neutral shared-evidence contract.
- Larger-goal alignment: Help readers understand a representative's reviewed behavior quickly while preserving exact legislative receipts and civic-integrity boundaries.

## Outcome

- User-visible or operational result: The three reviewed slices lead with one conclusion, compact coverage, structured findings, featured policy episodes, and a collapsed complete record; shared Justice facts remain reusable across member action overlays.

## Scope And Boundaries

- In scope: Generic editorial view/presentation contracts; episode and policy-family grouping; service-aware statuses; the three reviewed syntheses; Economy episode coverage; member-neutral Justice evidence; bounded review fixtures; tests, rendered review, and documentation.
- Out of scope: New legislative research, changed vote facts or sources, production promotion, real 118th-Congress content, comparison UX, nationwide generation, homepage redesign, merge, or manual production deployment.
- Files/systems likely touched: `frontend/components`, `frontend/lib`, editorial review artifacts, backend overlay validation/tests, golden-render harness, docs.

## Decision Envelope

- Codex may decide and execute: Data/view contract shape, component hierarchy, progressive-disclosure layout, deterministic fixture generation, focused copy cleanup, tests, build, and preview-ready documentation.
- Explicit approval required for: New civic semantics outside the requested statuses, production writes, real-slice approval/promotion/registry changes, merge, or manual deploy.

## Definition Of Done

- [x] Shared action + episode relationship + member overlay + issue synthesis contract is explicit and member-neutral.
- [x] Policy-family/Congress/episode/action hierarchy and all service-aware statuses are tested with synthetic fixtures.
- [x] Economy and both Justice reviewed slices render the requested conclusions, structured findings, coverage, and featured episodes.
- [x] Default rich surface stays bounded and preserves every action/source behind disclosure; procedural/context records remain secondary and non-counting.
- [x] Legacy/internal rich-surface sections and duplicate public titles/summaries are suppressed while the basic fallback remains intact.
- [x] Tests/build/rendered validation recorded.
- [x] Review packet and contract documentation updated.
- [x] Final reconciliation completed.

## Baseline

- Branch/base commit: `codex/episode-first-editorial-product-v1` from `25baf5b2e9578abfb307b5eb52f98b04f57953dc` (PR #97 merge); fetched `origin/main` matched this SHA on 2026-07-22.
- Production/deployment state, if relevant: Review-only slices are pending, not promoted, and production-ineligible; no production writes authorized.
- Tracked working tree: Isolated milestone worktree clean at branch creation.
- Known unrelated untracked artifacts: `review_bundle_public_editorial_product_frontend_v1/` preserved in the worktree; unrelated changes in the primary checkout are outside this branch.

## Implementation Sequence

1. Inventory PR #97 public presentation and checked-in Economy/Justice episode artifacts.
2. Formalize neutral shared evidence, episode/policy-family, member action, service-status, coverage, and featured-episode contracts.
3. Build the bounded episode-first adapter and rich surface while retaining the basic fallback.
4. Correct the three review syntheses, Economy coverage, and focused card duplication/filler.
5. Add contract, neutral-reuse, service-status, bounded-height, hierarchy, and regression tests.
6. Run targeted tests, frontend build, and desktop/tablet/mobile rendered review; document reconciliation.

## Progress Checklist

- [x] Discovery
- [x] Implementation
- [x] Validation
- [x] Documentation
- [x] Commit/PR readiness

## Discoveries

- PR #97 introduced `EditorialIssueExperience`, `editorialIssuePublicPresentation.mjs`, and rich-surface routing but still renders a flat action list plus large coverage/methodology panels.
- The current cross-member adapter copies Foushee's Justice records and replaces only headline/action-result fields, leaving member-specific argument boundaries and caveats in reusable evidence.
- The attached request's expected-main header matches fetched `origin/main`; a later numbered SHA is nonexistent and was treated as a typo. The attachment ends mid-way through section 19, so implementation follows all complete requirements supplied plus repository runbooks.

## Decisions And Rationale

- Interpretation boundary: conclusions remain bounded to the reviewed actions and concrete mechanisms; no motive, ideology, recommendation, or cross-time-change claim will be introduced.
- Preserve the action receipt as the authoritative detailed unit, but render it only inside its episode so repeated stages do not read as independent positions.
- Use upstream service metadata/status fields; React will render, not infer, service eligibility.

## Deviations Or Corrections

- The requested numbered startup SHA `25baf5b2e9578abfb307b5da871b294c17c5096503e` is not a repository object; the request's stated expected-main SHA and fetched `origin/main` both resolve to `25baf5b2e9578abfb307b5eb52f98b04f57953dc`.

## Validation Results

- `python -m pytest backend/tests/test_editorial_member_overlay.py -q`: 13 passed.
- `python -m pytest backend/tests/test_justice_cross_member_validation.py backend/tests/test_valerie_foushee_justice_public_safety_editorial_gold_v1.py backend/tests/test_valerie_foushee_economy_editorial_gold_v2.py -q -p no:cacheprovider`: 33 passed.
- `node --test frontend/lib/*.test.mjs`: 120 passed.
- `npm run build`: passed; only pre-existing hook warnings were reported.
- `npm run test:golden-render`: 8 passed and 12 skipped; 11 skips are superseded flat-card assertions and one is the opt-in screenshot capture.
- Browser review at 1440 px, 768 px, and 390 px confirmed one rich-surface title, closed default disclosures, the requested featured-episode counts, nested receipts, and no horizontal overflow.

## Production Writes

- Performed: no
- Scope: none
- Expected effects: none
- Actual effects: none

## Rollback Paths

- Revert the milestone commit(s); no schema migration, production data, approval state, or registry change is planned.

## Blockers

- None currently. The supplied attachment is truncated after the first field of section 19; completed requirements are sufficiently specific to proceed without inventing broader scope.

## Final Reconciliation

- Definition of done satisfied: Yes. The episode-first hierarchy, neutral shared evidence, service-aware statuses, bounded disclosures, three corrected review slices, tests, build, rendered review, and documentation are complete.
- Remaining limitations: The supplied brief ends mid-section 19; implementation is limited to its complete requirements and does not invent the missing tail. Eleven obsolete vote-first golden assertions are retained as explicit skips to document the replaced contract.
- Recommended next step: Review the draft PR and its automatic Vercel preview. Promotion, production registry inclusion, merge, and deployment remain separate decisions.
