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

## Revised candidate and before/after copy

This bounded revision continues draft PR #191 from reviewed head `783662d1254be23cde8f08993d43d8719679d5d8`. The same six findings remain after reconsidering all 28 available items; six is an outcome, not a target or a section quota.

The heading now immediately says **Selected findings - Reviewed coverage in 4 of 8 issues.** The recorded-vote scope remains distinct from the findings' 119th-Congress scope. The third section is **Mixed choices**. Links say **See the votes** or **Compare the proposals**, with the specific finding in every accessible name. Detail receipt links say **See N House votes**.

[Complete before/after wording](wording_changes.md) compares every headline, explanation and evidence label with the exact reviewed head. These are proposed source-bound wording changes, not automatically accepted public copy.

| Section | Headline | Proposed explanation | Evidence |
|---|---|---|---|
| Supported | Two terrorism-preparedness requirements | One required a cold-weather response exercise; the other required an assessment of vehicular-terrorism threats. | Based on 2 House votes |
| Supported | Removing U.S. forces from specified hostilities | Nine country-specific War Powers resolutions covered hostilities involving Iran, Lebanon and Venezuela; their wording and timing differed. | Based on 9 House votes |
| Opposed | Overturning two California vehicle-emissions waivers | The EPA waivers let California apply its own vehicle-emissions standards: the Omnibus Low NOX regulation and Advanced Clean Cars II. The resolutions would overturn those permissions; these votes do not show support for every part of either rule. | Based on 2 House votes |
| Opposed | Replacing or repealing specific D.C. public-safety rules | The reviewed proposals concerned youth cases, police bargaining and pursuits, pretrial detention, and policing reforms. | Based on 6 House votes |
| Mixed choices | College foreign-gift reporting: replacement supported, final package opposed | She supported an amendment to replace the bill's text with reporting thresholds, searchable disclosures, some exclusions, and fines or compliance plans. She then opposed the broader final H.R. 1048 package, which also restricted contracts. The final vote does not identify which part she opposed. | Based on 2 House votes · 1 legislative episode |
| Mixed choices | Security assistance differed by country and proposal | Ukraine: Opposed three aid restrictions with different scopes; supported a measure authorizing support for Ukraine. That whole measure also covered other purposes, so the vote does not isolate every provision.<br><br>Jordan: Opposed two proposals to cut or restrict assistance, affecting different accounts through different mechanisms.<br><br>Taiwan: Opposed removing funding for the Taiwan Security Cooperation Initiative.<br><br>Israel: Supported an amendment barring funds in the bill from being used for Israel. The same amendment reduced the Foreign Military Financing account by $3.3 billion.<br><br>The Israel and Taiwan amendments are individual choices, not recurring country patterns. These choices do not establish one uniform position on assistance across countries. | Based on 8 House votes |

The assistance contrast is one entry with parallel country paragraphs. All four countries and directions remain. Ukraine retains differing restriction scopes and the whole-measure limitation; Jordan retains different accounts/mechanisms. Israel's bill-specific prohibition and the account-wide $3.3 billion Foreign Military Financing reduction are separate sentences. The single-amendment limits and lack of a uniform cross-country position remain visible. The shorter preparedness heading names the category once; its explanation distinguishes exercise from assessment. No text size was reduced.

## Education direction trace and selection reconsideration

[education_direction_review.json](education_direction_review.json) binds both exact published wording objects to their accepted M14D semantic records, accepted M14F wording, and M14G human display authority by identity, complete action set and hashes:

| Published finding | Exact accepted semantic reference | Typed meaning | Card representation |
|---|---|---|---|
| `m14f:pattern:china_linked_education_funding` | `m14d:covered_china_linked_funding_exclusions` | opposition | Deliberately directionless presentation; no override |
| `m14f:pattern:collective_bargaining_continuity` | `m14d:continuity_of_collective_bargaining` | support | Deliberately directionless presentation; no override |

The absence is not an unavailable analytical meaning. M14F's existing compiler (`backend/app/semantic_ir/accepted_findings_public_wording.py`, behavioral direction display contract) explicitly requires `direction_display=null` for non-mixed behavioral findings. M14G maps that value to `direction=null` and `show_direction=false`, validates both patterns remain directionless, and its human `accept_as_rendered` authority explicitly records `directionless_repeated_patterns: 2`. This is evidence of a deliberate presentation restriction, not an accidental dropped field. Placing either under Supported/Opposed would override that restriction; this revision does not do so. Their exact typed semantics are visible to reviewers in the inventory, without parsing prose, titles or raw votes or modifying immutable payloads.

