# Evidence Depth and Coverage Expansion Plan

Date: 2026-06-05

Branch: `codex/evidence-depth-coverage-expansion-plan`

Base commit: `d04a03ead0c556f8ef168c4628bb858d0251ac3a`

Scope: research and planning only. No product code, UI behavior, ingestion, database writes, local launch scripts, or PR creation are included.

## Executive Recommendation

The next milestone should be source enrichment, not UI refinement or broad coverage expansion.

The readiness-first profile scaffold is now doing the right product job: it tells voters where the reviewed evidence is strongest and keeps weak sections cautious. The remaining value gap is that too many rows are visible without enough source-grounded bill or amendment context to explain what the vote practically meant.

The first implementation should be a bounded Congress.gov enrichment and packet-quality pass for high-impact insufficient rows, starting with House National Security & Foreign Policy defense authorization amendment rows and adjacent floor/procedural rows. This uses source infrastructure already present in the repo, keeps the work deterministic, and attacks the largest weak bucket without pretending the UI can fix missing evidence.

## Stage 1 - Current Data Audit

Read-only data source: local database through the current backend schema and evidence joins. The counts below are evidence-row counts unless explicitly marked as distinct roll calls. Evidence rows are what voters experience on representative profiles because one roll call appears once per relevant official/member vote.

### Top-Level Coverage

| Metric | Count |
|---|---:|
| Officials loaded | 548 |
| Roll calls loaded | 419 |
| Eligible roll calls | 74 |
| Distinct interpreted roll calls | 31 |
| Total profile evidence rows | 26,763 |
| Interpreted vote rows | 10,084 |

The product has broad official coverage but shallow interpreted roll-call coverage. The apparent volume comes mostly from repeating a small number of loaded roll calls across many officials.

### Domain Coverage

| Domain | Total rows | Distinct roll calls | Interpreted rows | Counted Yes/No rows | Ambiguous | Insufficient | Limited total | Not voting | Facets |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| National Security & Foreign Policy | 9,988 | 26 | 1,265 | 1,236 | 1,294 | 7,429 | 8,723 | 166 | 6 |
| Justice & Public Safety | 5,721 | 14 | 2,696 | 2,625 | 432 | 2,593 | 3,025 | 153 | 7 |
| Economy & Taxes | 4,297 | 13 | 3,427 | 3,359 | 870 | 0 | 870 | 89 | 11 |
| Education & Workforce | 2,594 | 6 | 1,298 | 1,257 | 0 | 1,296 | 1,296 | 76 | 5 |
| Health & Social Services | 1,732 | 4 | 433 | 416 | 0 | 1,299 | 1,299 | 60 | 3 |
| Environment & Energy | 1,299 | 3 | 433 | 397 | 0 | 866 | 866 | 48 | 2 |
| Infrastructure, Tech & Transportation | 700 | 7 | 100 | 97 | 600 | 0 | 600 | 22 | 2 |
| Immigration & Border Policy | 432 | 1 | 432 | 418 | 0 | 0 | 0 | 14 | 1 |

### Slice-Level Shape

| Slice metric | Count |
|---|---:|
| Official/domain slices with rows | 3,457 |
| Slices with 10+ evidence rows | 868 |
| Slices with 20+ evidence rows | 430 |
| Slices with 3+ counted interpreted Yes/No rows | 1,457 |
| Slices with 10+ rows and at least 60% limited/ambiguous/insufficient | 437 |

### Domains With Enough Rows But Weak Interpretation Quality

- National Security & Foreign Policy: 9,988 rows, but 8,723 limited/ambiguous/insufficient rows. The dominant weak bucket is defense authorization amendments.
- Justice & Public Safety: 5,721 rows and useful interpreted rows, but 3,025 limited rows, mostly procedural `house_of_representatives` rows.
- Health & Social Services: 1,732 rows, but 1,299 insufficient rows, mostly floor rules and one source-thin premium-assistance bill.
- Education & Workforce: 2,594 rows, but 1,296 insufficient rows, mostly floor-rule or censure/procedure rows.
- Infrastructure, Tech & Transportation: 700 rows, with 600 ambiguous rows around hydrogen vehicle rule procedure.

### Domains Where More Roll Calls Are Needed

