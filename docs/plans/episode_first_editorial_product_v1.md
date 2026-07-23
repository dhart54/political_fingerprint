# Milestone Plan: Episode-first editorial product v1

## Intent

- Immediate task: Replace the review-mode vote-first editorial surface with a bounded episode-first hierarchy and a member-neutral shared-evidence contract.
- Hardening extension: Freeze the three reviewed slices as presentation reference fixtures and add deterministic standardization, diagnostics, mutation coverage, and scalable quality-control contracts without promoting or publishing real content.
- Larger-goal alignment: Help readers understand a representative's reviewed behavior quickly while preserving exact legislative receipts and civic-integrity boundaries.

## Outcome

- User-visible or operational result: The three reviewed slices lead with one conclusion, compact coverage, structured findings, featured policy episodes, and a collapsed complete record; shared Justice facts remain reusable across member action overlays.

## Scope And Boundaries

- In scope: Generic editorial view/presentation contracts; episode and policy-family grouping; service-aware statuses; the three reviewed syntheses; Economy episode coverage; member-neutral Justice evidence; bounded review fixtures; tests, rendered review, and documentation.
- Hardening scope: Generic sentence/date/presentation corrections; machine-readable validation reports; source, episode, overlay, synthesis, language, bounded-presentation, and service fail-closed gates; malformed mutation fixtures; a synthetic large-record fixture; generation/escalation/sampling workflow documentation; PR #98 update.
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
- [x] Three real slices carry a non-publication reference-fixture designation and pass deterministic standardization gates.
- [x] All 20 required malformed fixtures fail or warn through stable rule IDs.
- [x] Generated JSON/Markdown validation reports pass drift checking.
- [x] Hardening tests, scans, lint, build, responsive/accessibility review, and PR reconciliation complete.

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
- [x] Hardening implementation
- [x] Hardening validation
- [x] Hardening PR update

## Discoveries

- PR #97 introduced `EditorialIssueExperience`, `editorialIssuePublicPresentation.mjs`, and rich-surface routing but still renders a flat action list plus large coverage/methodology panels.
- The current cross-member adapter copies Foushee's Justice records and replaces only headline/action-result fields, leaving member-specific argument boundaries and caveats in reusable evidence.
- The attached request's expected-main header matches fetched `origin/main`; a later numbered SHA is nonexistent and was treated as a typo. The attachment ends mid-way through section 19, so implementation follows all complete requirements supplied plus repository runbooks.
- PR #98 remained open and draft at the exact expected head `fa851a1f152fbc726b6e45e2b8bbde981018507c`; local and remote branch heads matched before hardening edits.
- The broken Massie result is produced by a generic period splitter in `justiceCrossMemberReviewSlices.mjs`, so the correction belongs in a shared abbreviation-aware sentence helper.
- Existing real partial-service candidates remain unusable as service-status fixtures because stored service metadata is year-only and the relevant seat rows omit oath/succession dates; deterministic service classification must fail closed to Missing.
- The available authoritative House service metadata therefore does not support a reliable real `not yet serving` to recorded-action trajectory for the reviewed Justice episodes. Exact transition behavior remains covered only by the synthetic service-status fixture; real year-only rows are regression-tested to remain `Missing` rather than overclassified.

## Decisions And Rationale

- Interpretation boundary: conclusions remain bounded to the reviewed actions and concrete mechanisms; no motive, ideology, recommendation, or cross-time-change claim will be introduced.
- Preserve the action receipt as the authoritative detailed unit, but render it only inside its episode so repeated stages do not read as independent positions.
- Use upstream service metadata/status fields; React will render, not infer, service eligibility.
- Reference-fixture status remains strictly separate from human approval, gold benchmark, and production eligibility.
- Deterministic validation may prove contract conformance and surface exceptions; it will not be described as proof of political truth, factual perfection, or human verification.

## Deviations Or Corrections

- The requested numbered startup SHA `25baf5b2e9578abfb307b5da871b294c17c5096503e` is not a repository object; the request's stated expected-main SHA and fetched `origin/main` both resolve to `25baf5b2e9578abfb307b5eb52f98b04f57953dc`.

## Validation Results

- Focused overlay hardening: 14 backend tests passed.
- Full editorial backend selection: 56 tests passed.
- `node --test frontend/lib/*.test.mjs`: 126 passed.
- Standardization validator: all three real reference fixtures and the 24-action scalability fixture passed 37 rules; 20 malformed mutations were blocked by their expected stable rule IDs.
- Generated JSON/Markdown standardization artifacts passed deterministic drift checking.
- `npm run lint`: passed with eight pre-existing hook warnings and no errors.
- `npm run build`: passed with the same eight pre-existing hook warnings.
- `npm run test:golden-render`: 11 passed and 12 skipped; 11 skips document superseded flat-card contracts and one is the opt-in screenshot capture.
- In-app browser review covered collapsed desktop views for all three formal slices; expanded Foushee and Massie fentanyl trajectories; the Economy funding episode; a single-action D.C. episode; complete-record and procedural disclosures; the 24-action/two-Congress scalability case; and consistent, selective, and divided mobile variants. No additional visual defect was found.
- Public-language scanning passed, selected-issue duplication remained absent, and the synthetic scalability profile remained isolated from the production registry.

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

- Definition of done satisfied: Yes. The implementation, local validation gates, scoped commits, branch push, and draft-PR reconciliation are complete; remote preview/check completion remains an external post-push signal.
- Remaining limitations: Exact `not yet serving` / `no longer serving` transitions remain synthetic-only because the available real House service rows are year-precision; they now fail closed to `Missing`. Eleven obsolete vote-first golden assertions remain as explicit skips to document the replaced contract.
- Recommended next step: Run one bounded pipeline validation on a newly researched slice in a later milestone. Promotion, production registry inclusion, merge, and deployment remain separate decisions.
