# Milestone Plan: Record Across Congresses Frontend Contract

## Intent

- Immediate task: Design the `Record Across Congresses` frontend contract and copy guardrails before runtime UI implementation.
- Larger-goal alignment: Prove how the PR #48 internal backend response should be presented to users without implying unsupported cross-Congress conclusions.

## Outcome

- User-visible or operational result: A product/UX review packet for a future House-only frontend panel using the internal adapter response contract.

## Scope And Boundaries

- In scope: UX/content specification, House only, 118th/119th Congresses only, existing PR #48 adapter response, existing validated profiles, local docs/review packets, optional lightweight copy guardrail validation.
- Out of scope: Runtime frontend implementation, backend/private/public routes, public API endpoints, production writes, schema/migration changes, ingestion, new classifications/interpretations, Senate, new Congress, public launch, unsupported cross-Congress claims.
- Files/systems likely touched: `docs/plans/`, `docs/review_packets/`, optionally `docs/validation/` or `scripts/` for copy guardrails.

## Decision Envelope

- Codex may decide and execute: review packet structure, placement recommendation, safe copy set, disallowed copy list, field mapping, profile examples, small copy-validation artifact.
- Explicit approval required for: any runtime frontend code, backend route, schema change, production write, adapter semantic change, or unsupported copy.

## Definition Of Done

- [x] Review packet defines purpose, placement, hierarchy, copy, disallowed copy, field mapping, profile examples, component contract, and readiness decision.
- [x] Proposed copy uses only `Record Across Congresses` framing and avoids unsupported implications.
- [x] Profile examples preserve not-voting and missing/no-record separately from Yes/No.
- [x] Related and ungrouped rows remain excluded by design.
- [x] No runtime frontend, backend route, schema, or production write changes.
- [x] Copy guardrail validation completed and recorded.
- [x] PR/deployment readiness recorded.
- [x] Final reconciliation completed.

## Baseline

- Branch/base commit: `codex/record-across-congresses-frontend-contract` from `main` at `f07fe8982d33edbd86de9002a97d8445b4272d4f`.
- Production/deployment state, if relevant: No production writes authorized. Deployment verification only after PR/merge.
- Tracked working tree: Clean at branch creation.
- Known unrelated untracked artifacts: `docs/review_packets/chamber_filtering_data_integrity_audit.md`; `review_bundle_frontend_data_grounding/`.

## Implementation Sequence

1. Discover current profile/front-end structure, PR #48 adapter contract, and existing review packet conventions.
2. Generate or reuse production-shaped adapter profile summaries for required profiles.
3. Draft the UX/content review packet with safe copy, disallowed copy, field mapping, examples, and component proposal.
4. Add a lightweight copy guardrail validation artifact if useful.
5. Validate no runtime files/routes/schema changed and run targeted checks.
6. Commit intended files, open PR, wait for green checks, merge if clean, and verify deployment health.

## Progress Checklist

- [x] Discovery
- [x] Documentation
- [x] Validation
- [x] Commit/PR readiness

## Discoveries

- Baseline confirmed at requested commit `f07fe8982d33edbd86de9002a97d8445b4272d4f`.
- Unrelated untracked artifacts are preserved and excluded from milestone scope.
- PR #48 adapter contract exposes factual availability, summary counts, family rows, caveats, roll-call IDs, and separated counts.
- Current profile page already prioritizes `ProfileQuickRead` and strongest issue evidence; the spec recommends a collapsed advanced section below that path.
- Production-shaped adapter summaries confirmed Foushee/Bean/Adam Smith have 11 display-eligible families; Hamadeh/Allred/James Gallagher have 0; Aumua Amata Coleman Radewagen has 1 conditional family.

## Decisions And Rationale

- No runtime frontend implementation will be added in this milestone.
- No route work is needed; the PR #48 adapter remains the source contract.
- Add a small JSON copy guardrail artifact rather than a generalized content-policy engine.
- Readiness decision is `READY FOR INTERNAL ENDPOINT`; the smallest next milestone is guarded private transport before runtime UI.

## Deviations Or Corrections

- None yet.

## Validation Results

- Production-shaped read-only adapter summaries generated for Valerie Foushee, Aaron Bean, Adam Smith, Abraham J. Hamadeh, Allred, Aumua Amata Coleman Radewagen, and James Gallagher.
- Copy guardrail validation passed: approved copy uses `Record Across Congresses` and contains no disallowed terms.
- Worktree validation confirmed no runtime frontend files, backend route files, schema/migration files, or adapter code were changed.
- No targeted test suite was needed beyond the copy guardrail command because this milestone adds docs/JSON only.

## Production Writes

- Performed: no
- Scope: Not authorized.
- Expected effects: None.
- Actual effects: None.

## Rollback Paths

- Revert this branch's documentation and any copy-validation artifact. No data rollback required.

## Blockers

- None yet.

## Final Reconciliation

- Definition of done satisfied: Yes. The milestone produced a frontend contract review packet, copy guardrail artifact, production-shaped profile examples, and validation notes without runtime code, routes, schema changes, or production writes.
- Remaining limitations: No user-facing UI exists yet, and no endpoint transports the adapter response. The spec must be rechecked during any future rendered frontend prototype.
- Recommended next step: Define a guarded private/internal endpoint contract for trusted backend transport, then prototype the collapsed frontend panel in a separate milestone.