- Immigration & Border Policy has one distinct eligible roll call. It can show one source-backed example but cannot support a durable issue read.
- Environment & Energy has three distinct eligible roll calls. The single interpreted measure is useful, but two floor-rule rows dominate the limited share.
- Health & Social Services has four distinct eligible roll calls and needs both more substantive votes and better source context.
- Infrastructure, Tech & Transportation has seven distinct eligible roll calls, but most are around one procedural/regulatory package.

### Domains Where Better Source Context Matters More Than More Rows

- National Security & Foreign Policy: already has 26 eligible roll calls and many 20+ row slices, but amendment/procedure context is weak.
- Justice & Public Safety: enough interpreted examples exist; the gap is procedural/floor-rule explanation and filtering/caveating, not raw volume.
- Economy & Taxes: strong gold-slice pattern exists; remaining ambiguous appropriations amendment and conference-instruction rows need precise amendment/instruction text rather than more generic roll calls.

### Domains Already Strong Enough For Useful Issue Reads

- Economy & Taxes for House members with the current gold-slice-like rows.
- Justice & Public Safety for slices with at least three interpreted Yes/No rows and limited rows caveated.
- Immigration & Border Policy only as a narrow single-measure read, not a broad issue read.

## Stage 2 - Evidence Value Gap

The app still feels scroll-heavy because the number of visible cards is larger than the number of source-grounded civic takeaways.

### Space That Does Not Add Enough Voter Value Yet

- Large limited National Security sections: many defense authorization amendments are visible but cannot yet explain the practical amendment effect.
- Repeated floor-rule rows: rules, previous-question votes, concurrence steps, and motions occupy card space while often saying only that the source does not explain the practical policy effect.
- Details-heavy cards on weak rows: progressive disclosure helps, but if the default-visible sentence is "limited context" over and over, the user learns more about the data limit than the issue.
- Drift/comparison/fingerprint surfaces are not wrong, but they can feel less valuable than evidence cards when the opened issue lacks concrete bill meaning.

### Where Issue Summaries Are Strong

- Valerie Foushee / Economy & Taxes: names actual measure groups before voting pattern, includes not-voting and limited caveats, and avoids broad tax ideology claims.
- Valerie Foushee / Justice & Public Safety: generic overview now uses domain-aware language and summarizes concrete public-safety/legal-policy questions.
- Other Economy slices with the same mapped facets can likely work if readiness remains sample-bound.

### Where Issue Summaries Are Thin

- National Security & Foreign Policy: the overview correctly says limited evidence, but that is not enough voter value for a high-volume section.
- Health/Education/Environment: some interpreted final-passage rows are understandable, but source-thin floor-rule rows drag the section into "not enough to summarize" or cautious-read territory.
- Infrastructure: repeated procedural rows around the same measure produce bulk without a strong issue read.

### Rows Visible But Not Meaningfully Interpretable

- Defense authorization amendments: 7,429 insufficient rows, 17 distinct roll calls, all missing source_basis and bill_summary in the current evidence rows.
- Procedural/floor-rule rows across Education, Health, Environment, Justice, and National Security.
- Motion to commit and motion to instruct rows where source text identifies the action but not the exact practical change.
- En bloc amendments where the official row does not tell the user what provisions were included.

### UI Elements That Should Wait

- Further card shrinking should wait; reducing height will not create value if the card has no practical interpretation.
- Demoting or reframing drift can wait; the bigger blocker is evidence depth.
- More grouped evidence UI can wait unless it is tied to enriched bill/package context.
- More visual hierarchy around caveats can wait; caveats are already doing their job.

### Is The Current Readiness-First Scaffold Sufficient?

Yes. The scaffold is sufficient for the next data milestone because it already prevents weak slices from sounding overconfident. It can absorb enriched rows by moving sections from limited toward mixed/strong evidence, without needing another broad UI pass first.

## Stage 3 - Insufficient-Evidence Root Causes

### Largest Weak Buckets

