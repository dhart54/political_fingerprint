# Foushee Justice activation HTTP 500 and rollback

Status: resolved and closed; corrected publication active.

This receipt records the failed public-availability check for activation bundle
`foushee_justice_public_safety_119_publication_activation_v1`, digest
`df081ea7fc93039926b5a8ac1e468444f30e28b25bb2862bb2980f7d2d83e813`.
It does not authorize another activation.

## Bounded production timeline

All times are UTC. The preserved operator evidence establishes:

- `2026-07-28T20:30:26.506420Z`: final pre-apply freshness report.
- After that report, one transaction inserted batch 12, artifacts 215-217, two
  relationships, and one registry row. Its internal postcheck passed at counts
  `3 / 143 / 157 / 1`.
- Two public smoke attempts, one for `scope=119` and one for `scope=all`, each
  returned `HTTP 500 Internal Server Error` within 60 seconds.
- The documented threshold triggered the exact database rollback, removing
  batch 12 and artifacts 215-217.
- `2026-07-28T20:33:56.327062Z`: recovered public checks returned HTTP 200.
- `2026-07-28T20:33:58.224066Z`: post-rollback preflight proved counts
  `2 / 140 / 155 / 0`, target absence, and fingerprint
  `3328dd38b4483f651a8459adec9b1d4ed2cfb8baa61ad413a282d3617d726b18`.
- `2026-07-28T20:34:28.074273Z`: the operator summary was sealed.

The retained evidence did not include separate transaction-start, commit,
internal-postcheck, smoke-attempt, or rollback-commit timestamps. It also did
not retain request IDs, instance IDs, database error codes, or production stack
traces. Those values must not be reconstructed from file modification times.
The bounded Render dashboard session available during diagnosis was not
authenticated, so no production log content was accessed.

## Exact local reproduction

The verified `pre-activation.dump` was restored into
`supabase/postgres:17.6.1.156` and the real FastAPI application was started
against that database. Before activation, the public HTTP route returned
`receipts_only`. The documented activation CLI then inserted the exact seven
rows.

On the uncorrected repository code, every request that reached the shared
publication-registry query failed deterministically with:

```text
ValueError: dictionary update sequence element #0 has length 7; 2 is required
```

The stack was:

```text
get_editorial_presentations
  -> _load_publication_rows
  -> EditorialArtifactRepository.publication_selector
  -> EditorialArtifactRepository._all
  -> dict(row)
```

The API connection uses Psycopg's default tuple row factory. `_all()` treated
each tuple as key/value pairs, so the first seven-column registry row raised
before selector execution, graph validation, artifact conversion, response
construction, or JSON serialization. With an empty registry, the loop had no
row to convert and the inactive route appeared healthy.

The activation CLI internal postcheck did not exercise this boundary. Its
connection explicitly uses Psycopg `dict_row`, and the previous PostgreSQL API
test replaced the application's connection with that same mapping-row helper.
The CLI and HTTP route otherwise used the same query, selector, stored graph,
artifact, receipt, scopes, and response construction. There was no additional
HTTP-only semantic validation involved.

## Correction and readiness effect

The repository now normalizes both mapping rows and ordinary DB-API sequence
rows using cursor column metadata. Missing metadata, invalid metadata, row-width
mismatch, database failures, and all governed-data validation failures remain
fail-closed; operational database failures are not converted to
`receipts_only`.

The real-server disposable proof covers inactive HTTP, exact activation,
reviewed `119` and `all`, inactive `118`, exact approved wording and provenance,
seven supporting actions, five episodes, two repeated patterns, the mixed
fentanyl trajectory, limitations, cross-member and cross-issue isolation,
exact rollback, recovered inactive HTTP, and canonical fingerprint restoration.

Runtime comparison found the defect was a connection-configuration difference,
not a dependency-version incompatibility:

| Boundary | Observed configuration |
| --- | --- |
| Repository requirements | FastAPI 0.116.1, Uvicorn 0.35.0, Psycopg 3.3.3 |
| Local reproduction | FastAPI 0.116.1, Pydantic 2.11.7, Uvicorn 0.35.0, Psycopg 3.3.3 |
| Activation CLI | direct Psycopg connection with `dict_row` |
| Public API | direct Psycopg connection with default tuple rows |
| Database | Supabase-compatible PostgreSQL 17.6 |

The precise deployed Python and Pydantic patch versions and connection-role
grants were not available from the unauthenticated log context. The reproduced
exception precedes role-sensitive graph hydration and is fully explained by
the verified row-factory difference.

At the time of this incident, production remained publication-inactive. Another
activation required a separate authorization after the corrected commit was
merged, deployed, reported exactly by `/health`, and followed by fresh production
preflight/backup evidence and a passing real-HTTP disposable proof.

## Merge-gate correction note

The PR #118 merge gate identified two repository-only defects in the proposed
correction. First, the initial row normalizer admitted ambiguous mapping keys,
duplicate cursor names, and arbitrary iterable or string rows. The corrected
closed contract now accepts only validated string-key mappings or supported
non-string sequences paired with unique, nonblank DB-API/Psycopg column names;
it preserves keys and values without coercion and rejects width mismatches.

Second, the initial real-Uvicorn harness depended on an operator-provisioned
database and discovered rollback IDs through postcheck. The authoritative proof
now owns a uniquely labeled PostgreSQL container, volume, and network from
validated snapshot restore through final destruction. It captures exact apply
identities before postcheck, attempts identity-bound rollback after any
post-commit failure, and destroys all current-run database resources regardless
of rollback outcome. Both rollback verification and verified resource absence
are required to pass.

These findings concerned the repository correction and its disposable
readiness proof. They did not cause another production activation, production
database change, backup replacement, or deployment.

## Successful activation and closure

A separately authorized activation completed on 2026-07-29 after corrected
commit `bbeafa1e64b4e7783739f5b2f6b2c343b39209e5` was deployed and fresh health,
production-freshness, public receipts-only, backup-lifetime, archive, and
lifecycle HTTP proofs passed. At `2026-07-29T02:01:07.388267Z`, one transaction
inserted batch 13, presentation artifact 218, source-manifest artifact 219,
validation-result artifact 220, two relationships, and one publication-registry
row. These numeric IDs record that production event; the natural keys and
content digests are the portable identities.

The internal postcheck proved counts `3 / 143 / 157 / 1`. The public smoke
completed at `2026-07-29T02:01:44.742108Z` without an HTTP 500: Foushee Justice
returned `reviewed_conclusion` for `scope=119` and bounded `scope=all`, while
`scope=118`, other issues, and other members retained their required isolation.
The identity-bound rollback was not triggered. The immutable, non-authorizing
closeout record is
`docs/editorial/publication_activations/foushee_justice_public_safety_119_successful_activation_receipt_v1.json`.
