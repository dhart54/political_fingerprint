# Repository and Documentation Hygiene Audit V1

Audit date: 2026-07-24
Mode: read-only investigation followed by creation of this report and its JSON companion only
Repository: `C:\Users\Dylan\Documents\Data Science\political_fingerprint`

## Decision

Do not run a broad cleanup.

The repository has three different kinds of state that currently look like one dirty checkout:

1. a stale root branch whose uncommitted files mostly reproduce work already committed and merged;
2. five registered worktrees nested under the root checkout;
3. local review evidence, test output, caches, and source caches with different retention requirements.

The stop condition in the request was reached. `review_bundle_frontend_data_grounding/` is referenced by:

- `docs/review_packets/chamber_filtering_data_integrity_audit.md`;
- several tracked ZIP plans that identify it as a preserved unrelated artifact;
- its own builder and trace documents.

It is therefore not disposable and is excluded from automatic cleanup. Two newer screenshot bundles are also named by tracked validation packets. They may be called “disposable local captures” in those packets, but deleting them would remove the exact rendered evidence named by the validation record. Human approval is required.

## Baseline

| Surface | Observed state |
| --- | --- |
| Remote `main`, queried without fetch | `3d0ffb252c54fb8b93e58fbd4724724ec40a2790`, `Persist editorial artifacts and seed pending review outcomes (#101)` |
| Local `origin/main` | Same commit as the remote query |
| Root checkout | `codex/foushee-justice-public-safety-gold-v1` at `38ad15999f4bfcea85c8777f25da816888750942` |
| Root upstream | Behind `origin/codex/foushee-justice-public-safety-gold-v1` by three commits |
| Root tracked changes before this report | 20 modified files, 1,562 insertions and 146 deletions relative to root `HEAD` |
| Root untracked substantive state before this report | 3 source/artifact files already present identically on `origin/main`; 1 unique chamber audit; 1 review bundle tree |
| Dedicated `main` worktree | Clean tracked tree at `88d6f3446f54b07735e084cbc958c1614b190fab`, one commit behind `origin/main` |

No fetch was run. `git ls-remote origin refs/heads/main` confirmed the remote hash without changing local Git metadata.

## Registered worktrees

| Exact path | Branch | Tracked state | Untracked state | Classification |
| --- | --- | --- | --- | --- |
| `C:\Users\Dylan\Documents\Data Science\political_fingerprint` | `codex/foushee-justice-public-safety-gold-v1` | dirty | unique audit and review bundle, plus files duplicated on `origin/main` | `unresolved_human_decision` |
| `_codex_worktrees/blind-editorial-pipeline-validation-v1` | `codex/blind-editorial-pipeline-validation-v1` | clean | generated test cases, Playwright state, four referenced screenshots | `move_outside_repository` |
| `_codex_worktrees/cross-issue-editorial-generality-v1` | `codex/cross-issue-editorial-generality-v1` | clean | none visible | `move_outside_repository` |
| `_codex_worktrees/editorial-artifact-persistence-v1` | `codex/editorial-artifact-persistence-v1` | clean | none visible | `move_outside_repository` |
| `_codex_worktrees/justice-cross-member-validation-v1` | `codex/justice-cross-member-validation-v1` | clean; upstream remote branch is gone | ignored build/dependency state | `move_outside_repository` |
| `_codex_worktrees/public-editorial-product-frontend-v1` | `main` | clean, behind `origin/main` by one | Playwright state and 15 referenced screenshots | `move_outside_repository` |

The blind-validation and Justice cross-member branch heads are ancestors of current `origin/main`, as is the dedicated `main` worktree’s current commit. The artifact-persistence content landed in `origin/main` through PR #101, but its branch head is a sibling rather than an ancestor, consistent with a squash-style merge. The cross-issue branch is a clean, blocked-result sibling branch and is not merged into `origin/main`.

### Worktree location decision

`_codex_worktrees/` should move outside the repository. Its current placement makes every registered checkout appear as one untracked root directory, causes recursive searches to traverse multiple repository snapshots, multiplies dependency/build storage, and makes broad status and artifact inventory misleading.

Recommended sibling root:

```text
C:\Users\Dylan\Documents\Data Science\political_fingerprint-worktrees\
```

Use Git’s worktree command for each registered child; do not use Explorer, `Move-Item`, or a raw directory move:

