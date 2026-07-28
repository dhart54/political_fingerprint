# Foushee pre-activation canonical hashing V1

This contract defines the governed, portable identity of the exact
pre-activation editorial persistence state for the Foushee Justice publication
bundle.

## Resolution

The production reconciliation originally hashed complete PostgreSQL artifact
rows after excluding only `artifact_id`, `batch_id`, and `created_at`. That
retained database-local references such as `canonical_roll_call_id` and
`supersedes_artifact_id`. Those surrogate identifiers are not governed by the
editorial manifests and differ in a fresh disposable database even when every
governed artifact and relationship is identical.

Canonical semantic normalization V1 therefore replaces those
environment-bound hashes. The reviewed reconciliation report
`fa8ccbf5d0549ed11b75d67b58b6e20e0346c67ac6ecb0b2dd13a712fb3f3a6d`
proved that all 71 frozen-V1 artifacts and 95 relationships exactly matched the
frozen manifest, and all 69 commissioning artifacts and 60 relationships
exactly matched the corrected commissioning manifest. There were no conflicting
or dangling relationships and the two batches were additive.

The prior environment-bound fingerprint
`df9aeb1a746785395e28c177785b6f560494661af20073262efb9e1a40648ee7`
is retained only as reconciliation provenance. It is not an activation
precondition.

## Field-level mismatch diagnosis

The prior reconciliation algorithm excluded `artifact_id`, `batch_id`, and
`created_at` from artifact rows, but otherwise hashed the persisted row shape.
The same algorithm deterministically produced these results:

| Batch | Captured production | Disposable fixture | Rows with a non-null local roll-call ID |
| --- | --- | --- | ---: |
| 1 | `417f715860554764376f58786444f8e8f37a3709dbb83eefa299a97d15713adb` | `88a6dd56e59c2668ad780c2ff88fe69070e69dd9359fe57e2a5d10338747d0f5` | 22 |
| 8 | `e84b2f1cbc8d5f0a9d887d213be51098f2492af9449ff30f509497e32301e864` | `fafaabe33be59105784dcac7be097124e0fc3b5879132170668ec260c54b8cf5` | 7 |

The deterministic field comparison found:

- batch key, source commit, manifest digest, status, and declared counts matched;
- database batch IDs were different from other generated IDs but were omitted
  from the old graph, so the old digest did not bind the required IDs 1 and 8;
- batch and artifact timestamps were omitted and did not cause the mismatch;
- every artifact natural key, version, type, schema version, canonical action
  identity, payload/content digest, source identity, editorial status, benchmark
  status, production-eligibility value, and review route matched its governed
  manifest;
- `canonical_roll_call_id` remained in the old persisted-row input. It is a
  database-local foreign key, and the 22 batch-1 plus 7 batch-8 populated values
  are assigned by each database rather than governed by the manifests;
- `supersedes_artifact_id` also remained in the old input, but it was null for
  every artifact in both governed batches and therefore was not the observed
  value divergence;
- relationship direction, endpoint natural keys and versions, endpoint content
  digests, relationship type, ordinal, and metadata matched exactly;
- relationship row IDs and endpoint foreign-key IDs were already replaced by
  semantic endpoint identities;
- actor/tool metadata is not stored in these persistence tables, and batch
  metadata, update timestamps, and relationship timestamps do not exist in this
  schema;
- both calculations used the same normalized JSON value types, UTF-8 encoding,
  sorted object keys, compact separators, and deterministic list ordering.
  There was no null-versus-omitted, numeric/string, line-ending, encoding, or
  ordering divergence.

Because all governed fields matched and the remaining populated, hash-relevant
field was a local roll-call foreign key, copying the production digests into the
fixture would have preserved an environment-specific contract. V1 instead binds
the exact canonical action ID while omitting its local database surrogate.

## Canonical batch graph

`editorial_persistence_batch_graph_v1` includes:

- exact database batch ID;
- deterministic batch key;
- source commit;
- manifest digest;
- applied status;
- declared artifact and relationship counts;
- every governed manifest artifact field, including canonical action identity,
  payload, content digest, statuses, and review route;
- every relationship endpoint natural key, artifact version, content digest,
  relationship type, ordinal, and metadata.

Artifacts and relationships are sorted by their declared semantic identities.
Canonical JSON uses UTF-8, sorted object keys, compact separators, JSON null for
null values, and SHA-256.

Generated artifact IDs, relationship IDs, foreign-key surrogate IDs, batch
creation/application timestamps, and artifact creation timestamps are excluded.
Their governed identities are represented by the corresponding natural keys,
versions, content digests, canonical action IDs, and exact batch ID.

The canonical graph digests are:

- batch 1: `1f00f5adaefa9dafdb40675bf6d40a28ca4f2cf730157c2d5a69ac5854dd155a`;
- batch 8: `2423aa44bfb3e4c06de2a334f7d8775c4d48f1fe2a06df3275a650c93b2ebeb8`.

## Full sets and target absence

The two canonical artifact sets are combined and sorted by artifact type,
natural key, and version. Relationships are combined and sorted by parent
natural key, relationship type, ordinal, and child natural key.

- artifact set:
  `6a981ebf2b645d8ac8072d8aa1cc2eceef2aa861addf4a551676c4cb8c586c4f`;
- relationship set:
  `8cc57ee52040861753e147d35c5ec0680be797b8416b18e9821922a4d913cd48`;
- empty registry:
  `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`;
- schema object:
  `8536bd81b66939487aa6ef0815507f945258a7034d9ba0634046d90ce876caba`.

Target absence is a typed subdocument covering all three artifact identities,
active and inactive content digests, activation batch, registry primary key,
and partial activation relationships. Every query result must be empty. Its
canonical digest is
`430d3a044a306789123d5c7130f935c3e1783a88e8a57ed3388673b49ba75ef3`.

## Reconciled fingerprint

`editorial_publication_pre_activation_fingerprint_v1` contains the schema
digest, both ordered batch identities and graph digests, full artifact and
relationship counts and hashes, registry count and hash, the complete target
absence document, and its digest. The expected SHA-256 is
`3328dd38b4483f651a8459adec9b1d4ed2cfb8baa61ad413a282d3617d726b18`.

The stored SHA-256 is only an assertion. Every operational path recomputes the
document from live rows and rejects a mismatch before it can generate
preflight, backup, apply, or rollback evidence.
