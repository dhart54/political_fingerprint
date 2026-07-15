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

One immutable analysis/source boundary. It pins Congress, ZCTA vintage, parser version, status, and manifest checksum. Deleting the snapshot is the bounded rollback root; child artifacts, relationships, and policy evaluations cascade only within that snapshot.

### `zip_mapping_source_artifacts`

Pins the official source name, URL, filename, byte size, checksum, and retrieval time. Snapshot-scoped uniqueness prevents a source artifact from being silently replaced.

### `zip_district_relationship_evidence`

Preserves the raw source row identity and geography without changing official codes:

- source line number, ZCTA, and congressional GEOID;
- canonical source state and unmodified source district;
- raw ZCTA land/water denominators and relationship land/water parts;
- reduced exact-fraction numerators and denominators, nullable only when a source denominator is zero;
- an optional candidate normalization rule and candidate pair, separate from the official row.

`DC-98 → DC-00` is stored, if used later, only as a candidate normalization. This analysis proves that `DC-00` is the seeded current delegate seat, but does not approve runtime normalization or mutate `DC-98`.

### `zip_mapping_policy_evaluations`

Stores a versioned evaluation of one immutable relationship. It records the policy definition checksum, survival decision, optional presentation rank and low-material-overlap label, House seat snapshot/classification, and evaluation time. New policy versions insert new evaluations; they do not rewrite source evidence.

## Reproducibility and rollback

The committed manifest pins the official checksum, parser version, exact policy definitions, deterministic ordering, local artifact paths, row counts, and generated artifact checksums. A later staging application must regenerate the ignored evidence batch from the pinned source and compare every checksum before any bounded write is considered.

Rollback is by `snapshot_id`. The candidate foreign keys use `ON DELETE CASCADE` from the snapshot through source artifacts, relationship evidence, and evaluations. No rollback is needed for this milestone because migration `0015` was not applied and no production row was written.

## Measured design inputs

- 39,967 accepted relationships across 33,642 ZCTAs; 430 existing-parser rejections.
- 37 water-only relationships across 37 ZCTAs and no zero-area accepted relationships.
- 32 positive-land relationships below 0.01% of ZCTA land area.
- All 33,642 accepted land partitions reconcile exactly.
- 31 water/total shortfalls, totaling 66,153,060 square meters, reconcile exactly to rejected official state-`ZZ` non-district water rows.
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

`backend/migrations/0015_zip_mapping_source_evidence.sql` is additive: four new tables and supporting indexes, no DML, no existing-table alteration, no route or feature-flag reference. It is a review candidate only and is unapplied.
