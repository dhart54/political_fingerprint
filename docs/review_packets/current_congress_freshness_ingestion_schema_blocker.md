# Current-Congress Freshness And Automated Ingestion

## Summary

This milestone refreshed current-Congress production coverage after first fixing a roll-call identity blocker.

The blocker was real: House and Senate roll-call numbers restart by session inside the same Congress, while production previously treated roll calls as unique by `(chamber, congress, rollcall_number)`. That would have caused 2026 rows to collide with 2025 rows. The branch therefore made roll-call identity session-aware before importing supported 2026 facts.

## Canonical Roll-Call Identity

The canonical natural key is now:

```text
chamber + congress + session + rollcall_number
```

This preserves distinct records for the same chamber/Congress/roll number across 2025 and 2026 sessions. Existing `roll_calls.id` values and dependent references were preserved.

## Production Baseline

Pre-migration baseline:

| Table / input | Count |
| --- | ---: |
| bills | 267 |
| roll_calls | 624 |
| votes_cast | 175,264 |
| vote_contexts | 175,264 |
| vote_classifications | 475 |
| vote_interpretations | 123 |
| support_position non-null | 97 |
| oppose_position non-null | 97 |

Pre-migration coverage:

| Chamber | Session state | Year | Rolls |
| --- | --- | ---: | ---: |
| House | null session | 2025 | 339 |
| Senate | mixed null/session 1 | 2025 | 285 |

No session-aware duplicate keys were present after assigning existing 2025 rows to session 1.

## Migration Applied

Applied migration:

```text
backend/migrations/0012_roll_call_session_identity.sql
```

The migration:

- backfilled `roll_calls.session`;
- required `session in (1, 2)`;
- made `session` non-null;
- replaced the old uniqueness constraint with `UNIQUE (chamber, congress, session, rollcall_number)`;
- added a session-aware identity index;
- preserved all existing row IDs.

Rollback artifact:

```text
docs/review_packets/current_congress_session_identity_rollback.sql
```

The schema rollback aborts if session 2 rows remain, so refresh rows must be removed before restoring the old single-session identity model.

## Source Cutoff And Fetch

Official source inspection found current 2026 activity through:

| Chamber | Source cutoff used | Cached source directory |
| --- | --- | --- |
| House | roll 222, 2026-06-11 | `backend/data_sources/house_clerk/2026` |
| Senate | roll 178 inspected; supported imported rows through roll 175 | `backend/data_sources/senate_xml/119_2` |

The refresh command fetches/caches sources under existing local source directories. Local source caches are operational inputs and are not intended as PR artifacts.

## Repeatable Refresh Command

Added:

```text
backend/app/etl/current_congress_refresh.py
```

Example dry-run:

```powershell
python -m app.etl.current_congress_refresh --house-latest-roll 222 --senate-latest-roll 178 --dry-run
```

Example fetch:

```powershell
python -m app.etl.current_congress_refresh --house-latest-roll 222 --senate-latest-roll 178 --fetch
```

Production writes require the exact bounded approval phrase built into the command. The command plans table effects before writing and is idempotent after a successful import.

## Refresh Preflight

Final preflight planned:

| Table | Planned inserts |
| --- | ---: |
| bills | 169 |
| legislators | 4 |
| roll_calls | 282 |
| votes_cast | 99,725 |
| vote_contexts | 99,725 |
| vote_classifications | 282 |
| vote_interpretations | 282 |

The 282 planned interpretation rows were conservative deterministic placeholders with `interpretation_status = insufficient_evidence` and null `support_position` / `oppose_position`.

Rollback artifact generated before write:

```text
docs/review_packets/current_congress_refresh_rollback.sql
```

The rollback is scoped to the exact session-aware 2026 refresh roll keys.

## Production Import Result

Actual inserted counts:

| Table | Inserted |
| --- | ---: |
| bills | 169 |
| legislators | 4 |
| roll_calls | 282 |
| votes_cast | 99,725 |
| vote_contexts | 99,725 |
| vote_classifications | 282 |
| vote_interpretations | 282 |

Post-import production counts:

| Table / input | Count |
| --- | ---: |
| legislators | 552 |
| bills | 436 |
| roll_calls | 906 |
| votes_cast | 274,989 |
| vote_contexts | 274,989 |
| vote_classifications | 757 |
| vote_interpretations | 405 |
| support_position non-null | 97 |
| oppose_position non-null | 97 |