| Domain | Bucket | Status | Vote type | Rows | Primary root cause |
|---|---|---|---|---:|---|
| National Security & Foreign Policy | Defense authorization amendment | insufficient | amendment | 7,429 | Missing amendment-level source basis and bill summary in evidence rows |
| Justice & Public Safety | house_of_representatives | insufficient | concurrence/rule/motion | 2,593 | Procedural rows identify House action but not practical policy effect |
| Environment & Energy | floor_rule_for_energy_and_budget_measures | insufficient | concurrence | 866 | Floor-rule/procedural context, missing source basis and bill summary |
| Health & Social Services | floor_rule_for_multiple_bills | insufficient | motion/rule | 866 | Multi-bill floor rule without source-grounded per-bill practical effect |
| Infrastructure, Tech & Transportation | floor_procedure_on_hydrogen_vehicle_rule | ambiguous | motion | 600 | Procedure around a regulatory disapproval package, not enough practical action text |
| Economy & Taxes | appropriations amendment | ambiguous | amendment | 438 | En bloc amendment lacks exact practical change |
| National Security & Foreign Policy | Motion to commit | ambiguous | motion | 433 | Procedural action cannot be collapsed into final policy |
| Economy & Taxes | conference instruction | ambiguous | motion | 432 | Instruction text not present enough to explain exact effect |

### Root Cause By Dimension

Vote type:
- Final passage is often interpretable with Congress.gov summaries/actions and roll-call context.
- Amendments and en bloc amendments are the largest source of weak rows.
- Floor rules, previous-question votes, and motions are correctly conservative but occupy a lot of screen space.
- Concurrence/conference-instruction rows need lifecycle/action context and sometimes exact instruction text.

Issue domain:
- National Security is not weak because voters do not care about it. It is weak because NDAA/defense-package rows are amendment-heavy.
- Justice has useful final-passage public-safety bills plus many procedural rows.
- Economy is strong because its gold slice has bill summaries, lifecycle context, and reviewed measure labels.

Source basis availability:
- Interpreted rows have strong source_url/source_basis/vote_context coverage.
- Limited rows often lack source_basis entirely, especially National Security amendments, floor rules, and infrastructure procedure rows.

Missing bill summary:
- Limited rows frequently have no bill summary in the evidence row even when a bill reference exists.
- Current local cache has 233 Congress.gov bill-detail files but only 35 summary/subject files and 25 action/text/amendment/committee companion files.

Missing amendment purpose:
- The largest single issue is not "no bill exists"; it is that the row needs amendment-specific source context. A defense authorization bill summary does not explain each amendment.

Procedural/floor-rule ambiguity:
- Procedure can be explained, but procedure should not become a claim about final policy. The product is correctly cautious here.

Not-voting status:
- Not voting rows are a smaller blocker numerically. They must remain explanatory only and not counted.

Lack of vote_context:
- Vote_context is not the main blocker. For interpreted rows, final_result, vote_margin, party totals, and context source list are complete. Member party/outcome booleans are present for about 96-97%.

Repeated rows around the same bill/package:
- Repeated groups are real: 7,861 National Security evidence rows cluster around `119:hr:3838`, with 18 roll calls and 7,429 limited rows.
- Grouping helps scanability, but source enrichment is needed to make those groups useful.

Source text that describes action but not practical effect:
- This is common for rules, motions, and amendment rows. The correct product behavior is to keep those rows visible but limited until richer official context is available.

### Main Blocker

The main blocker is a combination of not enough source context and too many procedural/amendment rows. It is not primarily weak UI. It is not primarily weak grouping. It is not primarily a lack of party/outcome context.

The practical order is:

1. Source enrichment for bill/actions/amendments/text on bounded high-value slices.
2. Human-reviewed or deterministic packet updates that can promote some rows while leaving truly procedural rows limited.
3. Then UI/grouping refinements around the improved evidence.

## Stage 4 - Source-Enrichment Opportunities

