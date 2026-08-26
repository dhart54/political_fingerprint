# Milestone Plan: Publication Activation Governance V2

## Intent

- Immediate task: introduce a future-only publication activation authority contract that separates stable human-ratified invariants from replaceable fresh execution evidence.
- Larger-goal alignment: preserve fail-closed publication safety without making evidence freshness a recurring human orchestration step.

## Outcome

- Future activation code can validate one durable V2 authority and stable write set against newly captured runtime and transaction-read-only production evidence, proceeding only when every governed invariant remains exactly equal.

## Scope And Boundaries

- In scope: a reusable V2 authority/write-set/execution-evidence validation layer, focused adversarial and compatibility tests, governance documentation, release validation, and a draft PR.
- Out of scope: M14, any new domain, production writes, historical artifact migration or regeneration, selector/frontend redesign, schema/database redesign, merge, and deployment.
- Files/systems likely touched: `backend/app/editorial_presentations`, focused backend tests, publication-governance docs, this plan, and a review packet if the established release workflow requires one.

## Decision Envelope

- Codex may decide and execute: the smallest additive V2 contract and function decomposition consistent with existing hashing/validation conventions; local validation; commit; push; draft PR.
- Explicit approval required for: production mutation, historical artifact changes, methodology or semantic changes, merge, deployment, or any expansion into M14.

## Definition Of Done

- [x] Stable V2 authority and write-set identities exclude volatile runtime/preflight evidence identity and timestamps.
- [x] Fresh equivalent evidence validates mechanically under existing authority; stale or materially drifted evidence fails closed.
- [x] Historical M11N/M12N/M13N artifacts and behavior remain exact; four-domain selector behavior and production isolation remain unchanged.
- [x] Tests/build/validation recorded, including requested release, benchmark, formatting, compile, catalog/diff, PostgreSQL, and hosted-CI gates.
- [x] Concise governance documentation and PR review question are present.
- [x] Final reconciliation completed; draft PR remains unmerged and undeployed.

## Baseline

- Branch/base commit: `codex/publication-activation-governance-v2` from exact `74b054bfb8f138b8b6a31289f48995ceefcb0240`.
- Production/deployment state: expected 7 batches, 155 artifacts, 165 relationships, 4 registry rows; read-only verification only.
- Tracked working tree: clean in isolated worktree at milestone start.
- Known unrelated untracked artifacts: protected ZIPs and unrelated edits exist only in the original checkout and remain outside this worktree and milestone.

## Implementation Sequence

1. Map V1 preparation/activation/write-set/fresh-evidence contracts and exact legacy regression commands.
2. Implement additive V2 stable models, canonical identity builders, and fail-closed execution validation; add focused unit/PostgreSQL tests.
3. Document governance, run targeted then release validation, inspect the diff and historical bytes, and prepare the draft PR with exact-head CI.

## Progress Checklist

- [x] Discovery
- [x] Implementation
- [x] Validation
- [x] Documentation
- [x] Commit/PR readiness

## Discoveries

- The user's original checkout was on an older dirty M12N branch; an isolated worktree was created to preserve all unrelated edits and protected ZIPs.
- Existing V1 activation authorities bind volatile preflight/proof subjects. V2 therefore remains a separate schema and validator module; selector compatibility stays entirely on V1.
- The Windows sandbox prevented temporary fixture writes, and the initial long worktree path exceeded a legacy documentation checker's effective path limit. Moving the same worktree to `.w/v2` allowed the unchanged release gate to pass.
- Full-repository Ruff/format has a non-clean baseline (539 lint findings and 187 formatting differences); scoped changed-file Ruff/format passes.

## Decisions And Rationale

- V2 will be additive rather than a reinterpretation of V1, so legacy authorities and historical replay retain their accepted contracts.
- Stable identity construction will accept only explicit stable fields; execution evidence will be validated separately and recorded only in an execution validation result/receipt boundary.
- Existing registry identities include artifact ID/version, natural key, content SHA, source commit, publication-metadata SHA, and active state so metadata-only or provenance-only drift fails closed.

## Deviations Or Corrections

- The isolated worktree path was shortened from `.w/publication-activation-governance-v2` to `.w/v2` solely to satisfy Windows long-path validation; branch and repository bytes were preserved.
- The first hosted V2 PostgreSQL run reached the new step but its read-only-mode assertion used tuple indexing against the repository's dictionary-row connection. The assertion was corrected to read the named `transaction_read_only` field; no contract or safety check was weakened.
- The next hosted run exposed the same dictionary-row mismatch in two count assertions; both were corrected to use the named `count` field.
- The following hosted run reached the negative candidate-write assertion and exposed a fixture-only table-name typo (`editorial_artifacts` instead of the canonical `editorial_artifact_versions`). Correcting that reference allowed the unchanged V2 gate and full lifecycle to pass.

## Validation Results

- Focused V2: 13 passed; disposable PostgreSQL case skipped locally because Docker/PostgreSQL is unavailable and is mandatory in hosted CI.
- V2 plus M11N/M12N V3/M13N-R/M13N compatibility: 76 passed.
- Full-record benchmark/activation: 46 passed.
- M11N validator, M12N validator, and frozen M12N V3 historical replay: passed.
- Governed release tier: passed all 7 checks.
- Public review-state catalog, Python compile, changed-file Ruff/format, and diff checks: passed.
- Read-only production: `7 / 155 / 165 / 4`, four exact active domains, 119/all reviewed-conclusion isolation, 118 receipts-only, fingerprint `090477315f73df6cadda662f2aa24ef4a30ed0b2e74669bb3e7d5cf73680e01e`.
- Hosted implementation-head CI run `32924329185` at `c9f3612b7699c76ced3e0a953a825429d4358684`: passed all four backend jobs, including the mandatory V2 transaction-read-only PostgreSQL proof, historical activation lifecycle, owned-resource cleanup, and full-record benchmark. Vercel and preview-comment checks also passed.

## Production Writes

- Performed: no
- Scope: none; this milestone permits read-only production verification only.
- Expected effects: zero database or publication-registry changes.
- Actual effects: read-only production verification passed; counts, registry identities, and selector behavior remained unchanged.

## Rollback Paths

- Code-only additive change; revert the milestone commit/PR. No production rollback is needed because no production write is authorized or performed.

## Blockers

- None.

## Final Reconciliation

- Definition of done satisfied: yes; the reusable future-only V2 boundary, adversarial coverage, historical compatibility, production isolation, and exact hosted proof are complete.
- Remaining limitations: local Docker/PostgreSQL remained unavailable, so the real-database proof was established in mandatory hosted CI; the unrelated repository-wide Ruff/format baseline remains non-clean and was not absorbed.
- Recommended next step: independent ChatGPT governance review of the draft PR; do not merge, deploy, or begin M14 in this milestone.
