# Caveat Density Cleanup Review Packet

## Scope

- Branch: `codex/caveat-density-cleanup`
- Intent: Clear finding first, receipts always available, limits shown once per claim type instead of repeated on every surface.
- Production writes: none.

## Caveat Terms Audited

Searched frontend user-facing copy and tests for:

`does not prove`, `what not to infer`, `not show motive`, `does not show motive`, `not a broad claim`, `not a simple statement`, `vote record alone`, `context rows`, `limited-context`, `procedural-context`, `caveat`, `infer`, and `motive`.

Repository-wide search also found many historical review packets, derived artifacts, backend contracts, methodology docs, and migration/test constants. Those were classified as retained methodology/history/internal material and not rewritten for this frontend copy milestone.

## Audit Classification

1. Top-level repeated caveats that interrupted interpretation:
   - `frontend/lib/issueOverview.mjs`: visible `howVoterMightRead` repeated "The vote record alone does not show her motive."
   - `frontend/components/PositionByIssue.js`: issue-level disclosure label `What not to infer` repeated the same boundary wording directly after each issue summary.

2. Useful global "how to read this" boundary:
   - `frontend/lib/issueOverview.mjs`: retained as one concise issue-level boundary: "This read is limited to reviewed votes in this sample..."
   - `frontend/components/SummaryPanel.js`: retained broad descriptive-purpose boundary for top-level takeaways.

3. Useful per-vote/source caveat:
   - `frontend/components/PositionByIssue.js`: retained `Source, caveats, and full context`.
   - `frontend/components/PositionByIssue.js`: retained vote-row `What not to infer` inside expanded source/caveat details.
   - `frontend/lib/proceduralContext.mjs` and `frontend/lib/evidenceGrouping.mjs`: retained procedural, limited-context, and not-voting distinctions.

4. Useful methodology/readiness copy:
   - `frontend/lib/recordAcrossCongresses.mjs` and `frontend/components/RecordAcrossCongressesPanel.js`: retained comparability, not-voting, missing-record, and non-inference boundaries.

5. Internal test/constant:
   - `frontend/lib/*.test.mjs`: updated expectations where they enforced old repeated caveat language; retained tests protecting vote-level caveats and civic-integrity boundaries.

6. Should remain unchanged:
   - Historical docs/review packets, backend analysis fields, migrations, and methodology workflow copy.

## Caveats Consolidated

- Removed the repeated visible sentence "The vote record alone does not show her motive" from issue `What that means` copy.
- Replaced issue-level `What not to infer` summary label with `How to read this`.
- Changed issue summary order so the visible top sentence is the bounded finding/pattern, followed by reviewed-vote receipts.
- Kept the non-inference boundary in one concise collapsible issue-level location.

## Caveats Retained

- Issue-level boundary: sample-limited read, no motive/ideology/character/corruption/voting recommendation, full-record limitation, not-voting and limited-context rows kept separate.
- Vote-level drawer: `Source, caveats, and full context`.
- Vote-level `What not to infer` fields remain inside expanded details.
- Record Across Congresses comparability and missing-record caveats remain unchanged.
- Methodology and historical review packet caveats remain unchanged.

## Interpretation Boundary

New hierarchy:

1. Finding first: what the reviewed sample shows.
2. Receipts next: what votes/measures were reviewed.
3. One issue-level read boundary: how to read the sample safely.
4. Vote-level caveats and source context inside each vote drawer.
5. Full methodology retained outside the repeated summary path.

## Validation

- `cd frontend; npm run lint`: passed with existing React hook dependency warnings.
- `cd frontend; npm run build`: passed with existing React hook dependency warnings.
- `cd frontend; node --test lib\*.test.mjs`: passed, 55 tests.
- `cd frontend; rg -n "INTERNAL_API_TOKEN|X-Internal-API-Token|/internal/record-across-congresses" .next\static`: no matches; `rg` exited with no-match status as expected.

## Rendered Validation

Local services used:

- Backend: `uvicorn app.main:app --host 127.0.0.1 --port 8000`.
- Frontend: production `next start` from the successful build.

Valerie Foushee:

- Desktop: issue summary rendered; evidence groups rendered; top issue summary led with the finding/pattern before reviewed-vote receipts; visible repeated "vote record alone does not show motive" copy was absent; issue-level `How to read this` boundary was present; vote-level `Source, caveats, and full context` drawers were present; no horizontal overflow detected; no token/header/internal-route text visible.
- Mobile 390x844: same issue summary, boundary, vote drawer, no-overflow, and no-internal-leak checks passed.

Aaron Bean:

- Record Across Congresses rendered successfully on the token-backed local frontend. The panel showed 11 eligible families, 4 closest, and 7 caveated. No horizontal overflow or visible token/header/internal-route text was detected.
- Issue-detail validation was not completed because the local page reported that issue readiness was unavailable for this legislator. This packet does not claim an Aaron issue-evidence rendered pass.

Record Across Congresses:

- Build output preserved the dynamic `/api/record-across-congresses/house/[legislatorId]` route.
- Static scan found no leaked token/header/internal route strings.
- Local browser rendering passed on a production `next start` server with a matching throwaway local `INTERNAL_API_TOKEN` on the frontend and backend. The rendered app did not expose `INTERNAL_API_TOKEN`, `X-Internal-API-Token`, `/internal/record-across-congresses`, or the local token value.

## Remaining Limitations

- Aaron Bean issue-detail rendered validation remains practical follow-up coverage because the local issue-readiness payload rendered as unavailable for that legislator.