```powershell
New-Item -ItemType Directory -Path 'C:\Users\Dylan\Documents\Data Science\political_fingerprint-worktrees'
git worktree move 'C:\Users\Dylan\Documents\Data Science\political_fingerprint\_codex_worktrees\blind-editorial-pipeline-validation-v1' 'C:\Users\Dylan\Documents\Data Science\political_fingerprint-worktrees\blind-editorial-pipeline-validation-v1'
git worktree move 'C:\Users\Dylan\Documents\Data Science\political_fingerprint\_codex_worktrees\cross-issue-editorial-generality-v1' 'C:\Users\Dylan\Documents\Data Science\political_fingerprint-worktrees\cross-issue-editorial-generality-v1'
git worktree move 'C:\Users\Dylan\Documents\Data Science\political_fingerprint\_codex_worktrees\editorial-artifact-persistence-v1' 'C:\Users\Dylan\Documents\Data Science\political_fingerprint-worktrees\editorial-artifact-persistence-v1'
git worktree move 'C:\Users\Dylan\Documents\Data Science\political_fingerprint\_codex_worktrees\justice-cross-member-validation-v1' 'C:\Users\Dylan\Documents\Data Science\political_fingerprint-worktrees\justice-cross-member-validation-v1'
git worktree move 'C:\Users\Dylan\Documents\Data Science\political_fingerprint\_codex_worktrees\public-editorial-product-frontend-v1' 'C:\Users\Dylan\Documents\Data Science\political_fingerprint-worktrees\main'
git worktree list --porcelain
git worktree repair
```

Run those commands only after copying or deliberately retaining the referenced review bundles and after removing low-value build caches if disk and move time matter. Do not use `git worktree remove` as a substitute: removal would delete the checkout and its local-only evidence.

## Dirty root checkout recovery

### What is already recoverable from Git

Of the root’s modified or substantive untracked files, 19 working-file blobs are byte-identical to `origin/main`. The following four working-file blobs differ from current `origin/main`, but each blob already occurs in committed history:

- `docs/workflows/editorial-issue-frontend.md`
- `frontend/lib/editorialIssueExperience.test.mjs`
- `frontend/lib/editorialIssueReviewSlices.mjs`
- `frontend/tests/golden-render.spec.mjs`

Their working blobs appear in commits from the correction, cross-member, or public-frontend sequence. They are not unique uncommitted content, but a recovery snapshot should still preserve them before the root branch changes.

The unique material that is not on `origin/main` is:

- `docs/review_packets/chamber_filtering_data_integrity_audit.md`
- `review_bundle_frontend_data_grounding/` and its 19 files

The bundle also contains one exact duplicate pair:

- `review_bundle_frontend_data_grounding/tests_and_build.txt`
- `review_bundle_frontend_data_grounding/raw/test_output_logs.txt`

Both have SHA-256 `2F0AB476361E20BA60FD20D15A09504DBA20DB513037EB0766B3143B749F53B2`. Do not deduplicate them automatically because the bundle is a protected provenance unit.

### Required recovery sequence

Before switching, resetting, cleaning, or repurposing the root:

1. Create an external recovery directory named with the audit date and root commit.
2. Export `git diff --binary HEAD` to that external directory.
3. copy the unique chamber audit and the entire review bundle to the recovery directory;
4. record SHA-256 hashes for every copied file and the current `git status --porcelain=v2 --branch`;
5. create a recovery branch at `38ad15999f4bfcea85c8777f25da816888750942`;
6. only with human approval, commit the intended root work on that recovery branch or preserve it solely as the external patch/bundle;
7. verify the patch with `git apply --check` in a temporary clean worktree based on the recovery commit;
8. verify the chamber audit links to the restored bundle;
9. only then convert the root path to a clean `main` checkout.

Suggested external recovery location:

```text
C:\Users\Dylan\Documents\Data Science\political_fingerprint-recovery\2026-07-24-root-38ad159\
```

The recovery package must contain:

```text
root-tracked.patch
root-status-porcelain-v2.txt
sha256.json
untracked/docs/review_packets/chamber_filtering_data_integrity_audit.md
untracked/review_bundle_frontend_data_grounding/**
```

## Classification matrix

The JSON companion contains the machine-readable records. This section records the actionable decisions.

### `keep_canonical`

