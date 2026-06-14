# Profile Evidence Integrity Recovery And Mobile Compression - Phase 23

## Scope

Phase 23 investigated the live Phase 22 profile regression and compressed the accountability profile for mobile review.

Guardrails:

- No production data writes were performed.
- No schema changes were made.
- No support/opposition counting logic changed.
- No alignment logic changed.
- No readiness thresholds changed.
- No interpretation semantics changed.

## Live Symptoms

The public Phase 22 deployment showed Valerie P. Foushee with:

- Quick Read copy saying no issue area had enough reviewed vote meaning.
- National Security & Foreign Policy showing 0 interpreted votes in the issue summary.
- Economy & Taxes showing 0 interpreted votes in the issue summary.
- No useful reviewed issue patterns.
- Repeated limited-evidence copy across the issue list.

This conflicted with previously validated production evidence, including 19 interpreted National Security rows, interpreted Economy rows, and interpreted Justice rows.

## Root Cause

Production data was not lost.

The public Render API was serving a stale or mismatched profile read path. The public `/positions` response included recorded vote totals but omitted the `interpreted_*` summary fields entirely. The public `/positions/{domain}/evidence` response returned roll-call and classification fields but omitted vote-interpretation fields. Local current `main` read against the same production database returned the expected interpretation fields and counts.

The code path also had a fragile backend join condition that required `vote_interpretations.classification_version` to match the active `vote_classifications.classification_version`. Because `vote_interpretations` is keyed by `roll_call_id`, the read path should join interpretations by roll call identity and let the active classification version filter only the classification rows.

Classification: deployment/environment mismatch plus fragile backend version-join behavior.

## Evidence Integrity Fix

Backend:

- Position summary, evidence, and alignment reads now join `vote_interpretations` by `roll_call_id`.
- The active classification version still filters `vote_classifications`.
- Interpretation rows remain one per roll call and are not duplicated.
- Procedural rows remain non-counting.
- Not-voting rows remain excluded from support/opposition counts.

Frontend:

- `ProfileQuickRead` and `PositionByIssue` now defensively fill missing interpreted summary counts from the domain evidence endpoint when the `/positions` payload omits those fields.
- The fallback only counts rows whose stored `interpretation_status` is `interpreted`.
- It uses the stored `support_position` and `oppose_position`; it does not infer vote meaning.

## Valerie Baseline And Restored Counts

Local current code against production data:

| Issue | Total rows | Recorded Yes/No | Interpreted Yes/No | Other interpreted | Ambiguous/insufficient | Not voting | Support | Oppose | Readiness |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Economy & Taxes | 9 | 8 | 6 | 1 | 2 | 1 | 0 | 6 | Strong evidence |
| National Security & Foreign Policy | 22 | 22 | 19 | 0 | 3 | 0 | 2 | 17 | Mixed but interpretable |
| Justice & Public Safety | 13 | 13 | 6 | 0 | 7 | 0 | 2 | 4 | Mixed but interpretable |
| Education & Workforce | 6 | 5 | 2 | 1 | 3 | 1 | 1 | 1 | Limited evidence |
| Health & Social Services | 4 | 4 | 1 | 0 | 3 | 0 | 0 | 1 | Limited evidence |
| Environment & Energy | 3 | 3 | 1 | 0 | 2 | 0 | 0 | 1 | Limited evidence |
| Immigration & Border Policy | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 1 | Limited evidence |

Rendered local validation showed:

- The old “no issue area has enough reviewed vote meaning” copy is absent.
- Quick Read starts with Economy & Taxes because it is the strongest one-direction issue read.
- National Security remains visible as a larger mixed read with 19 reviewed Yes/No votes.
- Justice remains visible as mixed but interpretable.

## Other Profile Checks

Production-backed local read-layer checks:

- Thom Tillis: Economy 34 interpreted, Health 16 interpreted, National Security 5 interpreted, Justice 2 interpreted.
- Ted Budd: Economy 34 interpreted, Health 16 interpreted, National Security 5 interpreted, Justice 2 interpreted, Infrastructure includes not-voting rows that remain non-counting.
- Adam B. Schiff: Economy 34 interpreted, Health 16 interpreted, National Security 5 interpreted with mixed support/opposition.
- Aaron Bean: House interpreted evidence remains visible, including Economy 7, National Security 19, Justice 6.
- Alex Padilla: Senate interpreted evidence remains visible; not-voting rows remain separated.

