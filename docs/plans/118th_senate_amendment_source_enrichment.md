# Milestone Plan: 118th Senate Amendment Source Enrichment

## Intent

- Immediate task: Resolve as many deferred 118th Senate amendment rows as authoritative direct amendment sources safely support, then promote the strongest rows into eligible issue evidence and reviewed interpretations.
- Larger-goal alignment: Make Prior Congress and Full Record views materially more useful for Senate officials while preserving current 119th behavior and civic-integrity semantics.

## Outcome

- User-visible or operational result: More source-grounded 118th Senate amendment evidence and interpretation coverage, with procedural context separated and non-counting where appropriate.

## Scope And Boundaries

- In scope: 118th Congress Senate amendment rows already loaded in production; source packets; deterministic matching/classification; interpretation packages; affected derived outputs; validation and deployment.
- Out of scope: new Congress expansion, broad historical redesign, PN nominations, treaty/executive votes, methodology changes, parent-measure-only amendment meaning, and unsupported comparison claims.
- Files/systems likely touched: `backend/app/classification`, `backend/app/etl`, `backend/app/summaries`, `backend/tests`, `scripts`, `docs`, production classification/interpretation/derived-output tables via bounded writes.

## Decision Envelope

- Codex may decide and execute: authoritative source fetching/caching, matching improvements, deterministic eligibility/classification, package generation, bounded production writes, affected-output recomputation, PR/merge/deployment verification when gates pass.
- Explicit approval required for: new schema or product semantics, destructive/unbounded operations, service/secret/environment changes, ambiguous civic meaning, conflicting authoritative sources, or writes outside the milestone envelope.

## Definition Of Done

- [x] Audit all 588 deferred rows and report exact defer-reason distribution.
- [x] Build authoritative source packets from direct amendment identity and purpose.
- [x] Report top ten opportunity families before production writes, or all ranked families when fewer than ten exist.
- [x] Improve matching and deterministic eligibility/classification where safe.
- [x] Generate source-grounded substantive and procedural interpretation packages.
- [x] Keep procedural/limited-context non-counting and not-voting excluded.
- [x] Create separate rollback coverage for classifications, interpretations, and derived outputs.
- [x] Perform bounded production writes only after preflight gates pass.
- [x] Recompute only affected derived outputs; no derived-output writes were needed for explicit scoped reads.
- [x] Reconcile support/opposition, readiness, alignment, not-voting, cross-Congress leakage, and duplication effects.
- [x] Preserve all 119th IDs, evidence, counts, and public outputs.
- [x] Prove idempotency with zero additional writes on rerun.
- [x] Verify `scope=118`, `scope=119`, and `scope=all` publicly.
- [x] Validate Thom Tillis, Ted Budd, Markwayne Mullin, J. D. Vance, one enriched 118th profile, and one sparse/still-deferred profile.
- [x] Tests/build/validation recorded.
- [x] Review packet or final documentation updated.
- [ ] PR, merge, and deployment verification completed.
- [ ] Final reconciliation completed.

## Baseline

- Branch/base commit: `codex/118th-senate-amendment-source-enrichment` from `173d6d4e201110f66ee3328ebe130d657b1435bb`.
- Production/deployment state, if relevant: canonical frontend `https://political-fingerprint.vercel.app`; canonical backend `https://political-fingerprint.onrender.com`.
- Tracked working tree: pre-existing modifications found in `docs/deployment.md` and `docs/workflows/pr-merge-deployment.md`; milestone also updates rendered-validation runbook.
- Known unrelated untracked artifacts: `docs/review_packets/chamber_filtering_data_integrity_audit.md`; `review_bundle_frontend_data_grounding/`.

## Implementation Sequence

1. Apply operating-model documentation corrections and record this active plan.
2. Discover current production data shape, deferred rows, defer reasons, table boundaries, source tooling, and validation scripts.
3. Build source-packet audit for all 588 deferred 118th Senate amendment rows using Senate roll questions, amendment numbers, purpose text, Congress.gov records, and official text/actions.
4. Rank top ten opportunity families by source strength, reach, issue value, and trust risk; stop any family with ambiguous amendment identity or purpose.
5. Implement safe matching/classification and package-generation improvements with targeted tests.
6. Preflight bounded writes, create rollback artifacts, execute only gated writes, and validate actual effects.
7. Recompute affected derived outputs, prove idempotency, and validate public scopes/profiles.
8. Complete review packet, tests/build/rendered validation, PR, merge, and deployment verification.

