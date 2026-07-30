# Editorial Issue Frontend Workflow

## Current runtime

Frontend Pass A uses the route-ready journey in
`frontend/components/RepresentativeExperience.js` and layers the IR-native
public presentation payload defined in
`docs/editorial_public_issue_presentation_v1.md`.

- The initial route is an explicit ZIP/name finder with no automatic sample.
- Representative, issue, and scope state are URL-backed.
- Issue discovery is a responsive overview grid with neutral evidence
  composition and deterministic sort/filter controls.
- Existing position evidence and vote receipts remain available.
- Present, Not Voting, procedural, and limited-context distinctions remain
  available when supplied by actual recorded vote rows.
- The current positions and evidence APIs do not emit expected-but-missing
  actions or service-status absence rows. React does not infer or synthesize
  those states.
- The frontend does not load old editorial registries, selectors, adapters,
  review fixtures, or rich editorial components.
- Tier, teaser, conclusion, repeated-pattern, trajectory, limitation, scope,
  review state, semantic role/direction, and supporting-action fields are
  backend-supplied. React does not derive them.
- Policy episodes render only when the backend supplies reviewed episode
  presentation; the live Pass A selector supplies none.
- The exact receipt ledger is newest-first, progressively disclosed, filtered
  without dropping evidence distinctions, and keeps the full record available.
- The former `/golden-render-fixture` route is removed and returns 404.

Expected-missing and service-status coverage belongs to a future upstream
Semantic IR presentation boundary. That future layer must preserve those typed
states rather than reconstructing them from the current actual-record APIs.

Use `docs/public_editorial_frontend_contract.md` for the normative reduced
frontend contract.

## Validation

Run the surviving frontend unit tests, production build, and bounded browser
smoke:

```powershell
node --test frontend/lib/*.test.mjs
npm run build --prefix frontend
npm run test:cutover-smoke --prefix frontend
npm run test:ir-presentation --prefix frontend
npm run test:frontend-pass-a --prefix frontend
```

The browser smoke mocks only API responses, exercises the real representative
route, confirms basic evidence and source receipts, and confirms the old route
is unavailable.

## IR-native presentation boundary

The backend presentation compiler consumes compiled Semantic IR after canonical
validation. It copies separately reviewed wording mapped to stable proposition
identities and derives tiers from compiled plans and typed boundaries. It must
not adapt Semantic IR back into the deleted format or infer civic meaning from
raw vote counts.

The overview cards, conditional section navigation, and chronological receipt
structure remain. Eligible payloads may layer reviewed conclusions, repeated
patterns, trajectories, and limitations only when every independent control
passes. The compiled evidence state determines `reviewed_conclusion`, `developing_read`,
`non_directional_or_limited_evidence`, or `receipts_only`; no arbitrary vote
threshold does. The public API rechecks publication eligibility and supplies
`receipts_only` when no eligible artifact exists.

The generated public review-state catalog is a descriptive agreement layer,
not publication authority. Build or drift-check it with:

```powershell
python scripts/build_public_review_state_catalog.py --check
python scripts/validate_full_record_issue_interpretation.py
```