| Exact path | Status | Owner / inbound references | Breakage if deleted | Confidence and rationale |
| --- | --- | --- | --- | --- |
| `docs/review_packets/chamber_filtering_data_integrity_audit.md` | untracked in root; absent from `origin/main` | References the bundle builder, raw excerpts, frontend tests, backend query paths, and fixture integrity evidence; several tracked plans already name it as preserved | Removes the only documented explanation that the Foushee/Senate mismatch is fixture-only and removes the recommended guardrail record | High; retain, review, and eventually track |
| `docs/workflows/bounded-production-write.md` | tracked | `AGENTS.md`, milestone template, operating-model packet | Breaks production-safety workflow | High |
| `docs/workflows/editorial-issue-frontend.md` | tracked and modified in root | PR workflow and current editorial implementation | Breaks the issue-publication workflow; root copy is historical while `origin/main` is canonical | High |
| `docs/workflows/editorial-standardization-pipeline.md` | tracked on `origin/main` | current editorial builders/tests and new artifact-persistence work | Breaks generator and validation governance | High |
| `docs/workflows/milestone-execution.md` | tracked | `AGENTS.md`, milestone template, operating-model packet | Breaks milestone operating model | High |
| `docs/workflows/pr-merge-deployment.md` | tracked | `AGENTS.md`, plans, milestone template | Breaks merge/deployment governance | High |
| `docs/workflows/product-and-rendered-validation.md` | tracked | `AGENTS.md`, milestone template | Breaks rendered-validation governance | High |
| `docs/workflows/MILESTONE_TEMPLATE.md` | tracked | operating-model packet | Distinct from the living-plan template; not a duplicate | High |
| `docs/plans/TEMPLATE.md` | tracked | `docs/PLANS.md`, operating-model packet | Breaks the living-plan convention | High |
| `README.md` | tracked | repository entry point | Deletion breaks entry point; five local links need repair from absolute WSL paths to repository-relative paths | High |

No byte-identical duplicates were found among tracked Markdown documents. The six workflow/runbook documents and the milestone template have distinct purposes; none is obsolete duplication.

### `generated_required`

These are deterministic or provenance-bearing outputs. They are generated, but deletion would break tests, drift checks, source manifests, publication boundaries, or rollback/restoration:

- `docs/editorial/valerie_foushee_justice_public_safety_gold_v1/policy_episode_map.json`
- `docs/editorial/valerie_foushee_justice_public_safety_gold_v1/review_packet.json`
- `docs/editorial/valerie_foushee_justice_public_safety_gold_v1/source_manifest.json`
- `docs/editorial/valerie_foushee_justice_public_safety_gold_v1/episode_inference.json`
- `docs/editorial/valerie_foushee_economy_gold_v2/review_packet.json`
- `docs/editorial/valerie_foushee_economy_gold_v2/source_manifest.json`
- `docs/review_packets/data_inventory_source_manifest_v1.json`
- `docs/review_packets/editorial_artifact_persistence_v1.json`
- `docs/review_packets/editorial_standardization_validation_v1.json`
- `docs/review_packets/legislative_interpretation_quality_benchmark_v1.json`
- `docs/review_packets/record_across_congresses_frontend_copy_guardrails.json`
- `docs/review_packets/current_house_member_metadata_hardening_v1/normalized_snapshot.json`
- `docs/review_packets/current_house_member_metadata_hardening_v1/normalized_snapshot_artifacts.json`
- `docs/review_packets/current_house_member_metadata_hardening_v1/normalized_member_service.json`
- `docs/review_packets/current_house_member_metadata_hardening_v1/normalized_member_service_evidence_artifacts.json`
- `docs/review_packets/current_house_member_metadata_hardening_v1/normalized_seat_status.json`
- `docs/review_packets/current_house_member_metadata_hardening_v1/normalized_seat_status_evidence_artifacts.json`
- every tracked `docs/review_packets/*rollback*.sql`
- every tracked source manifest under `docs/source_manifests/`
- every tracked machine artifact under `docs/editorial/blind_editorial_pipeline_validation_v1/`
- every tracked machine artifact under `docs/editorial/justice_cross_member_validation_v1/`

