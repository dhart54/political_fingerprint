# Record at a Glance — release candidate

This revision continues PR #191 from product-reviewed head `56a35e860783466f6079cba47f6338e2e6a09dab`. The user accepted the six-finding selection, source mappings and rationale, Education's intentional directionless display, first five entries, evidence labels and per-issue cutoffs. Those decisions are preserved. The exact release head and its completed CI run are recorded in the PR body because a commit cannot contain its own hash.

## Bounded wording change

The headline remains **Security assistance differed by country and proposal**. Previously, the complete five-paragraph country explanation appeared on the opening card. The card now says exactly:

> The reviewed choices cover Ukraine, Jordan, Taiwan and Israel; they do not establish one uniform position on assistance.

**Based on 8 House votes** and **Compare the proposals** are unchanged. One click opens the following complete existing explanation, immediately visible without an expansion control:

> Ukraine: Opposed three aid restrictions with different scopes; supported a measure authorizing support for Ukraine. That whole measure also covered other purposes, so the vote does not isolate every provision.
>
> Jordan: Opposed two proposals to cut or restrict assistance, affecting different accounts through different mechanisms.
>
> Taiwan: Opposed removing funding for the Taiwan Security Cooperation Initiative.
>
> Israel: Supported an amendment barring funds in the bill from being used for Israel. The same amendment reduced the Foreign Military Financing account by $3.3 billion.
>
> The Israel and Taiwan amendments are individual choices, not recurring country patterns. These choices do not establish one uniform position on assistance across countries.

The full explanation is not duplicated on the card. The finding view retains the eight exact action references, their receipts, and the complete issue record. Tests pin both the first five entries and this unchanged paragraph array to hashes of the accepted head. No other entry has been rewritten; no selection or interpretation has been reopened.

## Ordinary-route integration

The existing `/` journey now receives `frontend/lib/recordCardContent.json`: a small code-bundled presentation selection with wording, member/scope identity, exact source/finding hashes, complete action IDs and source-bound coverage metadata. The existing review builder derives it alongside the review packet. It contains no snapshot, full ledger, receipt payload, database access or replay loader.

The ordinary route continues to read profile, positions, editorial presentations and lazily selected issue evidence through `frontend/lib/api.js`. It does not request `/api/review/record-card`. There is no fixture fallback when the live API fails. No other representative or scope receives an invented selection. Foushee's card appears only against its exact `119` or `all` live presentations; `all` explicitly preserves the 119th-Congress findings boundary. The ordinary header, finder and scope controls remain intact.

This is presentation of existing eligible issue content, using the user's recorded product review in the existing execution plan/packet. No new publication registry, approval receipt, production-eligibility flag, human-approval claim, benchmark status or content-review pipeline has been introduced. The backend's existing eligibility and publication selection gates remain unchanged. Further substantive copy changes require review; this release preparation does not authorize activation.

`/review/record-card` and its replay API remain local opt-in only (`ENABLE_RECORD_CARD_REVIEW=1`), return 404 by default and are disabled on Vercel even if that flag is set. The review banner explicitly identifies the recorded snapshot and absence of live data. Both surfaces reuse the same card/finding rendering and exact-source validator. Route-relative links preserve the current surface through finding, receipt, full-record and return navigation, including refresh, Back/Forward, direct URLs and focus.

## Independent validity and failure behavior

The API envelope is validated independently for member, scope, complete eight-domain data, recognized tiers and required presentation fields. A card-specific source mismatch withholds only the card. It does not overwrite API presentation status or discard valid current summaries. The stale message is distinct from no reviewed findings. An old finding deep link falls back to the current issue summary/full record with a clear mismatch message.

Genuine API failure, member/scope mismatch and incomplete presentation data remain fail-closed for summaries. Independently available vote receipts remain accessible. Loading is distinct; a delayed response from an old scope cannot restore its card. A valid reviewed issue set without a prepared card uses the existing `not_selected` state; receipts-only scopes/members use the no-reviewed-findings state. No absence is converted into political meaning.

## Validation and rendered evidence

- 168 frontend unit tests passed, including exact accepted-copy hashes, source/action mappings, Education restriction, known/unspecified cutoff bindings and independent API/card validity.
- 150 existing API, public presentation, governed receipt, public record integrity and M15B semantic tests passed.
- Production build passed. Eight pre-existing hook-dependency warnings remain outside the touched components.
- Full existing plus new production-mode browser suite: 59 passed, one optional historical Pass A screenshot test skipped. After adding loading/delayed-scope coverage, all 14 release tests passed again. Together these cover 61 distinct passing browser tests. The existing nine review-card tests remain intact.
- Both routes prove complete first-click assistance, all eight references, all six selected action sets, Education's paired choices, full-record access, source/member/scope checks, stale-card isolation, no-summary versus unavailable, history, refresh, direct anchors, keyboard focus and return.
- Landing makes no full-evidence-ledger requests. Ordinary-route tests make no review API requests. Test-only interception at the real read-interface URLs supplies recorded public responses; it is not a runtime fixture fallback.
- With replay disabled in the production build, actual local HTTP checks returned `/` 200, `/review/record-card` 404 and `/api/review/record-card` 404. The existing unit guard additionally rejects Vercel even with the replay flag enabled.
- Eighteen captures cover ordinary and review routes at 1440×900, 390×844 and 360×800: landing, complete card and complete opened assistance. Complete cards and detail were inspected, not merely the first visible link. No horizontal overflow, text reduction, line clamp or hidden qualification. The ordinary mobile header/scope controls remain visible above the card and require scrolling to its entries.
- Source projection drift, final diff and whitespace checks passed. Existing exact-head CI also runs the card mapping and both-route tests in its existing job; no new workflow or infrastructure is added. Completed exact-head results belong in the PR body.

