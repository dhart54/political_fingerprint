# Milestone Plan: Golden Profile Read V1

## Intent

- Immediate task: improve profile-level record summary and issue-card preview copy after Golden Public Reads V1.
- Larger-goal alignment: make the flow from profile overview to issue card to expanded issue receipts feel coherent while preserving the PR #65-#68 safety and theme boundary.

## Outcome

- User-visible result: profile summary and issue cards preview the same reviewed-sample directions, counts, and safe policy themes that expanded issue reads use.

## Scope And Boundaries

- In scope: profile summary composition, issue card preview composition, source-level tests, rendered validation where available, and milestone documentation.
- Out of scope: backend/schema/data changes, support/opposition/readiness semantics, new theme mappings, issue overview composition changes unless required for consistency, scoring, ideology labels, recommendations, and LLM-generated copy.
- Files/systems likely touched: `frontend/lib/profileNarrative.mjs`, `frontend/lib/profileNarrative.test.mjs`, `frontend/components/ProfileQuickRead.js`, `frontend/components/PositionByIssue.js`, `frontend/lib/issueOverview.test.mjs`, `docs/plans/`, `docs/review_packets/`.

## Decision Envelope

- Codex may decide and execute: exact bounded profile/card wording, helper shape, tests, and documentation.
- Explicit approval required for: backend/data/schema changes, production writes, changed counting/readiness/support semantics, or weakening raw-copy safety.

## Definition Of Done

- [x] Valerie profile/card/read checkpoint completed before implementation
- [x] Profile summary uses reviewed-sample framing and points to issue cards/receipts
- [x] Issue cards preview dominant/mixed/limited status, counts, safe themes, and receipt path
- [x] PR #65-#68 protections preserved
- [x] Tests/build/validation recorded
- [x] Review packet updated
- [ ] Draft PR opened
- [ ] Final reconciliation completed

## Baseline

- Branch/base commit: `codex/golden-profile-read-v1` from `main` after merged PR #68 (`50412ac78fa83255e7bb874139e9d74892f396e7`).
- Production/deployment state: PR #68 production smoke passed before this milestone.
- Tracked working tree: clean before branch creation.
- Known unrelated untracked artifacts: `docs/review_packets/chamber_filtering_data_integrity_audit.md`, `review_bundle_frontend_data_grounding/`.

## Implementation Sequence

1. Read interpretation principles and recent public-copy/theme/read milestone docs.
2. Produce checkpoint audit for Valerie profile summary, issue cards, expanded reads, and mixed read.
3. Refine profile narrative and issue-card preview helpers.
4. Update tests for profile/card safety, count/status alignment, and mixed preservation.
5. Run requested validation and rendered smoke where available.
6. Update review packet, commit, push, and open a focused draft PR.

## Progress Checklist

- [x] Discovery
- [x] Checkpoint audit
- [x] Implementation
- [x] Validation
- [x] Documentation
- [ ] Commit/PR readiness

## Discoveries

- Profile summary correctly names strongest and mixed reads but leads with party-context methodology and does not point clearly to issue cards/receipts.
- Top profile cards use `for / against` order, while expanded reads use `opposed / supported` for mostly opposed samples.
- Issue-readiness cards show accurate counts/status but do not preview safe policy themes or receipt path.
- Mixed Immigration production read remains mixed and is the right rendered proxy for mixed-card behavior.

## Decisions And Rationale

- Keep expanded issue overview composition from PR #68 unchanged.
- Build profile/card copy from aggregate issue rows and safe domain themes only; do not read raw evidence fields.
- Align card count language with expanded issue direction: opposed/supported for dominant issue previews.
- Keep card theme previews compact and safe, even when they cannot exactly match expanded vote-level group lists.
- Avoid leading the profile summary with party-context methodology; leave party/outcome context in expanded issue reads and receipts.

## Deviations Or Corrections

- None so far.

## Validation Results

- `node --test lib\profileNarrative.test.mjs lib\issueOverview.test.mjs` passed: 26 tests.
- `node --test lib\*.test.mjs` passed: 71 tests.
- `npm run lint` passed with 8 existing React hook dependency warnings.
- `npm run build` passed with the same existing warnings.
- `rg -n "INTERNAL_API_TOKEN|X-Internal-API-Token|/internal/record-across-congresses" .next\static` returned no matches.
- Local built app shell at `http://localhost:3000` rendered.
- Desktop shell: no horizontal overflow; no visible internal token/header/internal-route text.
- Mobile `390x844`: no horizontal overflow; no visible internal token/header/internal-route text.
- Limitation: local ZIP/data path did not load Valerie Foushee for ZIP `27701`; local app showed the sample profile and unavailable quick read. Valerie-specific rendered validation should be repeated on hosted preview/production after deployment.

## Production Writes

- Performed: no
- Scope: none
- Expected effects: none
- Actual effects: none

## Rollback Paths

- Revert the focused branch commit before merge if copy, safety, or validation issues appear.

## Blockers

- None.

## Final Reconciliation

- Definition of done satisfied: pending draft PR creation.
- Remaining limitations: local rendered validation could not load Valerie Foushee data.
- Recommended next step: open a focused draft PR and use hosted preview for Valerie rendered validation.