Owners include the corresponding `backend/scripts/build_*`, `generate_*`, `analyze_*`, `apply_*`, and frontend build scripts. Confirmed drift checks include the Valerie Justice `--check` builder test, the Valerie Economy review builder, the blind editorial builder/validator, ZIP report generators, benchmark scorer, and data-inventory generator. Source manifests and rollback SQL preserve provenance and restoration paths even when they have no executable inbound reference.

### `archive`

Completed plans should remain in Git history but move, in a dedicated documentation-only milestone, to `docs/plans/archive/YYYY/`. Moving them requires reference updates and human approval. At minimum, this applies to:

- `docs/plans/118th_house_amendment_evidence.md`
- `docs/plans/blind_editorial_pipeline_validation_v1.md`
- `docs/plans/caveat_density_cleanup.md`
- `docs/plans/current_house_member_metadata_hardening_v1.md`
- `docs/plans/current_house_member_metadata_schema_seed_v1.md`
- `docs/plans/data_expansion_readiness_audit_v1.md`
- `docs/plans/data_inventory_source_manifest_v1.md`
- `docs/plans/editorial_artifact_persistence_v1.md`
- `docs/plans/episode_first_editorial_product_v1.md`
- `docs/plans/fallback_static_loading_copy_cleanup.md`
- `docs/plans/frontend_lint_next15_gate.md`
- `docs/plans/generic_editorial_issue_frontend.md`
- `docs/plans/golden_profile_read_v1.md`
- `docs/plans/golden_public_reads_v1.md`
- `docs/plans/golden_render_validation_harness_v1.md`
- `docs/plans/house_comparable_family_legislator_helper.md`
- `docs/plans/house_record_across_congresses_adapter.md`
- `docs/plans/internal_record_across_congresses_production_validation.md`
- `docs/plans/internal_route_auth_convention.md`
- `docs/plans/justice_cross_member_validation_v1.md`
- `docs/plans/legislative_interpretation_quality_benchmark_v1.md`
- `docs/plans/public_copy_safety_contract.md`
- `docs/plans/public_editorial_product_frontend_v1.md`
- `docs/plans/record_across_congresses_frontend_contract.md`
- `docs/plans/record_across_congresses_frontend_prototype.md`
- `docs/plans/record_across_congresses_internal_transport.md`
- `docs/plans/show_votes_proof_hierarchy.md`
- `docs/plans/top_summary_drift_cleanup.md`
- `docs/plans/valerie_foushee_economy_editorial_gold_v2.md`
- `docs/plans/valerie_foushee_economy_staged_website_v2.md`
- `docs/plans/valerie_foushee_justice_public_safety_gold_v1.md`
- `docs/plans/zip_district_ambiguity_hardening_v1.md`
- `docs/plans/zip_multi_row_readonly_route_eval_v1.md`
- `docs/plans/zip_multi_row_schema_migration_application_coverage_v1.md`
- `docs/plans/zip_overlap_sensitivity_bounded_staging_design_v1.md`
- `docs/plans/zip_population_weighted_ambiguity_evaluation_v1.md`
- `docs/plans/zip_schema_application_coverage_seed_readiness_v1.md`
- `docs/plans/zip_source_approval_dry_run_harness_v1.md`
- `docs/plans/zip_source_backed_ingestion_preflight_v1.md`
- `docs/plans/zip_source_member_readiness_gate_v1.md`
- `docs/plans/zip_source_metadata_ambiguity_payload_v1.md`
- `docs/plans/zip_source_retrieval_official_file_dry_run_v1.md`

Historical snapshot packets suitable for an archive subtree, but not deletion:

- `docs/review_packets/valerie_economy_taxes_current_state.md`
- `docs/review_packets/valerie_economy_taxes_after_overview_pass.md`
- `docs/review_packets/valerie_justice_public_safety_current_state.md`
- `docs/review_packets/valerie_justice_public_safety_after_generic_language_pass.md`
- `docs/review_packets/evidence_depth_coverage_expansion_plan.md`
- `docs/autonomous_handoff.md`

The three review bundles are also `archive`, not delete:

- `review_bundle_frontend_data_grounding/`
- `_codex_worktrees/blind-editorial-pipeline-validation-v1/review_bundle_blind_editorial_pipeline_validation_v1/`
- `_codex_worktrees/public-editorial-product-frontend-v1/review_bundle_public_editorial_product_frontend_v1/`

