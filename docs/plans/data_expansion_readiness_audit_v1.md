# Milestone Plan: Data Expansion Readiness Audit V1

## Intent

- Immediate task: audit what must be true before expanding Political Fingerprint beyond the current golden representative/profile flow.
- Larger-goal alignment: avoid scaling incomplete or misleading reads across more representatives, chambers, Congresses, or years before the data model, validation, and UI can support them safely.

## Outcome

- User-visible or operational result: a docs-only readiness audit and review packet that name current support, breakage/misleading risks, ready surfaces, not-ready surfaces, trust risks, recommended milestones, and no-go items.

## Scope And Boundaries

- In scope: repository audit, architecture/data coverage map, expansion risk matrix, readiness assessments for House, Senate, multi-Congress reads, validation harness gap analysis, and implementation milestone sequencing.
- Out of scope: production ingestion, production writes, schema/code changes, vote interpretation semantic changes, support/opposition/readiness/alignment changes, and public-copy behavior changes from PR #65 through PR #70.
- Files/systems likely touched: `docs/plans/data_expansion_readiness_audit_v1.md` and `docs/review_packets/data_expansion_readiness_audit_v1.md`.

## Decision Envelope

- Codex may decide and execute: audit structure, risk language, recommended milestone order, documentation wording, and cheap docs/source validation.
- Explicit approval required for: any code or data change, any production credential use, any production write, and any methodology or public-copy semantic change.

## Definition Of Done

- [x] Recent milestone plans and interpretation guardrails read.
- [x] Backend/frontend/data paths for lookup, profile loading, issue grouping, vote interpretation/loading, Record Across, fixture/render validation, ETL/scripts/seed paths inspected.
- [x] Current support and data coverage documented.
- [x] Expansion breakage/misleading risks documented for House, Senate, 118th/119th, and broader multi-year data.
- [x] Ready and not-ready components documented.
- [x] Highest trust risks and explicit no-go items documented.
- [x] Recommended next implementation milestones documented.
- [x] Tests/build/validation recorded.
- [x] Review packet created.
- [x] Final reconciliation completed.

## Baseline

- Branch/base commit: `codex/data-expansion-readiness-audit-v1` from `main` at `650853404526ea5abe4faca24f2189662f0293e3` (`Merge pull request #70 from dhart54/codex/golden-render-validation-harness-v1`).
- Production/deployment state, if relevant: no production write or production credential use authorized for this audit.
- Tracked working tree: branch started from clean tracked `main`; `git status` had permission warnings for existing `.pytest_tmp*` directories and known unrelated untracked artifacts.
- Known unrelated untracked artifacts: `docs/review_packets/chamber_filtering_data_integrity_audit.md`, `review_bundle_frontend_data_grounding/`.

## Implementation Sequence

1. Confirm base branch and branch creation after PR #70.
2. Read `AGENTS.md`, `docs/PLANS.md`, `docs/interpretation_principles.md`, milestone workflow, and requested recent milestone plans.
3. Inspect backend read layer, lookup/search APIs, ETL/import/seed paths, adapters, classifiers, interpretation rules, Record Across helpers, frontend profile/read components, and golden render fixture/tests.
4. Inspect fixture/source-cache coverage and analysis artifacts.
5. Create the active plan and review packet.
6. Run docs-only diff validation and cheap frontend source tests if available.
7. Commit, push, and open a focused draft PR.

## Progress Checklist

- [x] Discovery
- [x] Audit synthesis
- [x] Documentation
- [x] Validation
- [x] Commit/PR readiness

## Discoveries

- `main` had advanced to PR #70 at `6508534`; the requested branch was created from that merge commit.
- The default fixture path is intentionally tiny: 3 legislators, 1 House member, 2 senators, 14 roll calls, 21 votes, 2 ZIP mappings, and 118th Congress fixture rows.
- The database read layer supports `all`, `119`, and `118` scopes, but scope coverage is global and does not itself prove per-member/per-issue evidence strength.
- ZIP lookup returns one district per ZIP and has no ambiguity/address refinement model.
- Public profile/read composition is much more mature after PR #65 through PR #70, but it depends on reviewed interpretation counts and safe theme/facet coverage.
- Record Across Congresses is House-only, 118th/119th-only, family-artifact-based, internal-token gated, and explicitly non-authorizing for change/continuity claims.
- ETL has bounded current/historical refresh paths with rollback/approval gates, but broad expansion still needs inventory, source manifests, coverage reporting, and chamber-aware methodology hardening.

## Decisions And Rationale

- Keep this PR docs-only because the milestone is an audit/planning PR and explicitly forbids implementation or production ingestion.
- Treat House current-Congress expansion as the nearest plausible pilot only after source manifest and legislator/ZIP hardening, because the UI/readiness/harness foundation is strongest there.
- Treat Senate public reads and multi-Congress comparison as not ready for broad rollout until chamber-specific interpretation, amendment identity, source coverage, and validation gaps are closed.
- Use cautious language consistent with `docs/interpretation_principles.md`: evidence availability, support/opposition counts, and caveats, without motive, ideology, ranking, prediction, or voting advice.

## Deviations Or Corrections

- The first broad `rg` search was too noisy because cached XML sources contain hundreds of thousands of vote rows; discovery narrowed to source modules, fixtures, derived artifacts, and selected cached-source counts.

## Validation Results

- `node --test lib\*.test.mjs` from `frontend`: passed, 75/75. Existing Node warning remains about `frontend/package.json` not declaring `"type": "module"` while `frontend/lib/issueDomains.js` uses module syntax.
- `npm run lint` from `frontend`: passed with 8 existing React hook dependency warnings and 0 errors.
- `git diff --name-only`: run before staging and returned no tracked-file diff because the two new docs were untracked at that point. Staged diff validation will be run before commit to confirm only requested docs are included.
- `git diff --name-only --cached`: `docs/plans/data_expansion_readiness_audit_v1.md`, `docs/review_packets/data_expansion_readiness_audit_v1.md`.
- `git diff --name-only`: empty after staging, confirming no unstaged tracked code/doc changes outside the intended files.

## Production Writes

- Performed: no
- Scope: none
- Expected effects: none
- Actual effects: none

## Rollback Paths

- Revert the docs-only commit from this branch.

## Blockers

- None for docs-only audit completion. Production-backed coverage verification would require credentials and is out of scope for this milestone.

## Final Reconciliation

- Definition of done satisfied: yes.
- Remaining limitations: audit is repository-grounded and local-cache-grounded; it does not query production.
- Commit: `06aea2a` before final plan reconciliation; branch head contains this final reconciliation amendment.
- Draft PR: #71.
- Recommended next step: use the review packet's first milestone, Data inventory / source manifest, before any new expansion write.
