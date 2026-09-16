# Record at a glance V1

## Intent and outcome
Build a functioning, compact representative opening using explicitly selected accepted findings. Selection and shortened copy remain candidates in a disabled-by-default, local review journey. Deliver screenshots, source/omission inventory, focused validation and one draft PR.

## Baseline and boundaries
Verified origin/main `a27b5f12fb13ce261ab829ac1e8b3833b6beba45` on 2026-09-16 UTC; no delta from requested main. Isolated branch `codex/record-at-a-glance-v1` in `.w/record-card`. Original tracked edits and protected files remain outside this checkout.

Read interpretation principles and frontend, editorial, rendered-validation and PR contracts. Use the verified post-M15B green public snapshot already committed on main: roots Education 245, Environment 239, National Security 248, Justice 251. Inner legacy provenance is lineage, not the current publication identity.

In scope: explicit candidate projection, original journey integration, scoped request-state correction, finding/receipt history and focus, offline lazy evidence preview, tests, review packet. Expected roughly 15–22 code/test/document files plus screenshots; frontend/API/editorial regressions and required existing exact-head CI. No migration, new interpretation, ranking, publication authority, production access/write, merge or deployment. Candidate approval is not a build gate.

## Sequence and definition of done
- [x] Inspect baseline, journey, accepted inputs and review boundary.
- [x] Inventory every current reviewed finding; document selection and material omissions.
- [x] Implement isolated candidate and lazy full journey; distinguish failure/empty/mismatch/incomplete/loading states.
- [x] Verify exact source/action/scope bindings, mixed choices, no inflated accounting, navigation and switching.
- [x] Render desktop 1440×900, mobile 390×844 and 360×800; inspect actual screenshots.
- [x] Run relevant local regressions/build; inspect final diff.
- [x] Consolidate wording, source inventory, screenshots, reproduction and results.
- Draft PR and existing exact-head CI: final delivery records immutable head/run results after this review-packet commit.

## Decisions and discoveries
The public presentation fetch currently catches failure as an empty successful response. Fix within this path. Existing per-issue evidence loading remains lazy. No raw vote interpretation is permitted. Where a source lacks typed direction, retain its absence; do not parse prose to assign a section. Use source-supplied direction or typed semantic-lineage direction only in explicit selection validation.

## Progress / corrections / validation
Implemented six explicitly selected findings from 28 current presentation items across four domains, with 29 unique supporting actions and no overall evidence score. Source receipt episode bindings are retained without inferring absent item-level counts. The review route uses the existing journey and lazily serves exact public snapshot responses through a local opt-in API.

163 frontend unit tests and 150 focused API/editorial/receipt/M15B tests passed. Production build passed with eight pre-existing lint warnings. The production-mode browser regression suite passed 47 tests with one optional historical screenshot capture skipped; the final nine candidate tests and requested screenshots passed separately after rendered review corrections. Both candidate page and API returned actual HTTP 404 without the server flag. Vercel is excluded by a tested server gate. Projection drift and whitespace checks passed.

Corrections: an initial new test confused 17 reviewed Education actions with its 25-action full ledger; the test now asserts both counts and eight additional actions. A full-page screenshot replaced an oversized element capture where the sticky header obscured content. The finding view no longer repeats full-ledger coverage above its targeted finding. The PowerShell npm wrapper dropped start flags; documented preview instructions use the direct Next Node executable. Existing fixture tests require frontend cwd; rerunning there passed all 163. No tests or contracts were weakened.

## Production and rollback
No production operations. Review route requires an explicit server flag and rejects Vercel production. Suppress this branch's Git-triggered Vercel deployment before push, following existing branch suppression. Render deployment workflow triggers only main. Rollback is removal of the isolated candidate changes; source snapshots/published artifacts remain immutable.

## Blockers and final reconciliation
Local definition of done is satisfied; draft PR and required existing exact-head CI remain the final delivery gates. No unresolved implementation or product decision blocks this candidate. Selection and shortened wording require product review before any separately authorized publication. No production writes or live configuration changes occurred. Full review packet: `docs/review_packets/record_at_a_glance_v1/README.md`.
