# AGENTS.md - Political Fingerprint

This file defines durable repository rules for Codex and coding agents. Follow it
unless the user's current milestone request gives a more specific instruction.

Detailed execution guidance belongs in referenced workflow documents rather than
being duplicated here.

## Product identity

Political Fingerprint is a curiosity-led, trust-anchored civic analytics
platform.

Primary promise: "In 60 seconds, understand how this politician actually
behaves."

North star: "Who represents me, how are they acting on the issues I care about,
and what can I do next?"

The product maps observable legislative behavior. It must not rank politicians,
infer motives, make corruption claims, predict behavior, tell users how to vote,
or turn campaign statements into governing records.

Before product copy, summary, evidence, Semantic IR, or UI interpretation work,
read `docs/interpretation_principles.md`.

## Civic integrity

- Preserve amendment, final-passage, procedural, limited-context, Present,
  Not Voting, service-status, and missing-evidence distinctions.
- Do not infer motive, ideology, character, corruption, causality, endorsement,
  or voting recommendations.
- Procedural and limited-context rows remain non-counting unless an explicit
  methodology decision changes that.
- Present and Not Voting are resolved non-directional statuses and remain
  excluded from support or opposition.
- Parent-measure context cannot establish the meaning or domain eligibility of a
  narrower exact action.
- Do not change support/opposition, eligibility, evidence-tier, readiness,
  alignment, counting, or interpretation semantics without an authorized
  product or methodology decision.
- Rendering cannot add analytical meaning absent from the canonical semantic
  model.

LLMs may research, propose, challenge, and explain source-grounded semantic
interpretations. Their work must compile into typed, source-mapped artifacts and
pass the applicable evidence, civic-integrity, and review contracts.

Deterministic code owns repeatable application of established contracts across
members and records. Novel, genuinely ambiguous, conflicting, or unsupported
semantic decisions require review before acceptance or publication.

An LLM-generated interpretation is a candidate. It is not automatically approved,
gold, benchmarked, production-eligible, promoted, or publishable.

## Canonical editorial boundary

For new editorial work, the canonical contract between shared evidence and later
presentation is Editorial Semantic IR V1:

- `docs/semantic_ir/editorial_semantic_ir_v1.md`
- `docs/semantic_ir/editorial_semantic_ir_v1.schema.json`

The canonical output is the typed behavioral proposition graph, synthesis
propositions, evidence-state boundaries, action accounting, and conclusion plan.
Exact prose is a replaceable presentation result.

Later stages may select, relate, omit, or render established semantic objects.
They may not reinterpret earlier-stage meaning.

Semantic IR V1 is the only executable editorial semantic architecture. Frozen
pre-IR dossiers, receipts, proof artifacts, and provenance remain historical
evidence, but deleted pre-IR generators and old-format frontend adapters must
not be recreated for replay or compatibility.

Until an IR-native presentation milestone is separately authorized, the public
representative experience uses basic vote evidence and receipts without
reconstructing analytical conclusions in React.

## Repository operating model

- Use one accountable implementation owner and one meaningful outcome per
  milestone.
- Keep diffs centered on the requested outcome and preserve unrelated tracked
  and untracked work.
- Classify adjacent findings as blocking, follow-up, or historical. Only blocking
  findings may automatically expand the active task.
- Do not turn a bounded change into repository-wide reconciliation.
- Use direct execution for small isolated changes, a compact plan for normal
  cross-file work, and a living execution plan for production, methodology,
  infrastructure, or genuinely long-running work.
- Planning, audits, and documentation are not completion when implementation
  remains in scope.
- Follow `docs/workflows/editorial-standardization-pipeline.md` when legislative
  semantics, proposition generation, review routing, or publication state are
  affected.
- Follow `docs/workflows/codex-operating-model.md` for planning, scope,
  parallelism, RTK, and validation defaults.

## Autonomy

