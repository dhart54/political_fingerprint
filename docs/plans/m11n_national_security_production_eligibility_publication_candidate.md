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

None. M11N performs production reads only. Its command surface rejects production
`dry-run`, `apply`, and `rollback` before opening a database connection.
