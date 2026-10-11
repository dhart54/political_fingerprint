# Education79 bounded release candidate

## Intent and outcome

Prepare the missing production persistence operator and a decision-ready release
request for the already reviewed same-source locator candidate. Keep observable
legislative meaning and all six card findings unchanged. No production execution
or editorial approval is part of this milestone.

## Baseline and authority

PR210 and PR212 integrated ordinarily at main
`1cd9d124e613bfcc891a650896487381544794ef`, combined tree
`638f7e4273f1d93771e482b73efe54422eaa6034`. Their reviewed heads are preserved.
Final-main nine-job backend CI, dedicated 89-case/Node proof and automatic Render
smoke passed. Production health names that main commit, and all nine captured
Education public responses remain exactly unchanged after integration.

This branch may prepare code, fixtures, proposed decisions and a draft PR. It may
not merge itself, assign real approval, persist production rows, change serving
card bindings, activate the registry, manually deploy, or change configuration.
Interpretation principles and the existing V2R contracts remain authoritative.

## Sequence and definition of done

- [x] Identify missing operator: existing Education adapter is fixture-only;
  historical M15B persistence operator covers different issue keys.
- [x] Add a narrow candidate using the existing immutable store and ID resolver.
  Require separate candidate approval, bounded persistence authority, exact head,
  exact bundle, fresh read-only baseline, protected-state checks and confirmation.
- [x] Prepare pending decision templates, exact caps, ID-capture and activation
  authority requirements, paired card/registry rollback and source-access limits.
- [x] Verify negative gates locally; actual lifecycle requires hosted PostgreSQL.
- [x] Obtain original exact-head hosted operator fixture proof and review the final diff.
- [x] Deliver separate draft PR213 with unresolved reserved decisions stated.
- [x] Correct the two independent P2 review findings: inherited routing/actual
  connection identity and unbounded waits/stale preflight after locks/scans.
- [ ] Obtain corrected exact-head hosted proof and renewed independent review.

## Validation and discoveries

Original local preparation/operator/filter checks: 114 passed; dedicated PostgreSQL lifecycle explicitly
skipped because local Docker Linux daemon is unavailable. The new CI job has its
own PostgreSQL17 service and fresh named DB, avoiding shared fixture writes.
The operator itself exposes no disposable/synthetic CLI option. In-memory fake
authority used by tests is visibly synthetic; production defaults reject it.

Original head 3873538 has positive dedicated hosted proof (run 38168994780,
artifact 11713390562, 23 operator cases). Ordinary backend CI at that head passed
eight jobs and failed M14H's ordinary header navigation test. The early initial
focus race is independently reproduced and fixed in separate draft PR214; it is
not weakened or hidden in this operator branch.

The corrected operator rejects inherited PGHOSTADDR/PGSERVICE/PGSERVICEFILE/
PGOPTIONS before connection, requires verify-full TLS and checks the actual
connected tuple before SQL. Connection/lock/statement waits are bounded at
10/5/60 seconds, observation/operation budgets at 120 seconds, and preflight age
remains 1800 seconds measured from its recorded observation start. Freshness is
rechecked immediately before insertion. Fake connectors and synthetic clocks
exercise these failures without any remote database connection. Certificate
trust readiness remains a later release prerequisite; no secrets/configuration
were changed. Corrected local preparation/operator tests: 68 passed, one dedicated
PostgreSQL lifecycle skipped explicitly; no local Docker Linux daemon. Corrected
exact-head hosted proof and review are pending.

No real positive approval exists. Candidate content SHA remains
`dde91335f2a125463024275930e173afb562df0746fe00c394452d7759bcb698`.
Current official response-body SHA is unverified: retained governed bytes prove
the prior source identity, and HEAD only proves prior observed availability.

## Rollback and reserved decisions

Failed persistence rolls back its owned transaction. Committed non-serving
immutable rows remain inert; no deletion/recovery action is exposed. Activation
rollback later uses the established full-row V2R compare-and-swap and paired prior
frontend manifest. Sequence advancement on failed inserts is not a guessed ID.

Reserved decisions: exact candidate/status approval, acceptance of source-access
evidence limits, operator engineering review/integration, specific bounded
persistence authorization, real ID and deployed binding review, separately sealed
activation/rollback authority, and acceptance of the temporary card-withholding
window. Production writes performed: none. Final reconciliation: pending review.
