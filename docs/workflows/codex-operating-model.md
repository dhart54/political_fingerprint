# Codex operating model

## Purpose

This workflow defines how Codex should execute Political Fingerprint milestones
without duplicating product rules, civic methodology, or milestone-specific
instructions.

The repository root `AGENTS.md` remains authoritative for product identity,
civic integrity, production restrictions, and approval boundaries. This document
supplies execution defaults.

## Default owner and configuration

The user's selected model and reasoning effort are intentional. A single primary
Sol session should normally own the milestone from intent through final
reconciliation.

The owner is responsible for:

- understanding the intended product outcome;
- inspecting the relevant repository state;
- identifying material ambiguity and risk;
- choosing an efficient implementation path;
- making scoped changes;
- selecting proportional validation;
- inspecting the resulting behavior and diff;
- reconciling the result against the definition of done;
- reporting what changed, what was verified, and any real limitations.

Do not recommend a more expensive model, more reasoning, Pro/Max/Ultra mode,
Terra, Luna, or multiple agents unless the task shape supplies a concrete
advantage.

## Bounded autonomy

Continue autonomously through ordinary in-scope work:

- repository inspection;
- implementation;
- safe correction of defects introduced or exposed by the task;
- resolution of targeted test failures with clear in-scope causes;
- directly affected documentation;
- proportional validation;
- diff and behavior inspection;
- commit and PR preparation when authorized.

Do not stop for normal discoveries or safely correctable failures.

Stop only for a true repository stop condition, an authorization boundary, or a
material scope expansion that cannot be resolved from existing standards.

## Scope classification

Classify adjacent findings before changing scope.

### Blocking

The requested result would otherwise be incorrect, unsafe, corrupting, or
impossible to validate.

Blocking findings may expand the task only as far as required to make the
requested outcome safe and correct.

### Follow-up

The finding is useful or desirable but not required for the current outcome.

Record it in the active plan, PR summary, or follow-up inventory. Do not absorb
it into the current PR.

### Historical

The finding accurately records an earlier phase or no longer governs current
runtime behavior.

Do not rewrite historical material merely to make every old document read like a
current-state dashboard. Current state should be determined from designated
canonical contracts and receipts.

## Planning tiers

### Direct execution

Use for small, isolated, reversible changes.

- Provide a brief preread with intent and expected result.
- Inspect the relevant files.
- Implement.
- Run targeted validation.
- Inspect the final diff.

No persistent plan is required unless another repository instruction requires
one for that class of work.

### Compact plan

Use for normal cross-file features, meaningful bug fixes, or moderately
ambiguous tasks.

Record only:

- intent;
- scope and non-scope;
- implementation sequence;
- definition of done;
- selected validation.

Keep it operational and concise.

### Living execution plan

Use for:

- production writes;
- methodology or semantic-contract changes;
- multi-system runtime changes;
- deployment or infrastructure work;
- long autonomous milestones;
- work requiring rollback;
- work with multiple independent validation stages.

A plan supports execution. It is not a second copy of the prompt, and maintaining
it is not completion.

## Change-size awareness

Before substantial implementation, estimate:

- expected changed-file count;
- likely generated-output fan-out;
- selected validation tier;
- approximate runtime.

If a small change unexpectedly expands into a large regeneration or release
operation, diagnose the owning dependency before continuing blindly.

An imperfect estimate is not itself a reason to stop. Stop only when the fan-out
creates a real product decision, safety risk, or material departure from the
authorized milestone.

## Tool selection

Prefer the shortest dependable method.

- Use native Git and shell commands for ordinary work.
- Use `rg` or equivalent repository search for normal discovery.
- Use native file-reading tools when they require less command construction.
- Use wrappers only when they provide a demonstrated advantage.
- Use bounded commands and reasonable timeouts.
- Do not repeatedly rerun a hanging or clearly broken command.
- Distinguish local tooling limitations from product failures.
- Do not introduce proxy scripts, fragile quoting, or orchestration solely to
  satisfy a generic optimization rule.

### RTK

RTK remains an optional context- and output-reduction optimization.

Use dedicated RTK commands for supported commands with large or repetitive
output when compressed output remains sufficient for diagnosis.

Use `rtk batch` when:

- commands are independent;
- compressed output is useful;
- individual failures remain visible;
- coordination and quoting cost is low.

Do not use RTK or batching for:

- dependent commands;
- adaptive investigations;
- interactive commands;
- overlapping mutations;
- production writes;
- commands requiring exact raw output;
- cases where wrapper complexity exceeds the expected benefit.

On native Windows, do not use `rtk proxy` to wrap PowerShell, shell built-ins,
pipelines, compound expressions, script blocks, or nested quoting. Fall back to
native commands after one compatibility failure.

Concurrency and RTK selection are separate decisions.

## Parallelism and subagents

Parallelize only independent lanes with low coordination cost.

Good uses include:

- read-only repository exploration;
- independent source or documentation review;
- test-gap analysis;
- separate review lenses;
- independent validation commands;
- log or failure investigation.

Keep dependent work sequential.

The primary Sol session remains the integration and decision owner. Avoid
multiple agents editing the same worktree or overlapping files.

Terra may be useful for large read-heavy exploration. Luna should be reserved for
mechanical, tightly specified work. Product interpretation, architecture,
semantic decisions, difficult review, and final integration remain with Sol.

## Validation tiers

### Semantic loop

Purpose: validate authoring contracts and interpretation structure before runtime
generation.

Typical checks:

- JSON Schema;
- stable IDs;
- reference integrity;
- action eligibility and accounting;
- episode and policy-family hierarchy;
- coverage arithmetic;
- proposition role and presentation ownership;
- held-out answer leakage;
- focused property tests;
- documentation governance;
- `git diff --check`.

Canonical commands:

```powershell
python scripts/validate_editorial_semantic_ir.py
python scripts/compare_accepted_semantic_references.py
python -m unittest backend.tests.test_editorial_semantic_ir
```

Target: seconds.

### Domain loop

Purpose: validate all affected outputs for one issue domain.

Typical checks:

- all domain members;
- observed and synthetic vectors;
- domain mutations;
- review fixtures;
- domain persistence proposal;
- focused backend and frontend behavior directly affected by the domain.

Target: minutes.

### Release loop

Purpose: establish confidence near merge or deployment for integrated changes.

Typical checks:

- cross-domain regressions;
- frontend build and browser validation;
- disposable PostgreSQL proof;
- persistence round trips;
- migrations;
- publication and registry boundaries;
- broad backend and frontend suites;
- rollback and idempotency receipts;
- deployment verification when authorized.

Do not run this tier after every small semantic correction.

## PR scope rules

A PR owns the requested outcome and its direct invariants. It does not
automatically own every adjacent inconsistency in the repository.

Expand an active PR only when the adjacent issue:

- makes the requested output incorrect;
- creates data corruption or security risk;
- violates an approval, production, or publication boundary;
- prevents validation of the requested outcome.

Otherwise record it as follow-up debt.

Do not reopen a correct bounded PR for status-only wording, unrelated cleanup, or
historical-document normalization.

## Definition of done

A milestone is complete when:

- the requested outcome is implemented;
- directly affected behavior is validated at the appropriate tier;
- the final diff is inspected;
- actual behavior is reconciled against the intended outcome;
- material limitations are reported honestly;
- unrelated follow-up work has not been silently absorbed.

Planning, file generation, and passing tests are not completion when the intended
product result remains unfinished.