Rendered local checks:

- Valerie Foushee: repaired evidence hierarchy visible.
- Ted Budd: profile switching rendered strong Senate evidence without regression copy.
- Thom Tillis: profile switching rendered strong Senate evidence without regression copy.

Browser automation could not type into the search box because the in-app browser virtual clipboard was unavailable, so Adam Schiff and sparse-profile rendering were validated through the same local API/read-layer and shared component path.

## Mobile Compression

Changes:

- Compressed the top product hero into a shorter product header.
- Compressed the ZIP/result shell once officials are loaded.
- Removed the three-card Current Profile explainer.
- Reworked Quick Read into a compact summary strip with three small metrics.
- Removed the large “How To Read This” and “What You Can Learn In 60 Seconds” guidance blocks.
- Replaced repeated limited/not-ready issue cards with compact list rows.
- Suppressed the reviewed-pattern section when no interpreted patterns exist.
- Suppressed the alignment panel until at least one issue is selected.
- Kept global official search collapsed by default.
- Rendered upcoming race context only when race rows are actually loaded.
- Shortened long visible measure titles while preserving full titles in details.
- Added mobile CSS offsets for common injected accessibility controls.

Mobile before/after at 390x844:

- Public Phase 22 page height: about 9,542px.
- Local Phase 23 page height: about 7,100px.
- Approximate reduction: 26%.
- Phase 22 repeated “No reviewed Yes/No vote meaning is available yet” 7 times on the default Valerie path.
- Phase 23 removes that repeated not-ready card treatment from the default issue list.

## Responsive Validation

Local production build was validated at:

| Viewport | Horizontal overflow | Regression copy | Old explainer copy | Evidence visible |
| --- | --- | --- | --- | --- |
| 1920x1080 | No | No | No | Yes |
| 1440x900 | No | No | No | Yes |
| 1366x768 | No | No | No | Yes |
| 768x1024 | No | No | No | Yes |
| 390x844 | No | No | No | Yes |
| 375x812 | No | No | No | Yes |

## Tests And Build

Passed:

- `node --test frontend\lib\positionEvidenceCounts.test.mjs frontend\lib\evidenceGrouping.test.mjs frontend\lib\issueReadiness.test.mjs frontend\lib\issueOverview.test.mjs frontend\lib\profileMvpProfile.test.mjs frontend\lib\proceduralContext.test.mjs`
  - 31 passed.
- `backend\.venv_win\Scripts\python.exe -m pytest backend\tests\test_api_positions.py backend\tests\test_api_alignment.py`
  - 27 passed.
- `cd frontend; npm run build`
  - passed.

Rendered validation:

- Local backend and local production frontend served successfully.
- Public Phase 22 mobile baseline measured for before/after comparison.
- Local Phase 23 responsive checks passed at the required viewport set.

Known test warning:

- Node emitted existing `MODULE_TYPELESS_PACKAGE_JSON` warnings for ESM-style frontend library files. Tests passed.

## Production Data

Production data changed: no.

Tables changed: none.

The issue is recoverable through code/deployment. No production repair was needed.

## Known Limitations

- The public Render API appears stale or mismatched relative to current `main`; the backend fix needs deployment to restore the public API path directly.
- The frontend fallback cannot recover interpretation counts if a deployed evidence endpoint also omits interpretation fields. It is still useful for APIs that omit only summary counts.
- Mobile length is materially reduced, but the profile remains evidence-heavy when issue patterns and evidence details are available.
- Search-box rendered validation for Adam Schiff was blocked by the in-app browser typing/clipboard limitation.

## Next Recommendation

After this PR is reviewed and merged, confirm the backend deployment serving `political-fingerprint.onrender.com` is updated to the merged commit, then re-check the public Valerie page. If the public API remains stale after merge/deploy, the next milestone should be a Render deployment/config audit rather than more frontend compression.
