# Milestone Plan: ZIP Source Retrieval Approval And Bounded Dry-Run With Official File V1

## Intent

- Pin the exact official Census 119th Congressional District-to-2020 ZCTA relationship file and validate it through the existing no-write harness.
- Advance source readiness without changing database contents, lookup semantics, routes, or frontend behavior.

## Outcome

- An exact source manifest, a narrow official-layout parser, and JSON/Markdown dry-run review packets based on a reviewed local official file.

## Scope And Boundaries

- In scope: official source retrieval, checksum/layout inspection, ignored local file, tiny test-only excerpt, parser tests, dry-run reports, read-only postcheck, and static route checks.
- Out of scope: migrations, seeds, database ingestion or mutation, route switching, feature-flag enablement, member matching, address/provider integration, and frontend changes.

## Decision Envelope

- Codex may approve the exact source for bounded dry-run only and adapt the report-only parser to its documented layout.
- Production ingestion and any database write require a later explicit milestone.

## Definition Of Done

- [x] Branch starts at PR #84 merge commit `b7f4fb1e61157a7bcd97470487bec30ef73161d1`.
- [x] Exact official page, download, filename, size, checksum, version/vintage, terms basis, layout, and limitations are pinned.
- [x] Official layout parses through a narrow, tested adapter while legacy fixture tests remain intact.
- [x] JSON and Markdown review packets are generated from the ignored local official file.
- [x] Read-only postcheck confirms `zip_district_mappings` is empty and routes remain on `zip_district_map`.
- [x] Focused tests and JSON validation pass.
- [x] Commit, push, and draft PR are complete (PR #85).
- [x] Harden PR #85 so verified-official status requires exact filename, size, and SHA-256; remove stale PR #84 defaults.

## Baseline

- Branch/base: `codex/zip-source-retrieval-official-file-dry-run-v1` at `b7f4fb1e61157a7bcd97470487bec30ef73161d1`.
- Tracked working tree: clean at branch creation.
- Known unrelated untracked artifacts preserved: `docs/review_packets/chamber_filtering_data_integrity_audit.md`, `review_bundle_frontend_data_grounding/`.
- Public routes read `zip_district_map`; no route reference to `zip_district_mappings` was found.

## Implementation Sequence

1. Verify baseline and stop conditions.
2. Retrieve the official file into ignored `.local/`, inspect layout, size, and checksum.
3. Add manifest, official-layout adapter, tiny excerpt, and focused tests.
4. Run full-file dry-run, read-only postcheck, focused ZIP tests, static checks, and JSON validation.
5. Reconcile docs, commit, push, and open a draft PR.

## Progress Checklist

- [x] Discovery
- [x] Implementation
- [x] Validation
- [x] Documentation
- [x] Commit/PR readiness

## Discoveries

- Census links the national file at `https://www2.census.gov/geo/docs/maps-data/data/rel2020/cd-sld/tab20_cd11920_zcta520_natl.txt`.
- Retrieved file size: `6,195,997` bytes; SHA-256: `57fad59f65af5179ddd18dcfb8f72482dc0cf04fe26e2b9b2b34c51c04405f77`.
- The file is pipe-delimited with 17 documented columns; congressional GEOID contains state FIPS plus district and ZCTA GEOID is five digits.

## Decisions And Rationale

- Decision remains `approved_for_bounded_dry_run_only`; member-metadata gates and a production-write plan do not exist in this milestone.
- The full official file remains ignored under `.local/`; only a tiny, labeled excerpt will be committed for deterministic parsing tests.
- ZCTA relationships may surface possible districts only; they cannot establish address-level representation or cover all USPS ZIP Codes.

## Deviations Or Corrections

- The report initially carried every ambiguous ZCTA identifier. It was bounded to the first 100 examples per ambiguity class while preserving complete counts, reducing the committed review packet to about 27 KB.
- Hardening follow-up: filename-only official-file detection and PR #84 output/input defaults were unsafe. The harness now requires an explicit input, binds verified status to all three pinned identity fields, and fails before report writes when the official filename has mismatched bytes.

## Validation Results

- `python backend\scripts\apply_zip_district_mappings_migration.py --postcheck-only --env-path backend\.env`: passed; migration not applied, target row count `0`, unique ZIP count `0`, auto-select eligible count `0`.
- Official-file harness command: passed; 40,397 rows, 39,967 accepted, 430 rejected, 33,642 unique ZCTAs, 51 states/DC, 436 state-district pairs, 5,725 same-state multi-district ZCTAs, 137 multi-state ZCTAs, and zero final auto-select-eligible ZCTAs.
- Focused ZIP suite after identity hardening: `36 passed` in 9.96 seconds.
- Full-file identity gate: filename, `6,195,997`-byte size, and SHA-256 `57fad59f65af5179ddd18dcfb8f72482dc0cf04fe26e2b9b2b34c51c04405f77` all matched; `official_file_identity_verified=true`.
- Spoofed official-filename test: passed; mismatched bytes returned exit code `2` and wrote no JSON or Markdown report.
- New packet, PR #84 packet, and source manifest: valid JSON.
- Static route/flag checks: no `zip_district_mappings` read in public API modules; no enabled `ZIP_MULTI_ROW_LOOKUP_ENABLED` assignment.
- `git diff --check`: passed (line-ending notices only).

## Production Writes

- Performed: no.
- Scope/expected/actual effects: none; all work is local and report-only.

## Rollback Paths

- Revert branch files; delete the ignored local source copy. No database rollback is applicable.

## Blockers

- None currently. Any non-empty target table, route switch, unclear official layout/terms, or database write requirement is a hard stop.

## Final Reconciliation

- Definition of done satisfied: yes; implementation, validation, commit, push, and draft PR #85 are complete.
- Remaining limitations: production ingestion and member metadata gates remain unapproved.
- Recommended next step: ZIP Source-to-Member Readiness Gate V1, covering current-member matching, duplicate/stale member blockers, territory handling, and bounded rollback/preflight design without ingestion or a route switch.
