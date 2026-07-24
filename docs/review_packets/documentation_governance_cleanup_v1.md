# Documentation Governance Cleanup V1

## Scope and baseline

- Starting `origin/main`: `98029d77ad43f7e877eb545b25d9b6878e71cb1a`.
- Branch: `codex/documentation-governance-cleanup-v1`.
- Final branch head: reported by Git and the draft PR after commit creation; a commit cannot contain its own hash.
- Delivery: initial milestone commit `0cd6f733b70328374acf41c85c56badbdd8ea1fd`; draft PR #103.
- Root was clean and exactly matched fetched `origin/main` before branch creation.
- Recovery package, recovery branch `codex/recovery-root-20260724-38ad159`, named preservation stash, and detached validation worktree were present.
- All registered child worktrees were outside the repository root.
- `frontend/lib/editorialIssueProductionSlices.mjs` remained a frozen empty array.
- No production write, application change, civic-semantics change, publication, promotion, approval, merge, or deployment occurred.

## Classification method

The machine-readable hygiene audit supplied the only automatic archival candidates. Each candidate was rechecked on current `origin/main` for checklist state, final reconciliation, latest Git history, inbound tracked references, and code/builder/test/manifest use. Filenames and age were not treated as terminal evidence.

All confirmed candidates had zero unchecked checklist items and documented a terminal milestone reconciliation. Their contents describe historical execution rather than current authority. The audit Markdown and JSON remain unchanged historical provenance for every candidate.

## Complete archive manifest

Each `archive_confirmed` row moved from `docs/plans/<name>` to `docs/plans/archive/2026/<name>` with `git mv`.

