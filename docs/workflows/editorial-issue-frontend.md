# Editorial Issue Frontend Workflow

## Current runtime

After Editorial Hard Cutover V1, the public representative route retains the
basic evidence path in `frontend/components/PositionByIssue.js` and can layer
the IR-native public presentation payload defined in
`docs/editorial_public_issue_presentation_v1.md`.

- Representative and issue selection remain functional.
- Existing position evidence and vote receipts remain available.
- Present, Not Voting, procedural, and limited-context distinctions remain
  available when supplied by actual recorded vote rows.
- The current positions and evidence APIs do not emit expected-but-missing
  actions or service-status absence rows. React does not infer or synthesize
  those states.
- The frontend does not load old editorial registries, selectors, adapters,
  review fixtures, or rich editorial components.
- Tier, teaser, conclusion, repeated-pattern, trajectory, limitation, scope,
  and supporting-action fields are backend-supplied. React does not derive them.
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

The coverage-first cards, compact issue navigation, and vote-receipt structure
remain. Eligible payloads may layer reviewed conclusions, repeated patterns,
trajectories, and limitations only when every independent control passes. The
compiled evidence state determines `reviewed_conclusion`, `developing_read`,
`non_directional_or_limited_evidence`, or `receipts_only`; no arbitrary vote
threshold does. The public API rechecks publication eligibility and supplies
`receipts_only` when no eligible artifact exists.
