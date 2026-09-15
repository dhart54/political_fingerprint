# Green M15B persistence and activation preparation

## Production result

Execution head: `b1820d2b598eb2b5767e84040f6a8d6c0ef22d36`. Both writes ran before this evidence commit, from the clean authorized checkout; no merge or corrective commit preceded them. Exact authorized package: `55f81e763c085c4128de30863ec7d77c7f5bfb51695bbe739c4709cb3d80e362`. Green target: `yalpfkaxkxebwolhorha`, identity `0bdeba5d97ecc77e9117d15f50d952f534a6e6dd9c66950d98d96bcad72523ea`.

NS PERSISTED: batch23, presentation248, source249, validation250. Justice PERSISTED: batch24, presentation251, source252, validation253. Each added exactly1 batch/3 artifacts/2 relationships. Combined table counts changed batches8→10, versions158→164, relationships167→171. Registry remains4 rows. No registry, core-data or unrelated writes. No recovery or production activation was executed.

Fresh preflights passed before NS and again before Justice after the NS postcheck. Complete owned graphs, natural keys/versions/content hashes, source/validation eligibility and supersedes227/221 identities passed after persistence. Existing editorial rows and all unrelated public physical table fingerprints remain exact. All17 sequences changed only by the expected2 batch and6 artifact allocations. Capacity:231,500,947 before;231,574,675 after NS;231,722,131 after Justice, safely below400MB. Normalized schema is unchanged.

All four roots remain Education245, Environment239, Justice221, NS227. Exact full registry rows/fingerprint match. The21 live Foushee responses across118/119/all, including discovery, four domain ledgers, editorial presentations and fingerprints, match before/after each write. Direct database public output also matches the independently reviewed baseline. Live digest: `a290d49d177bf36b279a8ea139d4625f1ec10ee7ffa84b81335d88f373f4a297`. Persistence had zero user-visible effect. Blue was untouched.

Evidence is separate from the immutable earlier preparation and PR189 migration record. `production_audits.json.gz` retains full read-only before/NS/Justice states; `postchecks.json` exposes compact table fingerprints, sequences, roots and owned IDs. `persisted_rows.json.gz` contains exact committed2/6/4 rows for disposable replay. `persistence_receipts.json` retains the exact execution head, operation receipts and production preflights.

## Activation preparation — NOT AUTHORIZED

Preparation digest: `7fc9c7fcafbb9c952a010c5dcbd289dec6f69b2328b1c937975ce1d29230f37f`. Runtime evidence: `ba2ddc0fe44a76176f10ae593c5af75f609847311df97ac0d85fcaf96d83dcb5`. Both deployed source commits remain `f790163f90b8a71fae2bee3206f73953364f1e72`. Frontend source is trusted GitHub production deployment6460016105 / political-fingerprint-dp5svtqpz-dhart54s-projects.vercel.app; backend health reports the same main. Backend/frontend manifests use immutable Git objects and the established V2R runtime path contract.

### JUSTICE_PUBLIC_SAFETY

Write-set ID `replacement:F000477:JUSTICE_PUBLIC_SAFETY:01f237396226557347cb6a216ad4ae8ea6b20d04fabe084ec3f5cc9732e5545b`. Subject SHA256 `73362a184e333b6db031b6d9fe1924641d021c1f155e0d2f3092e706ffe28d31`. Read-only activation preflight `0d303a22e20d0adeb561c6f5dacfa617dba9897ee124d4488ec3859fb004bb97`. Persisted numeric graph binding `9c27957370bd442a383e8fbd7bc5662125663155451b4a3b47ec59e23cba0f76`. Rollback identity `{'artifact_id': 221, 'artifact_version': 1, 'content_sha256': '1c088fc4a98e8442263899faffd7e203967cf60c387944884e4ce755d6ba7943', 'natural_key': 'public-issue-presentation-candidate:f000477:justice_public_safety:119:v1'}`.

### NATIONAL_SECURITY_FOREIGN

Write-set ID `replacement:F000477:NATIONAL_SECURITY_FOREIGN:c675731a2602829f2c1d325673c50099cb3ef458d2ae0bf07b10237019858f29`. Subject SHA256 `703a9c49ab12f64ec05480225b1d79dd28c74f18bae7f0d7f5425c80a4d4e768`. Read-only activation preflight `589dc8f8e284fb3e8405c36b24929e10fe48072a6079cb83f131eda6b75df86a`. Persisted numeric graph binding `777f470a3996060e8d646dee5eddeee4ff2343d9c9a3e6db00663a31a4683164`. Rollback identity `{'artifact_id': 227, 'artifact_version': 1, 'content_sha256': '05661086601991075f04195090a41e0febaad7f8e6acda53f0cab838f97e860c', 'natural_key': 'site-integration-candidate:f000477:national_security_foreign:119:v1'}`.

