# Milestone Plan: Top Summary Drift Cleanup

## Intent

- Immediate task: Remove low-value drift/change language from the top profile summary and replace it with direct, bounded, evidence-backed interpretation.
- Larger-goal alignment: Make Political Fingerprint's highest-visibility profile summary read like a plain-English voting-record interpreter with receipts.

## Outcome

- User-visible result: The top profile summary no longer surfaces `Change`, `Steady mix`, or unsupported cross-time movement language, and instead highlights the strongest reviewed evidence, reviewed vote coverage, and where to inspect first.

## Scope And Boundaries

- In scope: Top profile summary card, drift/change indicator removal, top summary metric labels, profile summary/narrative strings directly feeding the top card, targeted tests, rendered validation, and review packet.
- Out of scope: Backend changes unless absolutely required, schema/data/model/methodology changes, Record Across Congresses methodology changes, token/config changes, production writes, broad redesign.
- Interpretation source: `docs/interpretation_principles.md` has been read and controls copy boundaries for this milestone.

## Decision Envelope

- Codex may decide and execute: Frontend copy/label changes within the top summary, removal of unused drift display from the top card, targeted tests, rendered validation, and review packet documentation.
- Explicit approval required for: New product semantics, backend/data/schema changes, Record Across methodology changes, production writes, or replacement copy that would overstate evidence.

## Definition Of Done

- [x] Frontend drift/change terms audited and classified.
- [x] High-risk top-summary drift/change copy removed or replaced.
- [x] Targeted tests updated or added.
- [x] Required lint/build/node/static scan validation completed.
- [x] Rendered validation completed for Valerie Foushee desktop/mobile and Aaron Bean if practical.
- [x] Review packet created.
- [x] Focused PR opened and ready for review.

## Baseline

- Branch/base commit: `main` at `95a199e67367cedf1c1c777472ec70dcf8d8fb8e`.
- Production writes: none authorized or planned.
- Known unrelated untracked artifacts: `docs/review_packets/chamber_filtering_data_integrity_audit.md`, `review_bundle_frontend_data_grounding/`.

## Implementation Sequence

1. Audit frontend terms: `Change`, `Drift`, `Steady`, `consistent`, `differs`, `shift`, `shifted`, `trend`, `movement`, `stronger`, `weaker`.
2. Identify top-summary source components/helpers and tests.
3. Replace/remove high-risk drift/change copy in the top summary only.
4. Update targeted tests for revised top-summary copy and absence of movement language.
5. Run required validations and rendered checks.
6. Create review packet and reconcile plan.
7. Commit, push, and open PR.

## Progress Checklist

- [x] Start/read instructions
- [x] Active plan creation
- [x] Discovery/audit
- [x] Implementation
- [x] Validation
- [x] Documentation
- [x] Commit/PR readiness

## Discoveries

- High-risk visible top-summary drift/change language was concentrated in `frontend/components/ProfileQuickRead.js` and `frontend/lib/profileNarrative.mjs`.
- `ProfileQuickRead` fetched the drift endpoint solely for the top summary metric and label, so removing that fetch did not require backend or schema changes.
- `frontend/components/DriftIndicator.js` contains legacy drift/change copy but is not mounted in the current app path; it is documented as out of scope.
- Record Across Congresses and issue-evidence uses of audited terms are guarded or policy-mechanism language and were left unchanged.

## Decisions And Rationale

- Replace the top metric `Change` with `Record read`, and add `Strongest evidence` as the first metric so the top card answers where to inspect first.
- Use `strongest reviewed evidence is in...` for the headline to align with `docs/interpretation_principles.md`.
- Replace cross-Congress movement statements with the bounded message that reviewed votes are available in both Congresses and Congress-specific counts are shown separately below.
- Keep internal comparison status names because they are mapped to safe public copy and changing them would widen the milestone.

## Deviations Or Corrections

- Aaron Bean ready-state rendered validation was not practical in the local UI path because the ZIP lookup quickly selected Valerie Foushee and the switcher was not exposed in the local rendered DOM. The Aaron loading top card and shared code path were checked, and this limitation is recorded in the review packet.

## Validation Results

- `cd frontend; npm run lint`: passed with 8 existing React hook dependency warnings.
- `cd frontend; npm run build`: passed with the same existing warnings and preserved `/api/record-across-congresses/house/[legislatorId]`.
- `cd frontend; node --test lib\*.test.mjs`: passed, 55 tests.
- `cd frontend; rg -n "INTERNAL_API_TOKEN|X-Internal-API-Token|/internal/record-across-congresses" .next\static`: no matches; no-match exit treated as success.
- Focused tests `node --test lib\profileNarrative.test.mjs lib\profileMvpProfile.test.mjs`: passed, 13 tests.
- Rendered validation: Valerie Foushee desktop and 390x844 mobile passed for top-summary drift removal, stronger evidence-backed summary, issue evidence rendering, Record Across rendering, no horizontal overflow, and no token/header/internal-route text.
- Rendered validation limitation: Aaron Bean ready-state issue summary was not practical locally; the initial Aaron loading top card used the new metric labels and no drift/change terms.

## Production Writes

- Performed: no
- Scope: none
- Expected effects: none
- Actual effects: none

## Rollback Paths

- Revert the focused frontend copy/test/doc commit.

## Blockers

- None currently.

## Final Reconciliation

- Definition of done satisfied. The focused implementation avoids backend/data/schema/methodology changes, keeps Record Across intact, documents the remaining Aaron local-rendering limitation, and PR #60 is open for review.
