# Milestone Plan: Codex Operating Model

## Intent

- Immediate task: institutionalize concise Codex milestone execution rules in repository documentation.
- Larger-goal alignment: reduce repeated long prompts while preserving civic, production, security, validation, and steering safeguards.

## Outcome

- A short root `AGENTS.md`.
- A reusable living-plan convention.
- Workflow runbooks for milestone execution, bounded production writes, product/rendered validation, and PR/merge/deployment.
- A concise milestone brief template.
- A review packet desk-checking prior milestone types.

## Scope And Boundaries

- In scope: documentation and workflow instructions only.
- Out of scope: application behavior, production data, product/data milestones, global Codex skills.
- Files/systems likely touched: `AGENTS.md`, `docs/PLANS.md`, `docs/plans/`, `docs/workflows/`, `docs/review_packets/`.

## Decision Envelope

- Codex may revise repository-local instruction and workflow docs.
- Codex may open and merge one PR if checks are green and the diff is clean.
- No production writes, application code changes, deploys, or product behavior changes are authorized.

## Definition Of Done

- [ ] Existing instruction structure audited.
- [ ] Root `AGENTS.md` is concise and durable.
- [ ] Living plan convention and template exist.
- [ ] Reusable workflow runbooks exist.
- [ ] Concise milestone template exists.
- [ ] Steering/status guidance is encoded.
- [ ] Instruction precedence is documented.
- [ ] Prior milestone desk-check is documented.
- [ ] Path/reference sanity and `git diff --check` pass.
- [ ] Intended docs are committed, PR opened, checks reviewed, and merged if green.
- [ ] Final reconciliation completed.

## Baseline

- Branch/base commit: `3a34e3011150b16367121c8349fb7936261177ea`.
- Production/deployment state: not touched.
- Tracked working tree: clean before branch creation.
- Known unrelated untracked artifacts: chamber filtering audit, frontend grounding bundle, pytest temp directories.

## Implementation Sequence

1. Confirm clean main and create branch.
2. Audit existing instructions and workflow-related docs.
3. Draft root instructions, plan convention, templates, runbooks, and review packet.
4. Validate references and whitespace.
5. Commit, open PR, review checks, merge if green, and update main.

## Progress Checklist

- [x] Discovery started.
- [x] Documentation drafted.
- [x] Validation complete.
- [ ] Commit/PR/merge complete.

## Discoveries

- One root `AGENTS.md` is canonical but long and mixes product identity with operational details.
- `docs/development_workflow.md`, `docs/deployment.md`, `docs/staging_readiness.md`, `docs/local_preview_runbook.md`, and `docs/monitoring.md` contain useful workflow details to reference.
- `docs/autonomous_handoff.md` is historical handoff material, not a durable instruction system.

## Decisions And Rationale

- Keep product identity and civic guardrails in `AGENTS.md`.
- Move repeated operational mechanics into workflow runbooks.
- Keep the plan convention project-local rather than creating a global Codex skill.

## Deviations Or Corrections

- Branch creation required escalated Git execution because sandboxed Git could not create the ref lock.

## Validation Results

- Referenced-path sanity check passed.
- `git diff --check` passed with the normal Windows CRLF notice for `AGENTS.md`.

## Production Writes

- Performed: no.

## Rollback Paths

- Documentation-only changes can be reverted by Git if needed.

## Blockers

- None currently.

## Final Reconciliation

- Documentation-only operating model is internally consistent and ready for commit/PR packaging.
