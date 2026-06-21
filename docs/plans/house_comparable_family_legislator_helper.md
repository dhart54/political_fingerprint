# Milestone Plan: House Comparable Family Legislator Helper

## Intent

- Immediate task: Build a bounded read-only backend helper that joins House legislators to eligible comparable policy-question families.
- Larger-goal alignment: Support safe `Record Across Congresses` product work by proving the versioned comparable-family artifact can join to existing legislator vote records without authorizing continuity/change claims.

## Outcome

- User-visible or operational result: A reusable internal backend helper that reports factual family-level evidence availability for a given House legislator across the 118th and 119th Congresses.

## Scope And Boundaries

- In scope: House only; 118th and 119th Congresses only; existing interpreted evidence; eligible artifact families from `house-comparable-policy-question-families-v1`; existing vote/member records; internal helper and targeted tests; optional review packet.
- Out of scope: Production writes, database tables, migrations, schema changes, ingestion, new interpretations/classifications, public API endpoint, frontend runtime changes, Senate, new Congress, continuity/change labels, broad-domain-only matching.
- Files/systems likely touched: `backend/app/analysis/`, `backend/tests/`, `docs/plans/`, `docs/review_packets/`.

## Decision Envelope

- Codex may decide and execute: internal helper API shape, targeted fixtures/mocks, read-only SQL query shape, validation profile examples, review packet, tests, commit/PR preparation.
- Explicit approval required for: production writes, schema changes, public routes, frontend changes, broad runtime service abstractions, or continuity/change language.

## Definition Of Done

- [x] Helper loads through the PR #46 artifact accessor and reuses artifact validation.
- [x] Helper accepts a House legislator identifier and returns structured family-level counts by Congress.
- [x] Counts preserve cast Yes/No, not-voting, present, missing/no-record, artifact membership, and eligible-family distinctions.
- [x] Related-but-not-comparable and ungrouped rows are excluded from eligible display counts.
- [x] Output includes explicit non-authorization metadata and no continuity/change/movement fields.
- [x] Required validation profiles are reported.
- [x] Targeted tests pass.
- [x] Full backend suite is run if shared runtime/query-layer behavior changes.
- [x] Review packet documents behavior, boundaries, and safe future consumption.
- [x] Final reconciliation and PR/deployment readiness recorded.

## Baseline

- Branch/base commit: `codex/house-family-legislator-helper` from `main` at `6f3f367f074af22b149892ed71c39bdfb9dc541d`.
- Production/deployment state, if relevant: No production writes authorized. Public deployment validation only after PR/merge.
- Tracked working tree: Clean at branch creation.
- Known unrelated untracked artifacts: `docs/review_packets/chamber_filtering_data_integrity_audit.md`; `review_bundle_frontend_data_grounding/`.

## Implementation Sequence

1. Discover PR #46 artifact accessor, current database/query conventions, and test patterns.
2. Implement focused internal helper under `backend/app/analysis/`.
3. Add targeted tests for output shape, counting semantics, eligibility boundaries, no public endpoint, and no movement fields.
4. Run targeted tests and any required broader backend tests.
5. Generate validation profile examples and write review packet.
6. Commit only intended files, open PR, wait for green checks, merge if clean, and verify deployment health.

## Progress Checklist

- [x] Discovery
- [x] Implementation
- [x] Validation
- [x] Documentation
- [x] Commit/PR readiness

## Discoveries

- Local `main`, `origin/main`, and `HEAD` all start at requested commit `6f3f367f074af22b149892ed71c39bdfb9dc541d`.
- PR #46 accessor exists at `backend/app/analysis/house_comparable_families.py`.
- Versioned artifact exists at `docs/derived/house_comparable_policy_question_families_v1.json`.
- Existing public legislator identifiers are `leg_` slugs generated from `name_display`; the helper accepts those and can also resolve bioguide/database identifiers internally.
- Production validation profiles confirmed expected display eligibility: Foushee/Bean/Adam Smith 11 display-eligible families; Hamadeh/Allred/James Gallagher 0; Aumua Amata Coleman Radewagen 1 conditional family.

## Decisions And Rationale

- Place helper in `backend/app/analysis/house_comparable_family_legislator.py` to extend the internal analysis package without creating an API/service layer.
- Reuse `load_house_comparable_family_artifact()` rather than duplicating artifact validation.
- Treat `record_across_congresses_display_eligible` as factual display availability only, with explicit non-authorization metadata on both result and family rows.
- Skip full backend suite because the milestone added a focused internal analysis helper and did not alter shared runtime/query-layer behavior or public API behavior.

## Deviations Or Corrections

- None yet.

## Validation Results

- `python -m pytest tests\test_house_comparable_families_accessor.py tests\test_house_comparable_family_legislator.py` passed (`25 passed`).
- Production read-only helper checks completed for Valerie Foushee, Aaron Bean, Adam Smith, Abraham J. Hamadeh, Allred, Aumua Amata Coleman Radewagen, and James Gallagher.
- Direct SQL reconciliation for Valerie Foushee / `eco_government_funding_packages` matched helper counts: 118th `yea=1`, `nay=4`; 119th `nay=5`.

## Production Writes

- Performed: no
- Scope: Not authorized.
- Expected effects: None.
- Actual effects: None.

## Rollback Paths

- Revert this branch's added helper, tests, and documentation. No production rollback required.

## Blockers

- None yet.

## Final Reconciliation

- Definition of done satisfied: Yes. The milestone adds a bounded internal House-only helper, targeted tests, read-only production validation, direct SQL reconciliation, and a review packet without schema, API, frontend, or production-write changes.
- Remaining limitations: The helper is not exposed through a public or private API route; it reports factual availability/counts only and intentionally does not generate continuity/change/movement labels or copy. Counts are limited to existing interpreted 118th/119th House evidence and the `house-comparable-policy-question-families-v1` eligible-family artifact.
- Recommended next step: Open PR for review/merge. A future milestone can add an internal API-facing adapter or private endpoint after response naming and copy guardrails are reviewed for `Record Across Congresses`.
