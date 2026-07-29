# Foushee Justice publication activation

This runbook records the completed exact publication activation for member
`F000477`, issue `JUSTICE_PUBLIC_SAFETY`, Congress/scope `119`, artifact
`f000477:justice_public_safety:119:v1` version 1. It does not authorize replay,
deactivation, rollback, deployment, or any other production action.

The immutable activation bundle is
`foushee_justice_public_safety_119_publication_activation_v1`. It adds one
three-artifact batch, two relationships, and one publication-registry row. It
does not update either governed pre-activation batch, approved wording, Semantic
IR, or approval receipt. No migration or cache invalidation is required. The API
reads PostgreSQL on every request and the frontend request uses `no-store`.

## Current production state

The activation completed at `2026-07-29T02:01:07.388267Z` on deployed commit
`bbeafa1e64b4e7783739f5b2f6b2c343b39209e5`. Batch 13 contains presentation
artifact 218, source-manifest artifact 219, and validation-result artifact 220.
Those numeric IDs are historical operational identities; the bundle's natural
keys and content digests remain authoritative. The public contract is
`reviewed_conclusion` for `scope=119` and bounded `scope=all`, and
`receipts_only` for `scope=118`. The successful, non-authorizing receipt is
`docs/editorial/publication_activations/foushee_justice_public_safety_119_successful_activation_receipt_v1.json`.

## Historical activation sequence

The following sequence records the gates used for the completed activation. It
must not be replayed without new explicit production authorization.

1. Deploy a commit containing source commit
   `bae70a3623b66a68cda40ac537dc4a1740e87f92` and verify `/health` reports its
   exact commit SHA. The deployed commit must also contain the tuple-row HTTP
   correction recorded in
   `docs/incidents/2026-07-28-foushee-justice-activation-http500.md`.
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
5. Run `foushee_justice_publication_http_proof.py` with the bound backup proof.
   This authoritative mode owns the complete disposable lifecycle: it creates a
   uniquely labeled PostgreSQL 17.6-compatible Docker network, volume, and
   container; generates local credentials; exposes a random loopback-only port;
   restores the verified snapshot; and proves the canonical baseline before
   starting the real backend. It then proves inactive HTTP, applies the exact
   bundle, captures the batch, artifact, relationship, registry, bundle, and
   digest identities before a separate postcheck, proves the complete activated
   HTTP contract and isolation, performs identity-bound rollback, and proves
   inactive HTTP and the exact canonical baseline. Finally it stops Uvicorn and
   removes its container, volume, and network. A passing proof requires both
   verified rollback and verified resource absence. Selector-only,
   CLI-postcheck-only, or externally provisioned database evidence is
   insufficient.
6. Confirm production is still at the exact inactive governed baseline, then
   obtain separate explicit publication authorization naming the bundle ID and
   digest.
7. Run `apply` with the exact bundle ID, bundle digest, deployed commit, backup
   proof, preflight report, target, and production confirmation. The tool repeats
   and binds preflight under an advisory lock and performs all seven row inserts
   (one batch, three artifacts, two relationships, and one registry row) in one
   transaction.
8. Run `postcheck`, then public API and frontend smoke checks. Any failed gate
   before commit aborts the transaction. After commit, immediately invoke exact
   database-only rollback on any blocking smoke failure. A deployment outage or
   unknown backend health must not prevent that rollback path.

The activation tool is:

```powershell
python backend/scripts/foushee_justice_publication_activation.py verify-bundle
python backend/scripts/foushee_justice_publication_activation.py preflight --target production --bundle-id foushee_justice_public_safety_119_publication_activation_v1 --deployed-commit <40-char-sha> --report-path <evidence-dir>/preflight-report.json
python backend/scripts/foushee_justice_publication_activation.py prepare-backup --target production --bundle-id foushee_justice_public_safety_119_publication_activation_v1 --deployed-commit <40-char-sha> --preflight-report <evidence-dir>/preflight-report.json --restore-database-url <fresh-disposable-url> --evidence-dir <evidence-dir>
python backend/scripts/foushee_justice_publication_http_proof.py --deployed-commit <40-char-sha> --preflight-report <evidence-dir>/preflight-report.json --backup-proof <evidence-dir>/backup-proof.json --bundle-id foushee_justice_public_safety_119_publication_activation_v1 --bundle-sha256 df081ea7fc93039926b5a8ac1e468444f30e28b25bb2862bb2980f7d2d83e813 --evidence-dir <local-http-proof-output-dir>
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

The authoritative HTTP proof does not accept an arbitrary database URL. An
externally managed database run is diagnostic only and cannot produce
activation-readiness evidence. After a successful apply, the authoritative
proof persists a closed local receipt containing the exact activation
identities before invoking its independent postcheck. Any later postcheck,
serialization, or HTTP assertion failure causes the outer cleanup path to stop
Uvicorn and attempt exact rollback from that captured receipt. Rollback failure
is reported as a proof failure but never prevents destruction of the
current-run labeled container, volume, and network. No global Docker cleanup is
permitted.

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

Publication is active following the separately authorized 2026-07-29
transaction and passing internal and public HTTP postchecks. The immutable
successful-activation receipt above is the current closeout authority.

The 2026-07-28 attempt inserted exactly seven rows, but its independent HTTP
checks returned 500 and the exact rollback restored `2/140/155/0`. That attempt
is not reusable activation evidence. A later authorization requires the
corrected deployed commit, exact `/health` identity, a fresh production
preflight, a fresh verified backup or an explicit in-lifetime revalidation of
the existing proof, a fresh lifecycle-owned real-server disposable HTTP proof,
and a final confirmation that production remains inactive. An operator-created
database cannot substitute for that proof.

The baseline-reconciliation PR was repository-only. It did not access or modify
production, create a production backup, activate publication, or deploy. The
two governed batches are legitimate additive corpora; neither is duplicate,
corrupt, or a cleanup target. The fingerprint is an exact required pre-state
and must be recomputed immediately before activation rather than treated as a
timeless production description.

## Current rollback target (record only)

The rollback target is batch 13; artifacts 218 (presentation), 219 (source
manifest), and 220 (validation result); the two exact bundle relationships; and
the `F000477 / JUSTICE_PUBLIC_SAFETY` registry row. The activation bundle is
`foushee_justice_public_safety_119_publication_activation_v1`, digest
`df081ea7fc93039926b5a8ac1e468444f30e28b25bb2862bb2980f7d2d83e813`.
The rollback tool must still verify the live natural keys, content digests,
registry identity, and graph before acting, and must refuse registry or graph
drift. This section and the successful-activation receipt do not authorize a
rollback.
