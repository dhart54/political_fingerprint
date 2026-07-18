# ZIP Population Evidence Contract V1

## Decision

Population evidence may complement the unapplied `0015` relationship model only as independently reproducible, source-snapshot-scoped aggregate evidence. It must not change the set of official possible mappings, choose a representative, or alter runtime behavior.

No `0016` migration is created in this milestone. The source and derivation contract is stable enough for analysis, but production storage is not yet justified and no presentation threshold has been selected. If a later reviewed milestone authorizes storage, prefer aggregate evidence with reproducible local derivation.

## Interpretation boundary

- A possible mapping is an official geographic relationship and remains evidence even when its allocated 2020 population is zero.
- A population-ranked mapping is a versioned presentation order based on 2020 Census resident population allocated through exact 2020 tabulation blocks.
- An address-resolved mapping identifies the district for a specific entered street address through an authoritative or validated resolver.

Population allocation may support “Most of this ZCTA’s allocated 2020 population was assigned to this district.” It cannot support “This is your district,” “Most current ZIP residents live here,” or automatic representative selection.

## Source and derivation lineage

The exact primary derivation requires all of:

1. 2020 Census PL 94-171 state files, using summary level `750`, the 15-digit block GEOID, shared `LOGRECNO`, and P1 total resident population.
2. The 2020 ZCTA-to-2020-tabulation-block relationship file.
3. The Census Bureau’s CD119 whole-2020-block equivalency file.
4. The CD119 split-block listing, which records the one Colorado block split by the legal boundary and its authoritative whole-block tabulation assignment to CD08.
5. The pinned PR #89 ZCTA/CD119 area relationship and House snapshot `house-119-20260713T011722Z`.

Only `exact_official_common_block` and `exact_official_assignment` enter the primary aggregation. Spatially apportioned block population is excluded.

## Required aggregate evidence

One aggregate row per accepted ZCTA/CD119 relationship should preserve:

- population source snapshot and artifact identities;
- geography source artifact identities;
- House snapshot identity;
- ZCTA, source CD119 GEOID, canonical state, and source district;
- exact relationship-population numerator and ZCTA-population denominator;
- contributing, populated, and zero-population block counts;
- excluded or unresolved block and population counts;
- constrained assignment quality;
- derivation-manifest checksum and parser version;
- deterministic population and land ranks;
- current-seat evidence classification;
- `auto_select_eligible = false`.

Zero-population rows remain in the evidence ledger. Whether a product hides them by default requires a separate product decision and must preserve a way to inspect the official possible mapping.

## Model comparison

### Full block ledger

This model stores every normalized 2020 block, population, ZCTA assignment, and CD119 assignment in production. Nationwide it requires millions of rows, large indexes, a lengthy load, and a rollback covering every block. It preserves maximum local query detail, but current product behavior does not require production block-level queries. The ignored local batch already preserves reproducible block provenance.

### Aggregate evidence with reproducible local derivation

This model stores source snapshots/artifacts plus one exact aggregate per accepted ZCTA/CD119 relationship. It preserves the numerator, denominator, block counts, quality, manifest checksum, source lineage, and House lineage while keeping the multi-million-row block join in ignored reproducible artifacts. It has substantially smaller storage, index, load, and rollback costs and meets the foreseeable presentation-ranking need.

The aggregate model is preferred if production storage is later authorized.

## Candidate additive schema envelope

A future `0016_zip_population_evidence.sql`, if separately approved, should depend on `0015` and may add:

- `zip_population_source_snapshots`;
- `zip_population_source_artifacts`;
- `zip_district_population_evidence`;
- an optional immutable link to `zip_mapping_policy_runs`.

It must be additive and DML-free; use exact integer numerators/denominators; constrain assignment quality; support deletion by population source snapshot; preserve artifact and House lineage; never update `zip_district_mappings`; never set auto-select eligibility; and never reference public routes, frontend behavior, or feature flags.

## Product-use matrix

| Use | Land share | Block population share | Full address |
|---|---|---|---|
| Preserve all possible districts | yes | yes | yes |
| Order possible districts | weak | stronger, with 2020-vintage caveat | definitive only for entered address |
| Hide zero-population relationships by default | no | potentially, after product review | yes |
| Label low-population overlap | no | yes, versioned | yes |
| Ask for street address | yes | yes | fulfills requirement |
| Automatically choose representative | no | no | potentially, after resolver validation |

## Remaining caveats

The resident population measurement is from 2020. CD119 boundaries describe the 2024 election-cycle plan, and current residents may differ from the 2020 count. A dominant ZCTA population assignment does not make addresses in a minority district incorrect. Full-address resolution remains necessary for automatic representative selection.
