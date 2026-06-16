# Milestone Execution Workflow

Use this runbook for substantial repository work. It supplies defaults; the user's current milestone request still controls scope and permissions.

## Start

1. Confirm the requested base branch and commit.
2. Confirm local branch matches its remote when required.
3. Confirm tracked working tree cleanliness with narrow checks when broad status is slow.
4. Preserve known unrelated untracked artifacts.
5. Create the requested milestone branch.
6. Create or update one active plan under `docs/plans/`.

## Reconcile The Work

- Restate the milestone intent in the active plan.
- Identify the definition of done and true stop conditions.
- Map the work into stages: discovery, implementation, validation, documentation, commit/PR readiness.
- Do not stop after planning or audit when implementation remains in scope.

## Execute

Move through established stages when the milestone permits them:

- read-only discovery
- source collection
- implementation
- deterministic classification or candidate generation
- bounded dry-runs
- rollback creation
- explicitly authorized bounded production writes
- post-write validation
- tests and builds
- rendered review
- documentation
- commit preparation

Completed intermediate artifacts are progress, not completion.

If one package fails its gates, continue any other package that independently remains safe and in scope.

## Status And Steering

- Treat user messages during active work as steering, not background noise.
- After the current safe command returns, acknowledge steering before launching the next command.
- Status updates should name the current stage, exact active command when one is running, elapsed time when relevant, whether progress is occurring, and whether interruption is safe.
- Use bounded commands and timeouts.
- Split long validation into smaller checks.
- If a command hangs, interrupt safely, report what was preserved, and continue with a narrower path.

## Correcting Defects

Normal defects discovered inside the milestone may be fixed autonomously:

- query or join bugs
- frontend rendering defects
- validation failures with clear causes
- copy duplication
- responsive layout issues
- test fixture gaps
- local-tool limitations that can be worked around safely

Stop only for the true stop conditions in `AGENTS.md` or the milestone.

## Validation

- Run targeted tests relevant to touched behavior.
- Run frontend build when frontend/runtime behavior changes.
- Use production-backed examples when the product depends on production-shaped data.
- Use rendered validation for meaningful UI changes.
- Record local-tool limitations separately from product failures.

## Documentation And Reconciliation

- Update methodology when logic or product semantics change.
- Create a review packet for substantial milestones.
- Reconcile expected versus actual behavior.
- Record tests, build, validation, limitations, and next recommendation.
- Commit only intended files.
