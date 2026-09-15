# Authorized green M15B production activation

National Security and Justice are active on green following the user's exact
`approve_exact_publication_replacement_v2` decision. National Security was applied
and fully verified before the new Justice preflight and Justice apply. Each
existing V2R operator call supplied `--confirm-production-replacement`.

Execution code and pre-activation evidence head:
`9fc3561c39b971504b5fc54a4e25b8b1698e1ae7`.
Persistence execution head remains
`b1820d2b598eb2b5767e84040f6a8d6c0ef22d36`.
Deployed backend/frontend source remains
`f790163f90b8a71fae2bee3206f73953364f1e72`.
This later evidence commit did not execute those production writes. The prior
`m15b_green_activation` directory remains the historical persistence/preparation
record; its then-absent activation authority is superseded by this separate
explicit decision, not rewritten.

Green project: `yalpfkaxkxebwolhorha`; target digest
`0bdeba5d97ecc77e9117d15f50d952f534a6e6dd9c66950d98d96bcad72523ea`.
Reviewer `dhart54` is the established production reviewer. Both authorities are
immutable, sealed, accepted, non-synthetic, and bind only their exact write set,
old/new identities, semantic authority, rollback target and production target.

| Binding | National Security | Justice |
|---|---|---|
| Replacement | 227 -> 248 | 221 -> 251 |
| Write-set subject SHA256 | `703a9c49ab12f64ec05480225b1d79dd28c74f18bae7f0d7f5425c80a4d4e768` | `73362a184e333b6db031b6d9fe1924641d021c1f155e0d2f3092e706ffe28d31` |
| Authority subject SHA256 | `1db6d83549f7fd62e7aeb7ab3507e3a6b0e9d483fd1103acfa38991b8ff2d018` | `6e3bdf133c0a8da7cd555bfee5f268899714433138e25df3e362f8b6619bda82` |
| Executed preflight subject SHA256 | `f78efbfd2cb5dadc4f4fc9bff03b0222c50e411eda8dcb0eeba618be63920b5d` | `eb9d6c83ea53295dd6661d183a97e0385deaa0d5fd04c705a81d1b51ed87d853` |

Runtime evidence SHA256:
`990804ae178c8ff33e0c64dc8252a34c7a03bb0a8d006221f020161f152a5375`.
The same fresh runtime evidence served both applies. The executed Justice
preflight was recaptured after National Security passed, at
`2026-09-15T16:23:28.973705+00:00`. The initial Justice preflight from before
National Security was not used to execute Justice. Trusted frontend deployment
is GitHub deployment6460016105, recorded in `frontend_deployment_source.json`.

Both raw apply receipts report `APPLIED`, exactly one registry update each and
zero insertions, deletions, artifact/batch/relationship writes or other updates.
Only the F000477/NATIONAL_SECURITY_FOREIGN and F000477/JUSTICE_PUBLIC_SAFETY
rows in `editorial_publication_registry` changed. Complete rows and metadata are
in `production_audits.json.gz`; all other27 public table fingerprints, all17
sequences and schema remained identical. Persisted artifacts248-253 and their
provenance graphs remain exact and eligible. No core legislative data changed.
Blue was not accessed or modified; no merge or deployment was performed.

Final roots: Education245, Environment239, National Security248, Justice251.
Final database size: **231,779,475 bytes**, comfortably below400 MB.

## Public validation

Each of the three stages captured99 complete direct database results and99
matching live Render responses, without dropping response fields. Coverage:
Foushee, Thomas Massie and Angela D. Alsobrooks; scopes118/119/all; positions,
eight-domain evidence, editorial presentations and fingerprints. The final
full response objects equal the exact prepared after-state for the two changed
domains, with all other baseline responses unchanged. No summary route was
requested over HTTP. The direct read helper uses a borrowed read-only connection.

National Security has zero policy trajectories,14 surviving findings and30
unique supporting actions. Justice has the accepted limitation on exactly35
receipts and retains2 noncounting controls. Justice trajectories and unrelated
wording are unchanged. Receipt meaning, episodes, action positions, current
review accounting and unreviewed ledgers are preserved. Discovery/detail totals
reconcile across118/119/all. `invariant_checks.json` records the focused checks;
the compressed direct/live files retain the complete public evidence.

| Stage | Exact direct/live canonical SHA256 |
|---|---|
| Before | `800bf779052636e7faaf59fec812dd1c32322e37b9fb77868627898d054d8cdf` |
| After National Security | `8ea73a38cba4ba8d3beeeb4b9ecde9f6860336d9f271a90d2e903907b06c2773` |
| After Justice | `ca2efa1e33b886628a25ae923094ef117252c8315b28417da85785901a8c47d8` |

Table fingerprints use ordered SHA256 digests of PostgreSQL `to_jsonb(row)::text`
with UTC timestamps and `extra_float_digits=3`, preserving the prior audit's
canonical method. Public results use the accepted backend read functions and
JSON normalization without removing fields. Exact expected changed output is
retained in the prior preparation's `expected_public_after.json.gz`.

## Rollback ownership and validation

Both final rows pass the existing `_owned` predicate against their exact sealed
authority and write set. Complete prior registry rows are preserved in each
write set. The existing V2R rollback path would restore NS227 or Justice221 only
from the exact owned post-state, using the same authority/write set and explicit
`--confirm-production-rollback`. This is recorded recovery evidence, not a new
request to execute rollback. **No rollback occurred.** No production repeat apply,
synthetic action, batch recovery or extra persistence was performed.

39 existing mocked V2R governance/confirmation and M15B semantic tests passed
locally. Exact-head hosted CI is requested for this evidence commit; the final
PR delivery records its immutable commit and workflow-run identity after checks
complete. Existing CI includes historical M14G/M14H, public receipt/browser,
V2R lifecycle and actual production-ID activation/owned rollback on disposable
PostgreSQL17. Production was not used to exercise failure or repeat behavior.

## Resolved execution anomalies

- The first read-only technical refresh timed out on Render health. One identical
  read-only retry succeeded before activation.
- The first read-only audit used `legislators.name`; correcting the local helper
  to `name_display` allowed the complete pre-activation audit to pass.
- Local launcher filename `operator.py` shadowed Python's standard library.
  Imports failed before the V2R operator or database connection was reached.
  Renaming the local helper allowed the single National Security apply.
- The first local mocked test run passed35 with4 Windows temporary-directory
  setup errors. A fresh local temporary directory resolved this; all39 passed.

No gate or production code was weakened to resolve these local/read-only issues.
There are no unresolved activation blockers. Keep PR190 draft/unmerged and
preserve its branch-specific Vercel deployment suppression.

Machine-readable execution: `execution_record.json`. File-byte digests are in
`file_manifest.json` (excluding this narrative and the manifest itself).
