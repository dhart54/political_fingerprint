# Record at a glance V1 — product review candidate

One functioning local candidate for Valerie P. Foushee, using the verified post-M15B published inputs on main `a27b5f12fb13ce261ab829ac1e8b3833b6beba45`. Selection and shorter wording remain pending product review. No publication, database write, deployment, merge, rating, new interpretation, or user study is part of this change.

## Open the working journey

From this branch's repository root, in PowerShell:

```powershell
npm ci --prefix frontend
npm run build --prefix frontend
$env:ENABLE_RECORD_CARD_REVIEW = '1'
cd frontend
node node_modules/next/dist/bin/next start --hostname 127.0.0.1 --port 3110
```

Open [Foushee, 119th Congress](http://127.0.0.1:3110/review/record-card?representative=leg_valerie_p_foushee&scope=119), [all available Congresses](http://127.0.0.1:3110/review/record-card?representative=leg_valerie_p_foushee&scope=all), or [Thomas Massie, no reviewed summary](http://127.0.0.1:3110/review/record-card?representative=leg_thomas_massie&scope=119).

The route and its API return 404 without the server flag. Vercel is explicitly excluded even if the flag is set. The normal `/` route never receives the candidate. No production API or database connection is used by the review journey. The review member picker is deliberately limited to these two identities; their evidence is replayed from their own recorded public responses. All eight issue paths remain accessible. The existing production ZIP/name finder is covered by unchanged regression tests.

## Actual proposed wording

**Record at a glance**

Selected findings from the reviewed voting record.

Findings below: **119th Congress** · Recorded-vote scope: **119th Congress** (or **All available Congresses**, when selected).

| Section | Headline | Explanation | Issue / evidence context |
|---|---|---|---|
| Supported | A terrorism-response exercise and threat assessment | A cold-weather response exercise and an assessment of vehicular-terrorism threats. | Justice & Public Safety · 2 supporting House votes |
| Supported | Removing U.S. forces from specified hostilities | Nine country-specific War Powers resolutions covered hostilities involving Iran, Lebanon and Venezuela; their wording and timing differed. | National Security & Foreign Policy · 9 votes · 9 country-specific resolutions |
| Opposed | Overturning two California vehicle-emissions waivers | The resolutions targeted separate EPA waiver decisions; these votes do not show support for every part of the underlying rules. | Environment & Energy · 2 resolutions · 2 separate decisions |
| Opposed | Replacing or repealing specific D.C. public-safety rules | The reviewed proposals concerned youth cases, police bargaining and pursuits, pretrial detention, and policing reforms. | Justice & Public Safety · 6 supporting House votes |
| Different choices, kept together | College foreign-gift reporting: replacement supported, final package opposed | The replacement set reporting, disclosure and compliance rules; the broader final H.R. 1048 package also restricted contracts, and the final vote does not identify which part she opposed. | Education & Workforce · 1 legislative episode · 2 House votes |
| Different choices, kept together | Security assistance differed by country and proposal | Foushee opposed proposals to restrict aid to Ukraine and Jordan, supported a measure authorizing support for Ukraine, opposed removing Taiwan security-cooperation funding, and supported an amendment barring funds in the bill from being used for Israel and reducing the Foreign Military Financing account by $3.3 billion. | National Security & Foreign Policy · 8 votes across 8 country-specific choices |

Every entry links to **Finding & supporting votes →**. The assistance sentence is unchanged accepted wording; its length preserves the country/account distinctions. Other headlines and shortened sentences are explicitly authored candidates, not runtime truncation of published prose.

Footer: **Reviewed findings available in 4 of 8 issues: Education & Workforce; Environment & Energy; Justice & Public Safety; National Security & Foreign Policy.**

**A selection of specific choices, not a complete statement of priorities. Explore all issues →**

Coverage details explain that no precise review cutoff is supplied. Snapshot capture and card generation timestamps are separately recorded; neither is presented as the evidence cutoff. Selecting `all` never broadens the reviewed findings beyond the 119th Congress.

## Sources, inventory and omissions

[candidate.json](candidate.json) binds every selection to the exact finding/proposition/wording ID, full finding hash, complete action list, supplied episode IDs, limitations and per-scope presentation hash. The [readable inventory](inventory.md) shows inclusions and omissions side by side. [inventory.json](inventory.json) retains **all 28 available presentation findings**, including overlapping syntheses and component findings, original accepted text, explicit receipt-to-episode bindings, scope and qualifications, with inclusion/omission reasons. These are 28 presentation items, not 28 independent corroborating observations.

| Current published root | Issue | Active content SHA256 |
|---|---|---|
| 245 | Education & Workforce | `76d06a43beb51c164a199c576c3d0aa539b6c05da2f8e4eff8fe54845547e4ec` |
| 239 | Environment & Energy | `7389aa33deca20cfa51293beab2b7602b39cb40258f1bca4a9cacf06aa818b53` |
| 251 | Justice & Public Safety | `01f237396226557347cb6a216ad4ae8ea6b20d04fabe084ec3f5cc9732e5545b` |
| 248 | National Security & Foreign Policy | `c675731a2602829f2c1d325673c50099cb3ef458d2ae0bf07b10237019858f29` |

Input: the committed `m15b_green_activation_execution/after-justice-live.json.gz`, byte-verified against its existing manifest. The paired production audit identifies the four active roots. Legacy IDs inside the public payload's `provenance` remain lineage; they are not substituted for current publication identities. The superseded National Security trajectory is absent. No historical presentation generator is restored or rerun.

Selection order is the existing domain order within Supported, Opposed, and the conditional mixed/contrast section. There is no scoring or ranking function. The six entries use 29 distinct supporting actions. That is audit accounting only, not a public evidence score. The preparedness actions shared by Justice and National Security appear once; the War Powers component patterns and broader environmental synthesis are not double-counted.

The selected set omits Education's bargaining and China-linked funding patterns; Environment's appliance/BLM choices; Justice's firearm and fraud-enforcement patterns and mixed HALT episode; and additional National Security choices including FISA, defense-package, military/DoD, AUMF, ICC and Haiti measures. These matter to a comprehensive issue interpretation, which this card does not claim to provide. All remain accessible in the full issue views. Education's two ordinary pattern fields have no typed direction; the candidate does not parse their prose to assign a section. The complete assistance contrast preserves Israel, Ukraine, Jordan and Taiwan together, so the War Powers selection does not imply a uniform stance on foreign involvement. The selected education pair is not split into two independent positions. No omission changes the exact selected policy objects; product review should assess whether this bounded selection creates an unwanted overall impression despite that framing.

## Complete journey and rendered evidence

[Desktop landing](screenshots/desktop-landing.png) · [Desktop full journey](screenshots/desktop-complete-journey.png) · [Mobile landing](screenshots/mobile-landing.png) · [Mobile full journey](screenshots/mobile-complete-journey.png) · [Narrow mobile](screenshots/narrow-landing.png).

[Specific finding](screenshots/mobile-specific-finding.png) → [supporting receipts](screenshots/mobile-supporting-receipts.png) → [complete issue record](screenshots/desktop-complete-record.png).

Browser validation uses the complete existing journey with the real snapshot. At 1440×900, 390×844 and 360×800, a complete substantive finding and its link fit on the initial screen without shrinking text; there is no horizontal scrolling. Support/opposition use the same neutral text and treatment. Full journey captures include the issue grid; no screenshot-only component or politician-wide synthesis is used.

Finding links carry representative, issue, selected scope, exact finding ID and source hash. They open the source finding rather than the top of the issue. The next click reuses the existing exact-action resolver and receipt ledger. Tests resolve every selected action, including both H.R. 1048 actions and all eight assistance choices. Refresh and Back/Forward restore the selected finding/receipt view; Back and the explicit return link restore focus to the originating card entry. The full-record link and existing “Show all” control remove the finding filter. Direct issue and exact receipt anchors still open their destinations. Keyboard activation and reduced motion are exercised.

The Education full record demonstrates honest coverage: **25 recorded actions**, **17 reviewed actions**, **8 additional recorded actions**. The two selected H.R. 1048 actions are neither the whole issue nor independent episodes.

These are implementation and rendered checks, not measured engagement or human usability validation.

## Sparse data and failures

- [Thomas Massie](screenshots/mobile-no-summary.png): his real 119th-Congress snapshot has no eligible reviewed summary; eight issue paths and recorded votes remain available, with no card.
- Foushee `scope=118`: real receipts, no eligible reviewed finding; no card. `all` retains a clearly 119th-bounded card.
- Foushee `119`/`all`: partial domain coverage, four of eight reviewed domains. Missing domain inputs are a distinct incomplete-input state, not “no reviewed findings.”
- [Unavailable presentation response](screenshots/mobile-unavailable.png): a simulated 503 yields an unavailable state with issue paths. Failure is no longer converted into a successful empty result.
- Delayed requests, member/scope mismatches, changed source hashes and incomplete inputs suppress stale or mismatched findings. Perturbation tests do not invent new named-representative claims.

## Verification and safety

- `node --test lib/*.test.mjs` from `frontend`: **163 passed**.
- Focused API, public presentation, governed receipt, public record integrity and M15B semantic regressions: **150 passed**.
- Production build: **passed**; eight existing hook-dependency lint warnings outside touched components remain.
- Production-mode browser suite: **47 passed**, one pre-existing optional Pass A screenshot test skipped because its separate screenshot variable was not requested. Candidate screenshot coverage runs explicitly.
- Offline projection drift check, final diff/whitespace review and all selected-action receipt resolution: **passed**.
- Existing exact-head CI is required on the draft PR; its immutable run/head results are reported in the final PR body and delivery, rather than introducing a new workflow.

Reproduce candidate checks:

```powershell
node scripts/build_record_card_review.mjs --check
cd frontend
node --test lib/*.test.mjs
$env:PLAYWRIGHT_PRODUCTION_BUILD = '1'
$env:RECORD_CARD_SCREENSHOT_DIR = '../docs/review_packets/record_at_a_glance_v1/screenshots'
npx playwright test tests/record-card.spec.mjs --workers=1
```

The generator reads only exact named committed inputs. It never writes source artifacts, registries or databases. Candidate JSON and the JSON/Markdown inventory are the only generated text outputs. The browser receives only requested snapshot API responses; it makes no eager evidence-ledger requests on representative landing.

Before push, repository workflows and GitHub deployments were inspected read-only: Render's deploy hook is main-only, and Vercel follows main for production. This branch adds the same narrowly scoped Vercel Git deployment suppression already used for PR190. No hosted preview or live setting change is needed. The public selector, backend code, published source snapshots and publication contracts are unchanged. Original working-tree edits and protected archives remain untouched.

No unresolved implementation/product decision blocks this candidate. The explicit selection and shortened wording still need the requested product review before any separate publication authorization.