Each write set permits one exact existing registry-row UPDATE, no insert/delete, no artifact/core writes, and preserves exact old/new identities, semantic authority, source/validation graph metadata, target, runtime manifests and prior row. `activation_preparation.json` additionally binds actual source/validation numeric identities and complete relationship metadata. The existing V2R schema/governance/CAS/ownership design is unchanged.

No human activation authority was fabricated, sealed or accepted. `activation_authorized` is false and `human_activation_authority` is null. Fresh runtime and preflight evidence are valid for1800 seconds; rerun the read-only technical preparer into a new output directory before later execution, verify the stable write-set hashes remain exact, and obtain the separate sealed human activation authority. Do not reinterpret a persistence receipt as activation acceptance.

`backend/scripts/prepare_m15b_green_activation.py --env-path .local/green-production.env --output-dir .local/<fresh-evidence-directory>` only reads production and trusted deployment records. It refuses to overwrite evidence, verifies exact current main/target/schema/registry/owned persisted state, and never calls apply or creates human authority.

## Actual-ID proof and expected public after-state

Normalized PostgreSQL17 replay inserted the actual production batch/artifact/relationship rows with exact IDs and timestamps. The existing synthetic test authority is used only in memory on a guarded loopback disposable database. Production evidence files are never promoted or modified by this test. Technical runtime fixture freshness is refreshed only in test memory; observed immutable file manifests remain exact.

The proof validates227→248 and221→251; rejects missing authority and competing state; rolls back injected failures; verifies one registry-row mutation per domain and zero-write repeat; and restores the exact old public state through owned V2R rollback. No production rollback/recovery occurred. `expected_public_after.json.gz` is the exact full disposable after-state and contains no synthetic activation authority.

NS: unsupported trajectory removed;14 surviving findings/30 supporting actions; accepted receipts, meanings and episodes retained. Justice: exact accepted limitation on35 receipts,2 non-counting controls, unchanged trajectory and all unrelated wording. Unreviewed current ledger rows remain present, discovery/detail totals reconcile, and Education/Environment are unchanged. Tests compare complete presentations and receipts, not selected headline counts alone.

## Rollback preparation — DO NOT EXECUTE

Only after separately authorized activation and rollback, use the same exact V2R write set and the exact sealed authority that owns the activated row. The operator requires `--confirm-production-rollback`; restore the complete prior registry row in each write set, including metadata and timestamps, to Justice221 or NS227. Use Justice then NS when reverting both. It must reject competing metadata/pointers rather than overwrite them. The persisted248–253 artifacts remain intact. Artifact persistence recovery is a separate forbidden operation under this request.

Example shape (not an executable authority): `python backend/scripts/publication_replacement_v2r.py rollback --database-url-env <protected-green-variable> --target production --write-set <exact-domain-write-set.json> --authority <separately-sealed-owned-authority.json> --confirm-production-rollback --report-path <distinct-receipt.json>`. No sealed-authority path exists yet; none is invented here.

## Validation and delivery boundary

Local:41 lifecycle/target/semantic/normalization tests,24 V2R governance/confirmation tests and15 frontend receipt/render tests passed. Prepared semantics/package checks and diff validation pass. Hosted CI covers exact production-ID proof plus full-cardinality normalized active producers, historical M14G/M14H, publication PostgreSQL lifecycle and browser receipts. Exact evidence commit and hosted results are attached to PR190 delivery.

The local read-only postcheck first encountered a composite-key comparison error, corrected before Justice. The persistence operation was not retried and production was not modified to resolve it.

To honor the explicit no-deployment boundary, frontend/vercel.json disables automatic Git deployments only for codex/m15b-green-production-preparation; other branches retain default behavior. This narrow guard avoids creating a preview merely to record evidence. Reference: https://vercel.com/docs/project-configuration/git-configuration . No Render/Vercel deployment command, production configuration change or merge is part of this milestone.

PR190 remains draft/unmerged. Activation authorization is the next gate. No semantic, production registry, blue or other domain/member changes occurred.