Rendered review caught a narrow-screen screenshot taken during focus/scroll transfer, placing the sticky header over the captured detail. Capture now waits for the real heading focus and settled scroll position; both capture tests passed again, and the regenerated full detail was inspected. No UI content was hidden to produce screenshots.

Fresh public read-only checks at **2026-09-16 15:01 UTC**, against `https://political-fingerprint.onrender.com`, resolved this runtime content as follows. These are live API compatibility checks; screenshots use deterministic recorded responses through the respective route interfaces.

| Member | Scope | HTTP | Card result |
|---|---|---|---|
| Valerie P. Foushee | `119` | 200 | Ready, six findings |
| Valerie P. Foushee | `all` | 200 | Ready, six findings bounded to 119 |
| Valerie P. Foushee | `118` | 200 | No reviewed findings; issue receipts remain |
| Thomas Massie | `119` | 200 | No reviewed findings; issue receipts remain |

## Screenshots

| Surface | Landing | Complete card | Opened assistance |
|---|---|---|---|
| Ordinary desktop | [Landing](release-screenshots/ordinary-desktop-landing.png) | [Card](release-screenshots/ordinary-desktop-complete-card.png) | [Detail](release-screenshots/ordinary-desktop-assistance-detail.png) |
| Ordinary mobile | [Landing](release-screenshots/ordinary-mobile-landing.png) | [Card](release-screenshots/ordinary-mobile-complete-card.png) | [Detail](release-screenshots/ordinary-mobile-assistance-detail.png) |
| Ordinary narrow | [Landing](release-screenshots/ordinary-narrow-landing.png) | [Card](release-screenshots/ordinary-narrow-complete-card.png) | [Detail](release-screenshots/ordinary-narrow-assistance-detail.png) |
| Review desktop | [Landing](release-screenshots/review-desktop-landing.png) | [Card](release-screenshots/review-desktop-complete-card.png) | [Detail](release-screenshots/review-desktop-assistance-detail.png) |
| Review mobile | [Landing](release-screenshots/review-mobile-landing.png) | [Card](release-screenshots/review-mobile-complete-card.png) | [Detail](release-screenshots/review-mobile-assistance-detail.png) |
| Review narrow | [Landing](release-screenshots/review-narrow-landing.png) | [Card](release-screenshots/review-narrow-complete-card.png) | [Detail](release-screenshots/review-narrow-assistance-detail.png) |

## Proposed deployment and code-only rollback — not executed

This is a frontend code release proposal requiring separate authorization to merge/deploy. No database migration, artifact publication, activation, registry-root change, backend deployment, environment change or blue operation is part of it.

1. Read PR191's current full head SHA and exact-head CI; require that it equals the release-reviewed SHA in the PR body, is mergeable and has passing checks. Recheck the diff and current public API source hashes. Stop if either changed: do not edit published sources or bypass a stale-card guard to force compatibility.
2. Immediately before an authorized release, record the current Vercel production deployment ID, URL and source SHA and confirm the production alias target. The latest successful GitHub-recorded Production deployment checked during this task is **6464088671**, source **`a27b5f12fb13ce261ab829ac1e8b3833b6beba45`**, completed September 15, 2026 at 16:59:53 UTC: `https://political-fingerprint-bpwm7lalx-dhart54s-projects.vercel.app`. Treat this as the identified rollback candidate; reverify the actual alias and whether a newer deployment exists at release time.
3. Verify the existing Vercel project `political-fingerprint`, frontend root `frontend`, production branch `main`, and built `NEXT_PUBLIC_API_BASE_URL=https://political-fingerprint.onrender.com`. Keep `NEXT_PUBLIC_EDITORIAL_PRESENTATION_PREVIEW`, local fixture flags and `ENABLE_RECORD_CARD_REVIEW` unset. This is a verification step, not permission to alter configuration. Resolve any discrepancy before release.
4. Only after explicit merge/deployment authorization, merge the exact reviewed PR191 head through the existing repository flow and record the resulting main commit. Let the existing Vercel main-branch build/deployment run. Keep branch deployment suppression in `frontend/vercel.json`; do not deploy this draft branch or use a manual activation path. Do not call a Render hook or touch source registries/data.
5. Confirm Vercel's successful deployment source matches that resulting main commit and the production alias serves it. On `https://political-fingerprint.vercel.app`, verify the ordinary representative route for the four member/scope cases above, all six entries and the immediately opened full assistance explanation, eight receipts, Education's pair, full record, refresh/history/return/focus. Verify no review API request or eager ledger fetch occurs on landing, and both `/review/record-card` and `/api/review/record-card` return 404. Reconfirm the API remains healthy and source identities unchanged. Simulated failure/staleness checks remain local; do not perturb production data.
6. If frontend verification fails, use Vercel's existing **Instant Rollback** for this same frontend project to restore the verified pre-release deployment recorded in step 2 (the identified candidate is the URL/SHA above), and verify the production alias and ordinary summary/receipt journey. This changes frontend code routing only. If rollback tooling is unavailable, create a reviewed revert PR for PR191's merge commit (`git revert -m 1 <merge-commit>` for a merge commit; `git revert <squash-commit>` for a squash), then merge/redeploy through the same authorized main flow. Do not execute both mechanisms blindly; record which source is serving. Reverting the entire frontend release restores the previous code, with no database, artifact, registry, environment or blue rollback.

Branch push safeguards are retained: this branch's Vercel Git deployments are disabled, and the Render workflow is main-only with backend/workflow path filters. The task has not merged, deployed, published, activated or written production state. No material implementation blocker remains; final exact-head CI is the remaining delivery gate until its completed result is attached to the PR.
