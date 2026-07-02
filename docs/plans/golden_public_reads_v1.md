# Milestone Plan: Golden Public Reads V1

## Intent

- Immediate task: improve the top-level issue overview copy for production-ready public reads after the PR #65-#67 safety and fallback foundation.
- Larger-goal alignment: make issue reads clearer and less repetitive without weakening the raw-evidence boundary or changing vote interpretation semantics.

## Outcome

- User-visible result: top-level issue copy reads more like a concise public explanation while preserving counts, caveats, and receipt affordances.

## Scope And Boundaries

- In scope: issue overview sentence composition, approved overview tests, a Justice mixed-sample guard, and milestone documentation.
- Out of scope: new curated mappings, backend/schema changes, issue-read layout changes, vote classification/readiness semantics, production writes, and raw vote-description parsing.
- Files/systems likely touched: `frontend/lib/issueOverview.mjs`, `frontend/lib/issueOverview.test.mjs`, `docs/plans/`, `docs/review_packets/`.

## Decision Envelope

- Codex may decide and execute: safer sentence templates using existing public themes, test fixture updates, and documentation.
- Explicit approval required for: any semantic change to support/opposition, readiness, counting, evidence eligibility, or production data.

## Definition Of Done

- [ ] Current National Security, Economy, and Justice overview shapes audited before implementation
- [x] Top-level copy uses safe public themes and avoids raw evidence fields
- [x] Dominant and genuine mixed samples remain distinct
- [x] Tests/build/validation recorded
- [x] Review packet or final documentation updated
- [x] Final reconciliation completed

## Baseline

- Branch/base commit: `codex/golden-public-reads-v1` from `main` after merged PR #67 (`d2b533c50f7edf834e33f7a79ea077f0cd9e55f8`).
- Production/deployment state: PR #67 smoke passed before this milestone; no production write is authorized here.
- Tracked working tree: clean at branch start.
- Known unrelated untracked artifacts: `docs/review_packets/chamber_filtering_data_integrity_audit.md`, `review_bundle_frontend_data_grounding/`.

## Implementation Sequence

1. Read interpretation principles and recent public-copy/theme milestone packets.
2. Produce checkpoint audit for current National Security, Economy, and Justice copy.
3. Refine issue overview composition while preserving safety and semantics.
4. Update focused tests and documentation.
5. Run validation and open a focused draft PR.

## Progress Checklist

- [x] Discovery
- [x] Checkpoint audit
- [x] Implementation
- [x] Validation
- [x] Documentation
- [x] Commit/PR readiness

## Discoveries

- National Security copy was safe but repeated long theme lists across Finding, What was reviewed, and How a voter might read.
- Economy copy had the same repetition pattern around fiscal and small-business measures.
- Existing Justice fixtures include both dominant and genuinely split interpreted samples; the split sample is the right guard against accidental mostly framing.

## Decisions And Rationale

- Keep all support/opposition counts, readiness gates, limited-context handling, and receipt/detail behavior unchanged.
- Use existing safe public theme lists only; do not parse raw description, summary, or audit fields.
- Prefer compact voter-read language that refers back to "those measures" after the reviewed measures are named.
- Use "mixed rather than mostly support or mostly opposition" for genuinely split interpreted samples.

## Deviations Or Corrections

- None so far.

## Validation Results

- `node --test lib\issueOverview.test.mjs` passed: 18 tests.
- `node --test lib\*.test.mjs` passed: 70 tests.
- `npm run lint` passed with existing React hook dependency warnings.
- `npm run build` passed with the same React hook dependency warnings.
- `rg -n "INTERNAL_API_TOKEN|X-Internal-API-Token|/internal/record-across-congresses" .next\static` returned no matches.
- Local built app response check passed: `http://localhost:3000` returned HTTP 200.
- Rendered browser automation limitation: Playwright browser binary is not installed in this environment, so no screenshot-based rendered pass was completed.

## Production Writes

- Performed: no
- Scope: none
- Expected effects: none
- Actual effects: none

## Rollback Paths

- Revert the focused branch commit before merge if copy, safety, or validation issues appear.
- Since no production writes are authorized, deployment rollback is not part of this milestone.

## Blockers

- None.

## Final Reconciliation

- Definition of done satisfied: yes.
- Remaining limitations: no screenshot-based rendered validation in this environment; no production validation because this branch has not merged or deployed.
- Recommended next step: review the focused draft PR.
