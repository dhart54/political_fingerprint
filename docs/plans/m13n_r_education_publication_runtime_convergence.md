# Milestone Plan: M13N-R Education Publication Runtime Convergence

## Intent

- Add the smallest fail-closed runtime support needed for a future, independently authorized Education publication row.
- Preserve the separation between runtime capability and publication activation.

## Outcome

- A draft PR from `df8d71103df616d6551b108fd8f680bc5a53c951` can be reviewed, merged, and deployed as a prerequisite to truthful M13N activation preparation.

## Scope And Boundaries

- In scope: Education constants, preparation/activation authority validation, explicit three-domain dispatch, public projection, focused adversarial tests, runtime-source-path documentation, validation, and draft PR.
- Out of scope: production preflight, runtime-health proof artifact, preparation or activation authority artifacts, write set, rollback evidence, registry mutation, production writes, activation, merge, and post-PR deployment.
- Accepted M13M content and wording remain byte-identical.

## Decision Envelope

- Codex may implement and validate production-inactive runtime capability and open the draft PR.
- Independent review is required before merge/deployment; M13N remains stopped until that exact merged runtime is deployed.

## Definition Of Done

- [x] Education is selectable only with the exact candidate, preparation authority, sealed activation authority, metadata, and active registry-row contract.
- [x] Unknown identities fail closed and no longer fall through to National Security.
- [x] No-row baseline keeps Education receipts-only while Justice, National Security, and Environment remain unchanged.
- [x] A synthetic exact future row projects 119/all as reviewed conclusions and 118 as receipts-only without wording changes.
- [ ] M11N/M12N/M13M compatibility, runtime drift guards, semantic pipeline, formatting/lint/compile, PostgreSQL suites, and hosted CI pass.
- [ ] Draft PR is open and unmerged; no production mutation or activation artifact exists.

## Baseline

- Branch: `codex/m13n-r-education-publication-runtime-convergence`.
- Base: `df8d71103df616d6551b108fd8f680bc5a53c951`.
- Deployed backend before this milestone: the same base commit, lacking Education publication dispatch.
- Original dirty checkout and protected ZIPs remain untouched.

## Implementation Sequence

1. Complete explicit fail-closed publication dispatch and exact Education authority contracts.
2. Add focused inactive, future-valid-row, mutation, unknown-identity, and compatibility tests.
3. Document the future M13N production-sensitive source paths.
4. Run focused and release-level validation, inspect the diff, commit, and open a draft PR.
5. Wait for exact-head hosted CI and stop for independent runtime/governance review.

## Progress Checklist

- [x] Exact-base isolated worktree and scope reconciliation
- [x] Runtime implementation
- [x] Focused/adversarial tests
- [x] Compatibility and release validation
- [ ] Draft PR and hosted CI

## Discoveries

- The prior dispatch explicitly recognized Environment but treated every other identity as National Security; this accidental fallthrough must be removed.
- The accepted M13M selector already supplies the required Education 119/all/118 projection, so no presentation or wording change is needed.
- Evolving `site_publication.py` exposed a missing frozen-successful-runtime entry in the M12N preparation replay. Adding the exact accepted `a831d472...` manifest restored governed V3 replay without changing current execution-runtime strictness.

## Decisions And Rationale

- Use explicit branches for the three accepted identities and fail closed for everything else; a dynamic registry would exceed this milestone.
- Reuse the hardened M12N V3 stable-runtime and historical-evidence validators for Education positive authority.

## Validation Results

- Focused M13N-R/M13M/dispatch tests: 34 passed.
- M11N/M12N/M13M compatibility and drift suite: 92 passed.
- Frozen M12N V3 candidate, authority materialization, and successful-activation closeout replay: passed with accepted identities unchanged.
- Governed editorial release pipeline: 7 checks passed outside the restricted Windows temporary-directory sandbox.
- Ruff check/format, Python compile, diff check, M13M deterministic builder, Semantic IR validation, and public review-state catalog: passed.
- Relevant local PostgreSQL suites: 2 skipped because no disposable database URLs are configured; hosted service-container jobs remain required.
- Live read-only surface check: Justice, National Security, and Environment are `reviewed_conclusion`; Education is `receipts_only`. No production mutation was performed.
- Two pre-existing `test_api_editorial_presentations.py` cases fail locally before publication selection because the local profile lookup returns 404 without the CI database fixture; the touched publication modules are not on those failing paths. Hosted CI is the authoritative environment for those cases.

## Production Writes

- Performed: no.
- Expected/actual effects: none; this milestone never connects a mutation path to production.

## Rollback Paths

- Code-only draft PR; no production rollback applies. Reverting the eventual runtime commit is the code rollback before any later activation.

## Blockers

- None currently. A regression in frozen M12N replay, existing-domain parity, or execution-runtime drift validation is a hard gate.

## Final Reconciliation

- Definition of done satisfied: pending.
- Next step after acceptance: merge/deploy this runtime in a separately governed action, then restart M13N from that post-convergence main.
