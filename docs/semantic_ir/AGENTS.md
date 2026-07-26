# Semantic IR instructions

Follow the repository root `AGENTS.md`.

This directory contains canonical semantic authoring, acceptance-corpus, and
held-out evaluation artifacts. These instructions apply to all files under
`docs/semantic_ir/`.

## Authority

- Editorial Semantic IR is the contract between authoritative evidence and later
  presentation.
- The canonical result is the typed behavioral proposition graph, synthesis
  propositions, coverage/method/source boundaries, action accounting, and
  conclusion plan.
- Exact prose is non-authoritative.
- Rendering and persistence may consume the IR but may not reinterpret it.
- Shared legislative semantics are member-neutral.
- Member identity and party are context only and cannot change semantic
  selection for identical evidence.

## Semantic roles

Keep these roles distinct:

- behavioral propositions;
- synthesis propositions;
- coverage boundaries;
- method boundaries;
- source/render constraints.

Only section-rendered behavioral propositions use the one-primary-analytical-
section invariant.

Coverage, methodology, and source constraints are not member behavioral
findings.

Every accepted action in a full-record case must contribute to behavioral
evidence or carry an explicit non-proposition reason.

## Review states

Development cases remain candidates until explicitly accepted.

Do not mark any artifact:

- approved;
- gold;
- benchmarked;
- production-eligible;
- promoted;
- published;

without explicit authorization.

Acceptance of an IR schema or candidate graph does not authorize runtime
adoption, persistence, production selection, or publication.

## Held-out cases

Held-out inputs must not contain:

- expected propositions;
- expected boundaries;
- expected action accounting;
- expected section ownership;
- expected conclusions;
- answer-bearing example prose.

Do not inspect or derive hidden expected outputs during implementation of the
engine being evaluated against those cases.

## LLM role

Sol may research, propose, challenge, and revise semantic candidates from
authoritative evidence and established standards.

When meaning is defensible under established rules, produce a candidate rather
than stopping merely because external acceptance is required.

Stop when authoritative sources conflict materially, evidence cannot support a
safe representation, or a genuinely new semantic decision falls outside the
authorized milestone.

## Validation

Use the semantic loop by default:

```powershell
python scripts/validate_editorial_semantic_ir.py
python -m unittest backend.tests.test_editorial_semantic_ir
```

Validate at least:

- schema conformance;
- stable identities;
- reference integrity;
- exact-action eligibility;
- episode and family hierarchy;
- coverage arithmetic;
- proposition evidence;
- semantic role and presentation target;
- action accounting;
- held-out answer leakage.

Do not trigger frontend builds, Playwright, screenshots, PostgreSQL,
full-population generation, persistence proposals, or release validation solely
because an authoring or candidate file changed.

## Scope discipline

Do not rewrite existing dossiers, runtime generators, persistence artifacts, or
historical review packets from this directory unless the current milestone
explicitly includes those changes.

Record adjacent cleanup as follow-up work unless it makes the Semantic IR invalid
or unsafe.
