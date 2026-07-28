# Foushee Justice publication activation

This runbook prepares, but does not authorize, one exact publication activation:
member `F000477`, issue `JUSTICE_PUBLIC_SAFETY`, Congress/scope `119`, artifact
`f000477:justice_public_safety:119:v1` version 1.

The immutable activation bundle is
`foushee_justice_public_safety_119_publication_activation_v1`. It adds one
three-artifact batch, two relationships, and one publication-registry row. It
does not update the historical 71-artifact seed, approved wording, Semantic IR,
or approval receipt. No migration or cache invalidation is required. The API
reads PostgreSQL on every request and the frontend request uses `no-store`.

## Mandatory sequence

1. Deploy a commit containing source commit
   `bae70a3623b66a68cda40ac537dc4a1740e87f92` and verify `/health` reports its
   exact commit SHA.
2. Run `verify-bundle`.
3. Run read-only `preflight` against the exact target. It must prove schema
   `0016`, the frozen historical 71/95 seed, counts `1/71/95/0`, and absence of
   all activation identities.
4. Create a custom-format `pg_dump`, calculate its SHA-256, restore it into a
   fresh disposable PostgreSQL database, and prove the restored schema, counts,
   and historical seed. Record the result using the backup proof contract in
   `foushee_justice_public_safety_119_backup_plan_v1.json`.
5. Obtain explicit publication authorization naming the bundle ID and digest.
6. Run `apply` with the exact bundle ID, bundle digest, deployed commit, backup
   proof, target, and production confirmation. The tool repeats preflight under
   an advisory lock and performs all five inserts in one transaction.
7. Run `postcheck`, then public API and frontend smoke checks. Any failed gate
   requires immediate exact rollback.

The activation tool is:

```powershell
python backend/scripts/foushee_justice_publication_activation.py verify-bundle
python backend/scripts/foushee_justice_publication_activation.py preflight --target production
```

Write modes additionally require `--bundle-sha256`, `--deployed-commit`,
`--backup-proof`, and an explicit production confirmation flag. Rollback also
requires the exact live batch ID and the comma-separated ordered artifact IDs
reported by postcheck.

## Public contract and thresholds

Before activation, the Justice presentation tier is `receipts_only` for
`scope=119`, `scope=all`, and `scope=118`.

After activation:

- Foushee `scope=119`: `reviewed_conclusion`;
- Foushee `scope=all`: `reviewed_conclusion`, explicitly bounded to the reviewed
  119th-Congress record;
- Foushee `scope=118`: `receipts_only`;
- every other member and every other issue: unchanged.

The smoke gate fails on any non-200 response, timeout, schema mismatch, wrong
tier, missing reviewed scope, receipt mismatch, digest mismatch, leak to scope
118/another member, or unexpected change to another issue. There is zero
tolerance for these failures.

## Rollback

Rollback validates the exact active artifact, receipt, registry primary key,
batch ID, artifact IDs, and bundle digests under the same advisory lock. In one
transaction it deletes the one registry row, the two bundle relationships, the
three immutable artifact rows using the exact rollback session setting, and the
activation batch. It then proves counts `1/71/95/0` and exact historical seed
equality. If transactional rollback cannot complete, restore the validated
pre-activation snapshot to a fresh database and cut over only under the bounded
production-write incident procedure.

Publication remains inactive until a later task supplies explicit authorization
and successfully completes every gate above.
