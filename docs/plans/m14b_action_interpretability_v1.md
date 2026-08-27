# Milestone Plan: M14B Action Interpretability Contract V1

## Intent

- Immediate task: define and exercise a typed, source-mapped, non-authorizing interpretability contract for all 17 governed Education & Workforce exact actions.
- Larger-goal alignment: qualify Shared Action Core meaning before later acceptance or presentation while preserving the accepted five-layer architecture.

## Outcome

- User-visible or operational result: a frozen candidate set and compact independent-review packet that explain each exact action concretely or place it on an explicit evidence hold.

## Scope And Boundaries

- In scope: additive schema, deterministic helper/validator, frozen Education candidates, reproducible builder and report, focused tests, a narrow dated authority clarification, and existing-CI integration.
- Out of scope: semantic acceptance, historical artifact mutation, Shared Action Core promotion, issue/member migrations, compiler changes unless strictly necessary, frontend/API/publication/production/deployment changes, and external source enrichment.
- Files/systems likely touched: `docs/semantic_ir`, `backend/app/semantic_ir`, `backend/tests`, `scripts`, `docs/editorial/interpretability_candidates`, `docs/governance` or the repository's existing decision-log location, and `.github/workflows/backend-tests.yml`.

## Decision Envelope

- Codex may decide and execute: field names preserving the requested boundaries, deterministic lint design, governed-source locators supported by existing artifacts, candidate wording grounded only in frozen repository evidence, and per-action hold states.
- Explicit approval required for: accepting/promoting candidates, changing methodology beyond this contract, rewriting historical records, production/publication/deployment, or unsupported external factual supplementation.

## Definition Of Done

- [x] All 17 governed actions occur exactly once and bind exact action/source identity.
- [x] Complete candidates carry concrete mechanism, affected entities, direct effect, limits, and field-level source mappings; insufficient evidence is an explicit hold.
- [x] Candidate bytes and digests are frozen; deterministic `--check` reproduces validation and the review packet without generating prose.
- [x] Required negative cases exercise real validation logic and protected historical artifacts remain byte-identical.
- [x] Tests/build/validation recorded.
- [x] Review packet or final documentation updated.
- [ ] Draft PR opened and exact-head GitHub CI recorded.
- [ ] Final reconciliation completed.

## Baseline

- Branch/base commit: `codex/m14b-action-interpretability-v1` from exact `main` `9b56358184e828e641ce2538cc9ed8788972b566`.
- Production/deployment state, if relevant: no production or deployment actions authorized.
- Tracked working tree: clean isolated linked worktree at milestone start.
- Known unrelated untracked artifacts: present only in the user's original worktree and deliberately not accessed from this isolated worktree.

## Implementation Sequence

1. Map M14A contracts, Education legacy decisions, source-readiness evidence, governance authority, and CI conventions.
2. Add the contract and validator; author frozen candidates and generate deterministic reports/digests.
3. Add negative/positive tests and existing-workflow CI coverage.
4. Run focused, M14A, canonical Semantic IR, Education parity, diff, and protected-artifact checks.
5. Inspect the final result, commit, push, open a draft PR, and verify exact-head CI.

## Progress Checklist

- [x] Discovery
- [x] Implementation
- [x] Local validation
- [x] Documentation
- [x] Commit/PR readiness

## Discoveries

- Local `main` exactly matches the required accepted M14A merge commit.
- The user's active worktree is dirty on an unrelated branch; M14B is isolated in a clean linked worktree.
- Existing repository authority already permits model-authored semantic candidates generally, but M14B still requires a narrow dated clarification at Shared Action Core meaning qualification.
- Live remote `main` was rechecked before PR preparation and still exactly matched the required SHA.
- `house:119:1:68` already exists in the 37-action House 119 core and is referenced; the other 16 retain legacy lineage.
- H.Amdt. 12 (`house:119:1:79`) requires full amendment text for concrete reporting/sanction detail. H.R. 2616 (`house:119:2:184`) requires the referenced Executive Order definition to explain its second provision. Both are explicit source-enrichment holds, not accepted semantic changes.

## Decisions And Rationale

- Use a detached candidate artifact rather than modifying Shared Action Core, because Education actions are legacy-governed and promotion is explicitly deferred.
- Keep deterministic validation separate from semantic prose generation; the builder consumes frozen candidates and never rewrites them.
- Apply the interpretation principle that neutrality requires concrete action verbs while excluding motive, judgment, and predictions.

## Deviations Or Corrections

- Initial rendered audit found that the draft bound each action's source-packet digest and field locators but did not enumerate every governed source identity/raw/projection digest inside each candidate. The contract and candidates were corrected before the final byte freeze.
- The hold-state schema was corrected to permit absent unsupported semantic fields without filler while complete candidates remain fail-closed.
- Source-by-source review removed an unsupported public-database detail from H.R. 1005, removed member-status language from shared limitations, and translated H.R. 2988's financial terminology. Candidate bytes were explicitly refrozen after those corrections.
- Final validator review closed a hold-state bypass: holds may omit unsupported explanatory fields, but cannot bypass source mapping, exact identity, neutrality, or action-boundary safeguards. Negative tests recompute qualification so cached-result mismatch cannot mask the intended failure. Frozen candidate and report bytes remain unchanged.

## Validation Results

- M14B builder `--check`: passed after final freeze; 17 actions, 15 complete candidates, 2 source-enrichment holds.
- Focused M14B tests: 18 passed, including the 12 required failure classes, source-mapping claim identity, hold invariants, complete-field requirements, and no-write reproducibility.
- M14A builder `--check`: passed with 37 unchanged actions; M14A tests: 15 passed.
- Canonical Semantic IR validator: passed; canonical unittest suite: 26 passed. The isolated worktree initially lacked `ajv`; the same test passed using the existing workspace's read-only Node module path, without changing dependencies.
- Education M13B-v2 source-readiness, M13C action-candidate, and M13D historical-acceptance validators: passed.
- Python compilation, staged `git diff --check`, and protected historical-directory diff check: passed.
- Legacy diagnostics: 9 sufficient unchanged, 6 would require revision, 2 require source enrichment.
- Candidate-set digest: `077479fd00602fbf13ce64809e675162a0857ccd0a043fce598611a0b0d62bbe`.
- Frozen candidate-file digest: `4944a8e2cd3217974e6af3f3b0c4c6a4fdc77e488f13ccb8e32f1ce68259d6ff`.
- Review-packet digest: `770da67da00210b1a5a5490f46d9a79b0b2998d78e9fc6033e0e89059658db52`.
- Draft PR: https://github.com/dhart54/political_fingerprint/pull/176 (draft, independent review only).
- Exact-head GitHub CI: required on the final pushed head; the final handoff and PR checks record its result without creating a self-invalidating commit-SHA cycle.

## Production Writes

- Performed: no.
- Scope: none.
- Expected effects: none.
- Actual effects: none.

## Rollback Paths

- Revert the additive milestone commit; no database, publication registry, accepted semantic artifact, or runtime surface is changed.

## Blockers

- No implementation blocker. Two per-action source-enrichment holds are explicit calibration outcomes and do not block this milestone.

## Final Reconciliation

- Definition of done satisfied: implementation, local validation, frozen review artifacts, protected parity, and draft PR complete. Exact-head CI remains a final handoff gate; no acceptance is requested before it passes.
- Remaining limitations: independent semantic/product review remains required; two source-enrichment holds remain non-authorizing.
- Recommended next step: stop after draft-PR/CI evidence for independent review; do not begin acceptance or remediation.
