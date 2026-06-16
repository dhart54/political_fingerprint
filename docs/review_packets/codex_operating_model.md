# Codex Operating Model

## Purpose

Large milestone prompts had become inefficient because they repeated the same workflow rules: how to plan, when to continue autonomously, when to stop, how to handle production writes, how to validate UI work, and how to package PRs.

This packet documents the repository-local operating model that now supplies those defaults through durable docs:

- `AGENTS.md`
- `docs/PLANS.md`
- `docs/plans/TEMPLATE.md`
- `docs/workflows/milestone-execution.md`
- `docs/workflows/bounded-production-write.md`
- `docs/workflows/product-and-rendered-validation.md`
- `docs/workflows/pr-merge-deployment.md`
- `docs/workflows/MILESTONE_TEMPLATE.md`

No application behavior or production data changed.

## Existing Instruction Audit

Instruction files found:

- `AGENTS.md`: root repository instruction file. It has repository-wide scope.
- `docs/development_workflow.md`: local verification modes, Windows pytest temp guidance, build, and local server notes.
- `docs/deployment.md`: Render/Vercel deployment settings and post-deploy checks.
- `docs/staging_readiness.md`: staging checklist and deployed smoke expectations.
- `docs/local_preview_runbook.md`: local backend/frontend preview path and known Windows limitations.
- `docs/monitoring.md`: lightweight monitoring, release checks, and privacy-safe logging.
- `docs/methodology.md`: civic/product methodology and evidence semantics.
- `docs/autonomous_handoff.md`: historical handoff/checkpoint log, useful context but not a durable canonical instruction system.

Recommended canonical structure:

1. `AGENTS.md` remains the top repository instruction file.
2. `docs/PLANS.md` defines living execution plans.
3. `docs/workflows/` holds reusable runbooks.
4. `docs/methodology.md` remains the civic/product methodology source.
5. Existing development, deployment, staging, local preview, and monitoring docs remain specific references.

Useful rules preserved:

- deterministic, neutral, source-grounded civic analysis
- no voting recommendations, ranking, motive inference, or corruption claims
- milestone branches and scoped diffs
- no PR before definition of done unless explicitly authorized
- targeted tests/builds
- Windows pytest and Next.js local preview caution
- Render/Vercel deployment separation
- production-backed validation for evidence work

Duplication or conflicts found:

- The prior root `AGENTS.md` mixed durable product identity with detailed workflow and command notes.
- Several docs included overlapping release or validation checklists.
- `docs/autonomous_handoff.md` included historical active-branch state that should not become durable instruction.
- No irreconcilable instruction conflict was found.

## Final Instruction Hierarchy

1. User's current milestone request.
2. Applicable `AGENTS.md` instructions by directory scope.
3. Active execution plan.
4. Workflow runbooks.
5. Broader methodology and product documentation.

The active plan records decisions but cannot override higher-priority instructions. Workflow runbooks provide defaults, not permission to violate the milestone. Production-write permission must come from the milestone decision envelope or explicit user approval.

## Durable Autonomy Rules

The new model preserves autonomy through established stages when the milestone permits them:

- read-only discovery
- active-plan creation and maintenance
- source collection
- implementation
- deterministic classification
- bounded dry-runs
- rollback creation
- explicitly authorized bounded production writes
- post-write validation
- tests and builds
- rendered review
- documentation
- commit preparation
- PR creation
- green-check merge
- deployment verification or redeployment of already-reviewed code

Normal movement between these stages is not a reason to stop. Completed intermediate artifacts are progress, not completion.

## Stop Conditions

The durable stop conditions are:

- new schema or product-semantics decisions outside the milestone envelope
- ambiguous civic meaning or conflicting authoritative sources
- a vote/evidence type the current model cannot represent safely
- failed hard gates
- incomplete rollback
- destructive or unbounded behavior
- production effects differing materially from preflight
- unexpected counting, readiness, alignment, API, security, accessibility, or data-integrity effects
- infrastructure/configuration ambiguity involving services, secrets, or environments

## Production-Write Workflow

`docs/workflows/bounded-production-write.md` supplies the standard pattern:

1. validate intended state and authoritative source basis
2. define exact target rows/objects and affected tables
3. predict inserts, updates, deletes, skips, and metric impacts
4. create rollback before writing
5. confirm authorization through the milestone decision envelope
6. execute only the bounded write
7. reconcile actual versus expected effects
8. run idempotency/no-write checks where applicable
9. preserve the audit trail

The runbook also states that a milestone may pre-authorize a bounded class of write, while schema changes, destructive operations, ambiguous semantics, or service/secret ambiguity remain stop conditions unless explicitly authorized.

## Planning Convention

`docs/PLANS.md` requires substantial work to maintain one active plan under `docs/plans/`.

The plan records:

- intent
- outcome
- scope and boundaries
- decision envelope
- definition of done
- baseline
- implementation sequence
- progress
- discoveries
- decisions and rationale
- deviations/corrections
- validation
- production writes
- rollback paths
- blockers
- final reconciliation

The plan is concise and operational. It is not a second giant prompt.

