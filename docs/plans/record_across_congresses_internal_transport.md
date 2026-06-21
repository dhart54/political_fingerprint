# Milestone Plan: Record Across Congresses Internal Transport

## Intent

- Immediate task: Define and implement guarded private/internal transport for the House `Record Across Congresses` adapter.
- Larger-goal alignment: Prove safe backend consumption before any runtime frontend component consumes the data.

## Outcome

- User-visible or operational result: A no-route internal transport callable for trusted backend code that returns the PR #48 adapter response while preserving PR #49 copy and naming guardrails.

## Scope And Boundaries

- In scope: House only; 118th/119th Congresses only; existing interpreted evidence; artifact v1; existing adapter; internal transport; targeted tests; OpenAPI/public-route validation; review packet.
- Out of scope: Production writes, database tables, migrations, schema changes, ingestion, new interpretations/classifications, frontend runtime changes, public routes, public OpenAPI exposure, Senate, new Congress, product copy beyond PR #49, continuity/change labels.
- Files/systems likely touched: `backend/app/analysis/`, `backend/tests/`, `docs/plans/`, `docs/review_packets/`.

## Decision Envelope

- Codex may decide and execute: no-route transport shape, tests, review packet, validation profile reporting, PR/deployment workflow.
- Explicit approval required for: route exposure, new auth infrastructure, secrets/environment changes, schema changes, frontend runtime changes, production writes, or unsupported copy/claims.

## Definition Of Done

- [x] Transport wraps the PR #48 adapter without duplicating adapter, helper, or artifact logic.
- [x] No FastAPI route is added because no safe private-route convention exists.
- [x] Tests prove public route list/OpenAPI contain no public record/congress/comparable/family transport endpoint.
- [x] Tests prove response shape, product framing, non-authorization metadata, disallowed term absence, copy guardrail artifact, and required profile summaries.
- [x] Validation confirms no frontend/schema/migration files changed.
- [x] Review packet explains transport choice, guard behavior, OpenAPI validation, naming/copy safety, allowed/disallowed downstream use, and next milestone.
- [x] Targeted tests pass; full backend tests run if shared routing/app startup behavior changes.
- [x] PR/deployment readiness recorded.
- [x] Final reconciliation completed.

## Baseline

- Branch/base commit: `codex/record-across-congresses-internal-transport` from `main` at `6692cbd290ca11473f9d70fc5c437fbd1cd48886`.
- Production/deployment state, if relevant: No production writes authorized. Deployment verification only after PR/merge.
- Tracked working tree: Clean at branch creation.
- Known unrelated untracked artifacts: `docs/review_packets/chamber_filtering_data_integrity_audit.md`; `review_bundle_frontend_data_grounding/`.

## Implementation Sequence

1. Confirm routing/auth conventions and choose route versus no-route transport.
2. Implement the smallest no-route internal transport wrapper.
3. Add targeted tests for response contract, copy guardrails, no public route/OpenAPI exposure, profiles, and no forbidden file changes.
4. Run targeted tests and production-shaped validation where needed.
5. Document review packet and reconcile plan.
6. Commit intended files, open PR, wait for green checks, merge if clean, and verify deployment health/OpenAPI.

## Progress Checklist

- [x] Discovery
- [x] Implementation
- [x] Validation
- [x] Documentation
- [x] Commit/PR readiness

## Discoveries

- Baseline confirmed at requested commit `6692cbd290ca11473f9d70fc5c437fbd1cd48886`.
- Unrelated untracked artifacts are preserved and excluded from milestone scope.
- `backend/app/main.py` has public routers only; no existing private/internal route namespace, header guard, token guard, or auth dependency pattern was found.
- Production-shaped transport validation matched the PR #48 adapter/helper profile patterns: Foushee/Bean/Adam Smith 11 display-eligible families; Hamadeh/Allred/James Gallagher 0; Aumua Amata Coleman Radewagen 1 conditional family.

## Decisions And Rationale

- Use a no-route internal transport callable rather than inventing a header/token route guard. This avoids public exposure risk and satisfies the milestone's equivalent internal transport option.
- Keep route guard behavior non-applicable rather than simulating auth in a Python function. The effective guard is no HTTP mount, no URL, and no OpenAPI exposure.
- Skip full backend tests because no route registration or app startup behavior changed; targeted tests cover the transport chain and route/OpenAPI absence.

## Deviations Or Corrections

- None yet.

## Validation Results

- `python -m pytest tests\test_house_comparable_families_accessor.py tests\test_house_comparable_family_legislator.py tests\test_house_record_across_congresses.py tests\test_house_record_across_congresses_transport.py` passed (`41 passed`).
- `python -m py_compile app\analysis\house_record_across_congresses_transport.py` passed.
- Production-shaped read-only transport checks completed for Valerie Foushee, Aaron Bean, Adam Smith, Abraham J. Hamadeh, Allred, Aumua Amata Coleman Radewagen, and James Gallagher.
- Worktree/file validation confirmed no frontend runtime files, backend route files, schema files, or migration files were changed.

## Production Writes

- Performed: no
- Scope: Not authorized.
- Expected effects: None.
- Actual effects: None.

## Rollback Paths

- Revert the transport module, tests, plan, and review packet. No data rollback required.

## Blockers

- None yet.

## Final Reconciliation

- Definition of done satisfied: Yes. The milestone adds a no-route internal transport callable, targeted tests, production-shaped validation, and a review packet without public route/OpenAPI exposure, frontend changes, schema changes, or production writes.
- Remaining limitations: No HTTP route exists. This is intentional because no safe private-route convention currently exists in the repository.
- Recommended next step: Design and explicitly approve a private-route authentication/exposure convention, then mount a guarded route that reuses this transport and remains excluded from public OpenAPI.
