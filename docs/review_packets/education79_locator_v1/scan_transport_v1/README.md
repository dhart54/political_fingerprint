# Education79 protected scan transport correction

Owner: voter reliability workstream, separate branch from verified main
577ce1ffeb8b9dfbcf323a937fa8ff69cb5f1426. Outcome: reduce named-cursor round trips
while preserving complete protected-row fingerprints and the reviewed safety gates.
No changed operator production execution, inserts, activation, schema/index/config
change or source-body fetch is authorized by this correction packet. Independent
review precedes any changed operator production execution.

## Observed diagnosis

The original fresh READ ONLY preflight ended at 2026-10-11T21:09:24.249874 UTC with
`StoreSafetyError: bounded observation/operation budget exceeded`, raised inside
`protected_state`'s per-row deadline check. Schema, registry and old-graph checks
had completed. The original receipt does not record table, row progress or exact
start time; those facts cannot be reconstructed from its stack trace. No sealed
persistence authority or persist invocation followed. The strict verify-full TLS
success and zero-insert receipt remain preserved in PR213 and the integration
worktree; this packet does not replace them or reuse the failed preflight.

Two subsequent explicitly bounded READ ONLY diagnostics used the unchanged original
main operator's target/TLS guards. Reports contain metadata only, no row contents,
credentials or connection strings:

- Catalog/EXPLAIN/limited fetch diagnostic: 5.953030s total, 5s statement timeout.
  SELECT1 median round trip 29.993ms. Statistics estimate 814,963 rows each for
  vote_context_members and votes_cast; these are estimates, not complete counts.
  EXPLAIN without execution shows the existing JSON conversion, sequential scan
  and full row_text sort. The first128-row fetch on vote_context_members reached
  the 5s statement timeout, so that attempt yielded no page timing.
- Refined limited fetch diagnostic: 35.971631s total under a 45s cooperative budget
  and 20s statement timeout. On the same original sorted query, first-page costs
  were 18.434086s at 128 rows and 16.019354s at 4,096 rows. Subsequent128-row pages
  took 40.062–85.907ms; subsequent4,096-row pages took 123.956–137.186ms for about
  1.29MB UTF-8 data. Exact hash work for a 4,096-row page took 1.823–1.978ms.

These measurements establish substantial page round-trip overhead and a separate
first-page sorting cost. They do not identify the original failed table or prove
complete production two-scan readiness. At the estimated cardinalities, 128-row
transport needs about 12,734 pages across the two vote tables for one full scan;
4,096 rows reduces that to about 398. Persistence requires both its before and
post-insert scans within the same unchanged 120s budget. No scan is removed.

## Scoped implementation

Use a fixed 4,096-row ServerCursor.itersize. This changes only transport batching:
retain every public table, exact SQL order, all exclusions, every UTF-8 row_text
plus newline byte and per-row deadline check. Add optional caller-owned timing
lists for query, retrieval, hashing, table/row/byte progress and failure. Timing
metadata stays outside state, baseline envelope and stable/preflight digests.
No CLI argument, baseline schema or transaction/authority contract changes.

Installed Psycopg 3.3.3's ServerCursor iterator sends FETCH FORWARD itersize; this
works with installed libpq 16.9. Do not use chunked Cursor.stream(size>1), whose
[documented capability requires libpq 17](https://www.psycopg.org/psycopg3/docs/api/cursors.html#psycopg.Cursor.stream).
Batching imposes a row cap, not an absolute byte cap; measure wide decoded pages
and process peak memory in the fixture rather than claiming a universal byte bound.

## Validation and completion gates

- [x] Pure tests compare old/new complete fingerprints and exact SQL/parameters
  for empty tables, duplicate strings, null/Unicode/escaping, wide rows and batch
  boundaries through 8,193 rows. A changed last row changes the full fingerprint.
- [x] Negative tests reject deadlines within a page, post-insert budget expiry and
  post-insert stale evidence; timing cannot change the baseline envelope/digests.
  Existing route/TLS identity, synthetic-authority and fixed-cap rejections remain.
- [ ] Hosted disposable proof: synthetic 815,000-row context and vote tables plus
  8,193 wide Unicode/null/duplicate rows; old 128 and new 4,096 complete state/count/
  hashes must match. Measure an actual serializable persistence's two full scans,
  injecting 40ms per server FETCH (no bandwidth emulation), under the unchanged 120s
  budget. Verify failed-transaction rollback, unchanged registry, exact caps,
  bounded decoded batch memory and process peak resident memory. Retain timings
  as a separate artifact. Existing drift/ownership/idempotency lifecycle still runs.
- [ ] Exact-head hosted validation and independent review before integration.

The hosted proof is a representative workload and latency model, not a guarantee
of production bandwidth, server load, sorting or memory. Before any later execution,
rebuild bundle and approval/authority bindings against the independently reviewed
new head, capture a new valid bounded READ ONLY preflight, and satisfy all existing
guards. Never reuse the failed baseline or old-head execution bundle. Production
persistence/activation remains outside this engineering PR's authority.
