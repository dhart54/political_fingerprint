# Editorial Artifact Persistence Contract V1

## Source-of-truth phase

Checked-in editorial artifacts remain canonical. PostgreSQL is a deterministic, queryable staging mirror. No public backend or frontend path reads this store, no dual write is introduced, and artifact presence never implies publication.

The existing `vote_interpretations` table remains the canonical roll-scoped interpretation store. It is not extended because its mutable one-row-per-roll shape cannot safely represent shared evidence graphs, member overlays, validation history, supersession, and exact-version publication. Migration `0016` therefore adds a narrow generic layer without replacing members, measures, roll calls, or existing interpretations.

## Relational core

- `editorial_artifact_batches` pins the deterministic batch key, originating commit, manifest SHA-256, and expected counts.
- `editorial_artifact_versions` stores one typed, schema-versioned immutable JSONB payload plus queryable identity, status, provenance, and canonical foreign keys.
- `editorial_artifact_relationships` connects exact artifact IDs and therefore exact versions.
- `editorial_publication_registry` can reference only one exact immutable public-presentation version per member and issue.

The type vocabulary contains the 15 reviewed artifact classes. Natural keys identify editorial concepts; positive integer artifact versions identify revisions. `(natural_key, artifact_version)` is unique. A new revision inserts a new row and may reference the exact row it supersedes. Updates are rejected by a database trigger.

## Canonicalization and hashes

Payload hashes are SHA-256 over UTF-8 JSON with recursively sorted object keys, no insignificant whitespace, and preserved array order. Source-manifest hashes cover sorted repository path/hash records. Formatting changes do not change semantic hashes. Every imported artifact retains source commit `88d6f3446f54b07735e084cbc958c1614b190fab`.

The same natural key, version, and hash is idempotent. The same natural key and version with a different hash fails closed before any insert. Canonical member and House roll-call identities must resolve before import.

## Status and routing

Editorial status, benchmark status, production eligibility, and review route are indexed columns rather than payload-only data. Review routes normalize to `standard_generation`, `sampled_audit`, `human_exception`, or `blocked`; they do not confer approval.

All V1 seed artifacts are `human_approval_pending`, `not_promoted`, and `production_eligible = false`. García is retained as sampled-audit calibration metadata, not a gold benchmark.

## Publication gates

The registry accepts active rows only. Its trigger rejects an exact slice version unless all of these are true:

- artifact type is `issue_public_presentation`;
- member and issue identities match;
- editorial status is `human_approved`;
- benchmark status is `gold_benchmark`;
- production eligibility is true;
- an exact relationship points to a current successful validation with zero blockers;
- an exact relationship points to a complete required source manifest;
- the presentation payload has zero blocking findings.

The V1 seed creates no active or inactive registry rows.

## Security

All four tables enable RLS. `anon` and `authenticated` receive no direct table or sequence privileges, and there are no public policies. Backend/service-role access and reviewed migration tooling remain the only write path. No public API endpoint is added.

## Import and export

`backend/scripts/build_editorial_artifact_seed.py` builds or checks the only accepted manifest. `backend/scripts/editorial_artifact_store.py` requires an explicit mode, target, batch key, source commit, manifest hash, and migration hash. Apply uses statement and lock timeouts, a transaction-scoped advisory lock, canonical identity checks, immutable inserts, exact postchecks, and redacted target reporting.

The exporter reads one exact batch, reconstructs deterministic artifacts and relationships, recomputes hashes, and requires equality with the checked-in bundle.

Arbitrary JSON import is not supported.

## Rollback and forward recovery

Seed rollback accepts only the V1 batch and manifest, acquires the same advisory lock, refuses published references, verifies exact pre-counts, sets the transaction-local batch guard, and deletes only that batch's relationships, versions, and batch row. The schema remains.

The rollback was not executed. Schema recovery is forward-only: correct a defect through a separately reviewed additive migration. Do not drop the persistence tables or rewrite version history in place.

## Future workflow and cutover

1. Research or reuse shared legislative meaning in Git.
2. Generate deterministic artifacts.
3. Run validators.
4. Create a versioned seed/import manifest.
5. Persist a new immutable batch.
6. Route slices to standard generation, sampled audit, human exception, or blocked.
7. Leave publication unchanged.
8. Approve and activate an exact version only in a separately authorized milestone.

A later read-path milestone may use approved database artifacts. It must preserve the static/public fail-closed behavior until that cutover is explicitly reviewed.
