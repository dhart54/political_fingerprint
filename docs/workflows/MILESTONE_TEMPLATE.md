# Milestone Brief Template

Use this concise shape for future requests. Do not restate all standard repository guardrails; reference the applicable workflow docs.

## Intent

- Immediate task:
- Connection to larger product goal:

## Outcome

- User-visible or operational result:

## Definition Of Done

- 
- 
- Tests/build/validation:
- Documentation/review packet:
- PR/merge authority, if any:

## Scope

- Included systems/product areas/data/environments:
- Excluded:

## Decision Envelope

- Codex may decide and execute autonomously:
- Explicit approval required for:

## Novel Stop Conditions

Only list risks not already covered by `AGENTS.md` or the runbooks.

- 

## Specific Constraints

- Caps:
- Target tables/files/profiles/viewports/deployments:
- Required examples:

## Workflow References

- `docs/PLANS.md`
- `docs/workflows/milestone-execution.md`
- Add one or more:
  - `docs/workflows/bounded-production-write.md`
  - `docs/workflows/product-and-rendered-validation.md`
  - `docs/workflows/pr-merge-deployment.md`

## Final-Report Additions

Only task-specific reporting beyond the standard workflow.

- 

## Example

Intent: Improve the accountability profile's issue evidence navigation so users can reach the strongest reviewed votes faster.

Outcome: Strong and mixed issue sections render a compact issue index, concise evidence cards, and preserved full source detail behind expansion.

Definition of done:

- Valerie, Thom Tillis, and one sparse profile validate the hierarchy.
- Frontend targeted tests and `npm run build` pass.
- Rendered validation covers mobile and desktop.
- Review packet records before/after hierarchy and limitations.

Scope:

- Frontend profile components and presentation helpers only.
- No production writes, no interpretation imports, no alignment algorithm changes.

Decision envelope:

- Codex may restructure components, copy, and presentation helpers.
- Codex may not change counting, readiness, or alignment semantics.

Workflow references:

- `docs/PLANS.md`
- `docs/workflows/milestone-execution.md`
- `docs/workflows/product-and-rendered-validation.md`

Continue until definition of done or a true stop condition. Do not ask for repeated approval for proven workflow transitions. Do not open or merge a PR unless this brief explicitly grants that authority.