## Steering And Status Behavior

The new runbook explicitly encodes the steering rule:

- user messages during active work are steering
- after the current safe command returns, acknowledge steering before launching another command
- status updates should name the current stage, exact active command when relevant, elapsed time, whether progress is occurring, and whether interruption is safe
- long validation should be split into bounded checks
- hanging commands should be interrupted safely rather than rerun blindly

This addresses the repeated failure mode where long opaque commands made it look like work was stuck.

## Desk-Check A: Bounded Interpretation Or Classification Import

Concise milestone prompt would need to state:

- target batch or discovery scope
- import/write authorization or preflight-only boundary
- caps and excluded tables
- any novel source or civic ambiguity risks

Repository documents supply:

- production-write preflight, rollback, authorization, post-validation, idempotency, and stop conditions
- civic integrity rules around procedural, limited, amendment, final-passage, and not-voting rows
- plan and final reconciliation expectations

Safety is preserved because production writes still require milestone authorization, rollback, bounded scope, expected-versus-actual reconciliation, and stops for counting/alignment/API divergence.

Codex should continue autonomously through validation, dry-run, rollback creation, write, and post-validation when every predefined gate passes.

Codex should stop for ambiguous vote meaning, conflicting authoritative sources, unsupported evidence type, incomplete rollback, or material mismatch.

## Desk-Check B: Frontend Product Pass

Concise milestone prompt would need to state:

- product outcome
- representative profiles or flows
- any specific viewports or sections
- PR/merge authority if desired

Repository documents supply:

- living plan
- production-backed examples
- rendered validation expectations
- responsive checks
- build/test expectations
- "audit is not completion" rule

Safety is preserved because civic/counted semantics cannot change without explicit product decision, while normal layout, copy, and component restructuring can proceed.

Codex should continue through diagnosis, implementation, rendered review, tests, build, and documentation.

Codex should stop for ambiguous civic meaning, accessibility/security regressions, or unexpected counting/readiness/alignment/API effects.

## Desk-Check C: Security Remediation

Concise milestone prompt would need to state:

- security issue
- affected environment
- desired remediation boundary
- whether production schema/security changes are authorized

Repository documents supply:

- least-privilege production safety
- exact scope and rollback requirements
- no secret exposure
- branch/worktree isolation through scoped-diff and artifact-preservation rules
- security as a true stop condition when ambiguity exists

Safety is preserved because security writes still need a bounded decision envelope, preflight, rollback, and post-validation.

Codex should continue through discovery, remediation, validation, docs, and PR packaging when scope is clear.

Codex should stop for service/secret ambiguity, destructive changes, or inability to verify affected scope.

## Desk-Check D: PR, Merge, And Deployment Recovery

Concise milestone prompt would need to state:

- PR number or branch
- merge authority
- deployment verification target
- whether redeploy of already-reviewed code is allowed

Repository documents supply:

- exact diff review
- unrelated artifact exclusion
- green-check merge rules
- clean-main verification
- branch cleanup
- frontend/backend deployment distinction
- bounded redeploy and smoke checks
- stops for service/config/secret ambiguity

Safety is preserved because deployment recovery is limited to reviewed code and cannot silently change config, secrets, or production data.

Codex should continue through merge and deployment verification when checks are green and targets are unambiguous.

Codex should stop for failing checks, dirty tracked tree, ambiguous service identity, or environment mismatch.

## Desk-Check E: Steering And Interrupted-Command Recovery

Concise milestone prompt would need to state:

- any special timeout or reporting needs beyond the default

Repository documents supply:

- bounded command defaults
- status-report content
- honor-steering rule
- safe interruption and preservation of completed work
- repository/production state verification before continuing

Safety is preserved because interrupted work must be reconciled before moving on, and long opaque commands are discouraged.

Codex should continue after confirming state and splitting validation into bounded pieces.

Codex should stop for partial writes, unclear production state, missing rollback, or unreconciled command effects.

## Concise Future Milestone Example

```text
Intent:
Improve Senate amendment evidence navigation so reviewed amendment records are easier to inspect.

Outcome:
Amendment-heavy profiles show concise amendment labels, representative examples, and full source detail behind expansion.

Definition of done:
- Valerie, Thom Tillis, and one sparse profile validate the hierarchy.
- Frontend tests and build pass.
- Rendered validation covers mobile and desktop.
- Review packet records before/after behavior.

Scope:
- Frontend profile presentation only.
- No production writes.
- No support/opposition, readiness, or alignment semantic changes.

Decision envelope:
- Codex may restructure components and copy.
- Codex may not change counting or interpretation logic.

Workflow references:
- docs/PLANS.md
- docs/workflows/milestone-execution.md
- docs/workflows/product-and-rendered-validation.md
```

## Validation

Planned validation:

- path/reference sanity check for new docs
- contradiction/circular-reference review
- `git diff --check`

Application tests are not required because this milestone changes documentation only.

## Remaining Limitations

- This operating model is repository-local. It is not a global Codex skill.
- The model depends on future milestone prompts referencing the runbooks rather than restating them.
- Some deployment verification still depends on external service access and configured secrets.
