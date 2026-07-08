# Milestone Plan: ZIP Schema And Source Metadata Design V1

## Milestone Intent

- Immediate task: decide the future database and payload shape needed to support multi-district ZIPs, source metadata, currentness, and safe auto-select gates.
- Larger-goal alignment: prepare production ZIP expansion without ingesting national ZIP data or weakening PR #76/#77 gates.
- Operational outcome: docs-only design packet with schema recommendation, migration/backfill sequence, production coverage report requirements, and future acceptance criteria.

## Scope And Boundaries

- In scope: schema options, recommended future table contract, payload contract, migration/backfill plan, source metadata gates, production read-only coverage report requirements, and implementation acceptance criteria.
- Out of scope: schema migration, editing `backend/migrations/0001_initial_schema.sql`, national ZIP ingestion, address lookup, provider integration, local or production DB mutation, fake source metadata, and frontend gate changes.
- Expected changed files: this plan, `docs/review_packets/zip_schema_source_metadata_design_v1.md`, and optional JSON companion.

## Decision Envelope

- Codex may decide documentation structure and make a clear recommendation within the requested options.
- Explicit future approval is required for schema changes, production credentials, source/vendor choice, national ZIP data, address lookup, provider integration, or any public behavior change.

## Definition Of Done

- Recent ZIP metadata, ambiguity, and address-design docs are read.
- Current schema/API/ETL/frontend ZIP surfaces are inspected.
- At least options A, B, and C are compared.
- Recommendation is explicit.
- Future schema fields are marked required vs optional.
- Payload contract covers single, multiple districts, multiple states, unsupported, stale/unknown, fixture/sample, and future address-resolved results.
- Migration/backfill and rollback sequence is documented.
- Production read-only coverage report requirements and future acceptance criteria are documented.
- Validation confirms docs-only diff.

## Baseline

- Branch: `codex/zip-schema-source-metadata-design-v1` from `main` after PR #77 merge commit `6fc686ee508166bc6fd188af16da380c709ab441`.
- Current DB table `zip_district_map` has `zip TEXT PRIMARY KEY`, `state`, `district`, and timestamps only.
- Current DB ZIP lookup emits standardized metadata but remains `source_currentness: "stale_or_unknown"` and `stale_or_unknown_source: true`.
- Current ETL paths dedupe ZIP mappings by `zip`, preserving one mapping per ZIP.
- Current frontend classifier blocks auto-select for ambiguous, multi-state, fixture/sample, unsupported, stale/unknown, and member-uncertain states.

## Implementation Sequence

1. Read instructions, planning convention, and recent ZIP/address docs.
2. Inspect schema, lookup, ETL, report, fixtures, and tests.
3. Draft active plan.
4. Draft review packet and JSON companion.
5. Run docs-only validation.
6. Commit, push, and open draft PR.

## Progress Checklist

- [x] Attachment and `AGENTS.md` read.
- [x] Recent ZIP/address docs inspected.
- [x] Schema/API/ETL/frontend ZIP surfaces inspected.
- [x] Active plan created.
- [x] Review packet drafted.
- [x] JSON companion drafted.
- [x] Validation run.
- [ ] Commit, push, and draft PR opened.

## Discoveries

- `zip_district_map.zip` as primary key is the central blocker for multi-district and multi-state ZIP representation.
- The existing DB lookup reads one row and selects one House member from one state/district pair.
- Seed/current/historical refresh merge ZIP rows using `key="zip"`, so future multi-row support also needs ETL dedupe changes.
- PR #77 metadata fields are enough for the frontend classifier, but current DB storage cannot populate real current source metadata.
- Unsupported ZIP payload normalization is frontend-owned today because backend `/lookup/zip/{zip}` still returns 404.

## Decisions And Rationale

- Recommend Option B: create a new canonical `zip_district_mappings` table and keep `zip_district_map` as a compatibility/deprecated path during migration.
- Rationale: Option B supports multiple districts and states per ZIP, preserves current rollback safety, avoids destructive primary-key rewrite, and lets the route compare old and new payloads behind a feature flag.
- Do not recommend address lookup as part of this milestone; future address-resolved payloads should reuse the same metadata gate model.

## Deviations Or Corrections

- None.

## Validation Results

- `git diff --name-only`: passed; listed only the plan, review packet, and JSON companion.
- `git diff --check`: passed; no whitespace errors. Git emitted expected LF-to-CRLF warnings.
- `python -m json.tool docs\review_packets\zip_schema_source_metadata_design_v1.json`: passed.

## Production Writes

- Performed: no.
- Scope: none.

## Rollback Paths

- Revert only the new plan/review-packet/JSON docs from this branch.
- Future implementation rollback should keep the old `zip_district_map` route path available until new payload parity and production coverage checks pass.

## Blockers

- None for docs-only design. Future implementation requires explicit approval for schema migration and any production credentialed read-only report.

## Final Reconciliation

- Design deliverables are docs-only.
- Recommended schema option: Option B, additive `zip_district_mappings` table with old `zip_district_map` retained as compatibility/deprecated path during migration.
- Current gates remain unchanged: no House auto-select for missing source metadata, ambiguous, multi-state, fixture/sample, unsupported, stale/unknown, or member-uncertain results.
- Remaining limitation: no schema migration or production coverage truth exists until a future explicitly approved implementation/credentialed read-only report milestone.
