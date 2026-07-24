# Milestone Plan: Record Across Congresses Frontend Prototype

## Intent

- Immediate task: Build the first guarded frontend prototype for the House `Record Across Congresses` panel.
- Larger-goal alignment: Advance user-facing cross-Congress evidence by rendering factual backend availability/counts without continuity, direction, motive, or voting guidance.

## Outcome

- User-visible or operational result: A collapsed advanced section on House profiles, backed by a server-side frontend proxy that keeps `INTERNAL_API_TOKEN` out of browser code.

## Scope And Boundaries

- In scope: Next.js server route/proxy, frontend fetch helper, House-only panel component, placement below strongest issue evidence, targeted frontend tests, build/lint as available, review packet.
- Out of scope: Production writes, schema changes, backend response semantics, public backend exposure, continuity/change analysis, campaign/candidate framing.
- Files/systems likely touched: `frontend/app`, `frontend/components`, `frontend/lib`, `docs/plans`, `docs/review_packets`.

## Decision Envelope

- Codex may decide and execute: minimal server-side proxy shape, sanitized response fields, component structure, test fixture shape, review packet wording, local validation commands.
- Explicit approval required for: production writes, secret/configuration changes, schema changes, product-semantics changes, merge/deployment actions if checks expose ambiguity.

## Definition Of Done

- [x] Server-side token boundary implemented or documented as blocked.
- [x] Collapsed House-only panel renders approved copy and factual counts only.
- [x] Sparse states, family ordering, caveats, and framing mismatch behavior covered by tests.
- [x] Tests/build/validation recorded.
- [x] Review packet or final documentation updated.
- [x] Final reconciliation completed.

## Baseline

- Branch/base commit: `codex/record-across-congresses-frontend-prototype` from `main` at `8f99ee7ce63424550228c308e57b2573c160e47a`.
- Production/deployment state, if relevant: PR #52 production validation is present in `main`; no production writes authorized for this milestone.
- Tracked working tree: clean at branch start.
- Known unrelated untracked artifacts: `docs/review_packets/chamber_filtering_data_integrity_audit.md`, `review_bundle_frontend_data_grounding/`.

## Implementation Sequence

1. Inspect frontend architecture and internal backend route contract.
2. Add a Next.js server route that calls the backend internal route with `X-Internal-API-Token` from server-only env and returns a sanitized body.
3. Add frontend data helper, panel component, and page placement below strongest issue evidence.
4. Add production-shaped fixtures and targeted tests for rendering, copy guardrails, token boundary, proxy failure modes, and bundle/source token checks.
5. Run targeted tests and frontend build/lint where available.
6. Update review packet and reconcile final status.

## Progress Checklist

- [x] Discovery
- [x] Implementation
- [x] Validation
- [x] Documentation
- [x] Commit/PR readiness

## Discoveries

- `main` is at `8f99ee7`, documenting internal route production validation.
- The frontend is a client-heavy Next.js app, but App Router route handlers are available and can hold the backend token server-side.
- The backend internal route is `/internal/record-across-congresses/house/{legislator_identifier}` and uses `X-Internal-API-Token`.
- Next 15 compiles the server route with the `server-only` marker, but direct standalone Node import of that route does not resolve `server-only` outside the Next runtime.
- `npm run lint` invokes deprecated `next lint` and opens an interactive ESLint migration prompt rather than running a configured linter.

## Decisions And Rationale

- Use a Next.js app-local API route as the token boundary because client components can safely call same-origin frontend routes while the backend token remains server-side.
- Sanitize the proxy response to the UI fields required by the frontend contract instead of returning raw internal metadata.
- Reuse the existing issue-domain evidence path for the drilldown affordance because no safe roll-call-family-specific frontend route exists yet.

## Deviations Or Corrections

- Local rendered validation used a header-checking mock backend for the internal route rather than live production token access.

## Validation Results

- `node --test lib\recordAcrossCongresses.test.mjs` passed: 10 tests.
- `node --test lib\*.test.mjs` passed: 50 tests.
- `npm run build` passed with the dynamic Next.js proxy route included.
- `npm run lint` did not run configured linting because `next lint` opened an interactive migration prompt under Next 15.
- `.next\static` token scan found no `INTERNAL_API_TOKEN`, `X-Internal-API-Token`, or backend internal route references.
- Rendered validation with local mock backend: desktop `1366x900` expanded panel had both family labels, 118th/119th separated count buckets, no horizontal overflow; mobile `390x844` collapsed panel was present with no horizontal overflow and response content in DOM.

## Production Writes

- Performed: no
- Scope: none
- Expected effects: none
- Actual effects: none

## Rollback Paths

- Revert the frontend proxy, panel, tests, and review packet from this branch. No data rollback is required because there are no production writes.

## Blockers

- None.

## Final Reconciliation

- Definition of done satisfied: yes.
- Remaining limitations: no live production frontend render was run; evidence drilldown opens the existing issue-domain path rather than a family roll-call-specific route.
- Recommended next step: add a dedicated family roll-call evidence drilldown path.
