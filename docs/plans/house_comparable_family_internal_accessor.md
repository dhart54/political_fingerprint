# Milestone Plan: House Comparable Family Internal Accessor

## Intent

- Immediate task: Build a backend/internal accessor for the versioned House comparable policy-question family artifact.
- Larger-goal alignment: Make the reviewed PR #45 derived artifact consumable by future backend/product work while preserving `Record Across Congresses` framing and non-authorization boundaries.

## Outcome

- User-visible or operational result: A small internal backend module that loads, validates, and queries `docs/derived/house_comparable_policy_question_families_v1.json`, with targeted tests and review documentation.

## Scope And Boundaries

- In scope: House artifact v1 only; existing interpreted House evidence; 118th/119th Congresses; backend/internal loading, validation, query helpers, targeted tests, and docs.
- Out of scope: Production writes, database tables, migrations, schema changes, ingestion, classifications, interpretations, frontend runtime changes, public API endpoints, Senate work, new Congresses, automatic family assignment, or product copy generation.
- Files/systems likely touched: `backend/app/analysis/`, `backend/tests/`, `docs/plans/`, and `docs/review_packets/`.

## Decision Envelope

- Codex may decide and execute: internal module structure, typed helper API, validation behavior, targeted tests, documentation, commit/PR/merge when gates pass.
- Explicit approval required for: production writes, schema changes, public API exposure, frontend output, eligibility semantic changes, or any continuity/change/movement label generation.

## Definition Of Done

- [x] Internal accessor locates and loads the stable artifact path.
- [x] Accessor validates artifact version, metadata, totals, non-authorization flags, family records, statuses, eligibility, ungrouped exclusion, and cross-Congress roll-call separation.
- [x] Accessor exposes all required family lookup/filter helpers and preserves caveats/criteria.
- [x] Accessor never synthesizes continuity/change, behavioral movement, ideological movement, causal, or changed-position outputs.
- [x] Optional legislator join helper is either safely implemented or explicitly deferred.
- [x] Targeted tests cover required behavior and pass.
- [x] Review packet documents exposed behavior, non-exposed behavior, trust boundaries, consumption guidance, and next milestone.
- [x] No production writes, schema changes, frontend changes, public endpoints, or runtime services are introduced.
- [ ] PR/deployment runbook followed.
- [x] Final reconciliation completed.

## Baseline

- Branch/base commit: `codex/house-family-internal-accessor` from `main` at `c97286f07bd2dbf4462695600f15b6d1526aa6c6`.
- Production/deployment state, if relevant: No production access expected; artifact is local and already validated by PR #45.
- Tracked working tree: Clean at branch creation.
- Known unrelated untracked artifacts: `docs/review_packets/chamber_filtering_data_integrity_audit.md`; `review_bundle_frontend_data_grounding/`; permission-denied pytest temp directories visible in broad status.

## Implementation Sequence

1. Inspect artifact shape and existing backend module conventions.
2. Add focused internal accessor module and typed structures.
3. Add targeted tests for load, validation failures, lookup/filter helpers, eligibility boundaries, caveat preservation, roll-call separation, and forbidden labels.
4. Write review packet and update this plan.
5. Run targeted tests and prepare PR/merge if gates pass.

## Progress Checklist

- [x] Discovery
- [x] Implementation
- [x] Validation
- [x] Documentation
- [ ] Commit/PR readiness

## Discoveries

- Baseline commit matches the requested PR #45 merge commit.
- PR #45 artifact is local JSON at `docs/derived/house_comparable_policy_question_families_v1.json`; no production access is needed for this milestone.
- Added internal package `backend/app/analysis/` and accessor `backend/app/analysis/house_comparable_families.py`.
- Accessor validates PR #45 totals, artifact version, metadata, non-authorization flags, family statuses, eligibility, related/ungrouped exclusion, and Congress-separated roll-call IDs.

## Decisions And Rationale

- Use `backend/app/analysis/house_comparable_families.py` because this is internal analysis/access logic, not API or ETL behavior.
- Defer the optional legislator join helper unless it remains small and does not require service/database integration.
- Deferred the optional legislator join helper because it should be a separate bounded backend milestone with read-only database join validation against `votes_cast`, member identity, not-voting handling, and support/opposition counts.

## Deviations Or Corrections

- Initial tests used `tmp_path`, which hit the known local Windows pytest temp permission issue; tests now validate mutated payloads directly and avoid temp filesystem dependence.
- Tests were narrowed to distinguish generated movement labels from required non-authorization guardrail text.

## Validation Results

- Targeted tests passed: `python -m pytest backend\tests\test_house_comparable_families_accessor.py` (`13 passed`).
- No full backend suite required because no shared runtime code changed.
- No frontend validation required because no frontend runtime changed.

## Production Writes

- Performed: no
- Scope: Not authorized.
- Expected effects: None.
- Actual effects: None.

## Rollback Paths

- Revert this branch's internal module, tests, plan, and review packet. No production rollback is required.

## Blockers

- None.

## Final Reconciliation

- Definition of done satisfied: yes, pending PR/check/merge completion.
- Remaining limitations: no legislator join helper yet; no public API or frontend consumption; artifact remains internal and does not authorize continuity/change.
- Recommended next step: build a bounded read-only backend helper that joins legislators to eligible artifact roll-call IDs and reports family-level cast Yes/No and not-voting counts by Congress.