| Plan | Decision | Terminal evidence and dependency result |
| --- | --- | --- |
| `118th_house_amendment_evidence.md` | `archive_confirmed` | 27/27 checked; definition of done satisfied; no live consumer |
| `blind_editorial_pipeline_validation_v1.md` | `archive_confirmed` | 29/29 checked; implementation and delivery reconciled; no live consumer |
| `caveat_density_cleanup.md` | `archive_confirmed` | 12/12 checked; focused cleanup complete; no live consumer |
| `current_house_member_metadata_hardening_v1.md` | `archive_confirmed` | 32/32 checked; exact-provenance milestone complete; no live consumer |
| `current_house_member_metadata_schema_seed_v1.md` | `archive_confirmed` | 49/49 checked; schema/seed milestone complete; no live consumer |
| `data_expansion_readiness_audit_v1.md` | `archive_confirmed` | 15/15 checked; audit complete; no live consumer |
| `data_inventory_source_manifest_v1.md` | `archive_confirmed` | 15/15 checked; manifest milestone complete; no live consumer |
| `editorial_artifact_persistence_v1.md` | `archive_confirmed` | 12/12 checked; persistence result merged in PR #101; no live consumer |
| `episode_first_editorial_product_v1.md` | `archive_confirmed` | 20/20 checked; implementation/delivery reconciled; no live consumer |
| `fallback_static_loading_copy_cleanup.md` | `archive_confirmed` | 13/13 checked; focused cleanup complete; no live consumer |
| `frontend_lint_next15_gate.md` | `archive_confirmed` | 12/12 checked; lint gate complete; no live consumer |
| `generic_editorial_issue_frontend.md` | `archive_confirmed` | 13/13 checked; definition of done satisfied; no live consumer |
| `golden_profile_read_v1.md` | `archive_confirmed` | 14/14 checked; definition of done satisfied; no live consumer |
| `golden_public_reads_v1.md` | `archive_confirmed` | 12/12 checked; checkpoint complete; no live consumer |
| `golden_render_validation_harness_v1.md` | `archive_confirmed` | 14/14 checked; draft-PR delivery complete; no live consumer |
| `house_comparable_family_legislator_helper.md` | `archive_confirmed` | 15/15 checked; merged historical helper milestone; no live consumer |
| `house_record_across_congresses_adapter.md` | `archive_confirmed` | 14/14 checked; merged historical adapter milestone; no live consumer |
| `internal_record_across_congresses_production_validation.md` | `archive_confirmed` | 14/14 checked; validation milestone complete; no live consumer |
| `internal_route_auth_convention.md` | `archive_confirmed` | 14/14 checked; merged route milestone; no live consumer |
| `justice_cross_member_validation_v1.md` | `archive_confirmed` | 14/14 checked; validation/publication isolation complete; no live consumer |
| `legislative_interpretation_quality_benchmark_v1.md` | `archive_confirmed` | 12/12 checked; analytical milestone complete; no live consumer |
| `public_copy_safety_contract.md` | `archive_confirmed` | 12/12 checked; contract/draft-PR milestone complete; no live consumer |
| `public_editorial_product_frontend_v1.md` | `archive_confirmed` | 13/13 checked; implementation and isolation complete; no live consumer |
| `record_across_congresses_frontend_contract.md` | `archive_confirmed` | 12/12 checked; contract milestone complete; no live consumer |
| `record_across_congresses_frontend_prototype.md` | `archive_confirmed` | 11/11 checked; prototype milestone complete; no live consumer |
| `record_across_congresses_internal_transport.md` | `archive_confirmed` | 14/14 checked; merged transport milestone; no live consumer |
| `show_votes_proof_hierarchy.md` | `archive_confirmed` | 15/15 checked; focused hierarchy milestone complete; no live consumer |
| `top_summary_drift_cleanup.md` | `archive_confirmed` | 14/14 checked; focused cleanup complete; no live consumer |
| `valerie_foushee_economy_editorial_gold_v2.md` | `archive_confirmed` | 15/15 checked; review-only candidate milestone complete; no live consumer |
| `valerie_foushee_economy_staged_website_v2.md` | `archive_confirmed` | 13/13 checked; staged review milestone reconciled; no live consumer |
| `valerie_foushee_justice_public_safety_gold_v1.md` | `archive_confirmed` | 24/24 checked; draft-PR delivery complete; no live consumer |
| `zip_district_ambiguity_hardening_v1.md` | `archive_confirmed` | 15/15 checked; audit milestone complete; no live consumer |
| `zip_multi_row_readonly_route_eval_v1.md` | `archive_confirmed` | 15/15 checked; definition of done satisfied; no live consumer |
| `zip_multi_row_schema_migration_application_coverage_v1.md` | `archive_confirmed` | 16/16 checked; migration-application milestone complete; no live consumer |
| `zip_overlap_sensitivity_bounded_staging_design_v1.md` | `archive_confirmed` | 13/13 checked; design/safety milestone complete; no live consumer |
| `zip_population_weighted_ambiguity_evaluation_v1.md` | `archive_confirmed` | 15/15 checked; evaluation milestone complete; no live consumer |
| `zip_schema_application_coverage_seed_readiness_v1.md` | `archive_confirmed` | 13/13 checked; readiness milestone complete; no live consumer |
| `zip_source_approval_dry_run_harness_v1.md` | `archive_confirmed` | 14/14 checked; dry-run milestone complete; no live consumer |
| `zip_source_backed_ingestion_preflight_v1.md` | `archive_confirmed` | 18/18 checked; preflight milestone complete; no live consumer |
| `zip_source_member_readiness_gate_v1.md` | `archive_confirmed` | 12/12 checked; readiness gate complete; no live consumer |
| `zip_source_retrieval_official_file_dry_run_v1.md` | `archive_confirmed` | 13/13 checked; retrieval dry-run complete; no live consumer |
| `zip_source_metadata_ambiguity_payload_v1.md` | `blocked_reference_dependency` | 9/9 checked, but `backend/scripts/generate_zip_source_metadata_report.py` loads the exact path |

The blocked plan remains at its original path. No redirect stub was created and no runtime code was changed.

## Retained unresolved plans

| Plan | Assessment | Routing |
| --- | --- | --- |
| `2026_evidence_eligibility_interpretation_expansion.md` | Core production/reconciliation work is recorded, but the definition-of-done and delivery items were never checked off. | `retain_unresolved`; completed but unreconciled; human terminal-status decision required |
| `codex_operating_model.md` | The current operating model exists, but the plan retains unchecked delivery and final-reconciliation items. | `retain_unresolved`; completed but unreconciled; human terminal-status decision required |
| `current_congress_freshness_ingestion.md` | Production refresh, tests, and idempotency are recorded; PR/merge/deployment remain unchecked. | `retain_unresolved`; completed but unreconciled; human terminal-status decision required |
| `zip_schema_source_metadata_design_v1.md` | Design packet and validation exist; commit/push/PR is unchecked, and later ZIP filenames do not prove supersession. | `retain_unresolved`; completed but unreconciled; human terminal-status decision required |

