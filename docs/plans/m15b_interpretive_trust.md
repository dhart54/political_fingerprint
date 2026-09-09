# M15B — interpretive trust

Baseline: `5a1593d67d5ccb952acf7234cebffa5a7d1d53fc`.

Outcome: enforce evidence-bound comparability for future trajectories and replace
lexical receipt-caveat deletion with an explicit semantic treatment boundary.
Prepare the bounded National Security remediation and affected caveat review set
without accepting or publishing new interpretations. This protects the product's
60-second explanation from structural signals substituting for policy meaning.

Scope: forward contracts/validators, minimal receipt projection/rendering changes,
one compact review package and one draft PR. Historical accepted artifacts and
M15A execution records remain immutable. No production writes, merge or deploy.

Sequence:
1. Trace the existing compiler, accepted lineage, publication and render paths.
2. Inventory only live trajectories and caveats hidden by the old filter.
3. Implement affirmative comparison evidence and explicit limitation treatments.
4. Generate deterministic before/after candidate views and targeted regressions.
5. Validate relevant semantic, receipt, four-domain and benchmark paths; inspect
   the diff; open one draft PR and check hosted CI for independent review.

Validation tier: release-level semantic/public boundary regressions, with focused
negative and positive synthetic cases during implementation. No database repair
or production persistence validation is part of this milestone.

Decisions and findings:
- Interpretation principles and editorial-standardization workflow read.
- Candidate compilation currently checks chronology/direction, not comparability.
- The public receipt renderer deletes mixed evidence/process text by regex.
- Substantive removal/copy remains a pending review candidate, not authority.

Definition of done: forward rules reject unsupported comparisons; valid comparable
input passes; mixed caveats survive or use explicit authored public copy; active
affected output is fully enumerated; independent review can inspect exact deltas.

Progress:
- Mapping complete. The candidate compiler, future pipeline and behavioral
  implementation validator enforce separately trusted comparability. Exact frozen
  historical replay is isolated and content-bound; it cannot accept changed input.
- Read-only public inventory matched repository sources. Two trajectories found:
  National Security FAIL; Justice NEEDS_HUMAN_SEMANTIC_REVIEW. No Environment or
  M14 Education trajectory. Only NS has a removal candidate.
- The 35 hidden Justice caveats are substantive, not process-status assertions;
  retain their exact source text. Breakdown PUBLIC 35 / INTERNAL 0 / MIXED 0.
  No new real-member wording is authored. Synthetic mixed-copy tests remain tests.
- Two-state limitation contract and receipt overlay implemented. Explicit public
  copy is authoritative; legacy handling preserves substantive text and blocks
  only complete known process boilerplate and structural internals.
- Three deterministic review artifacts complete. Actual React before/after render
  confirms NS trajectories 1→0, findings 15→14 and supporting actions 32→30 while
  receipts/accepted meanings/other findings remain unchanged. No runtime removal.
- Final focused backend run: 82 passed, including comparison, historical replay,
  receipt overlay and record integrity. Frontend regressions: 47 passed. One
  real-browser receipt test passed. Production frontend build passed with existing
  unrelated Hook warnings. Full-record benchmark-role validator passed.
- Broad backend regression: 265 passed initially; the schema dependency issue was
  corrected by finishing the locked dependency install and its test passed. Two
  existing held-out byte locks expect CRLF while this isolated checkout uses LF;
  no semantic fixture was edited. The existing hosted lane normalizes those bytes.
- CI reuses the existing M14H product-quality lane with an appended M15B step.
  Earlier job blocks remain intact. A prior lexical browser assertion was replaced
  with preservation of the exact substantive caveat, retaining metadata checks.

Final checkpoint: inspect the scoped diff, one draft PR and hosted CI. No merge,
deployment, production writes, M15A repair checks or historical artifact changes.
Rollback is reverting this unmerged branch; there are no production effects.
