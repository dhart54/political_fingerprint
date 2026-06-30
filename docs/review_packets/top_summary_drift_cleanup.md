# Top Summary Drift Cleanup Review Packet

## Scope

- Branch: `codex/top-summary-drift-cleanup`
- Intent: Remove low-value drift/change language from the top profile summary and replace it with direct, bounded, evidence-backed interpretation.
- Production writes: none.

## Interpretation Principles Consulted

- Read `docs/interpretation_principles.md` before copy/UI work.
- Applied the standard: clear, evidence-backed interpretation with receipts; no moral judgment, motive claims, unsupported ideology labels, unsupported cross-time movement claims, or future-behavior claims.
- Used the cross-Congress guidance: show Congress-specific counts side by side without inferring change, drift, consistency, or trend.

## Drift And Change Terms Audited

Searched frontend code for:

`Change`, `Drift`, `Steady`, `consistent`, `differs`, `shift`, `shifted`, `trend`, `movement`, `stronger`, and `weaker`.

## Audit Classification

1. High-risk visible top-summary copy changed:
   - `frontend/components/ProfileQuickRead.js`: top metric label `Change`, drift fetch/use, and values such as `Steady mix`, `Some shift`, and changed/steady issue-mix labels.
   - `frontend/lib/profileNarrative.mjs`: headline `clearest reviewed pattern` and body injection of cross-Congress comparison statements such as `consistent with the prior Congress`.
   - `frontend/components/ProfileQuickRead.js`: scope read that surfaced comparison statements such as `differs between the 118th and 119th Congresses`.

2. Acceptable issue-evidence interpretation left unchanged:
   - `frontend/lib/issueOverview.mjs`, `frontend/lib/voteCardSummary.mjs`, and related tests use `change` to describe concrete policy mechanisms, not cross-time movement.
   - Issue evidence still uses guarded labels such as `Mixed but interpretable`.

3. Record Across Congresses guarded copy/tests left unchanged:
   - `frontend/lib/recordAcrossCongresses.mjs` and `frontend/components/RecordAcrossCongressesPanel.js` keep guardrails for cross-Congress family reads.
   - Record Across tests intentionally include disallowed source wording to verify sanitization.

4. Internal constants/tests left unchanged:
   - `consistent`, `stronger`, and `weaker` remain internal comparison status names in `frontend/lib/profileNarrative.mjs`, mapped to non-movement public copy.
   - Tests retain old unsafe phrases as negative assertions or fixture input.

5. Out-of-scope legacy copy left unchanged:
   - `frontend/components/DriftIndicator.js` still contains drift/change language but is not mounted in the current app path. Removing that unused legacy component would be a broader cleanup than this top-summary milestone.

## Copy Removed

- Removed the top summary drift request from `ProfileQuickRead`.
- Removed the top metric `Change`.
- Removed visible values/copy including `Steady mix`, `Some shift`, and issue-mix changed/steady labels from the live top summary path.
- Removed cross-time comparison statements from the top summary body and scope note.

## Copy Changed

- Top headline now uses: strongest reviewed evidence is in the issue area.
- Top metrics now show:
  - `Strongest evidence`
  - `Coverage`
  - `Record read`
- Cross-Congress note now says reviewed votes are available in both Congresses and Congress-specific counts are shown separately below.

## Copy Intentionally Left Unchanged

- Issue evidence language that describes concrete policy changes.
- Record Across Congresses guarded methodology/copy.
- Internal status names and tests that ensure unsafe source wording does not leak.
- The unused `DriftIndicator` legacy component.

## Validation

- `cd frontend; npm run lint`: passed with 8 existing React hook dependency warnings.
- `cd frontend; npm run build`: passed with the same existing warnings and preserved `/api/record-across-congresses/house/[legislatorId]`.
- `cd frontend; node --test lib\*.test.mjs`: passed, 55 tests.
- `cd frontend; rg -n "INTERNAL_API_TOKEN|X-Internal-API-Token|/internal/record-across-congresses" .next\static`: no matches; no-match exit treated as success.

## Rendered Validation

Local services used:

- Backend: `uvicorn app.main:app --host 127.0.0.1 --port 8000` with a throwaway local `INTERNAL_API_TOKEN`.
- Frontend: production `next start` on `127.0.0.1:3000` with the same throwaway local token and `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000`.

Valerie Foushee:

- Desktop: passed. Top summary no longer showed `Change`, `Steady mix`, or movement terms such as `consistent`, `differs`, `drift`, `shift`, `trend`, `movement`, `stronger`, or `weaker`.
- Desktop: top summary showed `strongest reviewed evidence`, `Strongest evidence`, `Coverage`, and `Record read`.
- Desktop: issue evidence rendered, Record Across Congresses rendered, no horizontal overflow, and no token/header/internal-route text was visible.
- Mobile 390x844: passed for the same top-summary, issue evidence, Record Across, overflow, and internal-leak checks.

Aaron Bean:

- Initial local load briefly rendered Aaron Bean's loading top card with the new metric labels and without drift/change terms.
- A ready Aaron issue-detail pass was not practical because the ZIP lookup immediately selected Valerie Foushee in the local app path, and the switcher was not exposed in the rendered local DOM.
- Record Across rendered in the local app path.

## Remaining Limitations

- Aaron Bean ready-state top-summary validation remains a practical follow-up limitation in local rendering. The code path is shared and covered by tests, but this packet does not claim a completed Aaron ready-state issue summary pass.