The blocked cross-issue generality plan remains distinct on its clean unmerged branch. It was not merged, copied, deleted, or treated as active content expansion.

## Reference reconciliation

Changed navigational references:

- `docs/README.md` now identifies this branch's single active plan and links to the plan status index.
- `docs/plans/README.md` provides active, retained-unresolved, archive, and template/rules navigation.
- `docs/plans/archive/2026/README.md` supplies the archive authority boundary.

No current navigational link pointed directly to a moved plan. These historical literals deliberately remain unchanged:

- the candidate paths in `repository_hygiene_audit_v1.md` and `.json`, because they are the starting manifest;
- `docs/review_packets/golden_public_reads_v1.md` → old plan path;
- `docs/review_packets/show_votes_proof_hierarchy.md` → old plan path;
- `docs/review_packets/zip_source_backed_ingestion_preflight_v1.json` → old plan path.

Those three packet references record what the receipt cited at the time; rewriting them would make immutable historical evidence appear to have originally used the archive location.

## Legacy authority reconciliation proposal

No legacy document was moved, deleted, consolidated, substantially rewritten, or given a banner. The classifications below propose later action; they do not change authority.

| Source and sections | Classification | Canonical destination / unique-rule risk | Recommended later action and evidence |
| --- | --- | --- | --- |
| `CONSTRAINTS.md` §§1, 3, 13, 15–22 | `current_duplicate` | `AGENTS.md`, methodology, and interpretation principles cover determinism, civic language, evidence, alignment, readiness, grouping, and chamber integrity; some schema-field specificity could be lost. | Reconcile exact technical invariants into methodology/architecture docs, then retain this file as dated history. High confidence from direct rule comparison. |
| `CONSTRAINTS.md` §§2, 5–12, 14 | `historical_context` | Legacy fingerprint/drift/median/API/cost invariants are not the current product's sole authority; mathematical and contract details may still be unique. | Human technical review against current schema/routes before any archival. Medium confidence; no semantic preference applied. |
| `CONSTRAINTS.md` §4 | `human_product_decision_required` | The absolute “ineligible votes must not have a primary domain” wording may be narrower than current non-counting procedural-context visibility. | Decide the classification-domain versus interpretation-domain boundary explicitly before consolidation. Medium confidence. |
| `DECISIONS.md` 2026-02-28 entries | `historical_context` | Preserves original MVP decisions; later v2 entries explicitly describe the MVP as historical. | Keep as dated decision history or split into an ADR archive after human review. High confidence. |
| `DECISIONS.md` 2026-06-05 product/guardrail entries | `current_duplicate` | Current methodology and interpretation principles contain the operative civic rules. | Link to canonical docs and retain the dated rationale. High confidence. |
| `DECISIONS.md` workflow entry | `superseded_implementation_guidance` | `AGENTS.md` and mandatory workflows now govern branches, PRs, stopping, and completion. | Mark the workflow entry historical in a later non-semantic cleanup. High confidence. |
| `FIXTURES.md` §§1–11 | `superseded_implementation_guidance` | Exact fixture behavior is now enforced by fixture files and tests; the document still preserves intended edge cases. | Compare every asserted fixture count/path to current tests, migrate any unique invariant, then archive as MVP fixture history. Medium-high confidence. |
| `SKILLS.md` core, domains, eligibility, classification, calculations, ETL, summaries, API, tests | `current_duplicate` | Mostly overlaps constraints, methodology, code, and tests; exact keyword/algorithm recipes risk drifting from implementation. | Replace instruction authority with links to canonical implementation/tests after a technical diff. Medium-high confidence. |
| `SKILLS.md` interpretation, readiness, confidence, grouping, alignment | `current_duplicate` | Civic rules overlap current methodology and interpretation principles. | Preserve any unique field-level rule in methodology before archival. High confidence. |
| `TASKS.md` phases 0–11 and completion | `historical_context` | A completed MVP build log; no current execution authority is needed. | Add an unambiguous historical banner or archive later. High confidence. |
| `docs/staging_readiness.md` current status and latest verification | `status_stale` | Dated 2026-05-15 and predates later product/deployment milestones. | Re-run a separately authorized staging assessment or label the status snapshot historical. High confidence. |
| `docs/staging_readiness.md` limits, environment, checks, review focus | `current_duplicate` | Deployment and rendered-validation workflows are canonical; reviewer questions remain useful. | Merge still-valid checklist items into canonical workflows after environment verification. Medium confidence. |
| `docs/product_v2_tasklist.md` phases 1–11, 14–15 | `historical_context` | Checked roadmap history, not current execution authority. | Preserve as roadmap history or convert to dated status receipt. High confidence. |
| `docs/product_v2_tasklist.md` working priority | `status_stale` | Refers to an earlier Valerie checkpoint and handoff state. | Replace only after a human selects the next product milestone. High confidence. |
| `docs/product_v2_tasklist.md` phases 12–13, shelved ideas, follow-up polish | `human_product_decision_required` | Contains unfinished NC/state expansion and future product ideas not made canonical elsewhere. | Product owner decides retain, supersede, or commission as separate milestones. High confidence that a decision is required. |
| `docs/north_star_action_plan.md` destination, evidence ladder, civic action, decision rules | `current_duplicate` | Product identity, methodology, and interpretation principles carry the operative boundaries. | Preserve concise unique product rationale in a canonical product strategy document. High confidence. |
| `docs/north_star_action_plan.md` current state, phases A–I, immediate tasks | `status_stale` | Mixes implemented, deferred, and future work from an earlier repository state. | Reconcile status section by section only after product-owner sequencing decisions. High confidence. |
| `docs/autonomous_handoff.md` branch, completed work, checkpoint, verification, next tasks | `status_stale` | Names `codex/ballot-north-star`, 2026-05-19 state, and old commands/results. | Retain as historical handoff evidence; do not use as current instruction. High confidence. |
| `docs/autonomous_handoff.md` operating mode | `superseded_implementation_guidance` | `AGENTS.md` and workflows now govern execution and validation. | Later add a historical banner or archive after inbound-reference review. High confidence. |