Within the user's authorized milestone, continue through ordinary discovery,
implementation, safe correction, targeted validation, diff review,
documentation, commit preparation, and PR preparation without repeated
handoffs.

An ordinary in-scope defect or failing targeted test is not a stop condition when
its cause can be safely corrected without weakening a rule or changing the
authorized outcome.

Do not merge, deploy, publish, promote, approve editorial artifacts, alter
publication registries, or write to production unless the current milestone
explicitly authorizes that action.

## True stop conditions

Stop only when:

- authoritative sources materially conflict and no established rule resolves
  them;
- the task requires a new product, architecture, ontology, or methodology
  decision outside the milestone;
- the available evidence cannot support a safe representation;
- a new action, evidence, service-status, or semantic type cannot be represented
  safely by the established contract;
- a destructive, security-sensitive, or unbounded action would be required;
- production effects would exceed the approved envelope;
- a required rollback is absent, incomplete, or invalid;
- a hard gate remains unresolved after safe in-scope correction;
- the requested outcome cannot be completed without materially expanding scope.

When existing standards support a defensible candidate interpretation, produce
and route the candidate rather than stopping merely because later review is
required.

## Production safety

- No production write unless the milestone explicitly authorizes that class of
  write.
- Define exact bounded scope and caps before writing.
- Create and validate rollback before writing.
- Run preflight before writing.
- Validate actual versus expected effects after writing.
- Run idempotency or no-write checks where applicable.
- Preserve table and publication boundaries and stop on material mismatch.
- Do not expose secrets.
- Security changes must use least privilege.

Use `docs/workflows/bounded-production-write.md` for production-write milestones.

## Validation

Choose the lowest validation tier that establishes confidence in the behavior
actually touched.

### Semantic loop

Use for Semantic IR schemas, candidate cases, proposition logic, action
accounting, coverage contracts, and focused interpretation corrections.

Canonical commands:

```powershell
python scripts/validate_editorial_semantic_ir.py
python -m unittest backend.tests.test_editorial_semantic_ir
```

Do not trigger frontend, browser, database, persistence, or full-population work
solely because a Semantic IR authoring file changed.

### Domain loop

Use when a change affects one complete issue domain, its members, vectors,
fixtures, or persistence proposal.

### Release loop

Use near merge when changes affect cross-domain runtime behavior, frontend
runtime, migrations, production persistence, publication controls, or
deployment.

Do not run a release loop reflexively after every small correction.

Always inspect the resulting behavior and final diff. Passing tests alone does
not establish completion. Report unrelated baseline failures separately.

## Instruction precedence

1. The user's current milestone request.
2. Applicable directory-scoped `AGENTS.md` instructions.
3. This repository root `AGENTS.md`.
4. The active execution plan.
5. Workflow runbooks.
6. Broader methodology and product documentation.

The active plan records implementation decisions but cannot override
higher-priority instructions. Workflow runbooks supply defaults; they do not
authorize forbidden actions. Production-write, publication, promotion, approval,
merge, and deployment authority must come from the current milestone or explicit
user approval.

## Core stack and structure

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

## Reference documents

- Codex operating model: `docs/workflows/codex-operating-model.md`
- Editorial generation: `docs/workflows/editorial-standardization-pipeline.md`
- Semantic IR contract: `docs/semantic_ir/editorial_semantic_ir_v1.md`
- Planning convention: `docs/PLANS.md`
- Milestone execution: `docs/workflows/milestone-execution.md`
- Bounded production writes: `docs/workflows/bounded-production-write.md`
- Product/rendered validation:
  `docs/workflows/product-and-rendered-validation.md`
- PR, merge, deployment: `docs/workflows/pr-merge-deployment.md`
- Development workflow: `docs/development_workflow.md`
- Deployment details: `docs/deployment.md`
- Methodology and civic rules: `docs/methodology.md`
- Interpretation principles: `docs/interpretation_principles.md`
