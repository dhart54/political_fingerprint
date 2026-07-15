# ZIP Mapping Staging Contract V1

## Decision

The current `zip_district_mappings` table is not a sufficient evidence ledger. It can store multiple source-labeled state/district rows, but it cannot preserve the source snapshot, artifact checksum, raw source line, ZCTA denominators, relationship land/water parts, exact shares, candidate normalization, policy evaluation, or snapshot-scoped rollback needed to reproduce a mapping decision.

The supported contract separates immutable geographic evidence from versioned derived policy results. `zip_district_mappings` remains empty and may later serve as a bounded runtime materialization only after a separate product decision. Candidate migration `0015_zip_mapping_source_evidence.sql` implements this additive separation and remains unapplied.

## Evidence boundary

Three concepts remain separate:

1. A **possible mapping** is an immutable official relationship row. Water-only and tiny positive-land rows remain in evidence even if a presentation policy hides or demotes them.
2. A **preferred or ranked mapping** is a reproducible output of a named policy version. Ranking may order possible mappings but must be labeled as area-based and cannot claim address- or population-level certainty.
3. An **auto-select mapping** selects a representative without clarification. Area evidence does not support this. Candidate policy rows enforce `auto_select_eligible = false`.

Land share is not population share. ZCTAs are Census approximations rather than USPS ZIP delivery boundaries. Area dominance does not prove address dominance, and a threshold that reduces ambiguity does not establish correctness.

## Additive model

### `zip_mapping_source_snapshots`

One immutable analysis/source boundary. It pins Congress, ZCTA vintage, parser version, status, and manifest checksum. Deleting the snapshot is the bounded rollback root; child artifacts, relationships, policy runs, and evaluations cascade only within that snapshot.

### `zip_mapping_source_artifacts`

Pins the official source name, URL, filename, byte size, checksum, and retrieval date. The available source record proves a date, not a timestamp, so `retrieved_on DATE NOT NULL` and constrained `retrieval_precision = 'date'` preserve honest precision. Snapshot-scoped uniqueness prevents a source artifact from being silently replaced.

### `zip_district_relationship_evidence`

Preserves the raw source row identity and geography without changing official codes:

- source line number, ZCTA, and congressional GEOID;
- canonical source state and unmodified source district;
- raw ZCTA land/water denominators and relationship land/water parts;
- raw integers are the sole exact-share contract: land is `AREALAND_PART / AREALAND_ZCTA5_20`, water is `AREAWATER_PART / AREAWATER_ZCTA5_20`, and total is the sum of parts divided by the sum of denominators when each denominator is nonzero;
- an optional candidate normalization rule and candidate pair, separate from the official row.

`DC-98 → DC-00` is stored, if used later, only as a candidate normalization. This analysis proves that `DC-00` is the seeded current delegate seat, but does not approve runtime normalization or mutate `DC-98`.

No manually insertable share columns are retained, so stored fractions cannot contradict the official raw areas. Consumers must preserve a null/undefined share when its raw denominator is zero.

Each relationship also enforces that land part does not exceed ZCTA land, water part does not exceed ZCTA water, and the `NUMERIC`-cast total part does not exceed total ZCTA area. Candidate normalization is either wholly absent or has all three fields present; when present, its rule is nonblank and its state/district match exact two-character formats.

### `zip_mapping_policy_runs`

One immutable parent records a source snapshot, one exact House seat snapshot, a policy version, the exact policy definition as `JSONB`, evaluation time, and a complete/rejected status. `policy_definition` is the sole database source of truth; no independently writable checksum is stored. The analysis and manifest report a deterministic SHA-256 of each exact definition for review/reproduction.

`UNIQUE (snapshot_id, seat_snapshot_id, policy_version)` requires a version to identify one definition for a given source and House snapshot. A changed definition must use a new version. Previous source evidence and policy runs are never rewritten.

### `zip_mapping_policy_evaluations`

