# Milestone Plan: Family Roll-Call Evidence Drilldown

## Intent

- Immediate task: add a House-only drilldown from each eligible Record Across Congresses family card to the exact roll-call evidence used for that family.
- Larger-goal alignment: improve trustworthy cross-Congress evidence review by exposing the records behind comparable family summaries without implying continuity, movement, motive, or recommendation.

## Outcome

- User-visible or operational result: users can open a family-specific evidence view and inspect separated 118th and 119th roll calls, counts, caveats, summaries, and source links where available.

## Scope And Boundaries

- In scope: frontend route/component or inline detail path, existing House Record Across Congresses data, existing proxy/token boundary, targeted frontend tests, rendered/profile validation, review packet.
- Out of scope: production writes, schema changes, migrations, ingestion, new classifications, Senate work, continuity/change analysis, broad comparison scores, public token exposure, browser calls to backend internal routes.
- Files/systems likely touched: `frontend/app`, `frontend/components`, `frontend/lib`, frontend tests, `docs/plans`, `docs/review_packets`.

## Decision Envelope

- Codex may decide and execute: smallest safe drilldown pattern consistent with current UI, frontend data shaping, targeted tests, documentation, local validation.
- Explicit approval required for: production writes, schema or methodology changes, secrets/config changes, semantic changes to eligibility/counting/alignment/readiness, merge/deployment if checks reveal ambiguity.

## Definition Of Done

- [x] Existing data paths inspected and safe roll-call detail source confirmed or smallest safe adapter documented.
- [x] Family-specific drilldown implemented without exposing token/header/internal route strings to client code.
- [x] Required profiles validated, including eligible, caveated, unavailable, and no-eligible-family states.
- [x] Disallowed copy and continuity/change framing absent from rendered UI.
- [x] Targeted frontend tests added and passing.
- [x] `npm run build` passing or a true stop condition reported.
- [x] Review packet updated.
- [x] Tests/build/validation recorded.
- [x] Final reconciliation completed.

## Baseline

- Branch/base commit: `codex/family-roll-call-drilldown` from `main` at `abd67c5e9d2f758025af2b296b03ac8fbf8ce051`.
- Production/deployment state, if relevant: no production writes authorized.
- Tracked working tree: clean at start.
- Known unrelated untracked artifacts: `docs/review_packets/chamber_filtering_data_integrity_audit.md`, `review_bundle_frontend_data_grounding/`.

## Implementation Sequence

1. Discover current Record Across Congresses frontend data model, proxy route, family card, evidence paths, tests, and copy guardrails.
2. Confirm safe source for exact roll-call details; stop if details cannot be retrieved without violating the token/internal-route boundary.
3. Implement smallest family-specific drilldown pattern and data shaping.
4. Add targeted tests for selection, separated congress sections, count buckets, safe copy, source links, ineligible states, and security strings.
5. Run targeted tests, build, static bundle checks, and rendered/profile validation.
6. Create or update the review packet, reconcile plan, prepare commit/PR if definition of done is met.

## Progress Checklist

- [x] Discovery
- [x] Implementation
- [x] Validation
- [x] Documentation
- [x] Commit/PR readiness

## Discoveries

- Start state confirmed at requested commit on `main`; unrelated untracked artifacts are present and preserved.
- The existing sanitized Record Across Congresses response exposes family-level `roll_call_ids_considered_by_congress` and separated counts, but not roll-call row details.
- The existing public issue evidence endpoint returns the needed public-safe roll-call row fields; no new backend/internal adapter is needed.

## Decisions And Rationale

- No production writes will be performed for this milestone.
- Chosen drilldown pattern: inline expanded drawer under the selected family card, because it is the smallest change consistent with the current collapsed panel.
- Data path: app-local Record Across Congresses proxy for family IDs/counts, then public issue evidence endpoint filtered in-browser to the selected family roll-call IDs.

## Deviations Or Corrections

- The existing broader issue-domain evidence jump was replaced with a family-specific inline drilldown.

## Validation Results

- `node --test frontend\lib\recordAcrossCongresses.test.mjs` passed: 15 tests.
- `python -m pytest backend\tests\test_house_record_across_congresses.py backend\tests\test_house_record_across_congresses_transport.py backend\tests\test_internal_record_across_route.py` passed: 25 tests.
- `npm run build` passed.
- `npm run lint` remains blocked by the known interactive Next 15 `next lint` migration prompt.
- Client bundle check passed: no `INTERNAL_API_TOKEN`, `X-Internal-API-Token`, or `/internal/record-across-congresses` strings in `.next\static`.
- Rendered validation passed on desktop and `390x844` mobile using a local mock backend with the same server-side token boundary. Full-page screenshot capture produced distorted local artifacts, so no screenshot artifact was retained.

## Production Writes

- Performed: no
- Scope: none authorized.
- Expected effects: none.
- Actual effects: none.

## Rollback Paths

- Revert the feature branch commit(s); no schema, migration, production data, or configuration rollback expected.

## Blockers

- None yet.

## Final Reconciliation

- Definition of done satisfied: yes.
- Remaining limitations: rendered validation used a local mock backend rather than production data; the drawer over-fetches public issue evidence for the family domain and filters locally.
- Recommended next step: open PR and perform hosted preview validation against production-shaped data, then consider a public-safe family roll-call detail adapter only if over-fetching becomes a problem.
- PR: draft PR #54, `https://github.com/dhart54/political_fingerprint/pull/54`.
