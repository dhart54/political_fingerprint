# Commissioning Domain V1

This directory is the deterministic, source-grounded commissioning corpus for the 119th-Congress House `ENVIRONMENT_ENERGY` issue domain.

The corpus contains eight substantive actions grouped into four policy episodes. Shared action meaning, sources, claim maps, episode relationships, and policy traits were frozen before the eight-member cohort was selected. All real artifacts remain `human_approval_pending`, `not_promoted`, and `production_eligible: false`.

## Primary artifacts

- `domain_inventory.json` records the scored six-domain inventory and rejection reasons.
- `accepted_actions.json`, `rejected_actions.json`, `source_manifest.json`, `claim_source_map.json`, and `dossiers/` preserve action identity and evidence.
- `episode_map.json`, `policy_trait_contract.json`, and `trait_relationship_contract.json` preserve shared policy structure.
- `corpus_freeze.json` records the pre-cohort semantic freeze.
- `cohort_selection.json`, `member_overlays.json`, and `inference_candidates.json` preserve deterministic real-member evaluation.
- `actual_member_vector_evaluation.json`, `binary_vector_evaluation.json`, and `mutation_report.json` preserve broad non-persisted generality results.
- `first_failures.json` preserves initial failures and generalized corrections.
- `persistence_batch_manifest.json` is the exact immutable 74-artifact/68-relationship pending batch.
- `review_render_fixtures.json` and `renders/` contain bounded review-only frontend evidence.

The human-readable and machine-readable milestone receipts are:

- `docs/review_packets/commissioning_domain_v1.md`
- `docs/review_packets/commissioning_domain_v1.json`
- `docs/review_packets/commissioning_domain_v1_persistence.json`

Nothing in this directory grants editorial approval, benchmark status, production eligibility, or public publication.

## Eligibility and routing correction

Human inspection later identified `COMM-V1-004`: roll 5's exact Division A
retention action is not materially Environment & Energy, and unresolved shared
meaning was being propagated into member-level human-exception routes.

The original files in this directory remain unchanged historical evidence,
including the eight-action freeze, evaluations, and exact 74/68 production
batch. The distinct corrected seven-action corpus is under `corrected/`. Its
batch is prepared and disposable-tested only. The original production batch
has not been rolled back, and the corrected batch has not been applied to
production.