| Source type | Expected value | Complexity | Maintenance | Coverage improvement | Best helps | Reliability | Access shape | First implementation fit |
|---|---|---|---|---|---|---|---|---|
| Congress.gov bill summaries/actions | High | Low-medium | Low | High for final passage, CRs, appropriations, CRA, bill lifecycle | Final passage, appropriations, CRs, CRA, shutdown packages | High official source | API | Yes |
| Congress.gov bill text | Medium-high | Medium | Medium | Medium for exact statutory levers, high when summaries are absent | Final passage, CRA, appropriations, authorization | High official source | API metadata plus linked text | Yes, but after summaries/actions |
| Congress.gov amendment records | High | Medium | Medium | High for amendment-heavy domains if amendment records map cleanly | Amendments, NDAA, en bloc packets | High official source | API | Strong second step |
| House Clerk roll-call pages/XML | Medium | Already present | Low | Low for bill meaning, high for vote context | Roll result, member vote, chamber consistency | High official source | XML/page | Already used |
| Senate roll-call/XML data | Medium | Already present | Low | Low for bill meaning, high for Senate context | Senate roll result/member vote | High official source | XML | Already used |
| Amendment text | High | Medium-high | Medium-high | High for amendment purpose, especially NDAA | Amendments, en bloc, motions tied to amendment text | High when official text found | API or linked text | Good after amendment metadata |
| House Rules Committee pages | High for floor rules | Medium-high | Medium-high | High for floor-rule rows | Rules, previous question, multi-bill floor procedure | Official but scrape-like | Mostly scrape-like | Not first |
| Committee reports | Medium-high | Medium | Medium | Medium for complex bills and authorizations | NDAA, appropriations, authorizations | Official | Congress/GovInfo links | Later |
| CBO/JCT estimates | Medium | Medium | Low-medium | Targeted value for fiscal/tax/budget impact | Reconciliation, tax, appropriations, health finance | Official/authoritative | Congress.gov links and source pages | Later targeted |
| CRS reports | Medium | Medium-high | Medium | Useful background, uneven bill mapping | Complex policy background | Authoritative but not always direct vote source | Search/link-dependent | Not first |
| GovInfo bill text | Medium-high | Medium | Medium | Good for official text redundancy and PDFs | Bill text, conference reports, appropriations docs | High official source | API/files | Later |
| Bill text diffs | Medium | High | High | Narrow value for amendments/substitutes | Amendments, substitute texts | Depends on source mapping | Requires parsing/comparison | Not first |
| Appropriations summaries/explanatory statements | High | High | High | High for appropriations rows | Appropriations packages, committee/explanatory statements | Official when sourced | Mixed links/PDFs | Later targeted |

### Specific Gaps Closed

- Congress.gov summaries/actions close the "what was the bill and where was it in the lifecycle" gap.
- Amendment records/text close the largest current weak bucket: defense authorization amendments.
- House Rules Committee pages close the floor-rule gap, but at higher scrape/maintenance risk.
- Committee reports and explanatory statements help appropriations/NDAA substance, but should not be first because they are harder to automate safely.

## Stage 5 - Vote Types Needing Enrichment

| Vote type | Safe with current sources? | Additional source that helps | Should remain limited when | Readiness-first representation | First implementation candidate? |
|---|---|---|---|---|---|
| Final passage | Usually yes when bill summary/action exists | Congress.gov summaries/actions/text | Summary is absent or title is too vague | Strong or mixed if 3+ counted rows | Yes |
| Amendments | Often no | Congress.gov amendment records and amendment text | Amendment text/purpose unavailable or en bloc package unclear | Limited unless amendment effect is source-grounded | Yes, bounded to one package |
| En bloc amendments | Usually no | Amendment text, Rules Committee materials, Congressional Record if needed | The en bloc contents cannot be tied to practical effect | Limited-context rows grouped around package | Not first unless source is obvious |
| Floor rules | Usually no for policy meaning | House Rules Committee rule text/report | The row only sets consideration terms | Procedural/limited, not policy pattern | Later |
| Motion to recommit | Usually no | Motion text, bill action/context | Motion text is absent | Procedural/limited unless exact motion effect known | Later |
| Motion to instruct conferees | Usually no | Motion/instruction text, conference action context | Instruction text absent | Limited-context procedural row | Later |
| Appropriations packages | Often yes for final passage | Congress.gov summaries/actions, committee reports, explanatory statements | Amendment/instruction details absent | Strong for final passage, limited for amendments | Yes for final passage |
| Authorization/NDAA | Final passage yes, amendments no | Congress.gov summary/actions/amendments/text, committee report | Amendment-specific effect unavailable | Mixed: final passage interpreted, amendments limited | Yes, bounded |
| Continuing resolutions/shutdown packages | Often yes | Congress.gov summaries/actions, public-law status | Lifecycle/enactment status unsupported | Strong if final passage/lifecycle supported | Yes |
| CRA disapproval resolutions | Usually yes | Congress.gov summary/text, Federal Register rule reference | Underlying rule cannot be identified | Strong if rule and disapproval effect are clear | Good later |
| Nominations | Not central now | Senate nomination records | Policy issue meaning is not source-grounded | Separate confirmation evidence, not issue pattern | No for this milestone |
| Foreign military sales/privileged resolutions | Somewhat | Senate/House resolution text, arms-sale notice context | Sale specifics or disapproval mechanism unclear | Limited or narrow interpreted read | Later after chamber integrity review |

