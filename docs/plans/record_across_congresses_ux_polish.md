# Milestone Plan: Record Across Congresses UX Polish

## Intent

- Immediate task: run a focused UX/readability polish pass for the merged `Record Across Congresses` panel and family roll-call drilldown.
- Larger-goal alignment: make the cross-Congress evidence panel easier to discover and inspect while preserving the evidence-only civic boundary.

## Outcome

- User-visible or operational result: a small frontend polish PR with clearer hierarchy, mobile readability, accessible disclosure/drilldown states, validation results, and a review packet.

## Scope And Boundaries

- In scope: placement review, collapsed panel discoverability, summary/count label clarity, family and drilldown hierarchy, mobile wrapping, accessibility basics, approved guardrail copy, documentation.
- Out of scope: backend routes, ingestion, schema, methodology, comparison/continuity analysis, token/config changes, production writes, broad redesign, dependency upgrades unless validation requires them.
- Files/systems likely touched: `frontend/components/RecordAcrossCongressesPanel.js`, `frontend/lib/recordAcrossCongresses.mjs`, targeted frontend tests, `docs/review_packets/`.

## Decision Envelope

- Codex may decide and execute: conservative UI/copy polish that does not change evidence semantics or product interpretation.
- Explicit approval required for: production writes, token/config changes, schema changes, methodology changes, new evidence semantics, or copy implying continuity/change/movement.

## Definition Of Done

- [x] Read-only UX audit completed and documented.
- [x] Scoped UX/readability changes implemented.
- [x] Targeted tests updated if copy/UI behavior changes.
- [x] Required lint/build/tests/static scan recorded.
- [x] Rendered validation completed for desktop and mobile states.
- [x] Review packet updated.
- [x] Final reconciliation completed and PR opened for review.

## Baseline

- Branch/base commit: `codex/record-across-congresses-ux-polish` from `main` at `1f92d97c4a5ab2311da8be9d4dfd7a7679f29fd2`.
- Production/deployment state, if relevant: milestone says backend route, frontend proxy, production Vercel env vars, production rendering, family drilldown, lint gate, and static scans are already working on merged `main`.
- Tracked working tree: clean at start.
- Known unrelated untracked artifacts: `docs/review_packets/chamber_filtering_data_integrity_audit.md`, `review_bundle_frontend_data_grounding/`.

## Implementation Sequence

1. Complete read-only UX and copy-boundary audit.
2. Make the smallest safe UI/copy/accessibility changes.
3. Update targeted tests.
4. Run required local validation and static scan.
5. Perform rendered desktop/mobile validation.
6. Write review packet, reconcile files, commit, push, and open PR.

## Progress Checklist

- [x] Discovery started
- [x] Discovery complete
- [x] Implementation
- [x] Validation
- [x] Documentation
- [x] Commit/PR readiness

## Discoveries

- The panel currently renders after `PositionByIssue` (`strongest issue evidence`) and before the tools/preferences/comparison disclosure.
- The current collapsed state is a subtle uppercase `summary` row titled only `Record Across Congresses`.
- Existing nearby legacy language outside the panel includes `Change`, `changed`, `steady`, `consistent`, and comparison statuses in `ProfileQuickRead`, `DriftIndicator`, `profileNarrative`, and issue summary helpers.
- Production baseline at `https://political-fingerprint.vercel.app` confirmed the collapsed panel was a short row after strongest issue evidence; no horizontal overflow or sensitive token/internal-route text was visible.
- Local fixture-mode rendered validation cannot exercise the panel because the internal family route uses the database-backed helper and fails with the intentionally invalid fixture DSN.
- PR #56 Vercel preview deployed successfully but redirected this browser session to Vercel login, so hosted preview inspection is access-limited.
- Changed UI rendered validation was completed locally against a deterministic mock API with production-shaped family data for desktop and mobile collapsed/expanded/drawer states.
- PR #56 is open and marked ready for review.

## Decisions And Rationale

- Keep placement after strongest issue evidence for now: it avoids making the panel the primary profile interpretation and keeps it near inspectable evidence.
- Treat nearby legacy change/steady/consistent wording as documentation-only unless directly part of this panel.

## Deviations Or Corrections

- None yet.

## Validation Results

- `node --test lib\recordAcrossCongresses.test.mjs`: passed, 15 tests.
- `npm run lint`: passed with 8 existing React hook dependency warnings outside scope.
- `npm run build`: passed with the same existing hook warnings.
- `node --test lib\*.test.mjs`: passed, 55 tests; existing module-type warnings emitted.
- Static scan of `.next\static` for `INTERNAL_API_TOKEN`, `X-Internal-API-Token`, and `/internal/record-across-congresses`: no matches.
- Production baseline rendered audit completed at desktop `1366x900`.
- Changed UI local rendered validation completed for desktop `1366x900`, mobile `390x844`, collapsed state, expanded state, direct drawer, and caveated drawer.
- PR #56 Vercel status is ready/success; direct hosted preview inspection is blocked by Vercel login in this browser session.

## Production Writes

- Performed: no
- Scope: none
- Expected effects: none
- Actual effects: none

## Rollback Paths

- Revert the frontend component/copy/test/doc changes from this branch.

## Blockers

- None currently.

## Final Reconciliation

- Definition of done satisfied: yes, with hosted preview access limitation documented.
- Remaining limitations: local fixture mode cannot render the DB-backed panel; Vercel preview redirects to login from this browser session.
- Recommended next step: reviewer with Vercel preview access should spot-check Aaron Bean and Aumua Amata Coleman Radewagen; run a separate copy-boundary milestone for legacy change/steady/consistent language.