Stores one result per policy run and immutable relationship. It records the relationship ZCTA, survival decision, optional presentation rank and low-material-overlap label, and seat classification. Composite foreign keys require the evaluation snapshot and ZCTA to match both its policy run and relationship evidence. A non-surviving relationship cannot have a rank, and non-null ranks are unique within a run and ZCTA. `auto_select_eligible` is constrained permanently false.

## Current-seat evidence terminology

`all_surviving_mappings_have_supported_current_seat_evidence_zctas` preserves the prior broad 33,334-style metric: every surviving distinct pair has supported filled current-seat evidence, but multiple pairs may remain. It is not a single-mapping or auto-select metric.

`single_mapping_current_seat_ready_zctas` is strict: exactly one distinct surviving pair remains and it directly matches a filled current voting seat, delegate, or resident commissioner. Vacancies, DC candidate normalization, source conflicts, unsupported/stale/unknown evidence, and no-survivor cases do not qualify. Production auto-select eligibility remains independently fixed at zero.

## Reproducibility and rollback

The committed manifest pins the official checksum, parser version, exact policy definitions, deterministic ordering, local artifact paths, row counts, and generated artifact checksums. A later staging application must regenerate the ignored evidence batch from the pinned source and compare every checksum before any bounded write is considered.

Rollback is by source `snapshot_id`. The candidate foreign keys use `ON DELETE CASCADE` from the source snapshot through artifacts, relationship evidence, policy runs, and evaluations. Policy evaluations also cascade with their referenced relationship. House seat snapshot deletion is `ON DELETE RESTRICT`, preventing a run from silently losing its current-seat provenance. No rollback is needed for this milestone because migration `0015` was not applied and no production row was written.

## Measured design inputs

- 39,967 accepted relationships across 33,642 ZCTAs; 430 existing-parser rejections.
- 37 water-only relationships across 37 ZCTAs and no zero-area accepted relationships.
- 32 positive-land relationships below 0.01% of ZCTA land area.
- All 33,642 accepted land partitions reconcile exactly.
- The complete map of 31 positive-water state-`ZZ` rejected rows equals the complete 31-ZCTA accepted-row water-under-allocation map, totaling 66,153,060 square meters; no extra, missing, or mismatched partition remains.
- Ambiguity falls from 5,862 ZCTAs under any accepted relationship to 5,829 under positive-land evidence and 1,925 at the 25% sensitivity point. At 50%, 42 ZCTAs have no surviving mapping. These reductions are policy sensitivity, not correctness evidence.
- The current seat snapshot supplies 431 matched filled voting source pairs and four matched vacant source pairs. The sole DC source pair is a candidate normalization rather than a direct match.

## Product-use conclusions

| Use | Area-evidence conclusion |
|---|---|
| Preserve all possible districts | Supported when raw official rows and caveats are retained. |
| Order possible districts | Supported only as a versioned, labeled area-based presentation aid. |
| Hide water-only rows by default | Supported only if the rows remain visible in evidence/source detail. |
| Label low material overlap | Supported with an explicit versioned definition, not as a claim about population. |
| Ask for street address | Supported; ambiguity and non-dominant cases demonstrate the need. |
| Automatically choose a representative | Not supported by area, dominance, margin, or block-population evidence alone. |

## Next accuracy source

Use both Census block-level population allocation and a full-address congressional-district lookup. Block population can test whether area-based ranking is directionally useful for ZIP-level presentation. Only address-level resolution can support automatic representative selection for an entered address. Neither next step authorizes a route change or auto-selection by itself.

## Candidate migration status

`backend/migrations/0015_zip_mapping_source_evidence.sql` is additive: five new tables and supporting indexes, no DML, no existing-table alteration, no route or feature-flag reference. Its canonical UTF-8/LF repository bytes are pinned before structural inspection. The validator then permits only one `BEGIN`, the five exact `CREATE TABLE IF NOT EXISTS` statements, the seven exact `CREATE INDEX IF NOT EXISTS` statements, and one `COMMIT`; all unrecognized top-level SQL fails closed. It also pins foreign keys/delete actions, uniqueness/rank checks, raw-area bounds, normalization integrity, raw-area-only shares, retrieval precision, and indexes. It is a review candidate only and is unapplied.
