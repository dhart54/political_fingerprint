# Foushee Justice publication activation

This runbook prepares, but does not authorize, one exact publication activation:
member `F000477`, issue `JUSTICE_PUBLIC_SAFETY`, Congress/scope `119`, artifact
`f000477:justice_public_safety:119:v1` version 1.

The immutable activation bundle is
`foushee_justice_public_safety_119_publication_activation_v1`. It adds one
three-artifact batch, two relationships, and one publication-registry row. It
does not update either governed pre-activation batch, approved wording, Semantic
IR, or approval receipt. No migration or cache invalidation is required. The API
reads PostgreSQL on every request and the frontend request uses `no-store`.

## Mandatory sequence

1. Deploy a commit containing source commit
   `bae70a3623b66a68cda40ac537dc4a1740e87f92` and verify `/health` reports its
   exact commit SHA.
2. Run `verify-bundle` and record the exact bundle digest.
3. Run read-only `preflight` with the explicit bundle ID, deployed commit, and
   `--report-path` against the exact target. It must prove schema
   `0016`, both exact governed batches, counts `2/140/155/0`, their pinned
   identities and canonical V1 graph hashes, the canonical full-set hashes,
   the composed reconciled fingerprint, and absence of all activation
   identities. The two batches are the frozen V1 seed
   (`71/95`) and the corrected Environment & Energy commissioning corpus
   (`69/60`). The report binds those results to the database fingerprint,
   bundle digest, and deployed backend identity. The normalization contract is
   `docs/editorial/publication_activations/foushee_pre_activation_canonical_hashing_v1.md`.
4. Run `prepare-backup` with that report and a fresh empty disposable database.
   The tool creates the custom-format `pg_dump`, inventories the source, restores
   the archive, inventories the restored database, proves semantic equality and
   the `receipts_only` selector state, and emits a schema-validated evidence
   chain. Operator-authored booleans are not accepted as backup evidence.
5. Obtain explicit publication authorization naming the bundle ID and digest.
6. Run `apply` with the exact bundle ID, bundle digest, deployed commit, backup
   proof, preflight report, target, and production confirmation. The tool repeats
   and binds preflight under an advisory lock and performs all seven row inserts
   (one batch, three artifacts, two relationships, and one registry row) in one
   transaction.
7. Run `postcheck`, then public API and frontend smoke checks. Any failed gate
   before commit aborts the transaction. After commit, immediately invoke exact
   database-only rollback on any blocking smoke failure. A deployment outage or
   unknown backend health must not prevent that rollback path.

The activation tool is:

```powershell
python backend/scripts/foushee_justice_publication_activation.py verify-bundle
python backend/scripts/foushee_justice_publication_activation.py preflight --target production --bundle-id foushee_justice_public_safety_119_publication_activation_v1 --deployed-commit <40-char-sha> --report-path <evidence-dir>/preflight-report.json
python backend/scripts/foushee_justice_publication_activation.py prepare-backup --target production --bundle-id foushee_justice_public_safety_119_publication_activation_v1 --deployed-commit <40-char-sha> --preflight-report <evidence-dir>/preflight-report.json --restore-database-url <fresh-disposable-url> --evidence-dir <evidence-dir>
python backend/scripts/foushee_justice_publication_activation.py apply --target production --bundle-id foushee_justice_public_safety_119_publication_activation_v1 --confirm-bundle-digest df081ea7fc93039926b5a8ac1e468444f30e28b25bb2862bb2980f7d2d83e813 --deployed-commit <40-char-sha> --preflight-report <evidence-dir>/preflight-report.json --backup-proof <evidence-dir>/backup-proof.json --confirm-production-activation
python backend/scripts/foushee_justice_publication_activation.py rollback --target production --bundle-id foushee_justice_public_safety_119_publication_activation_v1 --confirm-bundle-digest df081ea7fc93039926b5a8ac1e468444f30e28b25bb2862bb2980f7d2d83e813 --confirm-rollback-token ROLLBACK:foushee_justice_public_safety_119_publication_activation_v1:df081ea7fc93039926b5a8ac1e468444f30e28b25bb2862bb2980f7d2d83e813 --confirm-batch-id <batch-id> --confirm-artifact-ids <ordered-ids> --confirm-production-rollback
```

Every database-facing mode requires the explicit bundle ID. `preflight` rejects
an absent, malformed, incompatible, or placeholder deployed commit before
opening the database. `apply` additionally requires
`--confirm-bundle-digest`, the same deployed commit, the successful preflight
report, the tool-generated backup proof, and an explicit production confirmation
flag. Rollback requires `--confirm-bundle-digest`, the exact rollback token, the
live batch ID, the comma-separated ordered artifact IDs reported by postcheck,
and the production rollback flag; deployed health is deliberately not required.
Preflight reports, freshness checks, source and restored backup inventories,
backup proofs, apply preconditions, postchecks, and rollback restoration all
use the same mandatory canonical graph and fingerprint functions. There is no
permissive operational hash mode.

## Public contract and thresholds

Before activation, the Justice presentation tier is `receipts_only` for
`scope=119`, `scope=all`, and `scope=118`.

After activation:

- Foushee `scope=119`: `reviewed_conclusion`;
- Foushee `scope=all`: `reviewed_conclusion`, explicitly bounded to the reviewed
  119th-Congress record;
- Foushee `scope=118`: `receipts_only`;
- every other member and every other issue: unchanged.

Rollback immediately after any semantic or identity failure: member, issue, or
scope mismatch; artifact or content digest mismatch; wording that differs from
the approved presentation; a missing or wrong approval receipt; validation or
source graph mismatch; selection of the wrong artifact; analytical copy exposed
for another member or issue; or a supporting-vote or provenance identity
failure.

Treat availability separately. For an API timeout, non-200 response, or frontend
unavailability, make two confirmed attempts within 60 seconds and record both
timestamps and responses. Roll back after the second confirmed failure. One
transient availability failure alone does not meet the rollback threshold.

Publication may remain active for a documented cosmetic-only defect with an
assigned immediate follow-up only when API semantics, every identity and digest,
exact approved wording, receipt/source resolution, and non-blocking
accessibility all pass. Examples are minor spacing, a non-semantic color
variation, or harmless line wrapping. Wrong wording, hidden limitations, broken
evidence navigation, cross-member exposure, and any accessibility blocker are
semantic or functional failures and never qualify for this exception.

## Rollback

Rollback validates the exact active artifact, receipt, registry primary key,
batch ID, artifact IDs, bundle digest, and explicit rollback token under the
same advisory lock. In one
transaction it deletes the one registry row, the two bundle relationships, the
three immutable artifact rows using the exact rollback session setting, and the
activation batch. It then proves counts `2/140/155/0` and exact governed
two-batch baseline equality. If transactional rollback cannot complete, restore the validated
pre-activation snapshot to a fresh database and cut over only under the bounded
production-write incident procedure.

Publication remains inactive until a later task supplies explicit authorization
and successfully completes every gate above.

The baseline-reconciliation PR was repository-only. It did not access or modify
production, create a production backup, activate publication, or deploy. The
two governed batches are legitimate additive corpora; neither is duplicate,
corrupt, or a cleanup target. The fingerprint is an exact required pre-state
and must be recomputed immediately before activation rather than treated as a
timeless production description.
