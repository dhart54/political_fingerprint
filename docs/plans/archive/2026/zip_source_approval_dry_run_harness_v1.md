# Milestone Plan: ZIP Source Approval And Dry-Run Import Harness V1

## Intent

- Build a no-write ZIP/ZCTA source approval and dry-run import harness after PR #83.
- Evaluate a concrete official source candidate without approving production ingestion before exact license/terms, effective date, file version, checksum, and technical layout are recorded.
- Keep `zip_district_mappings` empty, keep `ZIP_MULTI_ROW_LOOKUP_ENABLED=false`, and keep public ZIP lookup behavior on the existing compatibility path.

## Outcome

- Operational result: no production writes, no migration rerun, no seed load, no national ZIP ingestion, no route switch, and no frontend runtime behavior change.
- Product/readiness result: a local dry-run harness can parse source-like ZIP/ZCTA rows and produce a coverage, ambiguity, rejection, and future auto-select-blocker report.

## Scope And Boundaries

- In scope: plan, source approval decision record, dry-run-only parser/report script, local source-like fixture, focused parser/report tests, review packet JSON/Markdown, read-only postcheck, static route coverage checks, and JSON validation.
- Out of scope: database ingestion, inserts, updates, deletes, truncates, drops, migration rerun, public route switch, enabling `ZIP_MULTI_ROW_LOOKUP_ENABLED`, provider API integration, address lookup, frontend runtime changes, fake production metadata, secrets, and large external datasets.

## Decision Envelope

- Codex may document the source candidate and build a local dry-run parser/report harness.
- Codex may approve the candidate only for local dry-run fixture evaluation.
- Codex may not approve production ingestion unless source URL/path, exact effective date, source version, multi-district/multi-state capability, limitations, and license/terms are all explicit and non-inferred.
- A future write milestone must separately approve the official source file, bounds, rollback, caps, confirmation phrase, and any route switch.

## Definition Of Done

- [x] Start from latest `main` after PR #83 merge commit `7014777fdfa28875a7b9f852f1483356c0148d51`.
- [x] Confirm `zip_district_mappings` remains empty with postcheck-only/read-only verification.
- [x] Evaluate an official/non-commercial ZIP/ZCTA-to-congressional-district candidate.
- [x] Record a source approval decision and limitations without guessing missing approval metadata.
- [x] Add a dry-run-only local parser/report script under `backend/scripts/`.
- [x] Ensure the script fails closed unless `--dry-run` is explicitly passed.
- [x] Ensure the script has no database write path.
- [x] Add a small local source-like fixture covering single-district, same-state multi-district, multi-state, duplicate, invalid, and metadata-missing cases.
- [x] Generate JSON and Markdown review packets.
- [x] Add focused parser/report tests.
- [x] Confirm public ZIP routes do not read `zip_district_mappings`.
- [x] Confirm `ZIP_MULTI_ROW_LOOKUP_ENABLED` remains false/not enabled.
- [x] Run focused validation.
- [x] Commit, push, and open a focused draft PR.

## Baseline

- Branch: `codex/zip-source-approval-dry-run-harness-v1`.
- Base: latest `main` after PR #83 merge commit `7014777fdfa28875a7b9f852f1483356c0148d51`.
- Known unrelated untracked artifacts preserved: `docs/review_packets/chamber_filtering_data_integrity_audit.md` and `review_bundle_frontend_data_grounding/`.

## Implementation Sequence

1. Read the milestone request, ZIP route/read-layer code, prior ZIP plans, and review packets.
2. Run `backend/scripts/apply_zip_district_mappings_migration.py --postcheck-only` against `backend/.env`.
3. Evaluate official Census source pages and record the candidate decision conservatively.
4. Add `backend/scripts/dry_run_zip_source_import.py` with no DB imports, no env reads, and required `--dry-run`.
5. Add a tiny local fixture that exercises ambiguity and rejection paths without using a national dataset.
6. Add focused tests for report counts, fail-closed behavior, output generation, and static no-write posture.
7. Generate review packet Markdown/JSON from the harness.
8. Run focused backend ZIP tests, JSON validation, and read-only postcheck.
9. Commit, push, and open a focused draft PR.

## Discoveries

- `zip_district_mappings` remains empty: row count `0`, unique ZIP count `0`, auto-select eligible count `0`.
- `/lookup/zip/{zip}` and `/lookup/zip/{zip}/races` still resolve ZIP state/district through `zip_district_map`.
- The Census relationship files include a 119th Congressional District to 2020 ZCTA relationship file candidate and are suitable for evaluating many-to-many geography relationships.
- Census ZCTA guidance confirms ZCTAs are Census-created approximations and do not represent every valid USPS ZIP Code.
- Production ingestion should not be approved yet because exact license/terms, effective date, final file/checksum, and technical layout still need an explicit approval packet.

## Decisions And Rationale

- Source decision: approved for local dry-run fixture evaluation only; not approved for production ingestion.
- The dry-run harness accepts only local CSV/JSON files and writes only review/local dry-run outputs.
- Future strict auto-select remains blocked in the report because this dry run does not validate current House member metadata or duplicate current-member matches.
- Same-state multi-district and multi-state rows are first-class report outcomes, not errors to hide.

## Validation Results

- `python backend\scripts\apply_zip_district_mappings_migration.py --postcheck-only --env-path backend\.env`: passed; migration was not applied, row count `0`, unique ZIP count `0`, auto-select eligible count `0`.
- `python backend\scripts\dry_run_zip_source_import.py --dry-run --input backend\fixtures\zip_source_dry_run_sample\census_119_cd_zcta_sample.csv --output docs\review_packets\zip_source_approval_dry_run_harness_v1.json --markdown-output docs\review_packets\zip_source_approval_dry_run_harness_v1.md`: passed; generated JSON and Markdown review packets.
- Initial focused backend validation reached 31 passing assertions but failed during pytest `tmp_path` fixture setup because the local temp directory was permission-denied. The new tests were updated to use a repo-local scratch directory and the failed scratch directory was removed.
- `$env:DATABASE_URL='postgresql://invalid'; python -m pytest backend\tests\test_api_lookup.py backend\tests\test_zip_source_metadata_report.py backend\tests\test_zip_multi_row_schema_contract.py backend\tests\test_zip_lookup_payload_parity.py backend\tests\test_zip_seed_readiness.py backend\tests\test_zip_multi_row_readonly_route_eval.py backend\tests\test_zip_source_dry_run_import.py -p no:cacheprovider`: passed, 33/33.
- `python -m json.tool docs\review_packets\zip_source_approval_dry_run_harness_v1.json`: passed.
- `python -m json.tool docs\review_packets\zip_source_backed_ingestion_preflight_v1.json`: passed.

## Production Writes

- Performed: no.
- Read-only production/Supabase inspection: yes, postcheck-only mode.

## Rollback Paths

- Revert the dry-run script, local fixture, tests, plan, and review packet files from this branch.
- No database rollback is needed because no database write occurs.

## Blockers

- None for this no-write milestone.
- Production ingestion remains blocked until exact source file, terms/license, effective date, source version, checksum, and technical layout are explicitly approved.

## Final Reconciliation

- Definition of done satisfied: yes.
- Production writes performed: no.
- Route behavior changed: no.
- Frontend runtime changed: no.
- Remaining limitation: production source retrieval/approval and any bounded ingestion are deferred to future milestones.
