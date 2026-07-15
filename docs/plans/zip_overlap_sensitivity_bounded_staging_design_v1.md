# Milestone Plan: ZIP Overlap Sensitivity and Bounded Mapping-Stage Design V1

## Intent

- Immediate task: quantify land, water-only, and positive-land-sliver effects on ZCTA-to-House-district ambiguity and design a provenance-complete staging contract.
- Larger-goal alignment: improve ZIP-based representative discovery without claiming address-level certainty or enabling unsafe automatic selection.

## Outcome

- User-visible or operational result: a reproducible read-only analysis, review packet, source manifest, and bounded staging design; no public lookup or production data behavior changes.

## Scope And Boundaries

- In scope: pinned Census relationship parsing, exact area calculations, sensitivity policies, immutable House snapshot reconciliation, schema inspection, focused tests, documentation, draft PR.
- Out of scope: production writes, source refresh, migration application, route/flag/frontend changes, population/address integration, auto-selection, merge.
- Files/systems likely touched: `backend/scripts`, `backend/tests`, `docs/plans`, `docs/review_packets`, `docs/design`, `docs/source_manifests`, and optionally an unapplied additive migration.

## Decision Envelope

- Codex may decide and execute: pure analysis details, exact deterministic representations, bounded read-only queries, evidence-backed staging contract, candidate additive migration if stable.
- Explicit approval required for: any production mutation, runtime behavior change, threshold adoption, source replacement, migration application, or merge.

## Definition Of Done

- [x] Pinned official input identity and source baselines verified.
- [x] Exact parser, integrity analysis, policy evaluation, and seat reconciliation implemented and tested.
- [x] Verified full analysis and production read-only pre/postchecks completed without mutation.
- [x] Review packet, source manifest, staging design, and candidate migration decision completed.
- [x] Tests/build/validation recorded.
- [x] Review packet or final documentation updated.
- [x] Final reconciliation completed.
- [ ] Intended files committed, pushed, and opened as a draft PR against `main`.

## Baseline

- Branch/base commit: requested branch from `main` at `498c7c1891011fce45cfa8d273946934041b29f0`.
- Production/deployment state, if relevant: must be verified read-only against snapshot `house-119-20260713T011722Z`; `zip_district_mappings` must remain empty.
- Tracked working tree: clean at discovery.
- Known unrelated untracked artifacts: `docs/review_packets/chamber_filtering_data_integrity_audit.md`; `review_bundle_frontend_data_grounding/`; inaccessible ignored pytest temp directories reported by Git.

## Implementation Sequence

1. Verify repository/source pins and inspect reusable parser, database target verifier, schema, routes, and tests.
2. Implement pure parsing, exact integrity/policy analysis, reconciliation, report generation, and safety gates.
3. Add deterministic fixture/fake-connection tests and run focused validation.
4. Run the pinned full-file analysis with bounded production read-only checks; validate artifacts and checksums.
5. Finalize staging design and migration decision, reconcile documentation, run combined tests and diff checks.
6. Commit intended files, push requested branch, and open a draft PR without merging.

## Progress Checklist

- [x] Discovery
- [x] Implementation
- [x] Validation
- [x] Documentation
- [x] Commit/PR readiness

## Discoveries

- The requested `main` commit matches local `main` at milestone start.
- The tracked tree is clean; two unrelated untracked artifacts are explicitly excluded.
- The pinned source has 39,967 accepted relationships and 430 existing-parser rejections across 33,642 ZCTAs; all expected baselines and territory counts match.
- All accepted land partitions reconcile exactly. Thirty-one water/total shortfalls total 66,153,060 square meters and equal rejected state-`ZZ` non-district water rows exactly.
- There are 37 water-only relationships across 37 ZCTAs, 32 positive-land relationships below 0.01%, and no accepted zero-area rows.
- Ambiguity is 5,862 ZCTAs under any/positive-total overlap, 5,829 under positive-land overlap, 1,925 at the inclusive 25% sensitivity point, and zero at 50%; the 50% policy leaves 42 ZCTAs without a mapping.
- The immutable House snapshot matches all six approved canonical checksums. Source pairs reconcile to 431 filled voting seats, four official vacancies, and the DC candidate-normalization pair.

## Decisions And Rationale

- Interpretation boundary: area evidence will be described only as geographic overlap evidence, not population, address, motive, preference, or definitive representation evidence.
- All policy threshold decisions will use integer/rational comparisons rather than binary floating point.
- Area evidence supports preserving possible mappings and an explicitly caveated/versioned presentation rank. It does not support automatic representative selection.
- The next accuracy step should use both block-level population allocation and full-address district lookup: the first evaluates ZIP-level ranking quality; the second is necessary for address-level automatic selection.
- The existing runtime candidate table is insufficient as the evidence ledger. Candidate migration `0015` adds separate immutable snapshot/artifact/relationship tables and versioned policy evaluations and remains unapplied.

## Deviations Or Corrections

- Local pytest temp-root permissions required explicit repository-local `--basetemp` paths; this was a local tooling condition, not a product/test failure.

## Validation Results

- Focused overlap suite: 25 passed.
- Combined current-House, ZIP-readiness, route/parity, and overlap suite: 141 passed.
- Full official-file analysis: passed with exact identity and baseline gates.
- Production read-only pre/postchecks: passed; session and transaction read-only confirmed with 30-second statement timeout; protected checksums and legislators fingerprint unchanged; ZIP production rows remained zero.
- JSON validation: review packet and source manifest passed `json.tool`.
- `git diff --check`: passed.

## Production Writes

- Performed: no
- Scope: production access is read-only analysis/postcheck only.
- Expected effects: none.
- Actual effects: none; protected production fingerprints and counts were identical before and after analysis.

## Rollback Paths

- No production rollback is needed because no production/database/runtime writes are authorized; local branch changes can be reviewed independently and the candidate migration, if created, remains unapplied.

## Blockers

- GitHub CLI keyring token reports invalid, but the connected GitHub app is available for draft PR creation after the normal local Git push.

## Final Reconciliation

- Definition of done satisfied: implementation, analysis, production-safety verification, tests, documentation, and scoped publication readiness complete.
- Remaining limitations: area evidence cannot locate residents or addresses; no threshold is approved; DC normalization remains a candidate only; candidate migration is unapplied.
- Recommended next step: evaluate both ZIP population weighting and an address-resolution provider, without enabling auto-select until address-level evidence and a separate product decision support it.