## Stage 6 - Coverage Expansion Strategy

### Congress/Session Range

Prioritize the current 119th Congress and the existing 730-day product window. Do not expand backward yet. The product does not need more old votes; it needs clearer source-grounded reads inside the current accountability window.

### Improve Interpretation Inside Current Window First

Improve the interpretation quality of loaded roll calls before broadening. Current loaded data already creates 868 slices with 10+ rows and 430 slices with 20+ rows. Adding more rows before enrichment would make the profile longer without making it more useful.

### House vs Senate

Prioritize House first for the first implementation:

- The current high-volume weak buckets are heavily House-based.
- Valerie gold/generalization slices are House-based and already validated.
- House Clerk roll-call ingestion and current profile patterns are more mature for this product pass.

Senate should be improved later, especially once chamber filtering/data-integrity checks are fully resolved and Senate-specific vote types are treated separately.

### Current Officials Only

Prioritize current officials. Candidate/race expansion should wait; it would add lower-confidence stated-position work before the recorded-vote product has enough value.

### Domain Priority

Balance high user value and high data readiness:

1. National Security & Foreign Policy: high user value, high volume, biggest source gap.
2. Health/Education/Environment: high voter value, but many rows are currently source-thin/procedural.
3. Economy/Justice: already good enough for examples; use them as regression baselines, not the next major expansion target.

### Avoid Making UI Longer Without Increasing Value

- Do not add raw roll-call volume unless each added roll call has bill summary/action context and interpretation readiness.
- Prefer improving existing repeated bill/package groups.
- Promote rows only when source context supports practical meaning.
- Keep weak procedural rows grouped and limited rather than expanding their visible text.

## Stage 7 - Evidence-Confidence / Readiness Implications

### Row Promotion Path

Insufficient -> contextual:
- Source identifies the bill/package and vote type, but not enough practical effect for a support/opposition interpretation.
- Card can say what procedural step occurred and why it is limited.

Contextual -> strong:
- Source identifies the practical mechanism, direct stakes, vote lifecycle, and yea/nay meaning.
- Source_basis is populated.
- `what_happened`, `why_it_mattered`, `what_not_to_infer`, `policy_effect`, and `issue_facet` are populated.
- Vote_context confirms member position, party baseline, and outcome context when public copy uses those fields.

### Evidence Required To Promote A Row

- Official source URL.
- Source_basis naming the exact source records used.
- Bill summary or text explaining practical mechanism.
- For amendments: amendment text or official amendment description tied to the roll call.
- For rules/procedure: official rule text or clear procedural source explaining the effect, without converting it into final policy.
- Support/oppose positions only when yea/nay meaning is determinable.

### What Should Never Be Promoted Automatically

- Not-voting rows as support/opposition.
- Procedural rows into final policy votes without source support.
- En bloc amendments without exact included amendments/effects.
- Floor rules into substantive bill positions.
- LLM-drafted text into vote meaning without deterministic stored review/import.

### Protecting Gold-Standard Slices

- Keep Economy and Justice outputs as regression tests.
- Add source enrichment as new source fields/packet context, not as frontend inference.
- Do not change support/opposition counting.
- Do not alter existing interpreted rows unless a review packet proves the change improves source grounding and public copy.

### Issue-Level Readiness Effects

- Strong evidence should increase only when counted interpreted Yes/No rows increase and limited share drops.
- Mixed but interpretable can improve when more measures are source-grounded even if the vote pattern remains mixed.
- Limited evidence should remain when limited rows dominate, even if one or two high-quality interpreted rows exist.
- Not enough to summarize should remain for slices below the counted-row threshold.

