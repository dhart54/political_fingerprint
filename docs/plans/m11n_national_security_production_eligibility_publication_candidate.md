# M11N National Security Production Eligibility and Publication Candidate

## Intent

Prepare, but do not execute, the exact production-eligibility and publication
activation candidate for Valerie Foushee's accepted 119th-Congress National
Security & Foreign Policy presentation.

## Scope and boundary

- Exact base: `b12a0939b4452fb9dcc9ae150d8159ec0a18b6bd`.
- Bind the accepted M11M artifact, subject digest, and file digest exactly.
- Reuse the existing immutable artifact batch, relationship, publication
  registry, selector, rollback, and drift-guard mechanism.
- Preserve M11L semantics and wording and the accepted M11M presentation.
- Keep H.R. 8800 / `house:119:2:278` source-blocked and outside findings.
- Do not write production, mutate the publication registry, deploy, or activate
  publication in this milestone.

## Definition of done

- A detached authority records production eligibility while explicitly leaving
  production writes, registry mutation, deployment, and activation false.
- A deterministic write set identifies the exact future rows and natural keys.
- Fresh read-only production preflight proves the deployed commit, counts,
  active Justice row, selector state, and state fingerprint.
- Disposable-database validation proves apply, idempotency, rollback, drift
  rejection, Justice isolation, and exact state restoration.
- Unit, API, artifact, schema, formatting, compilation, and diff validation pass.
- A draft PR is opened and work stops for independent ChatGPT review.

## Implementation progress

- [x] Merge accepted M11M and capture exact post-merge main.
- [x] Inspect the existing Justice publication mechanism and production runbook.
- [x] Capture current production state in a read-only transaction.
- [x] Build content-bound authority, expected write set, and review packet.
- [x] Add fail-closed selector/API integration behind the absent registry row.
- [x] Add unit, adversarial, hosted disposable-Postgres, and workflow coverage.
- [x] Complete validation and inspect the final diff.
- [x] Commit the bounded candidate branch.
- [x] Push, open the draft PR, verify hosted CI, and stop for review.

## Current production state

Production remains at four batches, 146 artifacts, 159 relationships, and one
publication-registry row. Justice is that sole active row. National Security is
receipts-only for `118`, `119`, and `all`. The exact state fingerprint is
`2388462c457136a23ed043c4295dd1f26a6ab8bf935f616aa56f77531f8fe6db`.

## Expected future write set

If separately authorized after review, activation would insert one batch, three
artifacts, two relationships, and one additive National Security registry row.
It would update no registry row, delete no activation row, and touch zero Justice
rows. Rollback deletes only those bounded rows and restores the exact preflight
counts and state fingerprint.

## Production effects

None. M11N performs production reads only. Production `dry-run`, `apply`,
`postcheck`, and `rollback` require an exact sealed positive activation authority;
none has been accepted or materialized.

## Authorization-closure correction

The accepted M11N authority remains candidate-preparation authority. It retains
false authorization for production database writes, registry mutation,
publication activation, and deployment, and cannot make a row publicly
selectable. A distinct positive activation contract now binds the exact M11M
content, preparation authority, finalized write set, fresh preflight, actual live
runtime health proof, production target, registry target, presentation digest,
reviewer authority, and rollback. The governed decision form is intentionally
unsealed and unaccepted pending independent review.

The public selector fails closed unless both authority layers validate. The
future production command also requires the finalized write-set digest, sealed
positive-authority digest, exact production target, fresh runtime-bound
preflight, and explicit operation confirmation. Disposable tests alone may opt
into a clearly marked synthetic authority.

The intended later sequence is:

1. Merge and deploy the accepted runtime while the National Security registry
   target remains absent.
2. Confirm National Security remains receipts-only and capture the actual live
   backend commit from `/health`.
3. Bind that proof to a fresh read-only production preflight and finalize the
   exact write set and positive authority.
4. Stop for a small mechanical ratification of those exact identities.
5. Only after ratification, apply the bounded graph, perform the full exact-graph
   postcheck, verify the live API, and retain the exact rollback path.

The full postcheck verifies the batch, all three artifacts, both relationships,
the additive registry row and both authority bindings, global counts, Justice,
and the fingerprint of every pre-existing non-M11N row. A second apply performs
the same postcheck; rollback must restore the original complete fingerprint.