## Progress Checklist

- [x] Read applicable `AGENTS.md` and required runbooks.
- [x] Create milestone branch.
- [x] Apply initial operating-model documentation corrections.
- [x] Create active plan.
- [x] Discovery.
- [x] Source packet audit and opportunity ranking.
- [x] Implementation.
- [x] Bounded production preflight/write/validation.
- [x] Tests/build/rendered validation.
- [x] Documentation/review packet.
- [ ] Commit/PR/merge/deployment readiness.

## Discoveries

- The repository was already at requested commit `173d6d4e201110f66ee3328ebe130d657b1435bb`.
- Local tracked docs edits existed before branch creation; they match part of the requested operating-model correction and must be preserved.
- Several `.pytest_tmp_*` directories emit permission warnings during broad status scans; these are local-tool artifacts, not product failures.
- The 588 deferred amendment bucket is the full 118th amendment roll-call bucket: 406 House session 1, 160 House session 2, 7 Senate session 1, and 15 Senate session 2. The loaded 118th Senate amendment subset is 22 roll calls.
- Congress.gov direct amendment records supplied usable purpose for 10 of 22 loaded Senate amendment rows. Seven were safe to promote; three still lacked safe issue-domain grounding.

## Decisions And Rationale

- Keep the URL and hosted-preview documentation corrections in this milestone branch, per user instruction not to create a separate PR.
- Keep rows deferred when the source packet has generic/missing purpose or direct purpose without safe issue-domain mapping.
- Do not write derived-output tables for this package; explicit scoped public reads reflect the updated rows directly, and broad rolling precompute retention would risk changing 119th public outputs.

## Deviations Or Corrections

- Codex initially stopped after branch creation; work resumed and this plan records the correction.

## Validation Results

- Source-packet dry-run: 7 target rows, 4 substantive, 3 procedural context, 15 deferred, 0 errors.
- Production post-validation: 7 eligible target rows, 4 interpreted rows, 3 procedural non-counting rows, 0 non-target rows, 0 not-voting counted as support/opposition.
- Idempotency rerun: 0 classification updates and 0 interpretation updates.
- Local profile validation covered Thom Tillis, Ted Budd, Markwayne Mullin, J. D. Vance, Blumenauer, and Adelita S. Grijalva across `scope=118`, `scope=119`, and `scope=all`.
- Public backend validation: health 200, coverage metadata database source, Thom Tillis National Security evidence isolated by `scope=118`, `scope=119`, and `scope=all`.
- Public frontend validation: canonical Vercel URL returned 200 and rendered the app shell.
- Tests: 13 targeted amendment/118th tests passed; 33 API scope tests passed; 40 frontend unit tests passed; frontend build passed.

## Production Writes

- Performed: yes.
- Scope: 7 source-packet-approved 118th Senate amendment roll_call_ids: 2454, 2456, 2457, 2459, 3047, 3055, 3056.
- Expected effects: 7 classification updates and 7 interpretation updates; 4 substantive interpreted rows with support/oppose positions; 3 procedural-context rows with null support/oppose; no fact-table writes.
- Actual effects: matched expected.

## Rollback Paths

- Classifications: `docs/review_packets/senate_118_amendment_classification_rollback.sql`.
- Interpretations: `docs/review_packets/senate_118_amendment_interpretation_rollback.sql`.
- Derived outputs: `docs/review_packets/senate_118_amendment_derived_outputs_rollback.sql` records the no-op derived-output path.

## Blockers

- None yet.

## Final Reconciliation

- Definition of done satisfied: no.
- Remaining limitations: 15 loaded 118th Senate amendment rows remain deferred, and the broader 566 House amendment rows remain outside this Senate-focused package. Evidence is improved but still too thin for broad continuity/change claims.
- Recommended next step: commit and open PR after final diff review; merge/deployment verification remains pending.