### Grouped Evidence Effects

- Enriched repeated groups should show "same bill/package" more clearly.
- Amendment groups should remain limited unless amendment meaning is source-grounded.
- Grouping should expose related rows without changing counts.

### Card Summary Effects

- Enrichment should let generic summaries use `what_happened` and `why_it_mattered` instead of fallback `policy_effect` repetition.
- The best card summaries should still start with recorded vote, explain practical action, state member vote meaning, and add party/outcome context when stored.

## Stage 8 - Ranked Next Milestones

### 1. Bounded Congress.gov Enrichment For High-Impact Weak Rows

Goal: improve packet/source context for the largest weak bucket without broad rollout.

Why first: current source infrastructure already supports Congress.gov enrichment, and National Security defense authorization amendment rows are the largest value gap.

Expected files/modules:
- `backend/app/etl/fetch_sources.py`
- `backend/app/etl/congress_adapter.py`
- `backend/app/etl/manual_interpretations.py`
- `backend/app/etl/live_pipeline.py`
- `backend/tests/test_fetch_sources.py`
- `backend/tests/test_congress_adapter.py`
- `backend/tests/test_manual_interpretations.py`
- review packet under `docs/review_packets/`

Likely tests:
- cache companion payloads merge correctly
- packet export includes enrichment availability for selected bill refs
- no import/promotion occurs automatically
- missing amendment text keeps rows insufficient
- source_basis requirements remain enforced

Success:
- selected National Security packets show bill actions, text versions, amendments, committees, and available summary context
- review packet identifies which rows can be promoted and which remain limited
- no UI or counting behavior changes

Explicitly not included:
- no broad interpretation import
- no LLM interpretation rollout
- no support/opposition count change
- no UI rebuild

### 2. National Security Amendment Review Slice

Goal: use enriched packets to review one high-risk National Security slice and update only source-grounded interpretations where justified.

Why second: review should follow enrichment, not precede it.

Expected files/modules:
- `docs/interpretation_batches/`
- `backend/app/etl/manual_interpretations.py`
- backend API position tests
- frontend overview/card tests for cautious rendering

Likely tests:
- interpreted amendments require source_basis
- unsupported amendments remain insufficient
- readiness remains limited unless counted rows pass threshold

Success:
- one representative/domain packet proves whether NDAA amendment rows can become useful
- rows not supported by source stay limited

Explicitly not included:
- no all-member National Security rollout
- no curated roll-number summaries unless explicitly approved

### 3. House Rules / Floor Procedure Source Strategy

Goal: decide whether House Rules Committee pages can safely explain high-volume procedural rows.

Why third: floor-rule rows are numerous, but source access is more scrape-like and trust risk is higher.

Expected files/modules:
- review packet first
- possible future fetch/parser modules only after approval

Likely tests:
- no procedural row becomes final policy effect
- rule text links are stored as source context only

Success:
- clear decision on whether to enrich floor rules, hide/demote them, or keep them limited

Explicitly not included:
- no production scraper without approval

### 4. Cross-Domain Final-Passage Source Completion

Goal: fill missing Congress.gov summary/action/text context for final-passage interpreted rows in Health, Education, Environment, and Immigration.

Why fourth: these are high voter-value domains, but current distinct roll-call volume is modest.

Expected files/modules:
- same Congress.gov cache/fetch/adapter modules
- review packets for one slice per domain

Likely tests:
- generic card summaries use enriched reviewed fields
- limited rows remain limited

Success:
- more sections move from limited/not-ready into mixed or strong evidence without UI change

Explicitly not included:
- no broad issue rollout without slice review

### 5. Readiness-First UI Compression After Enrichment

Goal: reduce visual density only after evidence improves.

Why later: changing UI now risks making weak evidence look cleaner without becoming more useful.

Expected files/modules:
- `frontend/components/PositionByIssue.js`
- `frontend/components/ProfileQuickRead.js`
- `frontend/lib/issueOverview.mjs`
- frontend tests and screenshots

Likely tests:
- source links remain default-visible
- limited/not-ready status remains clear
- Economy/Justice baselines stable

