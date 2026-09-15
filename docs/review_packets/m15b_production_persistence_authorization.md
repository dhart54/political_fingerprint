# M15B actual replacement persistence authorization package

PR #186 merged as `5843bab9b1bed3e5db57976bae3b05466f2cbafe` from the exact
accepted head `e223bbf676c1762337c03bc3af0e78801c14f698`. Its reviewed base and
all checks matched. Normal code-only merge integrations were allowed; no manual
deployment, production persistence, activation, migration or rollback occurred.

This preparation branch is `codex/m15b-production-preparation`. Its exact final
head and hosted run are recorded in the draft PR, avoiding a self-referential
commit hash inside committed files. Authorization must name that reviewed head.

## Scope and immutable identities

All paths below are relative to
`docs/editorial/publication_replacements/m15b_authorization/`.

- `persistence_package.json`: exact two independent bundles, all artifact payloads,
  natural keys, versions, hashes, supersedes IDs, relationships and mutation caps.
- `production_baseline.json`: READ ONLY capture at
  `2026-09-15T01:15:05.420184+00:00`, exact prior registry rows and old identities,
  target fingerprint, absent proposed artifacts and snapshot hashes.
- `disposable_baseline.json.gz`: bounded current public database facts and required
  immutable provenance, for the existing disposable snapshot replay harness.
- `public_before.json.gz`: complete public API results for all four domains in
  both scopes at capture time, including current ledger and discovery counts.
- `public_before_after.json`: readable actual old/new NS/Justice presentations,
  with current ledger accounting. The new presentations are exact accepted data.

Package digest:
`ab89f46ed8886bb971a8236b36b9f7bda02d824a1a2a470df10bf62847aa6359`.
Accepted source preparation remains unchanged at
`../m15b_preparation/approved_semantics_preparation.json`.

| Domain | Exact old artifact | New presentation SHA-256 | Batch identity |
|---|---|---|---|
| NS | 227 / v1 / `05661086601991075f04195090a41e0febaad7f8e6acda53f0cab838f97e860c` | `c675731a2602829f2c1d325673c50099cb3ef458d2ae0bf07b10237019858f29` | `m15b:national_security_foreign:c675731a2602829f` |
| Justice | 221 / v1 / `1c088fc4a98e8442263899faffd7e203967cf60c387944884e4ce755d6ba7943` | `01f237396226557347cb6a216ad4ae8ea6b20d04fabe084ec3f5cc9732e5545b` | `m15b:justice_public_safety:01f2373962265573` |

Each new key is `public-issue-presentation:f000477:<lowercase_issue>:m15b:v1`.
Source and validation keys append `:source` and `:validation`. Every version is 1.
The presentation supersedes its exact old ID. Each presentation has exactly one
`has_validation` and one `uses_source_manifest` edge, ordinal 0, with the exact
metadata in the package. The source manifest references the existing old artifact
and accepted semantic authority. Validation retains the existing database gates:
successful/current, zero blocking findings, and complete required sources.

Derived persistence counts per domain: **1 batch + 3 artifacts + 2 relationships**.
Together: **2 batches + 6 artifacts + 4 relationships**. Registry updates, other
updates, raw-data writes and deletes during persistence: **0**. New production
artifact IDs are **null/unresolved**, never inferred from disposable IDs.
`source_commit_sha` remains merged main, which contains the exact accepted inputs;
the operator separately requires the exact reviewed preparation code head.

## Public effects and current baseline

No material target drift was found. Both old roots and their hashes match, all
four current registry roots pass the existing eligible-provenance query, and none
of the six proposed artifact identities exist in production at capture time.
This capture is evidence, not a perpetual preflight: the operator rechecks the
exact current row, old digest and provenance before each persistence transaction.

NS loses only the unsupported trajectory; the accepted surviving result is 14
findings and 30 unique supporting actions. Underlying receipts/meanings/episodes
remain. Justice has the approved public limitation at exactly 35 receipts and
retains two noncounting controls and the unchanged trajectory. No semantic
decision is created by the persistence operator.

| Domain | 119 available / reviewed / unreviewed | all available / reviewed / unreviewed |
|---|---|---|
| NS | 93 / 82 / 11 | 263 / 82 / 181 |
| Justice | 51 / 37 / 14 | 103 / 37 / 66 |
| Environment | 74 / 63 / 11 | 108 / 63 / 45 |
| Education | 25 / 17 / 8 | 52 / 17 / 35 |

The proof uses these real additional unreviewed actions. It does not manufacture
a production action. Persistence alone must leave all public output unchanged.

## Proposed persistence commands — NOT executed on production

After a separate human persistence authorization, use an isolated clean checkout
at the exact authorized preparation head. Set `$ReviewedPreparationHead` to that
literal reviewed SHA; do not derive authorization from whatever HEAD is current.
Set `$ProductionEnvFile` to the existing protected backend environment file and
`$ReportDirectory` to an operator-owned recovery-evidence directory. Neither the
DSN nor credentials belong in Git, shell output, tests or the review packet.

