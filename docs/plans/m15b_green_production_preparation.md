# Green production and M15B persistence preparation

## Authority and scope

The 2026-09-15 user request accepts the green cutover, authorizes merging PR189,
its normal deployment, and resumption of previously permitted normalized writers
after production verification. It authorizes a fresh M15B preparation and
disposable lifecycle proof, not production persistence, activation, registry
mutation, persistence rollback, blue modification or another migration.

PR189 merged at `f790163f90b8a71fae2bee3206f73953364f1e72` from the exact accepted
head `3f37b2bfe193e77f91754621fd67e15b7163663c`; prior main was
`638eac771e2d32db27258716c6334e2a7d7ea089`. Green is
`yalpfkaxkxebwolhorha`; blue `wfhnmuxlbfpweupisfao` remains untouched.

## Implementation and validation

1. Verify the post-merge runtime, green provenance, normalized flag, current
   schema/size, four registry roots, unchanged public output and Vercel API URL.
2. Record green as the target for already-permitted normalized producers. Do not
   manufacture a write. After new green writes, blue is a recovery checkpoint;
   any rollback requires separately authorized reconciliation.
3. Reuse the earlier M15B immutable-persistence preparation from branch
   `codex/m15b-production-preparation`, preserving the approved semantic payloads.
   Bind a separate new evidence directory to green and merged main. Preserve
   historical M14H/M15B/PR189 evidence and historical target defaults.
4. Capture bounded green baseline read-only: exact old identities, registry,
   required provenance, sequences, normalized schema and current public output.
5. Derive the actual per-domain write set, expected to contain one batch, three
   artifacts and two relationships, with no registry or raw-data writes. Leave
   future production IDs unresolved.
6. Prove actual persistence, idempotency, conflict/drift refusal, pre-publication
   recovery, disposable V2R activation, approved output and owned rollback on
   normalized PostgreSQL17. Run relevant normalization/producer, semantic,
   publication, frontend and historical regressions and exact-head hosted CI.
7. Run the exact final-code/package production preflight read-only, open one
   draft preparation PR and stop for explicit production-persistence authority.

Expected footprint: roughly 10–14 implementation/test/documentation files plus
bounded generated baseline/package/review evidence. No historical regeneration.
The existing immutable store and V2R governance remain the persistence and
activation architecture.

## Progress

- Exact PR/main/CI gate passed; PR189 merged with the established merge method.
- Post-merge green provenance and105-response public smoke passed.
- Fresh baseline/package and actual normalized PostgreSQL17 lifecycle passed.
- Final-head hosted CI and read-only preflight are remaining delivery gates.
- No routine ingestion was due or executed; no production application or M15B
  write is part of the preparation proof.

## Definition of done

Verified green production at merged main; preserved blue recovery checkpoint;
unchanged accepted NS/Justice payloads; target-bound package with exact caps and
owned recovery; passing actual normalized lifecycle and relevant CI; passing
read-only green preflight; exact later persistence/recovery commands and one
consolidated authorization-gate report.