Success:
- cards are easier to scan because they contain stronger source-backed statements, not because caveats were hidden.

Explicitly not included:
- no alignment logic changes
- no new interpretation data

## Stage 9 - First Implementation Recommendation

### Recommended Build Milestone

Bounded Congress.gov enrichment for National Security defense authorization amendment packets.

### Source

Congress.gov bill detail plus companion subresources already supported by the repo:

- summaries
- subjects
- actions
- text versions
- amendments
- committees
- CBO links when present

### Vote Type

Start with amendment-heavy House defense authorization rows, plus adjacent final-passage/procedural rows only as context. Do not attempt to interpret all floor-rule rows in the same milestone.

### Domain

Primary: National Security & Foreign Policy.

Cross-domain benefit: the same enrichment path helps appropriations, CRA, health, education, and environment final-passage rows later.

### Expected Rows Improved

Immediate target:
- 17 distinct defense authorization amendment roll calls.
- 7,429 evidence rows currently insufficient across officials.

Realistic first-pass outcome:
- not all 7,429 rows become interpreted.
- success is separating rows into:
  - source-grounded interpretable amendments
  - contextual amendment rows
  - still-insufficient rows

### Data Fields To Store Or Populate

Existing fields likely sufficient for first pass:

- `source_basis`
- `what_happened`
- `why_it_mattered`
- `what_not_to_infer`
- `policy_effect`
- `issue_facet`
- `confidence`
- `uncertainty_note`
- `interpretation_reason`

Source-packet context should include:

- bill lifecycle
- actions
- amendments
- text-version metadata
- committees
- CBO cost-estimate links when available
- source URLs for each enrichment item

### Tables Or Modules Likely Involved

Tables:
- `vote_interpretations`
- `roll_calls`
- `bills`
- `vote_contexts`

Modules:
- `backend/app/etl/fetch_sources.py`
- `backend/app/etl/congress_adapter.py`
- `backend/app/etl/manual_interpretations.py`
- `backend/app/etl/live_pipeline.py`
- `backend/app/api/precomputed.py` only if packet/API excerpt shape must expose existing fields more clearly

### Schema Changes

Probably not needed for the first implementation. Existing `source_basis` plus reviewed "so what" fields can store the outcome.

Potential stop point: if interpretation_source_list needs to be first-class in the API/database instead of implicit `source_basis`/packet context, ask before schema migration.

### Tests To Add

- Congress.gov companion cache merge includes summaries, actions, text versions, amendments, and committees.
- Packet export includes enrichment context for selected bill refs.
- Rows with no amendment-specific text remain insufficient.
- Interpreted rows require source_basis and reviewed fields.
- National Security readiness remains limited unless counted interpreted Yes/No rows meet the threshold.
- Economy and Justice approved outputs remain unchanged.

### Review Packet Needed

Create `docs/review_packets/national_security_enrichment_first_pass.md` with:

- selected bill/roll list
- before/after packet context
- rows promoted, contextualized, or kept insufficient
- exact source_basis per promoted row
- rendered overview/card copy for one representative slice
- tests and commands
- explicit statement that counting/alignment logic did not change

### Risks

- Congress.gov amendment metadata may list amendment records without enough text to explain practical policy effect.
- NDAA amendments may require Congressional Record, rule text, or amendment text links beyond the bill subresource.
- The same bill/package can contain many amendments; grouping must not imply all rows share the same substantive effect.
- A broad import could accidentally make weak rows sound strong. Keep first pass bounded and reviewed.

### Approval Stop Points

Codex should stop and ask before:

- database migrations
- source enrichment ingestion into production
- dependency installs
- automated LLM interpretation
- broad import of new interpretations
- changing support/opposition counting
- adding new public claims about a representative
- scraping House Rules Committee or GovInfo pages beyond existing API/cache approach

## Stage 10 - UI Implications

### UI Changes That Should Wait

- Shrinking evidence cards.
- Hiding or reframing drift score.
- Demoting comparison further.
- Moving grouped evidence after overview again.
- Reducing per-card pills/caveats.
- More aggressive progressive disclosure.
- New grouped measure-card layout for all high-volume sections.

These are not the current blocker. The UI is carrying too many limited rows because the data is limited, not because the UI lacks enough polish.

