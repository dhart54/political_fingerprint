# Milestone Plan: Amendment Evidence Canonical Path

## Intent

- Immediate task: consolidate and harden the existing amendment-source evidence pipeline before the separately scoped 118th House amendment expansion.
- Larger-goal alignment: make multi-Congress legislative evidence repeatable through one understandable, tested, source-grounded pathway.

## Outcome

- User-visible or operational result: documented and tested architecture for amendment enrichment, classification, interpretation packaging, bounded writes, rollback, recomputation, and validation, with only high-confidence refactors.

## Scope And Boundaries

- In scope: existing House and Senate amendment enrichment, source packets, supervised enrichment, manual interpretation packages, classification and interpretation writes, affected-output recomputation, rollback, idempotency validation, CI dependency reproducibility, and related runbooks.
- Out of scope: new production classifications or interpretations, new evidence collection, new Congress coverage, schema or methodology changes, broad frontend refactors, and speculative abstractions.
- Files/systems likely touched: `backend/app/etl`, `backend/app/classification`, `backend/app/summaries`, `backend/tests`, `scripts`, `docs`, CI configuration, and dependency lock/config files.

## Decision Envelope

- Codex may decide and execute: repository inventory, call-path tracing, high-confidence consolidation, historical marking of completed one-time code, test/CI improvements, documentation, review packet, PR, merge, and deployment verification when gates pass.
- Explicit approval required for: production data writes, schema or methodology changes, destructive operations, ambiguous civic semantics, unbounded imports, service/secret/configuration changes, or relocation/removal whose active callers cannot be proven.

## Definition Of Done

- [x] Evidence-based inventory covers active modules, scripts, tests, and runbooks in scope and classifies each as canonical runtime, source adapter, bounded job/orchestrator, historical backfill, test/fixture, or obsolete/superseded.
- [x] Call-path and data-flow map traces source retrieval through public API output.
- [x] Duplicated amendment identity, source matching, eligibility, packaging, write, rollback, and validation logic is identified and only high-confidence duplication required for the next House milestone is refactored.
- [x] Canonical amendment evidence path is documented from fetch/cache through idempotency rerun.
- [x] Production-write entry points require explicit scope, preflight, rollback location, and exact target-row confirmation.
- [x] Tests cover canonical contracts and existing 118th/119th public outputs remain unchanged.
- [x] CI/build/dependency reproducibility is strengthened without unnecessary package-management migration.
- [ ] Review packet, PR, merge, and deployment verification completed when all gates pass.

## Baseline

- Branch/base commit: `codex/amendment-evidence-canonical-path` from `main` at `3685bc37e1e96e22a8864c12cfc2e70153e070df`.
- Production/deployment state, if relevant: no production writes authorized for new data; deployment verification only after reviewed code is merged.
- Tracked working tree: clean at branch creation.
- Known unrelated untracked artifacts: `docs/review_packets/chamber_filtering_data_integrity_audit.md`, `review_bundle_frontend_data_grounding/`.

## Implementation Sequence

1. Inventory repository modules, scripts, tests, runbooks, and callers before editing.
2. Run baseline relevant backend tests and capture current behavior.
3. Document call paths, data flows, duplicate logic, and canonical pathway decisions.
4. Refactor high-confidence duplication and guard write entry points.
5. Add contract tests and CI/dependency reproducibility improvements.
6. Re-run tests/builds, validate unchanged public outputs, and complete review packet.
7. Prepare PR, merge only after green gates, and verify deployment state.

## Progress Checklist

- [x] Discovery
- [x] Implementation
- [x] Validation
- [x] Documentation
- [ ] Commit/PR readiness

## Discoveries

- Baseline includes unrelated untracked review artifacts that must be preserved and excluded from this milestone diff.
- No in-scope module was proven obsolete enough to remove. Historical backfill modules still have active tests, review packets, rollback provenance, or runbook references.
- Full backend tests exposed stale expectations for pre-session-aware sample roll-call ids and unsupported-reference examples; the product code already preserves session-aware ids.
- Phase 14 Senate fact import expected `sconres` support in its manifest; the Senate XML adapter already parsed `sconres`, so the importer allowlist was the narrow code gap.

## Decisions And Rationale

- Treat this as an architecture-hardening milestone with no new evidence production writes.
- Add `app.etl.amendment_evidence` as a shared contract module instead of reorganizing historical backfills.
- Keep milestone-specific rollback SQL generation in place because each package restores different prior rows.
- Pin existing backend dependency versions in `requirements.txt` rather than introducing a new package manager.

## Deviations Or Corrections

- Full-suite cleanup included narrow test expectation updates for session-aware roll ids and a `sconres` allowlist fix in `senate_fact_import`.

## Validation Results

- Baseline selected backend suite: `91 passed in 68.57s` after elevated rerun; sandboxed run reached 100% but failed pytest basetemp cleanup.
- Post-change selected backend suite: `98 passed in 68.67s` after elevated rerun; sandboxed run reached 100% but failed pytest basetemp cleanup.
- Previously failing full-suite subset after fixes: `32 passed in 0.36s`.
- Final full backend fixture suite: `293 passed in 266.37s`.
- Frontend build/rendered validation: not applicable; no frontend/runtime UI changes.

## Production Writes

- Performed: no
- Scope: none authorized for new data.
- Expected effects: no production data mutation.
- Actual effects: no production data mutation performed.

## Rollback Paths

- Code rollback: feature branch can be reverted or PR can be declined before merge.
- Data rollback: no production data writes planned; write-path documentation must still require rollback artifacts for future bounded writes.

## Blockers

- None currently.

## Final Reconciliation

- Definition of done satisfied: implementation/documentation/test portions complete; PR/merge/deployment verification remain as repository workflow steps.
- Remaining limitations: no production-backed write or deployment verification was performed because this milestone made no production data writes and no frontend changes.
- Recommended next step: enter the 118th House amendment milestone through `manual_interpretations`, `amendment_companion_enrichment`, `source_packets`, `supervised_enrichment`, and `app.etl.amendment_evidence`; add a permanent module only for a new authoritative source format or genuinely new bounded write orchestration.
