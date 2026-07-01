# Milestone Plan: Show Votes Proof Hierarchy

## Intent

- Immediate task: improve the `Show Votes` proof-view hierarchy so users can inspect evidence without opening a giant undifferentiated vote list.
- Larger-goal alignment: preserve receipts while keeping Political Fingerprint a plain-English voting-record interpreter: finding first, representative receipts next, full detail still available.

## Outcome

- User-visible result: issue evidence expansions open with an organized proof view that highlights a bounded first set of votes, separates countable and context evidence where safely available, and keeps the full reviewed vote list and source/caveat drawers accessible.

## Scope And Boundaries

- In scope: frontend `Show Votes` / issue evidence expansion UI, evidence group hierarchy, vote-row density/default count, show-more/show-all behavior, low-risk grouping labels, focused tests, rendered validation, review packet.
- Out of scope: backend/data/schema changes, methodology changes, new scoring/ranking, new interpretation model, Record Across methodology changes, token/config changes, production writes, broad page redesign.
- Files/systems likely touched: `frontend/components/PositionByIssue.js`, `frontend/lib/*.test.mjs`, `docs/review_packets/`, this active plan.

## Decision Envelope

- Codex may decide and execute: UI-only hierarchy and bounded default vote display using existing client-side fields; copy that preserves evidence limits; focused tests and documentation.
- Explicit approval required for: backend/data/schema changes, methodology semantics changes, ranking logic beyond current ordering, token/config changes, production writes, broad redesign.

## Definition Of Done

- [x] Required audit completed and recorded.
- [x] Proof view opens as organized hierarchy rather than full undifferentiated list.
- [x] Full reviewed vote list remains accessible.
- [x] Vote-level source/caveat/full-context drawers remain available.
- [x] Focused tests cover default bounded list, full-list access, source/caveat drawers, and Valerie Foushee evidence rendering where practical.
- [x] Required validation passes: `npm run lint`, `npm run build`, `node --test lib\*.test.mjs`, `.next\static` internal-token scan with no matches.
- [x] Rendered desktop and 390x844 mobile validation completed or limitations documented.
- [x] Review packet updated.
- [ ] PR revised, committed, pushed, and ready for review unless a true stop condition is reached.

## Baseline

- Branch/base commit: `codex/show-votes-proof-hierarchy` from production-verified `main` at `fa866b4ee18f24af8411871a4df9d80784c46f7c`.
- Production/deployment state: production verified serving PR #61 first-render fallback cleanup.
- Tracked working tree: clean at start.
- Known unrelated untracked artifacts: `docs/review_packets/chamber_filtering_data_integrity_audit.md`, `review_bundle_frontend_data_grounding/`.

## Implementation Sequence

1. Audit current `Show Votes`, vote row, grouping, and tests.
2. Design smallest safe proof hierarchy using existing client-side fields.
3. Implement bounded representative/default vote section and full-list access.
4. Add or update focused tests.
5. Run required commands and static scans.
6. Validate rendered production build locally with Valerie Foushee primary target if practical.
7. Create review packet and reconcile plan.
8. Commit intended files and open PR.

## Progress Checklist

- [x] Discovery
- [x] Implementation
- [ ] Validation
- [x] Documentation
- [ ] Commit/PR readiness

## Discoveries

- Interpretation principles consulted before implementation. Copy must preserve receipts, avoid unsupported ranking language, and keep procedural/limited/not-voting distinctions clear.
- `Show Votes` previously rendered every grouped bill card immediately after the issue summary, so the first expanded proof state could become a long full receipt list.
- Existing client evidence rows already expose enough fields for a UI-only hierarchy: interpreted/countable status, vote position, procedural context, limited/context status, roll call metadata, measure labels, source URL, and classification/detail copy.
- `VoteEvidenceRow` already owns the vote-level source/caveat/full-context drawer, so reusing it preserves receipt access without changing evidence semantics.
- Valerie Foushee is covered by source-level issue overview tests, but the local fixture backend search does not return Valerie. Rendered validation therefore used the available local fixture profile.
- Revision audit: `PositionByIssue.js` renders the issue evidence expansion and vote drawers; `issueOverview.mjs` generates `Issue summary`, `What was reviewed`, `What that means`, and `How to read this`; `profileMvpProfile.test.mjs` and `issueOverview.test.mjs` protect the proof hierarchy and copy behavior.

