# Milestone Plan: House Record Across Congresses Adapter

## Intent

- Immediate task: Add a private/internal API-facing response builder for the House comparable-family legislator helper.
- Larger-goal alignment: Advance safe `Record Across Congresses` product work by defining a reviewed backend response contract for family-level cross-Congress evidence availability without authorizing continuity/change claims.

## Outcome

- User-visible or operational result: A stable internal response-shaped object for trusted backend consumption that wraps the existing House comparable-family legislator helper.

## Scope And Boundaries

- In scope: House only; 118th and 119th Congresses only; existing interpreted evidence; artifact v1; PR #46 artifact accessor; PR #47 legislator helper; internal adapter/response builder; targeted tests; review packet.
- Out of scope: Production writes, database tables, migrations, schema changes, new ingestion, new interpretations/classifications, public API endpoint, frontend runtime changes, OpenAPI public exposure, Senate, new Congress, product copy generation, continuity/change labels.
- Files/systems likely touched: `backend/app/analysis/`, `backend/tests/`, `docs/plans/`, `docs/review_packets/`.

## Decision Envelope

- Codex may decide and execute: adapter module location, response field names within the user's guardrails, targeted fixture strategy, production read-only validation profiles, documentation.
- Explicit approval required for: any route, public OpenAPI exposure, schema/frontend/runtime service changes, production writes, or continuity/change/trend semantics.

## Definition Of Done

- [x] Adapter imports and wraps `backend/app/analysis/house_comparable_family_legislator.py` without duplicating counting or artifact validation logic.
- [x] Response includes product framing, artifact version, explicit non-authorization metadata, factual availability/counts, summary counts, family rows, caveats, roll-call IDs, and separated per-Congress counts.
- [x] Field names avoid disallowed change/trend/movement/continuity/consistency implications.
- [x] No public route or OpenAPI exposure is added.
- [x] Required validation profiles are reported.
- [x] Targeted tests pass.
- [x] Full backend suite is run if shared runtime code or API routing changes.
- [x] Review packet documents contract, guardrails, validation, and future-consumption guidance.
- [x] Final reconciliation completed.

## Baseline

- Branch/base commit: `codex/house-record-across-congresses-adapter` from `main` at `9d9a327b54ba43b1e197b42f8065914ebf5694d8`.
- Production/deployment state, if relevant: No production writes authorized. Public deployment validation only after PR/merge.
- Tracked working tree: Clean at branch creation.
- Known unrelated untracked artifacts: `docs/review_packets/chamber_filtering_data_integrity_audit.md`; `review_bundle_frontend_data_grounding/`.

## Implementation Sequence

1. Discover existing helper output shape, API route patterns, and tests.
2. Implement a focused internal response builder under `backend/app/analysis/`.
3. Add targeted tests for response contract, naming guardrails, summary counts, family rows, caveats, separated counts, and no public exposure.
4. Run targeted tests and required broader validation.
5. Run read-only production-shaped validation profiles and document results.
6. Commit intended files, open PR, wait for green checks, merge if clean, and verify deployment health.

## Progress Checklist

- [x] Discovery
- [x] Implementation
- [x] Validation
- [x] Documentation
- [x] Commit/PR readiness

## Discoveries

- Baseline confirmed at requested commit `9d9a327b54ba43b1e197b42f8065914ebf5694d8`.
- Unrelated untracked artifacts are preserved and excluded from milestone scope.
- Existing helper path is `backend/app/analysis/house_comparable_family_legislator.py`.
- No trusted private route convention was found, so the milestone avoided route code entirely.
- Production-shaped validation profiles produced expected availability patterns: Foushee/Bean/Adam Smith 11 display-eligible families; Hamadeh/Allred/James Gallagher 0; Aumua Amata Coleman Radewagen 1 conditional family.

## Decisions And Rationale

- Prefer a no-route internal response builder to avoid ambiguity about public exposure.
- Place the adapter in `backend/app/analysis/house_record_across_congresses.py` to keep it near the helper and outside API routing.
- Transform helper metadata into neutral internal-safety fields so the API-facing response shape avoids disallowed field names and serialized terms.
- Skip the full backend suite because no shared runtime code or API routing changed; targeted tests include explicit route/OpenAPI absence checks.

## Deviations Or Corrections

- None yet.

## Validation Results

- `python -m pytest tests\test_house_comparable_families_accessor.py tests\test_house_comparable_family_legislator.py tests\test_house_record_across_congresses.py` passed (`35 passed`).
- Production-shaped read-only adapter checks completed for Valerie Foushee, Aaron Bean, Adam Smith, Abraham J. Hamadeh, Allred, Aumua Amata Coleman Radewagen, and James Gallagher.
- Validation confirmed caveats, separated not-voting/missing counts, summary counts, and no disallowed serialized terms for all required profiles.

## Production Writes

- Performed: no
- Scope: Not authorized.
- Expected effects: None.
- Actual effects: None.

## Rollback Paths

- Revert the adapter, tests, plan, and review packet from this branch. No data rollback required.

## Blockers

- None yet.

## Final Reconciliation

- Definition of done satisfied: Yes. The milestone adds a focused internal response builder, targeted contract tests, production-shaped read-only validation, and a review packet without routes, OpenAPI exposure, schema changes, frontend changes, or production writes.
- Remaining limitations: The adapter is internal-only and not exposed through any API route. It reports factual availability/counts only and intentionally avoids unsupported inference labels or copy.
- Recommended next step: Define a private-route convention and guarded internal endpoint only if a future milestone needs trusted backend transport for this response contract.
