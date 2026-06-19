# Milestone Plan: 118th Congress Historical Expansion

## Intent

- Immediate task: add safely modeled House and Senate facts, evidence, classifications, interpretations, and derived outputs for the 118th Congress alongside existing 119th Congress data.
- Larger-goal alignment: make profiles show a richer multi-Congress voting record and establish the first repeatable historical-Congress load path for later change-over-time product work.

## Outcome

- User-visible or operational result: public profiles can show 118th and 119th Congress voting evidence without obscuring Congress/session/chamber distinctions or changing existing 119th records.

## Scope And Boundaries

- In scope: 118th Congress only, 2023-2024; House and Senate roll calls; official-source audit; cache/fetch support; bounded production writes; deterministic classifications and source-grounded interpretations where existing rules safely apply; derived-output recompute; idempotency and public validation.
- Out of scope: 117th Congress; new support/opposition, readiness, alignment, or interpretation semantics; combining votes across Congresses in a way that hides time; PN nomination and treaty/executive semantics unless already representable.
- Files/systems likely touched: `backend/app/etl`, `backend/app/classification`, `backend/tests`, `scripts`, `docs/plans`, `docs/review_packets`, possibly frontend/backend read paths only if current UI/API cannot safely surface multi-Congress evidence.

## Decision Envelope

- Codex may decide and execute: bounded fact, classification, interpretation, and derived-output writes after runbook gates pass; orchestration or source-adapter support required for repeatable historical-Congress loads.
- Explicit approval required for: new schema or product-semantics decisions, destructive/unbounded operations, ambiguous civic meaning, unresolved Congress/session identity issues, service/secret/environment changes, or material preflight divergence.

## Definition Of Done

- [ ] Official-source coverage audited for the full 118th Congress.
- [ ] Supported 2023-2024 House and Senate roll calls fetched and cached.
- [ ] Congress, session, chamber, amendment, final-passage, procedural, nomination, treaty, and not-voting distinctions preserved.
- [ ] Eligible facts imported with the established session-aware identity model.
- [ ] Deterministic classifications and source-grounded interpretations generated only where existing rules safely support them.
- [ ] Unsupported vote families explicitly deferred.
- [ ] Derived outputs recomputed.
- [ ] Import and precompute idempotency proven.
- [ ] Existing 119th-Congress IDs, counts, evidence, and public profiles proven unchanged.
- [ ] Representative House and Senate public profiles validated with both Congresses present, including Valerie Foushee, Thom Tillis, Ted Budd, an official in both 118th and 119th Congresses, an official in only one Congress, and one sparse profile.
- [ ] Historical-window behavior documented, including recommendation on current-Congress default, rolling window, or explicit Congress selector.
- [ ] Tests, rollback artifacts, review packet, PR, merge, and deployment verification completed.

## Baseline

- Branch/base commit: `codex/118th-congress-expansion` from `main` at `241921b`.
- Production/deployment state, if relevant: to be captured during production read-only discovery before any write.
- Tracked working tree: not clean at branch creation due to pre-existing edits in `docs/deployment.md` and `docs/monitoring.md`; these are unrelated deployment/monitoring notes and must stay out of the milestone diff unless intentionally adopted.
- Known unrelated untracked artifacts: `docs/review_packets/chamber_filtering_data_integrity_audit.md`, `review_bundle_frontend_data_grounding/`, plus permission-blocked pytest temp directories reported by Git status.

## Implementation Sequence

1. Discover current ETL, classification, interpretation, identity, precompute, rollback, and deployment paths.
2. Audit official-source coverage and existing cache shape for 118th House and Senate by session/year.
3. Implement or extend repeatable historical-Congress fetch/cache/preflight orchestration with strict session-aware roll-call identity.
4. Dry-run fact import, classification, interpretation, and derived-output recompute with predicted table effects and deferred categories.
5. Create rollback artifacts, execute bounded authorized production writes only after gates pass, and validate actual versus expected effects.
6. Prove idempotency and 119th invariance.
7. Run targeted tests/builds and production-backed/rendered profile validation.
8. Document results in a review packet, update active plan, prepare intended commit/PR, merge, and verify deployment.

## Progress Checklist

- [x] Start instructions and runbooks read
- [x] Milestone branch created
- [x] Active plan created
- [x] Discovery
- [x] Source coverage audit
- [x] Implementation
- [x] Bounded dry-runs and rollback
- [x] Production writes
- [x] Validation
- [x] Documentation
- [ ] Commit/PR/merge/deployment readiness

## Discoveries

- Current branch creation started from the current `main` tip, but the worktree already contained unrelated tracked and untracked changes.
- The database uniqueness model is already session-aware, but House and Senate adapter-local roll-call IDs were not Congress/session-aware and House parsed source URLs assumed 119th Congress years. This would be unsafe for a multi-session historical load without adapter fixes.
- Historical source dirs need to tolerate missing local fixture-style `bills.json` and ZIP maps; official Congress.gov cache can enrich bill context when present.

## Decisions And Rationale

- Preserve pre-existing dirty files and untracked artifacts instead of reverting or folding them into this milestone.
- Add a separate `historical_congress_refresh` entry point with its own 118th approval phrase instead of changing the established current-Congress refresh gate.
- Keep unsupported PN nomination and treaty/executive families deferred unless existing deterministic semantics can represent them.

## Deviations Or Corrections

