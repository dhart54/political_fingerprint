# Documentation authority and retention index

This index identifies the role and retention expectation of repository documentation. It does not replace the referenced documents or change product, evidence, publication, or production semantics.

## Governing project instructions

- `AGENTS.md` is the repository-wide operating instruction file.
- A more specific user request controls the active milestone.
- `docs/PLANS.md` defines the living-plan convention for substantial work.

## Current methodology and interpretation principles

- `docs/methodology.md` records current product and evidence methodology.
- `docs/interpretation_principles.md` governs evidence-backed public interpretation and civic-language boundaries.
- `docs/amendment_evidence_pipeline.md` records the canonical amendment evidence path.
- `docs/manual_interpretation_workflow.md` governs reviewed manual interpretation packets.
- `docs/methodology/full_record_issue_interpretation_v1.md` governs expansion
  from benchmark samples to content-addressed full issue records.

These documents are canonical. Changes that affect eligibility, vote meaning, support/opposition, readiness, alignment, evidence tiers, or publication semantics require an explicit product decision.

## Mandatory workflows

- `docs/workflows/milestone-execution.md`
- `docs/workflows/bounded-production-write.md`
- `docs/workflows/product-and-rendered-validation.md`
- `docs/workflows/pr-merge-deployment.md`
- `docs/workflows/editorial-issue-frontend.md`
- `docs/workflows/editorial-standardization-pipeline.md`

The templates in `docs/workflows/MILESTONE_TEMPLATE.md` and `docs/plans/TEMPLATE.md` serve different purposes: the first shapes a milestone request and the second shapes its living execution plan.

## Active plan

Substantial work must identify exactly one active plan under `docs/plans/`. The active plan is the plan for the current branch and milestone, not the newest file by timestamp.

Active plan: [M12H/I Environment & Energy Semantic IR Acceptance and Synthesis Candidates V1](plans/m12hi_environment_energy_semantic_ir_acceptance_synthesis_v1.md)

Current review packet: [M12H/I Environment & Energy Review Packet](review_packets/m12hi_environment_energy_semantic_ir_acceptance_synthesis_v1.md)

The compact [plan status index](plans/README.md) lists retained unresolved plans, archived plans, and planning rules. Archived execution records are historical evidence, not active instructions.

## Review packets and validation receipts

`docs/review_packets/` contains human-readable review packets, machine-readable validation reports, preflight and post-write evidence, rollback SQL, and other milestone receipts.

The accepted-reference [Editorial Semantic IR V1](semantic_ir/editorial_semantic_ir_v1.md)
defines the pre-render semantic contract. Its
[accepted corpus](semantic_ir/accepted/development_cases.json) and
[acceptance receipt](semantic_ir/accepted/acceptance_receipt.md) govern the
isolated compiler test contract. The Phase A
[candidate review packet](review_packets/editorial_semantic_ir_gold_v1_candidate_review.md)
is retained as historical review evidence, and the
[dependency inventory](review_packets/editorial_pipeline_dependency_inventory_v1.md)
remains descriptive. None of these artifacts changes runtime, production, or
publication state.

The downstream
[Editorial Public Issue Presentation V1](editorial_public_issue_presentation_v1.md)
contract governs deterministic wording mapping, public tiers, publication
controls, API serialization, and display-only React.

The [Full-Record Issue Interpretation V1](methodology/full_record_issue_interpretation_v1.md)
contract separately governs review scope, completion, action accounting,
episode completion, and full-record claim eligibility. Its detached authority
schemas govern complete issue universes, universe approval, compiled full-record
Semantic IR, semantic-validation receipts, and synthesis-approval receipts;
benchmark states carry none of those full-record references.

Do not delete a review packet or asset merely because its milestone is complete. First verify builders, tests, source manifests, publication governance, restoration documentation, and inbound references. Referenced local screenshot bundles require explicit archival decisions.

## Generated required artifacts

Committed generated artifacts are required when builders or tests drift-check them, code loads them, later reports cite them, or they preserve publication, provenance, rollback, or restoration evidence. Current examples live under:

- `docs/editorial/`
- `docs/review_packets/`
- `docs/source_manifests/`
- `docs/interpretation_batches/`

Generated does not mean disposable. Regeneration must remain deterministic, and publication status must not change through regeneration.

The Environment & Energy chain has reached M12H canonical internal Behavioral
Semantic IR: three independently accepted repeated patterns retain 13 primary
episodes and the complete 63-episode disposition ledger. M12I proposes one
detached, non-authorizing congressional-disapproval `uniform_direction`
synthesis candidate using only those three propositions as semantic inputs.
Synthesis acceptance and every later authority remain inactive.

## Local-only caches and output

Local dependency, build, test, and source caches belong outside version control according to `.gitignore`. Examples include `.local/`, Python virtual environments and caches, `frontend/node_modules/`, `frontend/.next/`, Playwright `frontend/test-results/`, and external sibling worktrees.

Do not apply blanket ignore rules to `review_bundle_*` directories. Review evidence must be inspected and either retained, archived with resolvable references, or explicitly approved for deletion.

## Legacy documents requiring semantic reconciliation

The following tracked documents overlap newer authority or describe historical product/build state and require a later human semantic review before consolidation, relocation, or deletion:

- `CONSTRAINTS.md`
- `DECISIONS.md`
- `FIXTURES.md`
- `SKILLS.md`
- `TASKS.md`
- `docs/staging_readiness.md`
- `docs/product_v2_tasklist.md`
- `docs/north_star_action_plan.md`
- `docs/autonomous_handoff.md`

Until that review occurs, retain them and follow the instruction precedence in `AGENTS.md`.
