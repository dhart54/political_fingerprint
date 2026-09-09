# M15A.2: source-verified core repair preparation

Baseline: `8cd2d6ee1fd31e876c0d1c67b7516f6405f1d67d`.

Outcome: prepare a content-bound, fact-only repair of the exact 31 user-listed
missing reviewed actions. Preserve exact identity, all different-session records,
accepted interpretations, and Education's 17-reviewed plus current raw ledger.
Production reads only; no production writes, merge, deployment, or acceptance.

Sequence and gates:
1. Retrieve and pin official Clerk bytes and roster. Independently validate all
   identities and member votes, then compare active publication lineage. Stop on
   any source discrepancy before preparing writes.
2. Capture an explicitly read-only production baseline and protected dependencies.
3. Reuse the Justice fact-repair pattern for a narrow bundle, exact caps, future
   executor, and ownership-bound rollback. No generic repair framework.
4. Prove public before/after behavior, drift rejection, idempotency, fault rollback,
   and explicit rollback in disposable PostgreSQL. Run relevant regressions.
5. Review the diff and open one draft PR; stop after hosted CI for independent review.

Expected footprint: one scoped operator, focused tests, pinned source evidence,
small review bundle and this plan; use the existing repair PostgreSQL CI lane.
Completion requires source validation, exact reproducible write graph, disposable
lifecycle proof, and draft PR. Planning and source acquisition alone are not done.

Production write envelope: zero. Future repair rollback must remove only exact
repair-owned rows and preserve reused dependencies. No rollback will run on production.

Progress and validation:
- Bounded connectivity recovery succeeded on the first attempt using unchanged
  production configuration: DNS, TCP, TLS, authenticated session and READ ONLY
  SELECT 1 passed. Preparation resumed without a new milestone or checkpoint.
- All 31 pinned Clerk identities and F000477 votes reproduce exactly. The source
  manifest remains 7e19a1ad8e2b9dbeb6dc442ed5bac1a4e81c0244193d0f84bf5d62bd03aa0d27.
- Fresh READ ONLY production capture at 2026-09-09T00:22:27.255231+00:00 verified
  active National Security, Environment and M14 Education lineage. All 31 votes
  match their active reviewed publications; all target core actions are absent.
- Fresh dependencies establish 14 reused bills, six missing bills, and 26 protected
  different-session collisions. Exact insert caps are 6/31/31/31 for bills,
  roll_calls, votes_cast and vote_contexts; every other write is zero.
- The non-authorizing bundle and production-shaped fixture are complete. Flags
  accepted, sealed and production_database_write are all false.
- 38 source/disposable tests passed, including HTTP 503 before and 200 after,
  discovery/detail reconciliation for 119/all, exact accounting, partial/conflict
  rejection, protected drift, six fault stages, receipt durability, idempotency,
  ownership-only rollback and unrelated-append preservation.
- 234 existing backend regressions and 41 frontend regressions passed. No frontend
  or public runtime implementation changed.
- The existing receipt-evidence-repair-postgres CI lane now includes this isolated
  proof. No duplicate permanent job was created. Hosted results belong to the
  single draft PR; obtaining and checking those results is the final step.

Material discoveries and corrections:
- Initial baseline work unnecessarily hashed global vote tables and encountered
  connectivity failures. Counts now use aggregate COUNT; fingerprints are scoped
  to protected dependencies. The resumed baseline and fixture completed normally.
- Current roster parties cannot describe every historical vote. The narrow source
  preparation now uses the exact roll's recorded party attributes with the
  established context builder separately per roll. All 31 party totals are
  independently compared to official recorded votes. No global ETL or accepted
  interpretation semantics changed, and no Foushee source vote discrepancy arose.
- PostgreSQL fingerprints explicitly sort with C collation for repeatability on
  Windows PostgreSQL 17 and hosted Linux PostgreSQL 16.
- Repair-owned rows are saved durably before commit; storage failure aborts the
  transaction. Rollback checks both exact target IDs and complete row fingerprints,
  and rejects new dependents. PostgreSQL sequence gaps are allowed, never rewound.
- Normal shared coverage metadata extends only to the exact latest inserted
  source date. Education/Justice receipt content and accounting remain unchanged;
  all accepted presentation wording and findings remain byte-for-byte equivalent
  as parsed JSON. Interpretation principles govern this evidence boundary.

Reconciliation and rollback:
- Disposable National Security changes from missing-record 503 to 82 reviewed
  actions resolved; Environment changes from 503 to 63 reviewed actions resolved.
  Both 119/all return 200 with matching discovery/detail counts.
- Education 119 remains 25 available = 17 reviewed + 8 unreviewed; Justice is
  unchanged. Existing publications and accepted artifacts are preserved.
- Repeated apply returns ALREADY_APPLIED with all write counts zero. Explicit
  rollback deletes only the 6/31/31/31 owned rows and restores the exact relevant
  baseline and pre-repair public state. Faults roll back transactionally.
- No production rollback is run or needed: production database writes performed:
  no. No merge, deployment, publication, approval or authority sealing occurred.
- Hosted CI first exposed a missing httpx test dependency and historical tests
  requiring earlier job blocks verbatim. The new proof now appends a step inside
  the existing repair job, preserves its earlier block, and installs httpx there.
  Both directly affected workflow-preservation tests pass. An additional local
  M14 run had 56 passes and 10 setup errors due solely to unchanged Windows CRLF
  fixture bytes; hosted Linux checks verify those exact-byte acceptance cases.
- No implementation blocker remains. The review checkpoint is one commit and one
  draft PR with hosted CI, followed by independent review. Production apply needs
  separate explicit authorization and the reviewed bundle digest.