```powershell
$PackageHash = 'ab89f46ed8886bb971a8236b36b9f7bda02d824a1a2a470df10bf62847aa6359'
python backend/scripts/m15b_persistence_preparation.py check

# Execute these steps separately for NATIONAL_SECURITY_FOREIGN, then JUSTICE_PUBLIC_SAFETY.
$Issue = 'NATIONAL_SECURITY_FOREIGN'
python backend/scripts/m15b_persistence_preparation.py preflight --target production --issue $Issue --env-path $ProductionEnvFile --package-sha256 $PackageHash --expected-code-head $ReviewedPreparationHead --report-path "$ReportDirectory/$Issue-preflight.json"
python backend/scripts/m15b_persistence_preparation.py persist --target production --issue $Issue --env-path $ProductionEnvFile --package-sha256 $PackageHash --expected-code-head $ReviewedPreparationHead --confirm-production-persistence --report-path "$ReportDirectory/$Issue-persistence.json"
python backend/scripts/m15b_persistence_preparation.py preflight --target production --issue $Issue --env-path $ProductionEnvFile --package-sha256 $PackageHash --expected-code-head $ReviewedPreparationHead --report-path "$ReportDirectory/$Issue-postcheck.json"
```

Require first persistence to report exactly 1/3/2 inserts and zero registry/other
writes. Postcheck must resolve the complete exact owned graph and its numeric IDs.
Retain both receipts. A repeated persist has an explicit zero-write result, but
read-only postcheck is sufficient for production verification. Sequential domain
commands are independently bounded; there is no implicit multi-domain transaction.

Stop on a changed old pointer, artifact digest, registry metadata, provenance,
target fingerprint, dirty/different code head, package digest, unexpected existing
artifact or partial/conflicting batch. Do not repair by retargeting or filling a
partial batch. Exceptions inside the owned transaction roll back its inserts.
If a report write fails after commit, use the exact read-only postcheck to identify
committed ownership before any retry; do not assume the transaction failed.

Owned persistence recovery, only if included in the separate authorization and
only while the old registry row remains exact and the new batch is unpublished:

```powershell
python backend/scripts/m15b_persistence_preparation.py recover --target production --issue $Issue --env-path $ProductionEnvFile --package-sha256 $PackageHash --expected-code-head $ReviewedPreparationHead --confirm-production-rollback --report-path "$ReportDirectory/$Issue-recovery.json"
```

This uses the existing exact-batch deletion guard. It validates every owned row
and relationship, refuses published or competing references, deletes only the
owned 2 relationships / 3 artifacts / 1 batch and confirms absence. Historical
artifacts, the prior registry and raw tables remain intact. Recovery is not
authorized by this preparation request.

## Later activation — NOT ready or authorized

After persistence, obtain each exact production presentation ID from its owned
persistence receipt and verify its natural key/version/digest. Never use the
disposable authority or IDs. For each domain separately:

1. Confirm the reviewed reusable runtime is deployed through the normal path.
   Obtain fresh, independently verified backend/frontend source manifests and
   health/source identities using the existing V2R runtime evidence contract.
   No current deployed-runtime evidence is fabricated in this package.
2. Call existing `prepare_write_set` with the package registry key, exact current
   prior row, old identity, newly resolved production identity, semantic authority
   binding, publication metadata, target fingerprint and reviewed runtime manifest
   binding. Capture read-only execution preflight using the reusable operator.
3. Obtain separate sealed accepted human replacement activation authority for each
   exact write set. Shared semantic approval is not execution authority.
4. Use `backend/scripts/publication_replacement_v2r.py apply --target production`
   with explicit `--database-url-env`, `--write-set`, `--authority`,
   `--runtime-evidence`, `--production-preflight`, `--report-path` and
   `--confirm-production-replacement`. Each operation updates one exact registry
   row. Execute only after fresh matching evidence and explicit authorization.
5. Verify actual public semantics and current ledger accounting in both scopes.
   Publication rollback, if separately authorized, uses the same operator's
   `rollback` and `--confirm-production-rollback`, restoring only the exact owned
   post-state to its bound prior row. It does not remove persisted artifacts.

Unavailable activation prerequisites: production numeric IDs, fresh deployed
runtime evidence, fresh execution preflight, and sealed activation authorities.
These are expected later-stage gates, not claims of activation readiness.

## Validation and disposition

The existing PostgreSQL snapshot harness and hosted lane exercise the actual
package through existing persistence, reusable V2R and real selector/evidence
paths. Test-only authorities remain marked synthetic; the test only opts in at
existing selector seams. No production credential is loaded by tests.

Local focused package/operator/historical tests passed; database proof is pending
hosted execution (a local skip is not a pass). Final exact-head hosted results and
disposition are recorded in the draft PR. No optional cleanup is bundled.
