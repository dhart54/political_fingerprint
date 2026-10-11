# Exact ordered single-row stream correction

Owner: voter reliability workstream. Separate feature branch from verified main
7794e8226d935bc08ae673e7aec447e7fe7f40f1. Outcome: reduce stop-and-wait transfer
without changing any protected-state fingerprint or execution gate. Estimated
scope: reader, focused tests/model, this review packet. No production use or merge
until independent review; no activation, schema/extension/security/trust/config,
architecture, evidence meaning, counting, authority, budget or rollback change.

## Verified problem and measured basis

PR215's COMPLETE actual production preflight covered 28 tables/1,663,292 rows in
73.918s. Protected scans alone took 72.787s; two equal-cost passes estimate 145.573s,
exceeding the unchanged 120s budget. No persistence authority or inserts followed.
vote_context_members took 42.041s and votes_cast 25.676s; their combined retrieval
bucket was 66.127s versus 0.903s hashing. Retrieval combines sort, transfer and decode.
Increasing 4096 to 16384 rows saves only ~17.9s RTT across two passes and does not
establish sufficient margin. Monolithic ordered string_agg risks ~501 MiB+ buffers;
it is not a bounded-memory transport replacement. Original failure, strict TLS,
candidate decision and admission-rejected complete baseline remain in PR213/215
and .w/eint/.w/eos. Do not reuse those baseline/head bindings for new execution.

One prior isolated native PG17.5/Psycopg3.3.3/libpq 16.9 comparison modeled 379,493,362
bytes EACH full pass at 12 MB/s and 29.993ms RTT. It measured actual serializable
two-scan insertion followed by rollback: batch4096 took 117.975s; prototype stream1
took 77.930s. Complete reference state/count/hash equality, cleanup and rollback
passed. These are modeled disposable times, not production timing or clearance.
Fixture server/locale/hardware differ. A discrepancy sensitivity adds the observed
14.213s production-versus-modeled batching gap to EACH stream scan, giving 106.355s;
that assumption does not guarantee actual margin. Retained prior receipt:
prior-disposable-comparison.json (SHA 8dd81d087c0ea38acaa91683d2185985cd001e47362a1377fd40167813b1dea1).

## Implementation boundary

Use ordinary Cursor.stream(size=1), supported on libpq 16, with the identical
SELECT, row_text ordering, own-batch exclusions, full public tables/rows, UTF-8
row_text plus one newline and SHA256/count result. No chunked size>1 or new
dependency. Existing production routing/actual TLS guard, fresh sealed authority,
120s cooperative deadline, 60s statements, 5s locks, 10s connect, 1800s freshness,
1/3/2 caps, owned serializable transaction and rollback remain unchanged.

Explicit closing(stream) encloses consumption even when row hashing, SQL/network,
deadline or BaseException interruption rejects the operation. The pinned driver's
finally cancels/drains ACTIVE results; the cursor then closes before the caller's
rollback. A lost socket cannot be made reusable: owned connection closes and
transaction abort is verified from a new guarded fixture handle. No exception is
suppressed by the reader and no partial result is returned as a valid fingerprint.

Diagnostic list is caller-owned and outside baseline.state, the exact envelope
and digests. Setup time measures lazy iterator creation; first-row time includes
initial SQL/server startup/sort/transfer; fetch time includes full retrieval/decode;
hash time is separate. Empty tables have no first-row time. No row contents or
connection-string/credential values are logged. A streaming table SELECT must
satisfy the same 60s timeout as one whole statement; no per-FETCH timeout reset.

## Validation and next gates

- [x] Pure full-count/hash tests for empty/duplicate/null/escaping/Unicode/wide
  records, historical 128/4096 boundaries, changed last row and exact exclusions.
- [x] Fake libpq 16-compatible adapter refuses size>1. Deadline advances between
  individual rows, not only a page boundary. Hash/read/SQL/network/interruption
  negatives assert the ACTIVE stream closes and no valid partial state returns.
- [ ] Actual PostgreSQL negative cases: hash rejection AFTER INSERT, SQL error,
  whole-statement timeout, per-row deadline, early interrupt and fixture socket
  loss; connection reuse after nonfatal rollback or closed broken handle, no graph.
- [ ] Exact-head full fixture proof compares the frozen128-row reader with the
  implementation across all rows. 815k context +815k vote rows +8,193 wide rows;
  model 379.5MB/12MBps/29.993ms per full pass. Two COMPLETE scans under one 120s
  serializable persistence window before forced rollback; exact caps, registry,
  ownership/drift, stale/budget-after-insert and zero-write repeat remain tested.
- [ ] Review exact diff and hosted head/artifact before independent review.

This engineering candidate grants no production approval. After independent review
and separately instructed integration, rebuild bundle/execution bindings at that
exact integrated head, run a new actual complete READ ONLY preflight with separate
timings, and assess BOTH scans plus final checks before any approved inert write.
If margin remains inadequate, stop persistence; never widen 120s/reduce coverage.
Stage2 activation, registry/frontend writes and validation-only PR209 stay excluded.
