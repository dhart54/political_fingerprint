# Publication Activation Governance V2

Publication Activation Governance V2 is the governing contract for future
publication activations. It is additive. Accepted V1 authorities, receipts,
registry metadata, and M11N/M12N/M13N replay remain governed by their original
contracts and must not be regenerated or reinterpreted through V2.

The rule is:

> Stable human authority does not expire. Fresh execution evidence does.

The executable boundary is
`backend/app/editorial_presentations/publication_activation_governance_v2.py`.
It must complete successfully before a production mutation transaction opens.

## Stable Authority

The V2 authority schema is
`site_integration_publication_activation_authority_v2`. Its canonical subject
contains only durable human-reviewed facts:

- `decision`
- `decision_recorded_at_utc`
- `reviewer`
- `reviewer_authority`
- `member_bioguide_id`
- `issue_id`
- `congress`
- `accepted_site_integration_binding`
  - `artifact_id`
  - `subject_sha256`
  - `file_sha256`
  - `content_sha256`
- `semantic_authority_lineage[]`
  - `artifact_id`
  - `subject_sha256`
  - `file_sha256`
  - `content_sha256`
- `preparation_authority_binding`
  - `artifact_id`
  - `authority_subject_sha256`
  - `decision_recorded_at_utc`
- `stable_runtime_binding`
  - `reviewed_runtime_manifest_sha256`
  - `reviewed_source_commit`
- `stable_production_baseline`
  - `production_target_identity_sha256`
  - `state_fingerprint_sha256`
  - `counts`
  - `existing_registry_identities` (member/issue, artifact ID/version,
    natural key, content SHA, source commit, publication-metadata SHA, and
    active state)
  - `target_registry_identity`
  - `target_artifact_natural_keys`
  - `state_predicates`
  - `write_preconditions`
- `exact_write_set_subject_sha256`
- `publication_registry_target`
- `rollback_contract_sha256`
- `expected_postconditions_sha256`
- `authorizations`

The activation decision timestamp must be truthful, timezone-aware, and no
earlier than the preparation decision it approves. The stable authority binds
the exact candidate, semantic authority lineage, reviewed runtime source,
governed production baseline, production target, write graph, rollback, and
postconditions. A change to any of those values changes or invalidates stable
authority and requires human review.

## Stable Write Set

The V2 write-set schema is `publication_activation_write_set_v2`. Its canonical
subject contains:

- `accepted_site_integration_binding`
- `preparation_authority_binding`
- `stable_runtime_binding`
- `stable_production_baseline_binding_sha256`
- `production_target_identity_sha256`
- exact `artifacts`
- exact `relationships`
- exact `publication_registry_target`
- exact `mutation_caps`
- exact `rollback_contract`
- exact `expected_postconditions`

Caps are derived from the graph and require exactly one batch and registry row,
the exact artifact and relationship counts, and zero updates, deletes, or
unauthorized-table writes. Equivalent runtime or preflight recapture cannot
change this subject because no volatile evidence identity is part of it.

## Fresh Execution Evidence

The machine captures two new evidence objects immediately before execution.
They are inputs to execution validation and later receipt provenance. They are
not human authority.

Runtime evidence records:

- `captured_at_utc`
- `healthy`
- `deployed_commit`
- `health_commit`
- `current_runtime_manifest_sha256`
- `runtime_health_proof_subject_sha256`

It must be internally hash-valid and within the configured freshness interval.
Both live commits must equal the ratified `reviewed_source_commit`, and the
current runtime manifest must equal the ratified manifest.

Transaction-read-only production evidence records:

- `captured_at_utc`
- `transaction_read_only`
- `production_target_identity_sha256`
- `state_fingerprint_sha256`
- `counts`
- `existing_registry_identities`
- `target_registry_identity`
- `target_registry_rows`
- `target_artifact_natural_keys_checked`
- `target_artifact_natural_keys_found`
- `state_predicates`
- `write_preconditions`
- `preflight_subject_sha256`

It must be internally hash-valid, fresh, and transaction-read-only. Every
governed value must exactly equal the ratified baseline. The target registry row
and all target artifacts must remain absent. All current write preconditions
must be true.

These volatile fields are intentionally excluded from stable authority and
stable write-set identity:

- runtime-health proof file SHA
- runtime-health proof subject SHA
- runtime-health `captured_at` timestamp
- execution-preflight file SHA
- execution-preflight subject SHA
- execution-preflight `captured_at` timestamp

If evidence expires, capture it again. When the new observations prove the same
runtime and state, the existing authority and write-set subjects remain valid
and execution may proceed without a new candidate, authority, or review cycle.
The execution-validation result records the exact fresh proof and preflight used.

## Fail-Closed Execution Boundary

Future executors must call `validate_execution_v2(...)` only after capturing a
fresh live health proof and transaction-read-only preflight, and before opening
the mutation transaction. The boundary performs, in order:

1. stable positive-authority validation;
2. exact candidate and write-set validation;
3. production-target validation through the ratified baseline;
4. runtime proof integrity and freshness validation;
5. exact live-runtime comparison;
6. preflight integrity, read-only status, and freshness validation;
7. exact governed-state comparison;
8. current write-precondition validation.

No failed or stale result authorizes mutation. Refreshing stale evidence is a
mechanical capture operation, not human orchestration.

## Review Reopen Conditions

Human review reopens when any stable governed fact differs, including:

- semantics or semantic authority lineage;
- candidate identity or bytes;
- preparation authority;
- reviewed runtime manifest or source commit;
- production target;
- baseline state fingerprint, counts, registry identities, target-absence
  predicates, or other governed state predicates;
- artifact or relationship graph;
- registry target or mutation caps;
- rollback contract;
- expected postconditions;
- positive authorization scope.

The machine must not decide that a changed stable fact is harmless, regenerate a
new stable write set under old authority, weaken freshness, or broaden the write
envelope. It must stop and route the changed facts for review.
