# Milestone Plan: Internal Route Auth Convention

## Intent

- Immediate task: Design and implement a minimal private/internal route convention before exposing `Record Across Congresses` over HTTP.
- Larger-goal alignment: Protect internal-only backend features while preserving the House `Record Across Congresses` product boundary.

## Outcome

- User-visible or operational result: A reusable internal-route guard plus a guarded, OpenAPI-excluded House `Record Across Congresses` endpoint that reuses the PR #50 transport.

## Scope And Boundaries

- In scope: Private/internal route convention, House `Record Across Congresses` internal endpoint if safe, existing PR #50 transport, PR #49 guardrails, backend tests, OpenAPI/public-route validation, review packet.
- Out of scope: Production writes, database tables, migrations, schema changes, ingestion, interpretations/classifications, frontend runtime changes, public endpoints, Senate, new Congress, broad auth framework, continuity/change labels.
- Files/systems likely touched: `backend/app/`, `backend/tests/`, `docs/plans/`, `docs/review_packets/`.

## Decision Envelope

- Codex may decide and execute: minimal env/header guard shape, internal path naming, route tests, review packet, PR/deployment workflow.
- Explicit approval required for: secrets/config changes in deployment, broad auth framework, frontend runtime work, schema changes, production writes, public route exposure, or unsupported product claims.

## Definition Of Done

- [x] Design note answers private-route convention questions.
- [x] Internal guard fails closed when env secret is missing/empty and when request token is missing/incorrect.
- [x] Internal route, if mounted, is under an internal namespace and excluded from public OpenAPI.
- [x] Endpoint reuses PR #50 transport without duplicating adapter/helper/artifact logic.
- [x] Tests cover unauthorized and authorized access, OpenAPI exclusion, response shape, guardrail copy, profiles, and file-boundary checks.
- [x] Full backend suite attempted because app routing/startup behavior changes; local environment failures recorded.
- [x] Review packet records convention, validation, deployment notes, and next milestone.
- [x] PR/deployment readiness recorded.
- [x] Final reconciliation completed.

## Baseline

- Branch/base commit: `codex/internal-route-auth-convention` from `main` at `c9dd20348015cb0a722f37d6e58422f3737abf49`.
- Production/deployment state, if relevant: No production writes authorized. Deployment secret changes are not authorized in this milestone.
- Tracked working tree: Clean at branch creation.
- Known unrelated untracked artifacts: `docs/review_packets/chamber_filtering_data_integrity_audit.md`; `review_bundle_frontend_data_grounding/`.

## Implementation Sequence

1. Confirm existing route/config patterns and write the design decision.
2. Add a minimal internal header guard using an environment variable and constant-time comparison.
3. Mount a guarded internal route with `include_in_schema=False` that calls the PR #50 transport.
4. Add targeted tests for all guard failure modes, success path, OpenAPI exclusion, profile summaries, and file-boundary checks.
5. Run targeted tests, then full backend suite.
6. Write review packet and reconcile plan.
7. Commit intended files, open PR, wait for checks, merge if clean, and verify deployment.

## Progress Checklist

- [x] Discovery
- [x] Implementation
- [x] Validation
- [x] Documentation
- [x] Commit/PR readiness

## Discoveries

- Baseline confirmed at requested commit `c9dd20348015cb0a722f37d6e58422f3737abf49`.
- Unrelated untracked artifacts are preserved and excluded.
- Existing configuration uses environment variables directly in `backend/app/main.py` and `backend/app/db.py`.
- No broad auth framework or existing private route convention exists.
- Production-shaped route validation confirmed unauthorized requests return 401 and authorized requests return expected adapter summaries for required profiles.

## Decisions And Rationale

- Use a minimal reusable internal guard: `INTERNAL_API_TOKEN` plus `X-Internal-API-Token`.
- Fail closed if the environment token is unset/blank or if the request header is missing/wrong.
- Exclude the route from OpenAPI with FastAPI `include_in_schema=False`.
- Do not change deployment secrets in this milestone; production will fail closed unless the environment variable is configured later.
- Use `401` with generic `Unauthorized` detail for guard failures; use `404` with generic `Record unavailable` for unresolved legislator identifiers.

## Deviations Or Corrections

- None yet.

## Validation Results

- Targeted route/transport tests passed: `52 passed`.
- Production-shaped route validation with `TestClient` and a temporary local token passed for Valerie Foushee, Aaron Bean, Adam Smith, Abraham J. Hamadeh, Allred, Aumua Amata Coleman Radewagen, and James Gallagher.
- Full backend suite was attempted with `python -m pytest`; it was not green due to local environment/data issues outside the new route tests. Failures included fixture API assertions seeing production-shaped data and Windows pytest temp permission errors.
- A rerun with `DATABASE_URL` cleared and `--basetemp .pytest_tmp_internal_route_full` still ended in a Windows permission error during pytest temp cleanup.
- Targeted tests for changed behavior remained green.

## Production Writes

- Performed: no
- Scope: Not authorized.
- Expected effects: None.
- Actual effects: None.

## Rollback Paths

- Revert guard, route, tests, plan, and review packet. No data rollback required.

## Blockers

- None yet.

## Final Reconciliation

- Definition of done satisfied: Yes for the scoped implementation: the internal route convention is implemented, guarded, OpenAPI-excluded, route/profile tested, and documented. Full-suite local validation was attempted and its unrelated local failures are recorded.
- Remaining limitations: Production authorized route probing requires `INTERNAL_API_TOKEN` to be configured in Render, which this milestone does not change. The local pytest temp directory from the prior full-suite attempt was removed during resume.
- Recommended next step: Configure `INTERNAL_API_TOKEN` in the backend deployment environment, then run authorized production route validation before any frontend prototype consumes the endpoint.
