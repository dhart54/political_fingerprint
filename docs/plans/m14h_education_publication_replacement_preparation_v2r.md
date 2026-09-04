# M14H Education Publication Replacement Preparation (V2R)

## Intent

- Prepare one exact, reviewable production-replacement package and executor for the human-accepted M14G Education & Workforce presentation.
- Preserve the existing M13 publication as immutable prior state and exact rollback target.

## Outcome

- An additive fail-closed V2R governance contract, exact M14H executor, compact governed review package, disposable-PostgreSQL proof, focused/release validation, and draft PR.

## Scope And Boundaries

- In scope: read-only production/runtime discovery, stable baseline and replacement graph, rollback, executor, unsealed activation candidate, tests, CI, draft PR.
- Out of scope: production writes, registry mutation, activation, deployment, sealing or accepting activation authority, merge, and modification of accepted M13/M14 artifacts or V2.
- Expected touch set: one V2R backend module, one M14H script, focused tests, CI, this plan, and eight compact review artifacts.

## Decision Envelope

- Codex may implement and validate the exact replacement preparation described by M14H.
- Only a later human decision may seal positive activation authority and authorize the prepared production replacement.

## Definition Of Done

- [x] Exact accepted M14G identities and payload are bound without transformation.
- [x] Read-only production baseline and runtime readiness are captured or an evidence limitation is recorded without inventing state.
- [x] Exact 1/3/2/0/1 activation envelope and exact rollback are implemented fail-closed.
- [x] Unsealed, unaccepted prospective positive authority is prepared.
- [x] Disposable apply, idempotency, injected rollback, explicit rollback, selectors, and isolation pass.
- [x] Focused and publication lifecycle/benchmark validation pass locally, subject to the recorded Windows-only baseline limitation and authoritative Linux CI.
- [x] Review package and final reconciliation are complete.
- [ ] Draft PR is open and exact-head CI passes.

## Baseline

- Branch/base commit: `codex/m14h-education-publication-replacement-preparation` from exact `ac922506fe9fd61120d3638060cc18398b461df2`.
- Production/deployment state: read-only production discovery captured; the backend health commit is the exact baseline and exact frontend deployment identity is unavailable, so deployment is required before activation.
- Tracked working tree: clean isolated worktree.
- Known unrelated artifacts: the original checkout contains unrelated tracked/untracked user work and will remain untouched.

## Implementation Sequence

1. Verify accepted inputs, immutable baselines, production/runtime access, and current persistence/selector contracts.
2. Implement V2R stable/fresh validation plus explicit M14H discovery/build/apply/rollback executor.
3. Capture governed review artifacts; prove disposable PostgreSQL behavior and public selection.
4. Run focused and release validation, inspect diff, commit/push, open draft PR, and await exact-head CI.

## Progress Checklist

- [x] Discovery
- [x] Implementation
- [x] Validation
- [x] Documentation
- [ ] Commit/PR readiness

## Discoveries

- The user-facing checkout was on an older dirty M12N branch; M14H is isolated in a new worktree to preserve it.
- Local `main` and `origin/main` both equal the exact requested baseline.
- Live read-only production state is 7 batches, 155 artifacts, 165 relationships, and 4 registry rows with fingerprint `090477315f73df6cadda662f2aa24ef4a30ed0b2e74669bb3e7d5cf73680e01e`.
- The exact active prior Education registry row is artifact 242 / `site-integration-candidate:f000477:education_workforce:119:v1`; no M14G target natural keys are present.
- Backend health reports exact baseline commit `ac922506fe9fd61120d3638060cc18398b461df2`; exact frontend deployment identity could not be proven.

## Decisions And Rationale

- Keep `publication_activation_governance_v2.py`, the migration, and accepted historical artifacts byte-identical; V2R is additive.
- Use the existing 30-minute V2 freshness default.
- Install the additive V2R runtime adapter from application startup so accepted historical selector and publication modules remain semantically unchanged.

## Deviations Or Corrections

- Direct edits initially considered for historical selector modules were removed after their exact-runtime regression contracts surfaced; equivalent M14H support is additive and those files are excluded from the change.

## Validation Results

- M14H focused tests: 12 passed; Ruff: passed.
- Fresh disposable PostgreSQL lifecycle proof: 1 passed, including exact 1/3/2/0/1 apply, four injected rollback points, idempotent second apply, exact explicit rollback, isolation, and 118/119/all selector behavior.
- Accepted M14G/public-receipt frontend tests: 22 passed.
- Historical V2 and M11-M13 focused suites: 126 passed; eight local errors are the same Windows sandbox temporary-directory access limitation reproduced at the exact baseline, not product failures.
- Release validation reached the same baseline Windows temporary-directory limitation; authoritative Linux exact-head CI is pending.

## Production Writes

- Performed: no
- Scope: read-only discovery only.
- Expected effects: none.
- Actual effects: none.

## Rollback Paths

- Activation rollback will restore the exact captured M13 registry row before removing only the owned M14H graph and batch.
- Repository work is isolated on a dedicated branch/worktree.

## Blockers

- No implementation blocker. Exact frontend deployment identity remains intentionally unproven and therefore fail-closes activation behind `deployment_required_before_activation=true`.

## Final Reconciliation

- Definition of done satisfied except for draft PR creation and its exact-head CI result.
- The review package remains an unsealed, unaccepted candidate and grants no production, activation, deployment, merge, or publication authority.
- Remaining limitation: a later fresh runtime proof must establish the deployed backend/frontend identity before any separately authorized production replacement.
- Recommended next step: independent review followed only by the exact production-replacement authorization decision.