- User requested clean `main`; local `main` was already dirty. Proceeding on a milestone branch while isolating unrelated work unless overlap or a hard gate requires stopping.

## Validation Results

- Targeted backend tests passed: `pytest --basetemp=..\.local\pytest_basetemp tests\test_congress_adapter.py tests\test_current_congress_refresh.py tests\test_historical_congress_refresh.py` (16 passed). First sandboxed run hit the known pytest temp cleanup permission issue; rerun with approved elevated execution passed.
- Expanded targeted backend tests passed after the vote-type correction: `pytest --basetemp=..\.local\pytest_basetemp tests\test_congress_adapter.py tests\test_current_congress_refresh.py tests\test_historical_congress_refresh.py tests\test_vote_context.py` (19 passed).
- Official source coverage is complete against cached official files: House 2023 724/724, House 2024 517/517, Senate 118-1 352/352, Senate 118-2 339/339.
- Post-write import dry-run is idempotent with zero planned fact, vote, context, classification, interpretation, bill, or legislator inserts.
- Post-write precompute write is idempotent for `window_end=2026-06-19`, `classification_version=v1`.
- Production facts now include 118th rows by chamber/session: House session 1 694 roll calls / 303,034 votes, House session 2 514 / 222,403, Senate session 1 61 / 6,098, Senate session 2 84 / 8,400.
- Existing 119th row counts matched the captured prewrite baseline after the write: House session 1 339 / 146,772, House session 2 216 / 93,125, Senate session 1 285 / 28,492, Senate session 2 66 / 6,600; 119 classifications remained 757 and 119 vote/evidence context rows remained 274,989.
- Public API profile routes return 200 for Valerie P. Foushee, Thom Tillis, and Ted Budd, but the existing profile evidence surface still exposes only eligible votes in the latest rolling 730-day window. The safely eligible 118th classifications are all in 2023, outside the current `2024-06-20` to `2026-06-19` public window.
- Follow-up scoped profile implementation added default `Full record` behavior plus `Recent Congress` and `Prior Congress` controls.
- Scoped API responses support `scope=all`, `scope=119`, and `scope=118` for fingerprint, positions, position evidence, and alignment paths. Response metadata includes selected scope, requested Congresses, date coverage, and Congress coverage.
- Valerie P. Foushee validation: `scope=all` returns 124 eligible rows with evidence attributed to 118th (3) and 119th (121); `scope=119` returns 121 119th-only rows; `scope=118` returns 3 118th-only rows.
- Thom Tillis validation: `scope=all` and `scope=119` return 73 eligible 119th-only rows; `scope=118` returns a zero-evidence empty prior-period treatment.
- Ted Budd validation: `scope=all` and `scope=119` return 73 eligible 119th-only rows; `scope=118` returns a zero-evidence empty prior-period treatment.
- One-Congress validation: `leg_blumenauer` returns 3 eligible 118th rows and an empty 119th scope.
- Sparse validation: `leg_vance_r_oh` returns zero eligible rows across all tested scopes.
- No tested profile has enough reviewed evidence in both Congresses for a confident continuity/change statement. The 118th load has only two interpreted eligible votes overall, so the comparison layer correctly reports insufficient evidence or one-Congress-only evidence.
- Rendered validation passed locally against the production-backed API: desktop scope switching had no horizontal overflow; mobile 390px rendered the compact scope control and profile summary with no horizontal overflow after a responsive grid fix.
- Scoped profile tests passed: `pytest --basetemp=..\.local\pytest_basetemp tests\test_api_positions.py tests\test_api_fingerprint.py tests\test_api_alignment.py tests\test_db_read_layer.py` (39 passed).
- Frontend tests/build passed: `node --test frontend\lib\profileNarrative.test.mjs frontend\lib\issueReadiness.test.mjs frontend\lib\positionEvidenceCounts.test.mjs` (12 passed), `npm run build` (compiled successfully).

## Production Writes

- Performed: yes.
- Scope: 118th Congress fact/classification/interpretation rows, then derived-output rows for `window_end=2026-06-19`, `classification_version=v1`.
- Expected effects: 531 bills, 85 legislators, 1,353 roll calls, 539,935 votes_cast, 539,935 vote_contexts, 1,353 vote_classifications, 1,353 vote_interpretations; derived rows of 5,096 fingerprints, 48 chamber medians, 637 drift scores, and 637 summaries.
- Actual effects: matched expected. A bounded follow-up correction updated 430 House 118 session 2 roll 110 vote_context rows from `nomination` to `motion` after the title-only phrase "Confirmation Act" exposed a false nomination inference.

## Rollback Paths

- Fact rollback: `docs/review_packets/118th_congress_historical_expansion_rollback.sql`.
- Derived-output rollback: `docs/review_packets/118th_congress_historical_expansion_precompute_rollback.sql`.
- Prewrite baseline: `docs/review_packets/118th_congress_historical_expansion_prewrite_baseline.json`.

## Blockers

- No true blocker remains for product behavior. Methodology limitation: current deterministic 118th interpretation coverage is too thin to produce confident continuity/change statements, so the UI must continue to show insufficient-comparison language until more reviewed 118th evidence exists.

## Final Reconciliation

- Definition of done satisfied: no
- Remaining limitations: commit/PR/merge/deployment verification remain outstanding.
- Recommended next step: prepare a scoped commit excluding pre-existing unrelated docs/monitoring/deployment changes, open PR, run checks, merge, and verify deployment.
