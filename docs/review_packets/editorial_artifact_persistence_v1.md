# Editorial Artifact Persistence and Pending Seed V1

## Outcome

Migration `0016` and deterministic batch `editorial-artifact-persistence-v1-88d6f344` were applied atomically to the pinned production PostgreSQL target. The database contains 71 immutable artifacts and 95 exact-version relationships. Four real slice candidates are staged; all remain pending, unpromoted, and ineligible. The database publication registry and selector both return zero.

## Existing-schema decision

The existing `vote_interpretations` table is roll-scoped and mutable and cannot represent the accepted shared/member graph without confusing canonical vote interpretation with editorial staging. The selected additive layer retains canonical foreign keys to `legislators.bioguide_id` and `roll_calls.id`; measures and existing interpretations are unchanged.

## Reviewed objects

- Four tables: batches, immutable versions, exact relationships, and an empty publication registry.
- Two guard functions and two triggers: append-only versions and fail-closed publication activation.
- Nine query indexes plus primary/unique indexes.
- RLS on every table; no `anon` or `authenticated` direct access and no public policy.

Migration SHA-256: `bfb654b7fbcb1adc4052e31ca019d9808d8c1c35819c4a687a10cd40974ca163`.

## Seed inventory

| Artifact type | Rows |
| --- | ---: |
| shared_action_dossier | 22 |
| source_manifest | 2 |
| claim_source_map | 2 |
| policy_episode | 9 |
| policy_family | 2 |
| issue_ontology | 2 |
| policy_trait_contract | 2 |
| trait_relationship_contract | 2 |
| member_action_overlay | 4 |
| member_episode_trajectory | 4 |
| issue_conclusion_propositions | 4 |
| issue_public_presentation | 4 |
| standardization_validation_result | 4 |
| reference_fixture_metadata | 4 |
| review_routing_result | 4 |
| **Total** | **71** |

The 95 relationships reuse Justice shared evidence once across Foushee, Massie, and García. The seed excludes the 128 synthetic vector universe, malformed mutations, fictional members, large-record and screenshot fixtures, browser traces, and test-only service profiles.

Manifest SHA-256: `f8c4c24f00f3835b4c1a82e415ae7f2fde77002529b3cc3a23d0785c15efd726`.

Artifact semantic SHA-256: `00cf0ecd953ca00926612dfdf5b163f54371fb4d50c7575f668646478a5cf86b`.

Relationship semantic SHA-256: `7efc0c1230a881617acb032d411aeac4cb53afb0ee25b2b2d2d66ad97a1a0016`.

## Database validation

Disposable PostgreSQL 16:

- existing migrations `0001` through `0015` applied;
- migration `0016` applied alongside the existing schema;
- 71 artifacts and 95 relationships inserted;
- exact export semantic hashes matched the repository;
- same-hash re-import inserted zero artifacts and zero relationships;
- conflicting content, invalid types/statuses/hashes, orphan relationships, mutation of an existing version, and pending publication activation were rejected;
- internal exact/latest/list/graph/shared-evidence/validation/pending/publication reads passed;
- `anon` and `authenticated` reads were denied.

Production:

- scheme, host, port, database, and normalized username identity matched the pinned target contract;
- 3 required members and 22 canonical House roll calls resolved;
- the four new tables were absent before application;
- one advisory-locked transaction applied exact migration bytes and exact seed content;
- exact columns, functions, triggers, required indexes, constraint classes, RLS, and privileges passed;
- 71 artifacts, 95 relationships, four pending presentations, zero registry rows, and zero publication-selector rows passed;
- savepoint-contained guard probes rejected a pending activation and conflicting immutable content and committed no probe rows;
- idempotent production re-import reported 71 existing exact artifacts, zero inserts, and zero relationship inserts;
- repository → database → export hashes matched.

Canonical pre/post fingerprints were unchanged:

| Table | Rows | SHA-256 |
| --- | ---: | --- |
| legislators | 637 | `9de212550eab468793571c44b079982d8d50d3c90cb3027385e9c1f0fd336b1e` |
| bills | 967 | `203f20ed686dc0e82b9fdce3e136f36862c0b7415915d3e7126f8920cb96b1c6` |
| roll_calls | 2259 | `bbe2f09873e896e85d71c9db474c4a563e040f18c3dbc3363212bd54b131e17b` |
| vote_interpretations | 1758 | `d780cd4b34faf92baba636ed63aa82aefe9461544c9229579369b1495f35b913` |

The redacted machine report is `docs/review_packets/editorial_artifact_persistence_v1.json`.

## Publication and runtime boundary

- Every real slice: `human_approval_pending`, `not_promoted`, `productionEligible: false`.
- Database publication registry: zero.
- Static frontend production registry: empty.
- No frontend or API route reads the new tables.
- No frontend or backend deployment was performed.
- Existing vote evidence remains the public fallback; pending review slices remain available only through guarded review tooling.

## Rollback readiness

The exact-batch rollback mode is implemented and covered by schema/guard tests. It refuses mismatched hashes or publication references and leaves schema intact. It was not executed. Schema correction is forward-only.

## Limitation and next step

PR #100 remains blocked because no eligible native cross-issue evidence corpus exists; its branch was not changed. The next content milestone should build one new issue domain's shared evidence corpus, persist it through this store, and rerun cross-issue generality validation.
