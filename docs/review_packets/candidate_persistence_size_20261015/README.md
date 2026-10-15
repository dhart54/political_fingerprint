# Candidate persistence capacity — bounded local receipt

**Green is currently below the supplied500MB database limit, with252447179bytes
of headroom. This task cannot certify the future complete candidate package.**
No such approved package exists: the candidate pipeline/adapter explicitly reject
persistence preparation. A hypothetical complete review mirror also fails JSONB
because retained witness strings contain `U+0000`. Sources were not stripped,
repaired, approved or published to make an import succeed.

The compatible **incomplete subset** was measured on a brand-new local PostgreSQL
17.5cluster. It adds21.96MB across the two domains including all artifact indexes
and TOAST. This is useful sizing evidence, not the full-package answer or a
production persistence authorization.

## Immutable inputs and actual contract

- Code/qualified Health: **af6cd6d78d6944d64a68a92653066c4c1625f96b**, verified
  current main at worktree creation. All seven Health generated products are
  identical to audit-corrected **5a523f857cab9d47090c62d77f43804a5dde6b5a**.
  [Health audit](../health_semantic_audit_7d53914.md) is candidate-quality review,
  not editorial acceptance.
- Immigration: pushed checkpoint238 **a327f4ccd6f5d95ea12331bb91a8606382a59e50**,
  independently verified on GitHub; later writer work is excluded. Both packages
  contain **F000477 and M001184**. Only committed Git blobs were read, never .w/ib.
- Own isolated worktree `.w/cps`, branch `codex/candidate-persistence-size-rehearsal`.
  Existing .w/vhi source packets/timing and unrelated root state were preserved.
  PR187's approved production preparation was read as contract context only.

The [persistence contract](../../design/editorial_artifact_persistence_contract_v1.md)
and existing `editorial_artifact_store.insert_bundle` insert immutable JSONB
versions, a batch and exact-version relationships. The natural-key/version pair
is unique; identical imports are idempotent and changed same-version content
fails. New versions append; supersedes references do not remove older payloads.

The existing M15B preparation selects **public presentation + file-reference
source manifest + validation**, with two relationships. It does not automatically
persist candidate source banks, authoring, caches, every generated representation
or research captures. The IR persistence proposal embeds compiled IR but is
inert and rejects shared candidates; current candidates also lack approved
public-presentation authoring. Therefore there is no actual authorized
Health/Immigration import manifest whose eventual size can be measured today.

The rehearsal deliberately uses a **hypothetical candidate-review mirror**:
seven generated products plus file-reference provenance; action cores become
individual rows, projections/readable products are split by member, and the other
objects remain whole. Exact candidate text/status is retained. Aggregate artifact
type labels exercise the existing schema/index widths; they are **not** a new
production mapping or evidence of compatibility with approved public schemas.
Only the local core insertion function was used, not a production import mode.

Raw `sources.json`, authoring, histories, validation logs and research captures
are excluded. `package_inventory.json` records all14selected file snapshots,
GitOIDs, raw/canonical SHA256/bytes and precise NUL JSON pointers.
`measurement.json` records the broader excluded-directory metadata, proxies,
sizes, exact code hashes and every included/omitted artifact.

## Current baseline and budget basis

The baseline is **supplied read-only Green evidence at2026-10-15 19:08:41UTC**,
not a production observation made by this task:

| Metric | Bytes |
|---|---:|
| All databases | 247552821 |
| Application database | 232279187 |
| Object Storage | 0 |
| Headroom to350MB reassessment | 102447179 |
| Headroom to400MB capacity decision | 152447179 |
| Headroom to500MB free-plan limit | 252447179 |

Published editorial storage was reported approximately1.16MB and already belongs
to the baseline; Health/Immigration were not persisted. No double counting.

