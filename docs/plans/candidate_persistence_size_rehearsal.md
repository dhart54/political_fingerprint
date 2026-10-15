# Candidate persistence capacity rehearsal

Intent: assess candidate-package database growth against the supplied Green
19:08:41UTC baseline and350/400/500MB thresholds, without production access.

Base: verified current main af6cd6d78d6944d64a68a92653066c4c1625f96b.
Immigration input: pushed checkpoint238 a327f4ccd6f5d95ea12331bb91a8606382a59e50.
Health input: qualified candidate files on exact main; audit scope is candidate
quality, not editorial acceptance. Both contain F000477 and M001184.
Own worktree .w/cps, scoped branch codex/candidate-persistence-size-rehearsal.
Source support .w/vhi and active .w/ib remain untouched.

Boundaries: no installs, shared-schema/data changes, production connections,
candidate edits, approval-state rewrites, publication, merge or deployment.
Use only an entirely new local PostgreSQL17.5cluster, localhost-only, then stop.
Do not delete existing data. Docker daemon is unavailable; no startup required.

Discovery: current pipeline and adapter reject candidate persistence. Therefore
there is no authorized Health/Immigration persistence package to import. Existing
approved M15B packages select presentation+source-manifest+validation, not entire
research directories. A future accepted candidate selection is a separate decision.

Rehearsal policy: measure the exact seven generated JSON files per domain plus a
file-reference manifest in the existing immutable-store schema/import function.
This intentionally redundant candidate-review mirror is a hypothetical capacity
proxy, not a new production representation or an approved public artifact. Retain
candidate JSON/status unchanged; use pending/nonpromoted/ineligible metadata.
Exclude raw research/source banks and authoring/history unless a separate later
selection includes them. Explicitly inventory excluded bytes and remaining unknowns.

Sequence and definition of done:

- [x] Read contract/importer/gates and verify pushed inputs/ownership.
- [x] Discover already-installed PostgreSQL; inspect exact store DDL/indexes.
- [x] Inventory exact payloads, hashes, retained-version/idempotency behavior.
- [x] Measure compatible subsets separately/combined with heap/index/TOAST and v2.
- [x] Round-trip/importer idempotency, unchanged source/gates, private-server stop.
- [x] Record capacity scenarios, timing/failures and full-package boundary.
- [x] Exact-index receipt verification and documentation-only draft PR readiness.

Validation: exact source hashes and JSON round trips, existing insert_bundle,
actual0016DDL/indexes/immutability, zero registry rows; no full candidate suite.
Canonical FK fixture scaffolding is explicitly local-only and outside measured
artifact-table deltas. No model/tier/configuration change or cold-cache claim.

Supabase documentation fetch initially failed in web tool (Markdown content type
and inaccessible page); use one direct official retrieval and record outcome.
Incidental guessed missing persistence.py and native-rg wildcard failures are
tooling overhead, not product failures. Oversized inspection output recorded.

Production writes: none. Recovery: stop only the uniquely created local server;
retain its private data/logs and receipts for audit; remove no existing database.
Four failed attempts are preserved: restricted-token startup, inherited-PIPE
capture/interruption, locale-setting probe and actualJSONBU+0000rejection.
Complete generated mirror cannot import unchanged. No sanitization/candidate
edits: entire incompatible artifacts are listed and excluded only from an
explicitly incomplete subset measurement. This is a specific full-package
measurement boundary, not an assertion about candidate semantic quality.

Result: subset artifact-table growth13.16MBImmigration/8.95MBHealth/21.96MBcombined;
retaining an identical-copy v2 adds21.76MB. Allcreatedservers are no longer running;
preexistingOct9services remain untouched. Production connections/writes zero.
Actualapprovedcandidateimportmanifeststillabsent; fullfuturecapacityuncertified.
Preserve350/400MBtriggers and qualify actualselectedpayloadsbeforeanypersistence.
Final reconciliation: requested assessment/partial receipt complete with explicit
boundary; exact-head verification/draft PR URL are recorded in the delivery after this source snapshot.
