# Decision request: exact Education79 locator release

This is a proposed bounded release, not execution authority. PR210/212 merged
only inert preparation; no real positive candidate or persistence approval is
present. The operator candidate is separate and must be independently reviewed.

## Exact scope to approve or defer

Only Foushee / EDUCATION_WORKFORCE, action `house:119:1:79`, source identity
`govinfo:CREC-2025-03-25-pt1-PgH1241:amendment-3` is in scope. Replace the existing
GovInfo details locator with its same-identity HTML locator. Candidate content
SHA is `dde91335f2a125463024275930e173afb562df0746fe00c394452d7759bcb698`.
The existing root 245 and source/validation children 246/247 remain untouched.
17 receipts, all meanings, statuses, counts and six card findings stay unchanged.
The expected public change is exactly six URL leaves across Education evidence
and editorial responses in all/119; 118, positions and other domains/members stay
unchanged.

Retained governed bytes have SHA
`eaafafb53de434c894f475a864a1cd951118a32f2f98e1e487109f7ef71f5b32`.
Previously permitted retained body bytes matched; the availability observation
was HEAD 200 only. **The current live response-body hash is unverified.** Approval
must explicitly accept that limited source basis or defer publication pending
permitted exact-body verification. No repeated restricted fetch, source proxy,
Congress API substitution or parent-measure meaning inference is proposed.

## Separate decisions and caps

1. Approve the exact candidate and final immutable insertion statuses for all
   three graph rows: human_approved, gold_benchmark, production_eligible=true.
   Those statuses cannot be assigned by merge, passing tests or pending-row UPDATE.
   `candidate-approval.request.json` is incomplete and unsealed; the operator
   rejects it. A real reviewer/time/artifact identity and separately sealed
   approval must be supplied after this decision.
2. Review/integrate the operator candidate, then authorize its exact reviewed
   production bundle and fresh baseline. Persistence caps: one batch, three
   immutable artifacts, two relationships, zero registry updates, zero other
   row updates/deletes. Only editorial_artifact_batches, versions and relationships
   may receive inserts; all prior rows and all other public tables remain unchanged.
   No schema/configuration/auth/secret/production interpretation mutation.
3. After persistence, review captured real IDs and the separately prepared card
   source binding, write set and positive activation authority. Fixture 257/258/259
   and fixture batch 26 are never production identities or authority.
4. Separately authorize the coordinated publication window: zero artifact/batch/
   relationship inserts and exactly one full-row compare-and-swap registry update
   at the existing Foushee/Education key. Preserve the established V2R authority,
   runtime, fresh read-only preflight and rollback gates.

Candidate approval does not authorize persistence. Persistence does not authorize
activation. No real positive decision is created by this packet or its templates.

## Operator candidate and ID capture

`backend/scripts/education79_locator_operator.py` accepts only the approved Green
target, exact clean reviewed head and exact bundle digest. It uses the existing
immutable insert/ownership contract. A separate accepted/sealed persistence
authority binds the candidate approval, exact source head, target, fresh stable
baseline, mutation caps and rollback policy. Production defaults reject every
synthetic candidate, authority and preflight object before mutation.

Preflight runs repeatable-read READ ONLY and records the complete prior registry
row, old graph eligibility, normalized schema fingerprint, full public-table
checksums/counts, and absent-or-exact-owned candidate graph. Evidence has its own
digest and a 30-minute freshness bound. Persistence locks the exact registry row,
checks that baseline again, inserts through the existing store in its owned
serializable transaction, and verifies actual counts plus all protected prior
rows/tables. Failures abort the transaction. Exact repeat is zero-write idempotent;
other baseline or graph drift requires review rather than retargeting.

After commit, `resolve` is READ ONLY. It resolves IDs only from the complete exact
owned batch and eligible graph, checks the unchanged old registry, and calls the
existing V2R builder with the separately reviewed runtime binding. It emits an
unapproved write-set candidate; it never seals activation authority. Keep its
report and proposed frontend manifest for independent review before any serving
change. No real positive files under `release/` currently exist.

Future commands are templates; do not run them under preparation authority:

```powershell
python backend/scripts/education79_locator_operator.py build --approval release/approved-candidate.json --expected-code-head <reviewed-head> --report-path release/bundle.json
python backend/scripts/education79_locator_operator.py preflight --bundle release/bundle.json --bundle-sha256 <reviewed-bundle-sha> --expected-code-head <reviewed-head> --database-url-env <approved-green-variable> --report-path release/fresh-persistence-preflight.json
python backend/scripts/education79_locator_operator.py persist --bundle release/bundle.json --bundle-sha256 <reviewed-bundle-sha> --expected-code-head <reviewed-head> --database-url-env <approved-green-variable> --preflight release/fresh-persistence-preflight.json --authority release/sealed-persistence-authority.json --report-path release/persistence-receipt.json --confirm-production-persistence
python backend/scripts/education79_locator_operator.py resolve --bundle release/bundle.json --bundle-sha256 <reviewed-bundle-sha> --expected-code-head <reviewed-head> --database-url-env <approved-green-variable> --runtime-binding release/reviewed-runtime-binding.json --report-path release/write-set.candidate.json
```

Resolve the existing approved secret variable locally without printing its value.
NORMALIZED_VOTE_STORAGE must already be 1; this packet does not change configuration.

## Coordinated serving change and rollback

Real root ID, natural key, version, content SHA and both presentation hashes must
be reviewed together in the serving card manifest. Both source directions expose
a temporary interval: backend-first makes the old frontend withhold all six
findings; frontend-first withholds them until the new backend registry matches.
Neither direction is a no-gap release. Receipts remain the established evidence
surface; no new dual-source fallback or interpretation adapter is proposed.

Stage the reviewed frontend PR, actual ID capture, exact sealed V2R write set,
positive activation/rollback authority and paired prior manifest/registry row
before starting. Let the normal approved merge trigger deployment; do not invoke
a manual hook. Fresh deployed backend/frontend submanifest evidence and a fresh
READ ONLY V2R preflight must match the sealed authority before the one-row apply.

Proposed response deadline: begin paired rollback after five minutes of card
withholding, or immediately on a failed binding/check. This is a rollback trigger,
not a guaranteed availability cap: restoration depends on automatic deploy
latency. The reviewer must accept that bounded execution plan and residual delay
risk, or defer for a separately authorized release mechanism. Record actual start,
withholding, restoration and deployment times.

Activation rollback restores the exact prior registry row through owned V2R
compare-and-swap and restores the reviewed prior frontend manifest through normal
merge/deploy. Restoring only one side can keep the card withheld. Newly committed
immutable artifacts remain inert and retained; there is no production deletion
entry point. A competing registry change stops rollback for review.

After apply/rollback compare complete public responses, both scopes, all six card
findings and finding/receipt/source return paths with the exact prediction; 118,
positions and other members/domains must remain unchanged. At any mismatch stop
and preserve evidence. Read-only recapture cannot grant stable human authority.