No section was classified `conflicts_with_current_authority` with sufficient confidence to justify a semantic change. Potential semantic tension was routed to `human_product_decision_required`.

## Governance check

`scripts/check_documentation_governance.py` deterministically checks:

- every tracked repository-relative Markdown link target;
- machine-specific link targets in current navigational documentation;
- the active-plan link in `docs/README.md`;
- active-plan existence and non-archive location;
- exactly one active plan in the plan index;
- duplicate plan status entries;
- plan-index link existence;
- the archive README requirement.

It introduces no dependency or generated documentation framework.

## Explicitly untouched

- `docs/editorial/**`
- `docs/source_manifests/**`
- pre-existing machine-generated review JSON
- rollback SQL and migrations
- backend/frontend application code and production registries
- review screenshot bundles and editorial artifacts
- external recovery package, stash, branch, and validation worktree
- external child worktrees, including the blocked cross-issue branch

## Deviations, stops, and exact human decisions

- One audit candidate was not moved because a live builder consumes its exact path. This is the intended `blocked_reference_dependency` outcome, not a weakened classification.
- No candidate required altering immutable evidence.
- No pre-existing documentation ambiguity required weakening the checker.
- Human decision 1: confirm whether each of the four retained unresolved plans is terminal, paused, superseded, or still active, and reconcile its checklist before archival.
- Human decision 2: decide whether the legacy fingerprint/drift/API invariants remain current technical authority before consolidating `CONSTRAINTS.md`.
- Human decision 3: decide whether the remaining NC/state roadmap and evidence-card polish items remain product priorities.
- Human decision 4: decide whether to change the report builder's pinned plan path; only a later code-authorized milestone can unblock that plan's archival.

## Validation

| Check | Result |
| --- | --- |
| Refetched `origin/main` | unchanged at `98029d77ad43f7e877eb545b25d9b6878e71cb1a` |
| Deterministic Markdown links and documentation governance | passed |
| Checker syntax compilation | passed |
| JSON receipt parse | passed |
| Machine-specific navigational-link search | zero |
| Old-path search | 41 moved paths checked; only three documented historical receipts outside the audit/archive; zero unexpected |
| Unresolved-plan location | all four unresolved plans and the blocked builder-dependent plan remain at original paths |
| Protected deletion search | zero deletions; zero review-packet/editorial/source-manifest/rollback/migration/bundle deletions |
| Production registry | frozen empty array |
| Worktree integrity | all seven registered paths exist; zero registered child worktrees beneath root |
| `git diff --check` | passed |

Final branch status and name-status were clean after the initial milestone commit and are rerun after this delivery reconciliation. Application builds were intentionally omitted because application behavior did not change.