### UI Changes That Might Be Worth Doing Before Enrichment

None are clearly blocking. The current readiness-first ordering, grouped preview, and confidence labels are sufficient for the source-enrichment milestone.

One small exception if it becomes necessary during review: keep high-risk limited sections visually lower priority and prevent them from being the default "start here" target. That behavior already exists after PR #10.

## Stage 11 - Final Recommendation

The next milestone should be source enrichment.

Exact recommended next build milestone:

`National Security Congress.gov enrichment first pass`

Build the smallest deterministic enrichment pass that improves source packets for the defense authorization/NDAA amendment bucket, proves what can and cannot be promoted, and keeps readiness/copy cautious.

Do not work next on:

- broad UI redesign
- more card-density polish
- personalized alignment quiz
- ideology score
- candidate expansion
- broad roll-call backfill
- automated LLM interpretation rollout
- House Rules scraping
- schema migration unless the packet proves it is needed

Broad scaling remains blocked. The blocker is not the readiness-first scaffold; it is uneven evidence depth, especially for amendment and procedural rows.

What would move the product from scoped MVP demo toward public useful MVP:

1. Enrich source packets for high-value current-window votes.
2. Promote only rows with source-grounded practical meaning.
3. Keep unsupported procedural/amendment rows limited.
4. Expand one reviewed slice at a time.
5. Let readiness labels decide what the representative page leads with.

## Commands And Read-Only Queries Run

```text
git branch --show-current
git status --short --branch --untracked-files=all
git log -1 --oneline
rg --files
Get-Content -Raw AGENTS.md
Get-Content -Raw CONSTRAINTS.md
Get-Content -Raw docs/product_direction_readiness_first_profile.md
Get-Content -Raw docs/methodology.md
Get-Content -Raw frontend/lib/issueOverview.mjs
Get-Content -Raw frontend/lib/voteCardSummary.mjs
Get-Content -Raw backend/app/api/positions.py
Get-Content -Raw backend/app/api/precomputed.py
Get-Content -Raw backend/app/etl/manual_interpretations.py
Get-Content -Raw backend/app/etl/vote_context.py
Get-Content -Raw backend/migrations/0001_initial_schema.sql
Get-Content -Raw backend/migrations/0002_vote_interpretations.sql
Get-Content -Raw backend/migrations/0003_vote_interpretation_details.sql
Get-Content -Raw backend/migrations/0008_vote_contexts.sql
Get-Content -Raw backend/migrations/0009_vote_interpretation_so_what_fields.sql
Get-Content -Raw backend/app/etl/fetch_sources.py
Get-Content -Raw backend/app/etl/congress_adapter.py
Get-Content -Raw backend/app/etl/live_pipeline.py
Get-Content -Raw docs/manual_interpretation_workflow.md
Get-Content -Raw docs/review_packets/readiness_first_mvp_profile_pass.md
Get-Content -Raw review_bundle_frontend_data_grounding/data_availability_summary.md
Get-ChildItem -Recurse -File backend/data_sources
rg -n "Defense authorization amendment|source enrichment|Congress.gov|insufficient|appropriations|Rules Committee|CBO|JCT|CRS|GovInfo" docs/review_packets docs/manual_interpretation_workflow.md docs/methodology.md
rg -n "source_basis|what_happened|why_it_mattered|issue_facet|policy_effect|interpretation_status" docs/interpretation_batches -g "*.json"
```

Read-only DB audit:

```text
.\backend\.venv_win\Scripts\python.exe -  # inline script using BEGIN READ ONLY
```

The DB audit queried counts from:

- `legislators`
- `roll_calls`
- `vote_classifications`
- `vote_interpretations`
- `votes_cast`
- `bills`
- `vote_contexts`

No database writes were performed.

## Known Limits Of This Plan

- The DB audit reflects the current local database available to this workspace. Production may differ.
- No web fetching was performed for this planning pass.
- The plan does not validate whether every Congress.gov cached companion file contains the amendment detail needed for promotion.
- The National Security chamber wording issue remains covered by the separate chamber-filtering audit and should be resolved before public reliance on that high-risk slice.
- The plan intentionally avoids recommending automated LLM interpretation as a substitute for source-grounded deterministic records.