Recommended destination: an external immutable review archive or a versioned `docs/review_packets/archive/YYYY/<milestone>/assets/` tree, with every inbound reference updated in the same commit.

### `safe_to_delete`

Only these items are eligible for automatic cleanup after this audit is approved:

- `docs/.gitkeep` — tracked; `docs/` is populated; no inbound reference.
- `_codex_worktrees/blind-editorial-pipeline-validation-v1/frontend/test-results/.last-run.json` — untracked Playwright run state; no inbound reference.
- `_codex_worktrees/public-editorial-product-frontend-v1/frontend/test-results/.last-run.json` — untracked Playwright run state; no inbound reference.
- `_codex_worktrees/blind-editorial-pipeline-validation-v1/backend/tests/_data_inventory_cases/` — untracked deterministic test output; `test_data_inventory_manifest.py` deletes and recreates each case.

No review screenshot, review packet, JSON report, SQL rollback, source manifest, or root dirty file is on the automatic cleanup list.

### `local_only_ignore`

| Exact path | Status / owner | Recommended ignore rule | Deletion impact |
| --- | --- | --- | --- |
| `.local/` | ignored; 7,999 readable files, about 3.40 GB; test bases, logs, fetched metadata, and local reports | already covered by `.local/` | Do not bulk-delete; contains source/provenance caches used for offline validation |
| `.pytest_cache/` | ignored pytest cache | already covered by `.pytest_cache/` | Regenerable |
| `backend/.pytest_cache/` | ignored pytest cache | already covered by `.pytest_cache/` | Regenerable |
| `backend/.venv/` | ignored Python environment | already covered by `.venv/` | Regenerable, but local setup cost |
| `backend/.venv_win/` | self-ignored by its internal `.gitignore`; about 40 MB | add `backend/.venv_win/` for visible root policy | Regenerable, but used by the Windows preview runbook |
| `backend/data_sources/` | ignored source cache; about 205 MB | already covered | May be required for offline source validation; retain unless separately archived |
| `frontend/.next/` | ignored Next build output; about 214 MB | already covered by `.next/` | Regenerable |
| `frontend/node_modules/` | ignored dependencies; about 588 MB | already covered by `node_modules/` | Regenerable |
| `.codex_pytest_staged_final/` | unignored and ACL-inaccessible | add `/.codex_pytest*/` | Treat as local test temp; inspect owner/ACL before deletion |
| `.pytest_tmp_phase21_final/` | unignored and ACL-inaccessible | add `/.pytest_tmp*/` | Treat as local test temp; inspect owner/ACL before deletion |
| `.pytest_tmp_pr95_correction/` | unignored and ACL-inaccessible | add `/.pytest_tmp*/` | Same |
| `backend/.pytest_tmp_phase10/` | unignored and ACL-inaccessible | add `/backend/.pytest_tmp*/` | Same |
| `backend/.pytest_tmp_phase13/` | unignored and ACL-inaccessible | add `/backend/.pytest_tmp*/` | Same |
| `backend/.pytest_tmp_phase17/` | unignored and ACL-inaccessible | add `/backend/.pytest_tmp*/` | Same |
| `backend/.pytest_tmp_phase1d/` | unignored and ACL-inaccessible | add `/backend/.pytest_tmp*/` | Same |
| `backend/.pytest_tmp_phase2/` | unignored and ACL-inaccessible | add `/backend/.pytest_tmp*/` | Same |
| `backend/.pytest_tmp_phase20/` | unignored and ACL-inaccessible | add `/backend/.pytest_tmp*/` | Same |
| `backend/.pytest_tmp_phase2026/` | unignored and ACL-inaccessible | add `/backend/.pytest_tmp*/` | Same |
| `_codex_worktrees/*/frontend/.next/` | ignored per worktree; 60–160 MB where present | inherited `.next/` rule | Regenerable; remove before worktree move if desired |
| `_codex_worktrees/*/frontend/node_modules/` | ignored per worktree; about 588 MB in three worktrees | inherited `node_modules/` rule | Regenerable; remove before worktree move if desired |

Add `/_codex_worktrees/` to `.gitignore` after the registered worktrees are moved, as a guard against recreating nested worktrees. Add `/frontend/test-results/`. Do not add a blanket `review_bundle_*/` ignore: it would hide evidence that may need review and archival.

### `move_outside_repository`

