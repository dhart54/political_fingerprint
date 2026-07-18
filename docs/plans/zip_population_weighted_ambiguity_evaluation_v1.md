# Milestone Plan: ZIP Population-Weighted Ambiguity Evaluation V1

## Intent

- Immediate task: determine whether official block-level 2020 population materially improves ZCTA-to-CD119 presentation ranking over land area.
- Larger-goal alignment: improve ambiguity explanations while preserving the boundary between population-ranked presentation and address-resolved representation.

## Outcome

- User-visible or operational result: a reproducible Census-only source batch and exact population analysis, or a source-feasibility packet if exact compatible assignment cannot be proved; no production/runtime changes.

## Scope And Boundaries

- In scope: official Census source discovery/retrieval/replay, compatibility proof, exact block aggregation if supported, read-only House reconciliation, policy sensitivity, staging design, tests, draft PR.
- Out of scope: production writes, migrations, ZIP seeds, route/frontend/flag changes, address collection/provider integration, representative auto-selection, merge.
- Files/systems likely touched: two backend scripts, focused tests, plan/review/design/source-manifest documents, ignored local source batch, and optional unapplied `0016` only if the evidence contract is stable.

## Decision Envelope

- Codex may decide and execute: Census-only source selection, bounded official retrieval, exact deterministic parsing/aggregation, fail-closed feasibility findings, additive schema recommendation.
- Explicit approval required for: any production mutation, migration application, runtime behavior, threshold adoption, third-party data, address provider, auto-selection, or merge.

## Definition Of Done

- [x] PR #89 baseline and migration hash verified unchanged.
- [x] Official source inventory and replay contract completed.
- [x] Exact block-vintage/join compatibility proved.
- [x] Population analysis and policy comparison completed after all hard gates passed.
- [x] Production read-only pre/postchecks completed without mutation.
- [x] Focused and combined validation recorded; JSON and diff checks pass.
- [x] Documentation and final reconciliation completed.
- [ ] Intended files committed/pushed and a draft PR opened against `main`.

## Baseline

- Branch/base commit: requested branch from `main` at `3d3222e382f36f8e13796b4053340b1e2db64795`.
- Production state: House snapshot `house-119-20260713T011722Z`; `zip_district_mappings` must remain empty; `0015` and any `0016` tables must remain absent.
- Tracked working tree: clean at discovery.
- Known unrelated untracked artifacts: `docs/review_packets/chamber_filtering_data_integrity_audit.md`; `review_bundle_frontend_data_grounding/`; inaccessible ignored pytest temp directories reported by Git.

## Implementation Sequence

1. Verify merged land-analysis pins and inspect reusable source/production safety helpers.
2. Inventory only official Census sources and prove or reject common-block compatibility.
3. Implement mutually exclusive retrieval/replay with manifest and official-host/inventory gates.
4. Implement pure population normalization, integrity, exact ranking/policy analysis, and tests if feasibility gates pass.
5. Retrieve/replay the official batch and run the full exact analysis, or emit a bounded feasibility packet at the hard stop.
6. Run production read-only pre/postchecks, combined tests, JSON validation, and diff checks.
7. Finalize staging decision, commit/push the intended scope, and open a draft PR without merging.

## Progress Checklist

- [x] Discovery
- [x] Retrieval/replay
- [x] Compatibility proof
- [x] Analysis or feasibility stop
- [x] Validation
- [x] Documentation
- [ ] Commit/PR readiness

## Discoveries

- Official Method A is feasible: 2020 PL 94-171 block population, the 2020 ZCTA/tabulation-block relationship, and the CD119 whole-block equivalency file join through the same 15-digit 2020 block GEOID.
- The official relationship files are complete but not uniformly sorted within state. Deterministic bounded external sorting is required before streaming joins; duplicate counts are zero.
- The Census Bureau documents one legally split Colorado block, `080010096072000`; it contains 90 people and has an authoritative whole-block tabulation assignment to CD08.
- The 50-state/DC PL population reconciles to 331,449,281. ZCTA-assigned population is 331,440,751; 8,530 people are in 144,187 official blocks without a ZCTA. The 89 unassigned-district blocks contain zero people.
- All 39,967 accepted PR #89 relationships are preserved. There are 589 zero-population relationships, including 552 positive-land and all 37 water-only relationships.
- Population and land top rankings differ for 627 ZCTAs. Among 5,862 ambiguous ZCTAs, 5,836 have a top population share at or above 50%; this is presentation evidence only.

## Decisions And Rationale

- Population allocation is not address resolution; production auto-select eligibility remains fixed at zero.
- Only exact supported block assignment classes may enter primary findings; spatial apportionment cannot drive recommendations.
- Do not create `0016` in this milestone. If later authorized, prefer aggregate source-backed evidence with a reproducible ignored block ledger over a production full-block ledger.

## Deviations Or Corrections

- The first local checker transcribed the PR #89 normalized artifact checksum incorrectly; the artifact itself reproduced the committed checksum and the checker was corrected before analysis continued.
- Initial streaming logic assumed within-state source ordering. Both official relationship files showed bounded order regressions, so the implementation now externally sorts and duplicate-checks state partitions before joining.
- The complete normalized block ledger was added after the first successful aggregate pass so every used block preserves required lineage; the authoritative report was regenerated afterward.

## Validation Results

- Official source retrieval: 56 artifacts, about 2.23 GB; manifest replay verified exact inventory, host, size, checksum, vintage, and documentation.
- Focused suite: 31 passed.
- Exact common-block analysis: 8,132,968 blocks; 331,449,281 source population; 39,967 aggregate relationship rows.
- Production pre/post: session and transaction read-only confirmed; 30-second statement timeout; House canonical checksums and legislators fingerprint unchanged; ZIP row count remained zero.
- JSON parsing, Python compilation, `git diff --check`, and the 161-test combined House/ZIP/route/parity/land/population suite passed.

## Production Writes

- Performed: no
- Scope: verified read-only pre/postchecks only.
- Expected effects: none.
- Actual effects: none; read-only pre/post state matched.

## Rollback Paths

- No production rollback is required because no production or migration write is authorized. Raw/derived local batches are ignored and reproducible from the pinned manifest.

## Blockers

- None. No hard stop was triggered.

## Final Reconciliation

- Definition of done satisfied: pending commit/push and draft PR publication only.
- Remaining limitations: population is from 2020, does not resolve a current address, and no production threshold or schema application is authorized.
- Recommended next step: likely full-address congressional-district resolver evaluation after independent review.
