# ZIP Schema And Source Metadata Design V1

## Summary Recommendation

Recommend **Option B: add a new canonical `zip_district_mappings` table and leave existing `zip_district_map` as a compatibility/deprecated table during migration**.

Why:

- It supports multiple districts and multiple states per ZIP without rewriting the current primary-key table in place.
- It can store source name, source type, retrieval date, effective date, version, currentness, confidence/status, and ambiguity detection level per mapping row.
- It gives the safest rollback path: keep current lookup behavior gated while the new table is validated and compared.
- It supports future address-level resolution by sharing source/currentness concepts without storing raw addresses.
- It preserves the PR #76/#77 contract: missing metadata remains gated and House auto-select remains limited to `single_district_ready`.

No schema migration, production credential use, national ZIP ingestion, address lookup, provider integration, or production write is included in this milestone.

## Current Schema Limitation Recap

Current `backend/migrations/0001_initial_schema.sql`:

```sql
CREATE TABLE zip_district_map (
    zip TEXT PRIMARY KEY CHECK (zip ~ '^[0-9]{5}$'),
    state TEXT NOT NULL,
    district TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Current limitations:

- One row per ZIP is enforced by `zip TEXT PRIMARY KEY`.
- Multi-district ZIPs cannot be represented.
- Multi-state ZIPs cannot be represented.
- Source name, source type, retrieval date, effective date, version, currentness, confidence/status, and ambiguity detection level cannot be stored.
- ETL paths currently dedupe ZIP rows by `zip`.
- DB lookup currently reads one `zip_record` and returns one state/district.
- PR #77 correctly marks DB ZIP rows as `source_currentness: "stale_or_unknown"` because real source metadata is unavailable.

## Schema Options Matrix

| Criterion | Option A: alter `zip_district_map` | Option B: new `zip_district_mappings` | Option C: keep single-row canonical plus source/ambiguity side tables |
| --- | --- | --- | --- |
| Multiple districts per ZIP | Yes, if primary key is replaced with composite key | Yes, natively | Partially; side table can describe ambiguity, but canonical table still cannot hold all rows cleanly |
| Multi-state ZIPs | Yes, if composite key includes state | Yes, natively | Partially; awkward because canonical table has one state |
| Source name/type/date/version | Yes, via added columns | Yes, via required columns on new rows | Yes, but split across tables |
| Source currentness | Yes | Yes | Yes, but resolution logic must join side tables |
| Confidence/status | Yes | Yes | Yes, but split across tables |
| Ambiguity detection level | Yes | Yes | Yes, but side table has to override canonical row |
| Compatibility with `/lookup/zip/{zip}` | Medium; route must adapt to changed primary key and multi-row reads immediately | High; old route can remain while new read path is feature-flagged | Medium; route must reconcile canonical row plus ambiguity/source tables |
| Migration risk | High; mutates existing table identity and rollback is harder | Low to medium; additive table first, controlled route switch later | Medium; fewer row changes but more joining and semantic ambiguity |
| Rollback path | Harder; primary-key rewrite may need table restore | Strong; disable new read path and keep old table | Medium; disable side-table path but stale canonical assumptions remain |
| Test complexity | Medium to high | Medium; direct multi-row fixtures and parity tests | High; must test canonical plus side-table precedence |
| Supports future address resolution | Possible, but table name remains ZIP-specific | Strong; can pair with future address-resolution payload/source tables | Possible, but side-table layering gets harder |
| Recommended? | No | Yes | No, except as a temporary compatibility helper if needed |

## Recommended Schema Contract

Future canonical table: `zip_district_mappings`.

Required fields:

| Field | Required | Notes |
| --- | --- | --- |
| `id` | yes | Stable surrogate key, e.g. `BIGSERIAL` or UUID. |
| `zip` | yes | Five-digit ZIP string. |
| `state` | yes | Two-letter state/territory code. |
| `district` | yes | House district string, normalized to `00` for at-large where applicable. |
| `source_name` | yes | Human-readable source name, e.g. reviewed internal source, Census-derived source, vendor/source name after approval. |
| `source_type` | yes | Controlled value such as `reviewed_zip_map`, `official_dataset`, `fixture_sample`, `manual_reviewed_seed`. |
| `source_retrieved_at` | yes | Date/timestamp when source was retrieved. |
| `source_effective_date` | yes | Date or cycle boundary the mapping is effective for. |
| `source_version` | yes | Dataset/version/vintage/benchmark string. |
| `source_currentness` | yes | Controlled value: `current`, `stale_or_unknown`, `fixture_sample`, `unsupported`, later maybe `expired`. |
| `confidence` | yes | Controlled value: `source_backed`, `reviewed`, `inferred`, `low`, `unknown`; auto-select eligibility requires a high-confidence source-backed/reviewed value. |
| `is_primary` | yes | Boolean for display ordering only; must not imply safe auto-select when more than one mapping exists. |
| `created_at` | yes | Audit timestamp. |
| `updated_at` | yes | Audit timestamp. |

Recommended optional fields:

| Field | Optional | Recommendation |
| --- | --- | --- |
| `district_type` | optional | Useful for `house`, `delegate`, `resident_commissioner`, `at_large`; include in first migration if cheap. |
| `congress` | optional but recommended | Useful for member reconciliation and redistricting-aware reports. |
| `cycle` | optional but recommended | Election/redistricting cycle label, e.g. `2026`. |
| `valid_from` | optional but recommended | Supports temporal validity and rollback comparison. |
| `valid_to` | optional | Supports expiration without deleting rows. |
| `provider_record_id` | optional | Useful for traceability when a source provides row IDs. |
| `notes` | optional | Internal review notes; never required for product copy. |

Recommended constraints and indexes for future migration:

- `CHECK (zip ~ '^[0-9]{5}$')`.
- `CHECK (source_currentness IN (...controlled values...))`.
- `CHECK (confidence IN (...controlled values...))`.
- Unique active source row key such as `(zip, state, district, source_name, source_version, COALESCE(valid_from, source_effective_date))`.
- Indexes on `zip`, `(zip, state, district)`, `source_currentness`, `source_name`, and `source_version`.
- Do not use `zip` alone as a primary key.

Compatibility/deprecation approach:

- Keep `zip_district_map` unchanged during first implementation.
- Add `zip_district_mappings` as the new canonical candidate table.
- Read old table until new read path is feature-flagged and validated.
- Later, deprecate `zip_district_map` only after production parity, rollback, and coverage reports pass.

## Recommended Payload Contract

The production-ready payload should stay compatible with PR #77:

```json
{
  "zip": "27701",
  "state": "NC",
  "district": "04",
  "data_source": "database",
  "lookup_metadata": {
    "source_type": "reviewed_zip_map",
    "source_name": "approved_source_name",
    "source_retrieved_at": "2026-07-01",
    "source_effective_date": "2026-01-03",
    "source_version": "approved-source-2026-v1",
    "source_currentness": "current",
    "fixture_sample_only": false,
    "stale_or_unknown_source": false,
    "member_metadata_uncertain": false,
    "can_represent_multiple_districts": true,
    "ambiguity_detection_level": "multi_row_source",
    "confidence": "source_backed"
  },
  "district_mappings": [
    {
      "zip": "27701",
      "state": "NC",
      "district": "04",
      "source_type": "reviewed_zip_map",
      "source_name": "approved_source_name",
      "source_version": "approved-source-2026-v1",
      "source_currentness": "current",
      "confidence": "source_backed"
    }
  ],
  "house_rep": {},
  "senators": []
}
```

State-specific payload rules:

| Result | Payload requirements | Auto-select |
| --- | --- | --- |
| Single district | One state/district in `district_mappings`; `source_currentness: "current"`; source name/retrieved/effective/version present; `ambiguity_detection_level: "multi_row_source"`; member metadata gates pass | May auto-select House only if frontend classifier returns `single_district_ready` |
| Multiple districts | Multiple district keys in `district_mappings`; one state or more; `can_represent_multiple_districts: true`; source metadata present if source-backed | Never auto-select House |
| Multiple states | Multiple state values in `district_mappings`; `can_represent_multiple_districts: true`; source metadata present if source-backed | Never auto-select House or Senate until state/address is confirmed |
| Unsupported ZIP | `data_source: "none"`; `source_currentness: "unsupported"`; `ambiguity_detection_level: "none"`; empty `district_mappings`; `house_rep: null`; `senators: []` | Never auto-select |
| Stale/unknown source | Missing or stale source metadata; `source_currentness: "stale_or_unknown"` or `stale_or_unknown_source: true` | Never auto-select |
| Fixture/sample source | `data_source: "fixtures"`; `fixture_sample_only: true`; `source_currentness: "fixture_sample"` | Never auto-select |
| Future address-resolved result | Reuse `lookup_metadata` with address-provider/source fields, but do not store raw address by default; include normalized ZIP/state/district and confidence/status only | May auto-select only after address source metadata and current member metadata gates pass |

No ZIP lookup result should auto-select a House member unless source metadata and current House member metadata both pass gates.

## Migration And Backfill Plan

Future implementation sequence, not performed in this milestone:

1. Create new additive schema/table.
   - Add `zip_district_mappings` with required source/currentness/confidence fields.
   - Keep `zip_district_map` unchanged.

2. Keep current lookup behavior gated.
   - DB path continues to report old rows as `stale_or_unknown_source`.
   - No production ZIP auto-select is enabled.

3. Build read-only local validation.
   - Extend local reports/tests to inspect new table shape and synthetic fixture rows.
   - Add deterministic split-ZIP and multi-state fixtures.

4. Load limited reviewed seed data only after approval.
   - Use bounded, reviewed data; no national ingestion.
   - Include complete source name/type/retrieved/effective/version/currentness metadata.

5. Run production read-only coverage report.
   - Requires explicit credential approval.
   - No writes.

6. Compare old vs new payloads.
   - Run old-table and new-table reads side by side.
   - Confirm DB old path remains gated and new path classifies ambiguous/stale/multi-state correctly.

7. Switch lookup route behind flag or controlled gate.
   - Feature flag controls new table read path.
   - Keep route output PR #77-compatible.
   - Monitor unsupported, ambiguous, stale, and eligible counts.

8. Deprecate old table only after confidence.
   - Remove old route dependency only after production parity and rollback criteria pass.
   - Keep rollback SQL/runbook ready before any destructive change.

Rollback steps:

- Disable new read-path flag and return to `zip_district_map` reads.
- Preserve `zip_district_mappings` for investigation; do not drop during incident rollback.
- If seed/backfill caused incorrect rows, mark rows inactive or stale via bounded rollback, then rerun read-only coverage.
- Only drop/deprecate old table in a later milestone with explicit approval.

## Source Metadata Requirements

Auto-select eligibility requires all of the following:

- `source_name` present and approved.
- `source_type` present and controlled.
- `source_retrieved_at` present.
- `source_effective_date` present.
- `source_version` present.
- `source_currentness: "current"`.
- Source can represent multi-district and multi-state ZIPs.
- `ambiguity_detection_level` is source-backed, preferably `multi_row_source`, not `single_row` or `none`.
- `confidence` is high enough for product use, e.g. `source_backed` or `reviewed`.
- ZIP maps to exactly one state/district in the payload.
- Fixture/sample flags are false.
- Stale/unknown flags are false.
- Current House member metadata gates also pass.

No ZIP lookup result should auto-select a House member unless source metadata and current House member metadata both pass gates.

## Read-Only Production Coverage Report Requirements

Future report design, not requiring credentials now:

- Total ZIP mapping rows.
- Unique ZIP count.
- ZIPs with multiple districts.
- ZIPs with multiple states.
- Rows missing source name/type.
- Rows missing source retrieved date.
- Rows missing effective date.
- Rows missing source version.
- Source distribution by name/type/version/currentness.
- Stale/unknown rows.
- Fixture/sample rows or leakage risk.
- Unsupported ZIP behavior and 404/contract handling.
- Ambiguity detection levels and counts.
- Auto-select eligibility counts.
- Rows ineligible by reason: missing metadata, ambiguous, multi-state, fixture/sample, stale/unknown, member metadata uncertain.
- House match success/failure by state/district.
- Multiple House matches.
- Senate state coverage and state ambiguity.
- Old-table vs new-table parity results.
- Feature-flag state and environment metadata.
- Production credential usage statement and read-only assurance.

The report must clearly state whether it is local-only or production-backed. Local reports must not be described as production coverage truth.

## Future Implementation Acceptance Criteria

- Schema can represent multiple districts per ZIP.
- Schema can represent multi-state ZIPs.
- Source metadata fields exist and are required for auto-select eligibility.
- ETL/import dedupe no longer collapses all mappings by `zip`.
- Payload preserves `district_mappings`.
- Ambiguous ZIP never auto-selects House.
- Multi-state ZIP never auto-selects House or Senate until state/address is confirmed.
- Missing metadata remains gated.
- Fixture/sample rows remain blocked and visibly labeled.
- Unsupported ZIP uses the standardized `data_source: "none"` contract or documented frontend normalization.
- Tests cover DB, fixture, unsupported, ambiguous, multi-state, stale/unknown, and current-source cases.
- Read-only production coverage report exists before any production rollout.
- Rollback path exists and is tested before route switch.
- No address lookup is introduced unless explicitly approved in a later milestone.

## No-Go Items

- No schema migration in this milestone.
- No edits to `backend/migrations/0001_initial_schema.sql`.
- No national ZIP ingestion.
- No address lookup.
- No Census, Google, Smarty, Cicero, or other provider integration.
- No local or production database write.
- No fake source metadata.
- No auto-select for missing metadata.
- No weakening current PR #76/#77 frontend gates.
- No vote interpretation, Record Across, issue read, or profile behavior changes.

## Recommended Next Milestone

**ZIP Multi-Row Schema Migration Prep V1**

Scope:

- Draft the additive migration for `zip_district_mappings` without applying it to production.
- Add synthetic multi-district and multi-state fixtures.
- Update read-only local report checks for the new schema contract.
- Add route-adjacent tests for old-table vs new-table payload parity.
- Keep current UI gates unchanged.
- Do not ingest national ZIP data.
- Do not add address lookup.
