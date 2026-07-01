# Milestone Plan: Public Copy Safety Contract

## Intent

- Immediate task: prevent raw evidence, audit, amendment, and classification text from appearing in top-level public interpretation copy.
- Larger-goal alignment: preserve clear civic interpretation while keeping receipts and audit detail inspectable in the appropriate lower-level surfaces.

## Outcome

- User-visible or operational result: issue summaries, issue cards, record summaries, "What was reviewed," and "What that means" use only public-safe themes, counts, directions, and bounded context.

## Scope And Boundaries

- In scope: frontend public-copy helpers, issue overview copy, profile narrative theme snippets, issue-card copy checks, source-level tests, review documentation, and local validation.
- Out of scope: backend schema/data changes, support/opposition semantics, readiness semantics, alignment semantics, production writes, and removal of raw details from vote rows or drawers.
- Files/systems likely touched: `frontend/lib/issueOverview.mjs`, new or existing frontend copy helper tests, `frontend/lib/profileNarrative.mjs` only if needed, `frontend/components/PositionByIssue.js` only if needed, `docs/plans/`, and `docs/review_packets/`.

## Decision Envelope

- Codex may decide and execute: helper names, exact safe fallback phrases, tests, documentation structure, and scoped UI/copy fixes that enforce the requested contract.
- Explicit approval required for: backend/data/schema changes, production writes, altered interpretation semantics, or any rollback of PR #64 behavior.

## Definition Of Done

- [x] Public-copy source contract is implemented by explicit helper behavior.
- [x] Unsafe phrase filtering blocks production-like raw evidence strings from top-level copy.
- [x] Safe fallback behavior avoids row-derived text in public interpretation copy.
- [x] PR #64 behavior remains intact: dominant records, proof hierarchy, representative votes, full reviewed vote list, and drawers remain available.
- [x] Tests/build/validation recorded.
- [x] Review packet or final documentation updated.
- [x] Final reconciliation completed.

## Baseline

- Branch/base commit: `codex/public-copy-safety-contract` from `main` / `origin/main` at `79d489875f6731e80a2e001ec71a6e2b96f1fb9f` (`Merge pull request #64 from dhart54/codex/issue-read-v2-clarity`).
- Production/deployment state, if relevant: requested as latest production commit after merged PR #64; remote fetch confirmed `origin/main`.
- Tracked working tree: clean before branch creation.
- Known unrelated untracked artifacts: `docs/review_packets/chamber_filtering_data_integrity_audit.md`, `review_bundle_frontend_data_grounding/`.

## Implementation Sequence

1. Audit top-level public-copy paths for row-derived fallback text.
2. Add explicit public-safe theme helpers and unsafe phrase filtering.
3. Route issue overview top-level copy through safe themes and generic domain fallbacks.
4. Add production-like tests for Valerie Foushee National Security leakage and PR #64 behavior.
5. Run targeted/full frontend validation and static scan.
6. Update review packet and commit/PR.

## Progress Checklist

- [x] Discovery started.
- [x] Implementation.
- [x] Validation.
- [x] Documentation.
- [x] Commit/PR readiness.

## Discoveries

- `frontend/lib/issueOverview.mjs` has curated facet copy, but unknown facets currently fall back to `why_it_mattered`, `what_happened`, and `policy_effect` for public overview fields.
- `IssueEvidenceSummary` renders `buildIssueOverview` copy directly into issue summary, "What was reviewed," and "What that means."
- Vote rows, full reviewed vote list, and details drawers intentionally use raw row fields and should remain receipt surfaces.
- Local rendered validation could load the app shell, but ZIP `27701` was not in the loaded map and the sample profile had issue readiness unavailable.

## Decisions And Rationale

- Public interpretation copy will prefer curated facet themes, domain themes, safe short facet labels, and generic domain fallbacks. It will not use row text as a public-theme fallback.
- Unsafe phrase filtering will reject audit-like or sentence-like phrases unless explicitly curated in the helper table.
- Interpretation principles read before implementation; copy remains bounded to reviewed samples, counts, directions, party/outcome context, and receipts.
- "What was reviewed" now uses safe theme lists rather than `whether to...` question chains.

## Deviations Or Corrections

- None yet.

## Validation Results

- `node --test lib\*.test.mjs`: passed, 67/67.
- `npm run lint`: passed with 8 existing React hook dependency warnings and 0 errors.
- `npm run build`: passed with the same 8 warnings.
- `rg -n "INTERNAL_API_TOKEN|X-Internal-API-Token|/internal/record-across-congresses" .next\static`: no matches.
- Rendered shell at `http://127.0.0.1:3000`: desktop default and mobile `390x844` had no horizontal overflow, no visible token/header/internal-route text, and no unsafe raw phrase text.
- Valerie Foushee production-backed rendered validation was not available locally because ZIP `27701` was not in the loaded map and issue evidence was unavailable in the default sample profile.

## Production Writes

- Performed: no
- Scope: none.
- Expected effects: none.
- Actual effects: none.

## Rollback Paths

- Revert the scoped frontend helper/test/documentation commit from this branch.

## Blockers

- No blocker for source-level hotfix completion. Production-backed rendered validation remains limited by unavailable local Valerie data.

## Final Reconciliation

- Definition of done satisfied: yes. Draft PR opened as #65.
- Remaining limitations: repeat production-backed rendered validation where Valerie Foushee live/local issue evidence is available.
- Recommended next step: review PR #65 and repeat production-backed rendered validation where the Valerie data path is available.