That leaves an honest representation limitation for these two items in the existing directional card. The funding pattern is distinct from the selected reporting episode and necessary context for any broader foreign-influence claim. Bargaining is an independent finding. Neither is rejected as weak evidence or mislabeled as overlapping H.R.1048. The card makes no domain-wide claim, and both remain accessible in the full issue view.

Every item was reconsidered using the same established considerations: exact policy object, distinct information and actual action overlap, necessary contextual pairing and qualifications, faithful representation, and reading cost. The [item-specific inventory](inventory.md) distinguishes **actual overlap**, **necessary contextual pairing**, **representation limitation**, and **limited space**. Distinct appliance, BLM, firearm, fraud, HALT and National Security omissions each explain what they would add and the particular space tradeoff. No ranking model, fixed entry count, direction quota or issue quota is introduced. The selected findings do not become an overall political verdict.

## Sources and temporal coverage

[candidate.json](candidate.json) retains exact published finding hashes, full action lists, supplied episode identities and per-scope presentation hashes. Its `wording_source_bindings` explicitly map the California explanation to the two existing governed receipt projections (H.J.Res.89 and H.J.Res.88: waivers of preemption for Omnibus Low NOX and Advanced Clean Cars II). The prose explains those permissions; it does not infer support for the underlying rules. Assistance qualification bindings resolve to the four accepted country components, all contained in the selected eight-action finding.

[inventory.json](inventory.json) retains all 28 presentation items, including overlapping syntheses/components, full accepted wording, scope, limitations and explicit episode bindings. They are not 28 independent corroborating observations. The six entries use 29 distinct actions; there is no public evidence score. Shared preparedness actions appear once, and all country assistance choices remain together.

| Issue | Current published root | Precise cutoff in bound review scope |
|---|---|---|
| Education & Workforce | 245 | Unspecified |
| Environment & Energy | 239 | Unspecified |
| Justice & Public Safety | 251 | Unspecified: source refers to a review cutoff without giving its date |
| National Security & Foreign Policy | 248 | **July 23, 2026**, explicit in `scope_boundary` |

Known and unspecified cutoffs are carried in explicit per-issue, per-requested-scope metadata. The `119` and `all` boundaries have separate source text/hash bindings because `all` adds a 119th-Congress limitation. The detailed scope list below the card preserves all four states. No common cutoff is invented. Snapshot capture, card generation, ledger windows and maximum vote dates are not evidence-coverage dates.

The source remains the verified `m15b_green_activation_execution/after-justice-live.json.gz` and its paired audit. All four active root content hashes are unchanged in the candidate. Inner legacy provenance remains lineage; no superseded National Security trajectory or historical generator is restored. Published payloads are immutable and unchanged.

## Complete journey and rendered evidence

[Desktop landing](screenshots/desktop-landing.png) · [Desktop full journey](screenshots/desktop-complete-journey.png) · [Mobile landing](screenshots/mobile-landing.png) · [Mobile full journey](screenshots/mobile-complete-journey.png) · [Narrow mobile](screenshots/narrow-landing.png) and [complete narrow journey](screenshots/narrow-complete-journey.png). [Expanded desktop coverage](screenshots/desktop-coverage-details.png) and [expanded mobile coverage](screenshots/mobile-coverage-details.png) show the known versus unspecified cutoffs.

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

Revision validation includes exact Education lineage and restriction checks, waiver/country context mappings, per-scope cutoff bindings and mismatch rejection. An initial narrow-mobile check found the first link at the 800px screen edge; eight pixels of spacing above the sections were removed on mobile, preserving text sizes and all qualifications. The existing navigation, full-record, history, focus, member/scope, source, mixed-finding and failure tests remain.


- `node --test lib/*.test.mjs` from `frontend`: **166 passed**.
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

The generator reads only exact named committed inputs. It never writes source artifacts, registries or databases. The generated text outputs are candidate JSON, the JSON/Markdown inventory and the Education direction trace; all are review-packet artifacts. The browser receives only requested snapshot API responses; it makes no eager evidence-ledger requests on representative landing.

Before push, repository workflows and GitHub deployments were inspected read-only: Render's deploy hook is main-only, and Vercel follows main for production. This branch adds the same narrowly scoped Vercel Git deployment suppression already used for PR190. No hosted preview or live setting change is needed. The public selector, backend code, published source snapshots and publication contracts are unchanged. Original working-tree edits and protected archives remain untouched.

No unresolved implementation/product decision blocks this candidate. The selection, wording and the documented Education representation limitation remain for the requested product review; no public-copy acceptance or operational authority is implied.
