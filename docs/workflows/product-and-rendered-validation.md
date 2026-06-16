# Product And Rendered Validation Workflow

Use this runbook for UI, profile, evidence, narrative, accessibility, and product-flow changes.

## Evidence Integrity

Validate production-shaped examples when the product depends on real evidence structure:

- strong profiles
- mixed profiles
- sparse or limited profiles
- procedural-context profiles
- amendment-heavy profiles
- final-passage rows when relevant

Check backend/API evidence integrity before assuming a frontend bug:

- active interpretation and classification selection
- evidence joins
- chamber and version filtering
- support/opposition counts
- procedural and not-voting exclusion
- amendment and final-passage serialization

## Rendered Review

Review desktop, tablet, and mobile layouts when the visual hierarchy changes.

Check:

- first useful answer
- information hierarchy
- scroll length and density
- duplicate content
- horizontal overflow
- focus, tap, and keyboard usability
- accessibility controls obstructing content
- empty states and limited-evidence states
- evidence details, sources, caveats, and expanded proof

Use screenshots or reproducible rendered output when possible.

## Local And Preview Paths

- Prefer local rendering when it is reliable.
- If local rendering hits known Windows/Codex limitations, report the exact failing command and use Vercel/live preview when available.
- If preview is deployment-protected, distinguish that access limitation from a product failure.
- Do not repeatedly rerun a hanging local server command.

## Continue Beyond Audit

Do not stop after diagnosing duplication, scroll problems, or evidence issues when the milestone includes implementation. Continue through fix, validation, build, and documentation unless a true stop condition is hit.

## Record Results

Document:

- representative profiles reviewed
- viewports or rendered paths checked
- before/after hierarchy or scroll observations
- tests/builds
- local-tool or preview-access limitations
- remaining product risks
