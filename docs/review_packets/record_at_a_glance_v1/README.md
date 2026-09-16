# Record at a Glance V1 — release candidate

[Current release candidate, validation, screenshots and proposed deployment/rollback](release_candidate.md) is the consolidated review packet for PR #191. It continues product-reviewed head `56a35e860783466f6079cba47f6338e2e6a09dab`; the exact new head and completed CI are in the PR body.

The user accepted the six findings, source mappings, item-specific rationale, Education directionless restriction, first five entries, evidence labels and cutoffs. This revision preserves them. Only the requested assistance shortening and immediate-detail relocation change substantive wording. The ordinary representative route now uses the existing live read interfaces; card-specific staleness no longer suppresses valid current issue summaries.

## Open the local replay

From this branch's repository root, in PowerShell:

```powershell
npm ci --prefix frontend
npm run build --prefix frontend
$env:ENABLE_RECORD_CARD_REVIEW = '1'
cd frontend
node node_modules/next/dist/bin/next start --hostname 127.0.0.1 --port 3110
```

Open [Foushee, 119th Congress](http://127.0.0.1:3110/review/record-card?representative=leg_valerie_p_foushee&scope=119), [all available Congresses](http://127.0.0.1:3110/review/record-card?representative=leg_valerie_p_foushee&scope=all), or [Thomas Massie](http://127.0.0.1:3110/review/record-card?representative=leg_thomas_massie&scope=119). This opt-in route explicitly identifies its snapshot replay, uses no live API or database, and remains disabled on Vercel. Without the server flag its page and API return 404.

The ordinary `/` route uses the configured `NEXT_PUBLIC_API_BASE_URL` through the existing profile/positions/editorial/evidence interfaces. It never falls back to the replay snapshot. The committed runtime file contains only reviewed wording and exact source bindings; evidence ledgers are lazy. Do not mistake a localhost API absence for a product no-summary state.

## Accepted source and selection record

- [Candidate and complete action bindings](candidate.json).
- [Item-specific inventory/rationale](inventory.md) and [full source-mapped inventory](inventory.json): all 28 items were assessed on the same established grounds. The bounded six-item outcome is accepted; no fixed section quota or ranking model is introduced.
- [Exact Education direction trace](education_direction_review.json): accepted typed semantics exist, but M14F/M14G deliberately preserve directionless display. No override or new direction is projected.
- [Earlier before/after wording](wording_changes.md): historical comparison of heads `783662d…` and `56a35e8…`, accepted in the current product review. The new assistance-only before/after is in [the release packet](release_candidate.md#bounded-wording-change).
- [Existing execution plan and acceptance record](../../plans/record_at_a_glance_v1.md).

The four source roots remain Education 245, Environment 239, Justice 251 and National Security 248. National Security's explicit July 23, 2026 cutoff remains bound to each requested scope; the other three reviewed issue scopes do not supply precise cutoffs. Snapshot capture/card generation dates are not evidence coverage. Full-record access retains additional recorded actions beyond reviewed findings, including Education's 25 recorded / 17 reviewed / eight additional actions.

## Reproduce focused checks

```powershell
node scripts/build_record_card_review.mjs --check
cd frontend
node --test lib/*.test.mjs
$env:PLAYWRIGHT_PRODUCTION_BUILD = '1'
$env:RECORD_CARD_RELEASE_SCREENSHOT_DIR = '../docs/review_packets/record_at_a_glance_v1/release-screenshots'
npx playwright test tests/record-card-release.spec.mjs tests/record-card.spec.mjs --workers=2
```

[The release packet](release_candidate.md) contains current unit/backend/build/browser results, live read-only compatibility checks, ordinary/review desktop/mobile/narrow captures and exact proposed deployment/rollback steps. Earlier files in `screenshots/` document prior product review; current release captures are in `release-screenshots/`.

No merge, deployment, publication, activation, database write or blue operation is authorized or performed. Selection review and user testing are not reopened. Substantive changes beyond the specified wording remain for review.
