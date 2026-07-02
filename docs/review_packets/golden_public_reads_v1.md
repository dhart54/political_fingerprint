# Golden Public Reads V1 Review Packet

## Intent

This focused PR improves top-level issue overview composition now that PR #65-#67 established the public-copy safety contract, curated theme coverage, and domain-specific fallback behavior.

## Checkpoint Findings

| Area | Current Structure | Working | Weak | Target |
| --- | --- | --- | --- | --- |
| National Security & Foreign Policy | Finding, What these votes were about, How a voter might read that, How to read this | Counts and safe public themes are enforced; raw fields are blocked | Long theme lists repeat across sections; dominant sample sounds mechanical | Keep the 128 opposed / 22 supported finding, make the pattern sentence cleaner, and shorten the voter read |
| Economy & Taxes | Same overview sections | Fiscal and small-business themes are safe and specific | Finding, reviewed section, and voter read repeat the same list | Preserve counts and caveats with a compact golden-read sentence |
| Justice & Public Safety | Same overview sections | Dominant fixture and mixed fixture both exist | Mixed-sample guard needed to stay explicit as copy changes | Keep genuine mixed samples out of mostly-supported/mostly-opposed framing |

## Interpretation Boundary

- Top-level overview copy continues to use issue facets, curated public themes, and domain fallbacks.
- Raw fields such as descriptions, questions, summaries, uncertainty notes, interpretation reasons, classification reasons, and source basis are not used for top-level public interpretation copy.
- Receipt/detail surfaces remain separate and are not changed by this PR.
- No support/opposition, readiness, counting, eligibility, or alignment semantics are changed.

## Files Changed

- `frontend/lib/issueOverview.mjs`
- `frontend/lib/issueOverview.test.mjs`
- `docs/plans/golden_public_reads_v1.md`
- `docs/review_packets/golden_public_reads_v1.md`

## Before / After Examples

Before:

> In this reviewed sample, Foushee mostly opposed these reviewed National Security & Foreign Policy measures...

After:

> In this reviewed sample, Foushee mostly opposed the reviewed National Security & Foreign Policy measures...

Before:

> The opposed measures centered on defense authorization legislation...

After:

> Opposition was concentrated in defense authorization legislation...

Before:

> If you favored the reviewed measures on [full list]...

After:

> A voter who favored those measures...

## Validation

- `node --test lib\issueOverview.test.mjs` passed: 18 tests.
- `node --test lib\*.test.mjs` passed: 70 tests.
- `npm run lint` passed with existing React hook dependency warnings.
- `npm run build` passed with the same React hook dependency warnings.
- `rg -n "INTERNAL_API_TOKEN|X-Internal-API-Token|/internal/record-across-congresses" .next\static` returned no matches.
- Local built app response check passed: `http://localhost:3000` returned HTTP 200.
- Screenshot-based rendered validation was not completed because the local Playwright browser binary is not installed.

## Limitations

- This PR does not add new public theme mappings.
- This PR does not redesign the issue UI.
- This PR does not change backend data, schema, readiness, support/opposition counting, or vote interpretation.
- This PR has not been production-smoked because it is a draft branch and has not deployed to production.