Exact registered worktree paths:

- `_codex_worktrees/blind-editorial-pipeline-validation-v1/`
- `_codex_worktrees/cross-issue-editorial-generality-v1/`
- `_codex_worktrees/editorial-artifact-persistence-v1/`
- `_codex_worktrees/justice-cross-member-validation-v1/`
- `_codex_worktrees/public-editorial-product-frontend-v1/`

These paths are untracked from the root’s perspective, but they are registered Git worktrees and must be moved with `git worktree move`.

### `unresolved_human_decision`

| Exact path | Issue | Why approval is required |
| --- | --- | --- |
| Root checkout at `C:\Users\Dylan\Documents\Data Science\political_fingerprint` | whether to preserve root work as a recovery commit or external patch only | switching the root affects unique untracked evidence and a large dirty state |
| `docs/plans/2026_evidence_eligibility_interpretation_expansion.md` | 12 unchecked items | no current branch ownership; may be superseded, paused, or still active |
| `docs/plans/codex_operating_model.md` | 12 unchecked items | appears to be an operating-model migration plan, not a normal completed milestone |
| `docs/plans/current_congress_freshness_ingestion.md` | 2 unchecked items | incomplete production-oriented work; cannot archive as complete |
| `docs/plans/zip_schema_source_metadata_design_v1.md` | 1 unchecked item | likely superseded by later ZIP milestones, but status was never reconciled |
| `docs/plans/cross_issue_editorial_generality_v1.md` on the cross-issue branch | blocked result, unmerged | decide whether the blocked-result record should merge, archive, or remain branch-only |
| `CONSTRAINTS.md` | legacy root authority overlaps current `AGENTS.md` and methodology | still referenced and contains hard civic rules; consolidation could change semantics |
| `DECISIONS.md` | calls old MVP decisions authoritative and retains drift-first framing | no inbound references, but it is an architectural decision log |
| `FIXTURES.md` | old required-fixture specification | referenced by `DECISIONS.md`; fixture expectations may have evolved |
| `SKILLS.md` | legacy implementation guide | referenced by `TASKS.md`; overlaps `AGENTS.md`, methodology, and workflows |
| `TASKS.md` | completed build-from-scratch master plan | references `SKILLS.md`; historical rather than active execution guidance |
| `docs/staging_readiness.md` | stale “current status” includes drift-first language | referenced by deployment, monitoring, and operating-model documents |
| `docs/product_v2_tasklist.md` | roadmap with completed historical phases | referenced by README and product docs; decide whether roadmap remains live |
| `docs/north_star_action_plan.md` | product roadmap/action plan | referenced by README and other canonical docs |

## Generated reports: authority decision

The repository uses committed generated reports as contracts and receipts, not as disposable run output.

Evidence:

- `backend/tests/test_valerie_foushee_justice_public_safety_editorial_gold_v1.py` runs the Justice builder with `--check`.
- Valerie Economy tests load `review_packet.json`, `claim_source_map.json`, and `source_manifest.json`, and invoke its deterministic review builder.
- the record-across-Congresses copy guardrail JSON is loaded by a frontend test;
- ZIP report JSON files are inputs to later analyzers, apply scripts, and readiness tests;
- `data_inventory_source_manifest_v1.json` enumerates other manifests and rollback assets;
- current-House normalized artifacts are referenced by later ZIP reports and source manifests;
- rollback SQL is named by preflight/post-validation packets and is part of restoration governance;
- the new editorial persistence and standardization JSON files are current `origin/main` artifacts.

Rule for future cleanup: a generated file may be `safe_to_delete` only when its builder writes to a temp/output directory, no test compares it, no tracked document or manifest names it, it is not publication/restoration evidence, and regeneration prerequisites are available. None of the tracked JSON/Markdown reports reviewed here meets all of those conditions.

## Broken and stale references

Five README links are machine-specific WSL absolute paths and are broken as repository links:

- `/mnt/c/Users/Dylan/Documents/Data%20Science/political_fingerprint/docs/real_data_runbook.md`
- `/mnt/c/Users/Dylan/Documents/Data%20Science/political_fingerprint/docs/development_workflow.md`
- `/mnt/c/Users/Dylan/Documents/Data%20Science/political_fingerprint/docs/deployment.md`
- `/mnt/c/Users/Dylan/Documents/Data%20Science/political_fingerprint/docs/accessibility_mobile_checklist.md`
- `/mnt/c/Users/Dylan/Documents/Data%20Science/political_fingerprint/docs/monitoring.md`