[Supabase's current size documentation](https://supabase.com/docs/guides/platform/manage-your-usage/database-size)
describes the500MB free-project database limit and a database-size calculation
summing `pg_database_size` across databases. Data/indexes belong to that metric;
WAL/disk and object Storage are distinct. Official docs/changelog retrieval
identities are retained in `documentation_evidence.json`. This assessment covers
Green database storage, not every account/project/service quota. For conservative
planning all MB here mean **1000000bytes**; provider internal conversion was not
independently established. PostgreSQL's pretty-size MB uses powers of two.

## Measured subset — not complete packages

| Case | Version rows / relationships | Artifact-table growth, bytes | Whole local DB growth, bytes |
|---|---:|---:|---:|
| Immigration compatible subset | 86 / 85 | 13156352 | 13172736 |
| Health compatible subset | 121 / 120 | 8945664 | 8962048 |
| Combined compatible subsets | 207 / 205 | 21962752 | 21979136 |
| Combined with one retained identical-copy v2 | 414 / 410 | 43720704 | 43737088 |

Every case has **zero publication-registry rows**, pending/nonpromoted/ineligible
metadata and unchanged candidate payloads. SQL round trips recomputed v1canonical
payload hashes; real insertion-function reruns inserted zero artifacts/relations
and preserved counts/table bytes. Candidate proposal guards still rejected the
unchanged IR. V2retained every v1row, appended207new versions and exact supersedes
references; identical content was intentionally used to expose retention cost,
not to forecast changed revision content. Extra v2table growth was21757952bytes.

Exact0016DDL includes its ordinary/unique/partial B-tree indexes, JSONBTOAST,
immutability/publication triggers and RLS. Only two minimal canonical-FK fixture
tables and the chamber enum were scaffolded in the private database. Baselines
include schema allocation. The extra16384bytes in the whole-DB versus artifact
delta include local canonical fixture allocation; production already has those
identities. No existing/shared schema was altered or production schema inspected.

For the combined subset, growth includes **21274624TOAST heap bytes**,
**245760TOAST index bytes**, **229376direct index bytes**, plus ordinary heap/maps.
TOAST figures are components of total size, not added a second time.
The [PostgreSQL size-function documentation](https://www.postgresql.org/docs/17/functions-admin.html#FUNCTIONS-ADMIN-DBSIZE)
defines total relation size as table size plus direct indexes, with TOAST included.
Native17.5,8192byte pages, pglz and Ccollation were observed. Green runtime version,
compression, live custom indexes, fragmentation and concurrent growth remain
unverified. This is a fresh append workload, not a cold-cache comparison.

## Specific boundary: complete JSONB mirror failed

The complete mirror reached the actual JSONBinsert and failed on `\u0000`:

- Immigration: affected whole action artifacts **2:65 and2:101**, plus both
  readable-member artifacts. The source core file has33NULoccurrences; readable
  output duplicates those into66occurrences.
- Health: affected whole action artifact **2:266**, plus both readable-member
  artifacts;9and18occurrences respectively.

These are retained witness/claim-map strings. No meaning, screening decision or
source was changed; this does **not** establish a semantic defect or block the
writer's research. It blocks this particular full JSONBmirror. The partial run
omitted the **entire** incompatible artifacts and enumerates their IDs, canonical
hashes/bytes and NULcounts. It did not clean fields, suppress a validation failure
or claim that the resulting subset covers the complete package. A later reviewed
production selection may reference witnesses rather than copy them, as current
source-manifest patterns do. That decision is outside this task.

## Bounded scenarios — assumptions, not storage guarantees

Adding the **measured subset's whole-DB delta** to the supplied Green baseline
gives269531957bytes, below350MB. This omits the stated incompatible artifacts.
Repeating that subset footprint5times gives357448501bytes, crossing350MB;
10copies give467344181bytes. Such copies duplicate shared data and are not a
reuse-aware forecast for additional members, domains or sessions.

The seven complete generated files total **88244625raw /86867335canonical bytes**
for Immigration and **57412345raw /56368897canonical bytes** for Health.
They include redundant input/core/readable representations, not raw source banks.
The combined **143236232canonical bytes** support transparent reserve sensitivities:

| Assumed reserve | Baseline + reserve, bytes | Budget implication |
|---|---:|---|
| One full-generated canonical-byte equivalent | 390789053 | Above350MB; close to400MB |
| Same reserve plus25% | 426598111 | Above400MB; below500MB |
| Two retained canonical-byte equivalents | 534025285 | Above500MB |

These are **arithmetic sensitivities, not SQL measurements or proven upper
bounds**: they assume byte equivalence/reserve factors, ignore compression and
JSONBencoding, and do not make the incompatible representation importable.
`capacity_analysis.json` retains exact arithmetic and assumptions.

The supported conclusion is: **no present evidence requires a paid upgrade for
these unpersisted candidates, but their full future footprint is not certified.**
Keep350/400MBtriggers. Next select the actual reviewed presentation/provenance/
validation package, qualify JSONBcompatibility without altering canonical
evidence, and rerun that exact package before authorized persistence. Do not
treat whole research-directory size, the partial21.96MBresult or immutable
version supersession as a complete capacity forecast or automatic reclamation.

## Execution, overhead, cleanup and reproduction

First tool **2026-10-15 19:43:19UTC**. `timing.json` records gross elapsed and
command costs; no remainder is labelled model latency/idle. Four failed attempts are
preserved: sandbox restricted-token startup error; inherited Windows PIPE-handle
capture stall/interruption; unsupported locale-setting probe; complete JSONB
mirror's real NULrejection. No earlier failed attempt is counted as passed.
The successful subset ran **2026-10-15T20:00:23.957107+00:00** to **2026-10-15T20:00:52.789832+00:00**; exact timestamps are retained.
Local process-start outputs now use files/timeouts. A one-off CIMinspection
denied in the sandbox is also retained as tooling overhead.

All newly created servers are no longer running; private data/logs remain under
own ignored `.local` for audit. The interrupted cluster retains a stale PIDfile,
but its process is absent; final process inspection distinguishes existing
October9services, which were not connected to, stopped or altered.
`local_cluster_cleanup.json` records that closure. No installs, Docker startup/
pruning, existing-data deletion, background monitor, production connection/write,
candidate edit, full candidate gate, model/tier change, merge or deployment.

The offline verifier checks exact source files/receipts/arithmetic and corrupted
receipt controls, without PostgreSQL or network:

```powershell
python -X utf8 docs/review_packets/candidate_persistence_size_20261015/verify.py HEAD
```

Optional **new private rehearsal**, only with installed PostgreSQL17/psycopg:

```powershell
python -X utf8 docs/review_packets/candidate_persistence_size_20261015/rehearse.py --execute-new-local-cluster --selection jsonb-compatible-subset
```

Do not silently substitute this subset for the rejected complete package. Early
harness versions were not separately committed; failed exception/environment
receipts are retained, while final Git identities bind the delivered helper and
successful measurement. No unchanged full candidate suites or production probes
were run to obtain this result.
