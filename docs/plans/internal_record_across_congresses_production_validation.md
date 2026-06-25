# Milestone Plan: Internal Record Across Congresses Production Validation

## Intent

- Immediate task: Validate the deployed guarded internal `Record Across Congresses` backend route after `INTERNAL_API_TOKEN` was configured in the backend deployment environment.
- Larger-goal alignment: Confirm private transport behavior in production before any frontend runtime code consumes the route.

## Outcome

- User-visible or operational result: A production validation result showing whether the internal route is private, excluded from public schema, and returning the expected guarded response shape.

## Scope And Boundaries

- In scope: Read-only production probes against `https://political-fingerprint.onrender.com`, active plan updates, and a short review packet if validation passes.
- Out of scope: Frontend work, schema changes, migrations, production writes, token disclosure, and repository code changes unless validation reveals a repository defect.
- Files/systems likely touched: `docs/plans/internal_record_across_congresses_production_validation.md`; if validation passes, one review packet under `docs/review_packets/`.

## Decision Envelope

- Codex may decide and execute: Bounded read-only production HTTP validation, response-shape inspection without logging secrets, documentation, commit, push, and a small documentation PR if validation passes.
- Explicit approval required for: Any production write, deployment configuration change, frontend implementation, schema change, or token-handling change.

## Definition Of Done

- [x] Production `/health` returns ok.
- [x] Production `/coverage/metadata` is database-backed.
- [x] Public OpenAPI excludes the internal route and forbidden public route substrings.
- [x] Unauthenticated and wrong-token requests return `401`.
- [x] Authorized Valerie Foushee request returns `200` and expected response shape.
- [x] Authorized spot checks pass for Aaron Bean, Abraham J. Hamadeh, and James Gallagher.
- [x] Tests/build/validation recorded.
- [x] Review packet or final documentation updated.
- [x] Final reconciliation completed.

## Baseline

- Branch/base commit: `codex/internal-route-production-validation` at `102bc1b7a09d4e74edbff7f1231f1bd5c4bf7bc8`.
- Production/deployment state, if relevant: Backend target is `https://political-fingerprint.onrender.com`; `INTERNAL_API_TOKEN` has been configured manually in backend deployment.
- Tracked working tree: No tracked changes at resume.
- Known unrelated untracked artifacts: `docs/review_packets/chamber_filtering_data_integrity_audit.md`; `review_bundle_frontend_data_grounding/`.

## Implementation Sequence

1. Confirm token availability without printing or storing the token.
2. Run bounded production validation checks.
3. Stop and report if any stop condition is hit.
4. If validation passes, create review packet, update this plan, stage only documentation, commit, push, and open a small documentation PR.

## Progress Checklist

- [x] Discovery
- [x] Implementation
- [x] Validation
- [x] Documentation
- [x] Commit/PR readiness

## Discoveries

- `INTERNAL_API_TOKEN` was available in ignored `backend/.env`; only this variable was loaded into the validation process and only presence/non-empty status was reported.
- Production OpenAPI exposed zero paths containing `internal`, `record-across`, `record`, `congress`, `comparable`, or `family`.
- The deployed response kind is `internal_house_record_across_congresses_family_evidence`, matching the repository route contract.

## Decisions And Rationale

- Treat this as read-only production validation; no frontend or data-writing activity is needed.
- Record only statuses and response-shape findings in documentation; do not include token, headers, or response bodies.

## Deviations Or Corrections

- Initial validation attempt failed in a local response-key summarizer after reaching the backend; it did not print the token or response body. The validation command was rerun with a simpler local summarizer and produced the recorded status-only result.

## Validation Results

- Production validation date: 2026-06-25.
- Backend URL: `https://political-fingerprint.onrender.com`.
- Token loaded from ignored `backend/.env`; present and non-empty; value not printed, logged, committed, or documented.
- `/health`: `ok`.
- `/coverage/metadata`: `data_source = database`.
- Public OpenAPI forbidden route scan: zero matching paths for `internal`, `record-across`, `record`, `congress`, `comparable`, or `family`.
- Unauthenticated internal route request: `401`.
- Wrong-token internal route request: `401`.
- Authorized Valerie Foushee request: `200`.
- Authorized spot checks: Aaron Bean `200`; Abraham J. Hamadeh `200`; James Gallagher `200`.
- Valerie response shape: product framing `Record Across Congresses`; response kind `internal_house_record_across_congresses_family_evidence`; explicit `non_authorization_metadata`; separated Yes/No/not-voting/present/missing counts.
- Disallowed continuity/change/movement/trend/consistency/changed-position matches: none.

## Production Writes

- Performed: no
- Scope: none
- Expected effects: none
- Actual effects: none

## Rollback Paths

- Documentation-only changes can be reverted by reverting the documentation commit. No production state will be modified.

## Blockers

- None.

## Final Reconciliation

- Definition of done satisfied: yes
- Remaining limitations: No repository code, frontend runtime, schema, migration, production-write, or rendered UI validation was in scope.
- Recommended next step: Merge the small documentation PR after review.
