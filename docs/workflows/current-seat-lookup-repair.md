# Current-seat lookup repair review

## Scope and contract

ZIP lookup describes currently stored officeholders, while name search and direct
member profiles retain historical records. Filter House and Senate ZIP selections
by the existing `legislators.in_office` flag. When more than one House member is
marked current for a seat, return the existing nullable House field rather than
choose an occupant by insertion order. Null means no uniquely resolved current
member in this lookup, not an authoritative vacancy determination. Explicit demo
ZIP and race lookups follow the same rules.

No schema, publication registry, editorial interpretation, historical vote, or
production data changes are included. Historical name/direct member retrieval is
unchanged. A current status flag is not a day-level service interval and must not
be used to infer absence from historical roll calls.

## Validation

`backend/tests/test_current_seat_lookup.py` executes the actual production SQL
against a disposable in-memory SQLite fixture (only placeholder syntax is
adapted). It covers successor selection with lower-ID former members, duplicate
active House rows, no current House member, unknown status, Senate filtering,
historical retrieval, query failures, and fixture parity. This is SQL behavior
coverage, not a PostgreSQL integration claim.

Focused backend suites cover lookup, positions, DB read layer, ZIP payload parity,
public-record failure behavior, and ZIP member readiness. Database URL is set to
`postgresql://invalid`; no production writes are permitted or required.

## Separate data prerequisite

The November 6 read-only candidate audit found Scott (GA-13) and Swalwell (CA-14)
still flagged current and their successors absent. This code does not make those
rows fresh. Inserting successors alone will produce an unresolved House result,
not silently select the predecessor. A separately authorized, bounded data repair
must reconcile current status and successor identity with official evidence,
preserve predecessor records, and validate rollback before production execution.
The July 13 stored vacancy snapshot is historical evidence, not current proof.

Exact term ends and oath dates belong in source-backed preparation. The existing
member-service evidence schema supports year precision only; do not invent exact
service intervals in it or reinterpret Not Voting as physical absence.
