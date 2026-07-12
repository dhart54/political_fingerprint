# Milestone Plan: ZIP Source-to-Member Readiness Gate V1

## Intent

- Independently evaluate whether verified Census state/district pairs can map safely to exactly one current House member.
- Advance readiness evidence without ingestion, database mutation, route changes, or production auto-selection.

## Outcome

- A pure readiness contract, read-only production evaluator, deterministic tests, and JSON/Markdown review packets with every blocker explicit.

## Scope And Boundaries

- In scope: schema audit, bounded read-only member query, verified local Census parsing, pure classification, territory/at-large reporting, tests, and review artifacts.
- Out of scope: migrations, metadata repair, ZIP ingestion, member mutation, route/flag/frontend changes, address lookup, and production auto-select.
- Likely files: isolated readiness module, evaluation script, focused tests, this plan, and two review packets.

## Decision Envelope

- Codex may classify only from stored fields and explicit source facts; missing currentness, vacancy, or member-type evidence must block readiness.
- Any production write, inferred metadata, route change, or new product semantics requires a later milestone.

## Definition Of Done

- [x] Exact PR #85 source identity is verified before evaluation.
- [x] Production member schema/data are inspected through a guarded read-only session.
- [x] Pure contract covers single, zero, duplicate, former, stale/unknown, identifier, mismatch, at-large, delegate, territory, and vacancy cases.
- [x] JSON/Markdown packets report source/member/status/candidate-ZCTA counts and final production eligibility zero.
- [x] Target table remains empty; public routes and flag remain unchanged.
- [x] Tests, JSON checks, postcheck, static checks, and diff hygiene pass.
- [x] Commit, push, and draft PR are complete (PR #86).

## Baseline

- Branch/base: `codex/zip-source-member-readiness-gate-v1` from `ae9a4fa5def263f9df12ac6c5a67814412e7702f`.
- Production postcheck: `zip_district_mappings` exists with zero rows; compatibility table exists.
- Public routes: `zip_district_map`; no multi-row route switch.
- Known unrelated untracked artifacts preserved: `docs/review_packets/chamber_filtering_data_integrity_audit.md`, `review_bundle_frontend_data_grounding/`.

## Implementation Sequence

1. Audit schema, current lookup semantics, and production-read member coverage.
2. Implement pure readiness statuses and deterministic fixtures/tests.
3. Implement guarded dry-run/read-only evaluator reusing PR #85 source verification.
4. Run verified full-source evaluation and requested validation gates.
5. Reconcile packets/plan, commit scoped files, push, and open draft PR.

## Progress Checklist

- [x] Discovery
- [x] Implementation
- [x] Validation
- [x] Documentation
- [x] Commit/PR readiness

## Discoveries

- Stored `legislators` schema has `bioguide_id`, `chamber`, `state`, `district`, and `in_office`, but no Congress, term dates, vacancy, voting/delegate type, metadata source, retrieval date, or source-currentness fields.
- Current public House lookup selects the first state/district House row by ID and does not require `in_office` or detect duplicates.
- Production read inspected 637 member rows, including 441 rows marked `in_office=true` and `chamber=house`.
- Of 436 accepted source pairs, 435 had exactly one matching row marked current; all 435 remain blocked because stored metadata cannot prove term/currentness, vacancy, or voting-member type. Census source pair `DC-98` is separately delegate-review-required.
- The official source district code for DC is `98`. Any future conversion to the repository's internal `00` convention requires a documented normalization rule; this milestone preserves `98` and performs no conversion.
- The source rejected territory rows before member matching: AS 2, GU 8, MP 4, PR 133, and VI 7. They remain explicitly reported rather than silently discarded.

## Decisions And Rationale

- Presence plus `in_office` alone will not prove reliable current-member readiness; absent evidence will produce schema-insufficient or review-required statuses.
- Final production auto-select eligibility remains zero regardless of source-to-member diagnostic counts.
- Connection-level `default_transaction_read_only` and transaction-level `transaction_read_only` are both established and verified before bounded schema/member reads.

## Deviations Or Corrections

- PR #86 correction: generated safety claims are now derived from read-only database inspection or bounded repository-source checks, with evidence recorded in the packet.
- Corrected the prior `DC-00` description to source-accurate `DC-98` without altering source data or delegate-review behavior.

## Validation Results

- Initial read-only postcheck passed: target row count `0`, migration not rerun by this milestone, seed not loaded.
- Verified source: filename, 6,195,997-byte size, and SHA-256 `57fad59f65af5179ddd18dcfb8f72482dc0cf04fe26e2b9b2b34c51c04405f77` all matched.
- Evaluator: passed in explicit dry-run/read-only mode; source-to-member-ready pairs `0`, ready candidate ZCTAs `0`, production eligibility `0`.
- Focused ZIP/member suite after safety-derivation corrections: `55 passed` in 9.71 seconds.
- New packet, PR #85 packet, and PR #85 source manifest: valid JSON.
- Evaluator table check: `zip_district_mappings` exists with actual row count `0`; empty status is derived from the inspected count.
- Evaluator route check: both public ZIP endpoints use `zip_district_map`; neither reads `zip_district_mappings`.
- Feature flag check: `ZIP_MULTI_ROW_LOOKUP_ENABLED` is absent/not configured and therefore not enabled.
- Final read-only postcheck: row count `0`; migration not rerun; seed not loaded.
- Static checks: no public `zip_district_mappings` read and no enabled `ZIP_MULTI_ROW_LOOKUP_ENABLED` assignment.
- `git diff --check`: passed.

## Production Writes

- Performed: no.
- Scope/expected/actual effects: read-only inspection and local report writes only.

## Rollback Paths

- Revert branch-only code/docs and delete generated local packets; no database rollback is applicable.

## Blockers

- Reliable current-member readiness cannot be established from the existing schema. This is the expected fail-closed outcome and blocks ingestion readiness, not completion of the audit/report milestone.

## Final Reconciliation

- Definition of done satisfied: yes; implementation, validation, commit, push, and draft PR #86 are complete.
- Remaining limitations: member terms, vacancy, member type, metadata source/retrieval evidence, and explicit currentness are not stored.
- Recommended next step: Current House member metadata hardening V1; do not proceed to staging ingestion or a route switch until those gates are represented and source-backed.
