# Actual M15B replacement preparation

Merged PR #186: `5843bab9b1bed3e5db57976bae3b05466f2cbafe`, accepted
head `e223bbf676c1762337c03bc3af0e78801c14f698` on the exact reviewed base.
All accepted-head checks passed. Documented Render hook/Uvicorn and Vercel
build integrations are code-only; no manual deployment is requested.

Outcome: one reviewable persistence-authorization package for the actual NS
and Justice content. Production writes, activation, migration, rollback and
merging the preparation PR remain unauthorized.

Sequence: capture fresh read-only exact production baseline; form two bounded
immutable graphs using existing persistence; prove actual payload lifecycle in
the existing disposable PostgreSQL infrastructure; run release checks; present
one draft PR with commands, counts, recovery and unavailable activation inputs.

Scope: preserve accepted payloads and historical files, raw data and protected
untracked ZIP. No semantic generation or new publication framework. Tests use
only explicit loopback credentials, never production environment inheritance.

Validation: persistence counts/content/idempotency; exact independent registry
updates and rollback; real API/selector output in 119/all; additional unreviewed
ledger rows and controls; authority/identity/provenance/ownership failures;
injected transaction failure; other-table fingerprints; historical/release CI.

Expected footprint: bounded package/operator, persistence parameters if needed,
read-only capture, actual payload test, existing CI lane, plan/review packet/data.
New production IDs and sealed activation authority remain unresolved by design.

Progress:
- Fresh read-only production capture and both exact persistence preflight commands
  passed. Old NS 227 and Justice 221 are exact; all proposed artifacts are absent.
- Actual approved graph packages, derived 1/3/2 per-domain insert caps, independent
  commands and exact owned recovery are consolidated in the review packet.
- Existing snapshot replay now includes the eligible source rows needed by global
  scope headers, without acquiring another member's votes. Full captured public
  output replays exactly; no comparison is weakened.
- Actual payload persistence, sequential replacement, zero-write repetition,
  drift/authority rejection, transaction rollback, public 119/all behavior,
  protected tables, exact publication rollback and persistence recovery passed
  hosted PostgreSQL at afdc8c02cb9034c515157c2d8b570c9a060fed0c, run 34916596571.
- Historical call-time store defaults are preserved; historical and release jobs
  passed. The final commit additionally makes unchanged receipt/control assertions
  explicit and pins the reused CI lane to the PR head. Final exact-head results
  belong to draft PR #187 and must pass before the final readiness disposition.
- Merge-triggered backend health serves merged main. Its legacy Alex Morgan smoke
  route returns 404; recorded as a smoke follow-up, not folded into this milestone.

Persistence authorization blockers after final green validation: none identified.
Later activation gates remain unresolved: production IDs, fresh deployed-runtime
and execution-preflight evidence, and separate sealed human activation authority.
Production writes performed: no. The protected untracked ZIP was not accessed.
