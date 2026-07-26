# Editorial Issue Frontend Workflow

## Current runtime

After Editorial Hard Cutover V1, the public representative route uses only the
basic evidence path in `frontend/components/PositionByIssue.js`.

- Representative and issue selection remain functional.
- Existing position evidence and vote receipts remain available.
- Procedural, limited-context, Present, Not Voting, and missing-evidence states
  remain distinct.
- The frontend does not load old editorial registries, selectors, adapters,
  review fixtures, or rich editorial components.
- The former `/golden-render-fixture` route is removed and returns 404.

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

## Deferred IR-native work

Do not add a new rich editorial design within the cutover. A future presentation
milestone may consume compiled Semantic IR through a meaning-preserving public
view model. It must not adapt Semantic IR back into the deleted format or infer
new civic meaning in React.

The coverage-first cards, compact issue navigation, and vote-receipt structure
are intended to remain as that presentation evolves. A future IR-native
milestone may layer reviewed conclusions, repeated patterns, trajectories, and
limitations onto this structure only when they come from compiled Semantic IR
and reviewed dossiers, never from frontend vote-count logic. The compiled
evidence state must continue to determine whether the UI shows a full
conclusion, a bounded developing read, non-directional coverage, or receipts
only.