Support/opposition inputs were unchanged.

## Coverage After Import

| Chamber | Congress | Session | Year | Rolls | Roll range |
| --- | ---: | ---: | ---: | ---: | --- |
| House | 119 | 1 | 2025 | 339 | 3-362 |
| House | 119 | 2 | 2026 | 216 | 2-222 |
| Senate | 119 | 1 | 2025 | 285 | 1-618 |
| Senate | 119 | 2 | 2026 | 66 | 4-175 |

The apparent gaps are unsupported or unavailable source categories under the current adapters and product semantics. They are deferred rather than guessed.

## Collision Validation

The corrected identity allows valid overlaps:

| Chamber | Roll number | Distinct session rows |
| --- | ---: | ---: |
| House | 4 | 2 |
| House | 175 | 2 |
| Senate | 4 | 2 |
| Senate | 175 | 2 |

This proves 2026 rows are not being attached to same-number 2025 rows.

## Timed-Out Write Recovery

An initial production write attempt timed out and raised concern about a stale database backend. After approval to terminate stale backend `1574486`, validation showed the process was already gone, no idle transaction remained, no target-table locks remained, and counts matched the pre-write state before the successful retry.

## Idempotency

Post-import dry-run planned zero additional writes:

| Table | Additional planned writes |
| --- | ---: |
| bills | 0 |
| legislators | 0 |
| roll_calls | 0 |
| votes_cast | 0 |
| vote_contexts | 0 |
| vote_classifications | 0 |
| vote_interpretations | 0 |

## Derived Precompute Refresh

Public deployment validation found that the fact/classification rows were present in production but not visible in public position/evidence endpoints because the latest precomputed fingerprint window still ended before the new 2026 rows.

The refresh workflow now supports a bounded derived-output stage:

```powershell
python -m app.etl.current_congress_refresh --house-latest-roll 222 --senate-latest-roll 178 --precompute-dry-run --as-of 2026-06-17
python -m app.etl.current_congress_refresh --house-latest-roll 222 --senate-latest-roll 178 --write-precompute --as-of 2026-06-17 --approval-phrase "<approval phrase>"
```

Precompute dry-run found zero existing rows for the `2026-06-17` window and planned:

| Table | Planned rows |
| --- | ---: |
| fingerprints | 4,416 |
| chamber_medians | 48 |
| drift_scores | 552 |
| summaries | 552 |

The bounded precompute write inserted/updated exactly those rows. A repeat run changed zero rows.

Rollback artifact:

```text
docs/review_packets/current_congress_precompute_rollback.sql
```

The rollback is scoped only to the `2026-06-17` / `v1` precomputed output window and does not touch facts, classifications, or interpretations.

## Guardrails

- No support/opposition methodology changed.
- No readiness methodology changed.
- No alignment methodology changed.
- Procedural context remains non-counting.
- Not-voting remains excluded.
- Parent-measure context does not replace amendment vote meaning.
- Unsupported categories are deferred.

## Unsupported / Deferred Backlog

This milestone did not broaden product semantics for PN nominations, treaty/executive votes, unsupported amendment handling, or ambiguous civic meaning. Those categories should remain deferred until a dedicated model and methodology decision exists.

## Tests And Validation

Targeted validation covered:

- migration/schema behavior;
- same chamber/Congress/roll number across two sessions;
- session-aware lookup/conflict behavior;
- Senate fact and amendment import session-aware state;
- current refresh planning;
- production read-only baseline and post-import validation;
- idempotency dry-run.

Final command results:

- targeted backend suite: 32 passed;
- production post-import invariant check: passed;
- post-import idempotency dry-run: passed, zero planned writes;
- derived precompute idempotency: passed, zero changed rows on rerun;
- `git diff --check`: passed with normal Windows CRLF notices.

## Next Operating Cadence

Use the refresh command as the repeatable path for current-Congress updates:

1. Inspect official House/Senate latest roll numbers.
2. Fetch/cache official source files.
3. Dry-run against production.
4. Generate/confirm rollback.
5. Write only after the bounded approval gate.
6. Validate actual effects and idempotency.
7. Deploy backend changes when importer/API code changed.

Recommended cadence: run this workflow after meaningful roll-call batches accumulate, or before product review cycles that depend on current evidence freshness.