Replace them with `docs/<file>.md` relative links in the cleanup milestone.

No other missing local Markdown link target was found by the tracked-file link scan. Plain-code path references still need updates if plans or packets move; Git does not rewrite them automatically.

## Proposed future directory map

```text
political_fingerprint/                     # clean canonical checkout of main
  AGENTS.md
  README.md
  backend/
  frontend/
  scripts/
  docs/
    README.md                              # documentation index and authority map
    methodology.md
    interpretation_principles.md
    product/
      north_star.md
      roadmap.md
    workflows/
      milestone-execution.md
      bounded-production-write.md
      product-and-rendered-validation.md
      pr-merge-deployment.md
      editorial-issue-frontend.md
      editorial-standardization-pipeline.md
      templates/
        milestone-brief.md
        living-plan.md
    plans/
      active/
        <exactly-zero-or-one-current-plan>.md
      archive/
        2026/
          <completed-plan>.md
    review_packets/
      <milestone>/
        README.md
        report.json
        manifests/
        rollback/
        assets/
      archive/
        2026/
    editorial/
      <slice>/
        README.md
        source_manifest.json
        generated/
        review/
    source_manifests/
    archive/
      legacy_root_docs/

political_fingerprint-worktrees/           # sibling, outside repository
  main/                                    # optional dedicated clean main worktree
  <branch-slug>/

political_fingerprint-review-archive/      # optional immutable local review evidence
  2026/
    <milestone>/

political_fingerprint-recovery/
  2026-07-24-root-38ad159/
```

Do not implement this map as one bulk move. First add `docs/README.md` with authority and retention rules, then move one document family per reviewable commit with automated reference checks.

## Cleanup sequence, lowest to highest risk

1. Delete the two Playwright `.last-run.json` files and the regenerated `_data_inventory_cases/` tree.
2. Delete `docs/.gitkeep`.
3. Add narrow ignore rules for Playwright output, named pytest temp roots, the Windows venv, and future nested worktrees.
4. Repair the five README links.
5. Create the external recovery package for the dirty root and validate its hashes and patch.
6. Archive the three referenced review bundles only after updating every inbound reference.
7. Remove ignored `.next/` and duplicate `node_modules/` trees from child worktrees if desired; retain `.local/` and `backend/data_sources/`.
8. Move each registered child with `git worktree move`; verify with `git worktree list --porcelain` and `git worktree repair`.
9. Decide and reconcile the four incomplete root plans and the blocked cross-issue plan.
10. Move completed plans into a dated archive with reference updates and a link check.
11. Consolidate legacy root authority documents only after a human semantics review against `AGENTS.md`, `docs/methodology.md`, and `docs/interpretation_principles.md`.
12. After recovery validation and explicit approval, make the repository root the clean, up-to-date `main` checkout.

## Automatic cleanup allowlist

Exactly these paths, and no others:

```text
docs/.gitkeep
_codex_worktrees/blind-editorial-pipeline-validation-v1/frontend/test-results/.last-run.json
_codex_worktrees/public-editorial-product-frontend-v1/frontend/test-results/.last-run.json
_codex_worktrees/blind-editorial-pipeline-validation-v1/backend/tests/_data_inventory_cases/
```

## Human-approval list

Human approval is required for:

- every registered worktree move;
- every review-bundle archive, move, deduplication, or deletion;
- every completed-plan move;
- every legacy root-document consolidation or archive;
- every inaccessible pytest-temp deletion;
- any deletion under `.local/` or `backend/data_sources/`;
- any change to the dirty root branch or checkout;
- any classification change for the incomplete/blocked plans;
- any removal of tracked generated JSON, Markdown, SQL, source manifests, or editorial artifacts.

## Audit limitations

- ACL-inaccessible pytest temp directories could be named and statted at the directory level but not inspected internally.
- This audit did not fetch, checkout, reset, clean, stage, move, delete, or run builders/tests.
- The remote query confirms `main` at the audit time; later remote changes are outside this snapshot.
- Inbound-reference counts are conservative literal-path checks. Runtime discovery by glob or directory convention can create additional ownership not visible as a literal reference.