## Decisions And Rationale

- Add a bounded `Representative votes` section before the full list. It uses the existing evidence ordering and shows up to 8 countable Yes/No rows by default.
- Keep the full receipt list behind `Show all reviewed votes`, grouped by bill/measure as before, with countable/context labels preserved.
- Revise expanded-section order to: `Issue summary`, `Representative votes`, `Full reviewed vote list`, `Evidence group overview`, `Evidence tools`.
- Rename the visible grouping preview from `Evidence groups` to `Evidence group overview` and move it below the full-list access so it is secondary to receipts.
- In issue-summary copy, treat interpreted Yes/No samples with at least a two-thirds support/opposition direction as `mostly supported` or `mostly opposed`; keep genuinely close records as `split`.
- Enforce `Policy substance first. Party context second.` by leading findings and `What that means` with reviewed policy substance and counts, then placing party context as a supporting sentence.
- Move broader limitation copy into `How to read this`; top-level findings use the concise `In this reviewed sample...` boundary and receipt prompt.
- If a selected issue has no countable Yes/No rows, fall back to the sorted available rows for the representative proof set and tell users to inspect the full reviewed list.
- Summarize limited, procedural, and not-voting context rows without treating them as support/opposition evidence.
- Preserve `VoteEvidenceRow` and its `Source, caveats, and full context` disclosure rather than creating a new evidence-card format.

## Deviations Or Corrections

- Rendered validation did not use Valerie Foushee because the local fixture search returned no Valerie/Foushee results. The Valerie-specific issue overview copy remains covered by `frontend/lib/issueOverview.test.mjs`.
- Record Across Congresses did not render in the local fixture page because the server route returns no ready response without the internal token/backend data path. Record Across source and tests are unchanged, and the static bundle leakage scan remained clean.
- Current revision rendered validation completed with the local fixture profile after reloading through the fallback ZIP path.

## Validation Results

- `cd frontend; node --test lib\*.test.mjs`: passed, 58 tests.
- `cd frontend; npm run lint`: passed with 8 existing React hook dependency warnings.
- `cd frontend; npm run build`: passed with the same 8 existing warnings.
- `cd frontend; rg -n "INTERNAL_API_TOKEN|X-Internal-API-Token|/internal/record-across-congresses" .next\static`: no matches.
- Rendered desktop production build at `http://localhost:3000`: passed for the local fixture proof path. After `Show Votes`, the order was `Issue summary`, `Representative votes`, `Full reviewed vote list`, `Evidence group overview`, then evidence tools. Full-list expansion, source/caveat drawers, and no page-level horizontal overflow were verified. No token/header/internal-route text was visible.
- Rendered 390x844 production build: passed with the same order, full-list expansion, source/caveat drawer availability, no page-level horizontal overflow, and no token/header/internal-route text.
- Record Across Congresses: source wiring and existing tests remained unchanged. The local fixture path still does not provide a ready internal-token-backed Record Across response, so rendered visibility remains limited by the local fixture/server-token setup rather than this revision.

## Production Writes

- Performed: no
- Scope: not authorized.
- Expected effects: none.
- Actual effects: none.

## Rollback Paths

- Revert the focused frontend, test, plan, and review-packet commit for this branch.

## Blockers

- None currently.

## Final Reconciliation

- Definition of done satisfied: yes, except commit/push/PR creation remains.
- Remaining limitations: Valerie Foushee is still source-test covered rather than locally renderable from fixture search; local Record Across rendered visibility remains limited by the internal-token-backed fixture/server setup.
- Recommended next step: commit and push the revision, then open a follow-up PR because PR #62 has already been merged.
