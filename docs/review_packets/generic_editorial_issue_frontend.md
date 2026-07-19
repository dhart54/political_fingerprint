# Generic editorial issue frontend review

## Outcome

The staged Foushee Economy & Taxes experience now uses a generic presentation adapter and renderer shared with the real representative issue flow. Production mode retains the existing basic evidence experience until a matching slice satisfies all public eligibility gates. Pending content remains available only through the explicit, visibly labeled review harness.

## Integration and contract

- Real route: `frontend/app/page.js` -> `PositionByIssue` -> `EvidencePanel`.
- Existing evidence source: `/legislators/{legislatorId}/positions/{domain}/evidence` through `fetchPositionEvidence`.
- Selector/adapter: `frontend/lib/editorialIssueExperience.mjs`.
- Registry data: `frontend/lib/editorialIssueSlices.mjs`.
- Generic renderer: `frontend/components/EditorialIssueExperience.js`.
- Review harness: `/golden-render-fixture`, which passes explicit review mode to the same `PositionByIssue` path.
- Fallback: unchanged basic `IssueEvidenceSummary` and `RepresentativeVotesSection` path when selection returns `null`.

The view model carries supplied identity, synthesis, indicators, optional context/guidance, inclusion classes, staged vote explanations, attributed arguments, important context, and grouped official sources. It never computes broader philosophy or vote direction from raw counts.

## Eligibility proof

- Pending Foushee slice + review mode: rich renderer, with an `Editorial review preview - not published` label.
- Pending Foushee slice + production mode: selector returns `null`; basic experience remains.
- No/mismatched/incomplete slice: selector returns `null`.
- Synthetic `human_approved` + `gold_benchmark` + explicit production eligibility: rich renderer in a production-mode unit test.

No current candidate status changed. No database, API, persistence, source mapping, legislative claim, vote interpretation, episode count, alignment, or readiness semantics changed.

## Synthetic genericity coverage

The review-only fixture uses fictional Jordan Example / Synthetic Energy Choices data. It has four records rather than nine, two policy episodes, mixed Yes/No actions, one Not Voting row, one context-only row, variable source groups with a duplicate URL, an omitted opponent argument, an omitted fact, and no Voting context or How to read panel. It makes no real political claim and is unavailable as ordinary production content.

## Validation

- Focused backend/content/interpretation tests: 52 passed.
- Frontend Node tests: 91 passed.
- Responsive Playwright suite: 8 passed across 1440, 1024, 768, and 390 pixel widths, including the production-mode pending-slice fallback.
- Deterministic staged-content generator `--check`: passed.
- ESLint: zero errors; eight pre-existing React hook warnings.
- Production Next.js build and type validation: passed.
- `git diff --check`: passed before final publication.
- Generic selector/adapter/renderer search: no Foushee ID/name, Economy label, current roll, or fixed six/four count references. Existing Foushee-specific basic-fallback copy remains untouched outside the generic path.

The first sandboxed pytest attempt was invalidated by Windows temp-directory permissions; the identical bounded suite passed outside the sandbox.

## Rendered review

Ten captures in the scoped Codex visualization folder cover the production-mode fallback path, pending review label, summary/collapsed records, first expansion, deeper arguments/context, grouped sources, Foushee mobile, synthetic desktop/mobile, and clean omission of optional panels:

`C:\Users\Dylan\.codex\visualizations\2026\07\19\019f7a4b-4b9e-78a0-bc95-b860f4e0e50d`

Rendered checks found no horizontal overflow, empty optional panels, equal-height forcing, stale deeper disclosure, or mobile stacking defect.

## Publication state

No production write or manual deployment occurred. This milestone may create a draft PR and automatic Vercel preview only. Merge remains unauthorized. The second real issue domain is the next validation milestone.
