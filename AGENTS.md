# AGENTS.md - Political Fingerprint

This file defines durable repository rules for Codex and coding agents. Follow it unless the user's current request gives a more specific instruction.

## Product Identity

Political Fingerprint is a curiosity-led, trust-anchored civic analytics platform.

Primary promise: "In 60 seconds, understand how this politician actually behaves."

North star: "Who represents me, how are they acting on the issues I care about, and what can I do next?"

The product maps observable legislative behavior. It must not rank politicians, infer motives, make corruption claims, predict behavior, tell users how to vote, or turn campaign statements into governing records.

Before product copy, summary, evidence, or UI interpretation work, read `docs/interpretation_principles.md`. Political Fingerprint should make clear, evidence-backed interpretations with receipts while avoiding moral judgment, motive claims, unsupported ideology labels, and unsupported cross-time movement claims.

## Civic Integrity

- Preserve amendment, final-passage, procedural, limited-context, and not-voting distinctions.
- Do not infer motive, ideology, character, corruption, causality, endorsement, or voting recommendations.
- Procedural and limited-context rows remain non-counting unless an explicit methodology decision changes that.
- Not-voting remains excluded from support/opposition.
- Do not change support/opposition, readiness, alignment, or interpretation semantics without an explicit product decision.
- Parent-measure context cannot replace the meaning of a narrower amendment vote.
- LLMs may draft cached/source-grounded explanations, but must not decide eligibility, vote meaning, alignment, readiness, or evidence tier.

## Repository Operating Model

- Prefer one branch and one meaningful product outcome per milestone.
- Keep diffs scoped to the active milestone and preserve unrelated untracked artifacts.
- Do not open a PR until the milestone definition of done is met unless the user explicitly authorizes preview or deployment validation.
- Do not treat planning, audit, preflight, or documentation alone as completion when implementation remains in scope.
- Substantial milestones must follow `docs/PLANS.md` and maintain one active plan under `docs/plans/`.
- Reference workflow runbooks in `docs/workflows/` instead of duplicating their full content in prompts or `AGENTS.md`.
- Editorial generation and standardization work must follow `docs/workflows/editorial-standardization-pipeline.md`, including its non-negotiable autonomy, failure-handling, and review-routing contract.

## Autonomy

When the milestone permits it, Codex may continue autonomously through established stages:

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

Normal movement between these stages is not a reason to stop.

## True Stop Conditions

Stop for:

- new schema or product-semantics decisions outside the milestone envelope
- ambiguous civic meaning or conflicting authoritative sources
- a vote/evidence type the current model cannot represent safely
- failed hard gates
- incomplete rollback
- destructive or unbounded behavior
- production effects differing materially from preflight
- unexpected counting, readiness, alignment, API, security, accessibility, or data-integrity effects
- infrastructure/configuration ambiguity involving services, secrets, or environments

## Production Safety

- No production write unless the milestone explicitly authorizes that class of write.
- Define exact bounded scope and caps before writing.
- Create rollback before writing.
- Run preflight before writing.
- Validate actual versus expected effects after writing.
- Run idempotency or no-write checks where applicable.
- Preserve table boundaries and stop on material mismatch.
- Do not expose secrets.
- Security changes must use least privilege.

Use `docs/workflows/bounded-production-write.md` for production-write milestones.

## Quality And Tooling

- Run targeted relevant tests.
- Build when frontend/runtime behavior changes.
- Perform production-backed and rendered validation for meaningful UI work.
- Use bounded commands with timeouts.
- Split long validation into independently reported checks.
- Do not repeatedly rerun a hanging command.
- Distinguish local-tool limitations from product failures.
- Report the exact active command/status when steered.
- Honor user steering before starting another command after the current safe command returns.

## Instruction Precedence

1. The user's current milestone request.
2. Applicable `AGENTS.md` instructions by directory scope.
3. The active execution plan.
4. Workflow runbooks.
5. Broader methodology and product documentation.

The active plan records implementation decisions but cannot override higher-priority instructions. Workflow runbooks supply defaults; they do not permit actions forbidden by the milestone. Production-write permission must come from the milestone decision envelope or explicit user approval.

## Core Stack And Structure

Backend: Python 3.11+, FastAPI, Postgres/Supabase.

Frontend: Next.js, Tailwind CSS.

Deployment: Render backend, Vercel frontend.

Maintain the repository structure:

- `backend/app/api`
- `backend/app/classification`
- `backend/app/etl`
- `backend/app/metrics`
- `backend/app/summaries`
- `backend/db`
- `backend/tests`
- `backend/migrations`
- `frontend/app`
- `frontend/components`
- `frontend/lib`
- `docs`
- `scripts`

## Reference Documents

- Planning convention: `docs/PLANS.md`
- Milestone execution: `docs/workflows/milestone-execution.md`
- Bounded production writes: `docs/workflows/bounded-production-write.md`
- Product/rendered validation: `docs/workflows/product-and-rendered-validation.md`
- PR, merge, deployment: `docs/workflows/pr-merge-deployment.md`
- Development workflow: `docs/development_workflow.md`
- Deployment details: `docs/deployment.md`
- Methodology and civic rules: `docs/methodology.md`
- Interpretation principles: `docs/interpretation_principles.md`
