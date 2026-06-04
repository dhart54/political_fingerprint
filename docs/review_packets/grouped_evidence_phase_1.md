# Grouped Evidence and Repeated-Measure Handling, Phase 1

Scope: frontend-derived grouping metadata for opened evidence rows. This pass does not change backend/API shape, interpretation logic, support/opposition counting, alignment math, curated roll-number summaries, or visible evidence-card UI.

## What Changed

- Added `frontend/lib/evidenceGrouping.mjs`.
- Added `evidenceGrouping` metadata to the derived issue-overview object in `frontend/lib/issueOverview.mjs`.
- Added tests for repeated bill grouping, no broad-facet grouping, count preservation, limited-row exclusion, and high-risk National Security caution.
- Added a targeted methodology note explaining that evidence grouping is presentation metadata only.

Counting/alignment logic changed: no.

## Grouping Approach

Grouping uses existing frontend evidence row fields only:

1. Stable bill/measure identifiers when available:
   - `source_bill_id`
   - `bill_id`
   - `bill_ref`
   - `bill_identifier`
   - `roll_call_bill_id`
   - `roll_call_bill_ref`
   - `bill_congress` + `bill_type` + `bill_number`
   - matching values inside `vote_context`
2. Normalized measure/title text when no identifier exists:
   - `bill_title`
   - `measure_title`
   - `source_bill_title`
   - `title`
   - `description`
3. Singleton fallback:
   - one row per roll call when no stable grouping key exists

Broad `issue_facet` alone is not a grouping key. That prevents unrelated rows, such as separate foreign military sales, from being grouped just because they share a facet.

Group categories:

- `primary_bill_or_measure`
- `related_amendments`
- `related_floor_or_procedural_votes`
- `limited_context_rows`
- `not_voting_rows`

## Representative Slice 1: Valerie Foushee / Economy & Taxes

Status: safe.

Rows:

- total rows: 9
- counted in summarized Yes/No pattern: 6
- ambiguous/insufficient/procedural excluded: 2
- not-voting rows excluded from support/opposition: 1

Rendered overview remains stable:

```text
What these votes were about
In this Economy & Taxes sample, the reviewed votes where Foushee cast a Yes or No covered several concrete fiscal questions: whether to advance a budget framework for later tax, spending, deficit, and debt-limit legislation; whether to restrict SBA 7(a) and 504 loan eligibility based on citizenship or lawful-residency status; whether to fund military construction, military housing, veterans benefits, and Veterans Affairs programs; whether to keep federal agencies operating through temporary government funding; and whether to accept a shutdown-ending funding package. A separate not-voting row concerned an SBA regulatory-cost cap bill, but Foushee was recorded as not voting, so it is explained below and not counted as support or opposition. Two ambiguous or limited-context rows remain visible for an appropriations amendment and a conference instruction, but they are not used to summarize the vote pattern.

What Foushee did
Foushee voted No on all 6 reviewed votes where she cast a Yes or No. Each of those votes matched most House Democrats, and each was against the final House outcome.

What pattern that creates
Foushee consistently opposed the House Republican fiscal, funding, and small-business measures reviewed in this sample. Her record here is best read as opposition to this specific set of Republican-led House measures, not as a simple statement that she is "for" or "against taxes."

How a voter might read that
If you generally favored these House Republican packages, this section may look misaligned with your views. If you generally wanted Democrats to oppose those packages or objected to their terms, this section may look aligned. The vote record alone does not show her motive.

What not to infer
Do not infer motive, ideology, character, corruption, or a voting recommendation from this section. The rows show recorded votes and reviewed bill meaning for this sample, not her full fiscal record. Not-voting and limited-context rows remain visible below, but they are not forced into the pattern.
```

Grouped rows summary:

- 5 total groups.
- 3 repeated bill/measure groups detected.
- Budget framework group: rolls 50 and 100, `primary_bill_or_measure`, 2 counted rows.
- Military construction / VA appropriations group: rolls 180, 182, and 263, `related_floor_or_procedural_votes`, 1 counted row and 2 ambiguous/limited rows.
- Continuing appropriations group: rolls 281 and 285, `primary_bill_or_measure`, 2 counted rows.
- Small Business Regulatory Reduction Act: roll 310, `not_voting_rows`, excluded from support/opposition.

First 5 default-visible card summaries:

1. `Nay. The House adopted a budget blueprint that helped start a fast-track reconciliation process for later tax, spending, deficit, and debt-limit legislation. Foushee voted against adopting that framework, matching most Democrats. The measure passed narrowly.`
2. `Nay. The House agreed to the Senate-amended budget framework, keeping the reconciliation process moving for later tax, spending, deficit, and debt-limit legislation. Foushee voted against agreeing to that framework, matching most Democrats. The measure passed narrowly.`
3. `Nay. The House passed a bill that would restrict SBA 7(a) and 504 loan eligibility based on citizenship or lawful-permanent-residency status. Foushee voted against adding those eligibility restrictions, matching most Democrats. The bill passed the House.`
4. `Limited-context row. This was an en bloc appropriations amendment, but the available source text does not explain the full practical change. It remains visible below but is not counted in the summarized vote pattern.`
5. `Nay. The House passed an FY2026 funding bill for military construction, military housing, veterans benefits, Veterans Affairs programs, and related agencies. Foushee voted against passing that funding bill, matching most Democrats. The measure passed the House.`

Does grouping improve scanability: yes. It shows that several rows are not separate issue claims, but repeated activity around the budget framework, the military construction/VA appropriations bill, and the continuing appropriations package.

Grouping mistakes or uncertain groups: the military construction/VA group label may inherit the first row label when the first row is an amendment. Future UI copy should prefer a final-passage or bill-title label when available.

## Representative Slice 2: Valerie Foushee / Justice & Public Safety

Status: safe.

Rows:

- total rows: 7
- counted in summarized Yes/No pattern: 5
- ambiguous/insufficient/procedural excluded: 2
- not-voting rows: 0

Rendered overview remains stable:

```text
What these votes were about
In this Justice & Public Safety sample, the reviewed votes where Foushee cast a Yes or No covered several public-safety and legal-policy questions: whether to permanently schedule fentanyl-related substances and apply related penalty-threshold and research-registration changes; whether to create a program for federal law-enforcement officers to buy retired agency-issued firearms; whether to require DOJ reporting on targeted attacks against law-enforcement officers, reporting-system feasibility, and officer mental-health resources; whether to change D.C. police pursuit rules by removing current restrictions and adding a general pursuit requirement with exceptions; and whether to repeal D.C.'s 2022 policing and justice reform act and restore provisions changed by that act. Two additional rows remain visible below but are not counted because the available source text does not clearly explain the practical policy effect.

What Foushee did
Of the 5 reviewed Yes/No votes that could be interpreted, 1 supported the measures shown and 4 opposed them. All of those votes matched most Democrats. Most opposed measures that passed the House.

What pattern that creates
Foushee's reviewed votes where she cast a Yes or No in this sample were mixed. Her record here is best read as a mixed record on this specific set of Republican-led House measures, not as a simple statement that she is broadly for or against this issue area.

How a voter might read that
If you generally favored these House Republican measures, this section may look misaligned with your views. If you generally wanted Democrats to oppose those measures or objected to their terms, this section may look aligned. The vote record alone does not show her motive.

What not to infer
Do not infer motive, ideology, character, corruption, or a voting recommendation from this section. The rows show recorded votes and reviewed bill meaning for this sample, not her full record in this issue area. Not-voting and limited-context rows remain visible below, but they are not forced into the pattern.
```

Grouped rows summary:

- 7 total groups.
- 0 repeated groups in this sample fixture.
- 5 primary bill/measure groups counted in the summarized pattern.
- 2 limited-context singleton groups excluded.

First 5 default-visible card summaries:

1. `Nay. The House passed the HALT Fentanyl Act, which would permanently place fentanyl-related substances as a class into Schedule I and apply fentanyl-analogue penalty thresholds, while creating or revising research-registration paths. Foushee voted against passing the bill, matching most Democrats. The bill passed the House.`
2. `Nay. The House passed a bill directing GSA to create a process for federal law-enforcement officers to buy retired agency-issued firearms. Foushee voted against passing the bill, matching most Democrats. The bill passed the House.`
3. `Yea. The House passed a bill requiring DOJ reports on targeted attacks against law-enforcement officers, reporting-system feasibility, and officer mental-health resources. Foushee voted to pass the bill, matching most Democrats. The bill passed the House.`
4. `Nay. The House passed a bill changing D.C. police pursuit rules by removing current restrictions and adding a general pursuit requirement with listed exceptions. Foushee voted against passing the bill, matching most Democrats. The bill passed the House.`
5. `Nay. The House passed a bill that would repeal D.C.'s 2022 policing and justice reform act, including provisions related to neck restraints, body-worn cameras, and police disciplinary records. Foushee voted against passing the bill, matching most Democrats. The bill passed the House.`

Does grouping improve scanability: neutral but harmless. There are no repeated bill clusters in this fixture, so grouping confirms the rows are mostly separate measures and leaves the approved overview unchanged.

Grouping mistakes or uncertain groups: none identified in this fixture.

## Representative Slice 3: High-Risk National Security & Foreign Policy

Status: limited.

Rows:

- total rows: 10
- counted in summarized Yes/No pattern: 5
- ambiguous/insufficient/procedural excluded: 5
- not-voting rows: 0
- readiness reason: limited/ambiguous rows are 50% of the slice

Rendered overview:

```text
What these votes were about
This National Security & Foreign Policy sample has limited interpreted evidence. The rows that can be summarized concern whether to allow or disapprove specific foreign military sales; whether to pass defense and national-security authorization legislation; and whether to use a procedural motion to send the measure back for further consideration. Five additional rows remain visible below but are not counted because the available source text does not clearly explain the practical policy effect.

What Foushee did
Of the 5 reviewed Yes/No votes that could be interpreted, 1 supported the measures shown and 4 opposed them. All of those votes matched most Democrats. Most were against the final House outcome.

What pattern that creates
This section is best read as limited evidence, not a stable issue pattern, because limited-context rows make up much of this sample.

How a voter might read that
A voter can use these rows as source-backed examples of what was reviewed, but should look at the individual evidence cards before drawing a broader issue-area conclusion. The vote record alone does not show her motive.

What not to infer
Do not infer motive, ideology, character, corruption, or a voting recommendation from this section. The rows show recorded votes and reviewed bill meaning for this sample, not her full record in this issue area. Not-voting and limited-context rows remain visible below, but they are not forced into the pattern.
```

Grouped rows summary:

- 5 total groups.
- 1 repeated bill/measure group detected.
- National Defense Authorization Act group: rolls 200, 201, 202, 203, 204, and 205.
- That defense group is `related_floor_or_procedural_votes`: 2 counted rows, 4 ambiguous/insufficient rows, 3 procedural rows, and 3 amendment rows.
- Separate foreign military sales without shared identifiers remain separate groups, even though they share the `foreign_military_sales` facet.
- House floor procedure for multiple bills remains a singleton `limited_context_rows` group and is excluded.

First 5 default-visible card summaries:

1. `Nay. The Senate voted on whether to allow a specific foreign military sale to proceed. Foushee voted against allowing that foreign military sale to proceed, matching most Democrats. The measure passed.`
2. `Yea. The House passed defense and national-security authorization legislation. Foushee voted to pass that defense authorization legislation, matching most Democrats. The bill passed the House.`
3. `Nay. The House considered a procedural motion to commit. The vote concerned whether to send the measure back for further consideration. Foushee voted Nay, matching most Democrats. The measure failed.`
4. `Nay. The available source text identifies an amendment but does not explain the full practical policy effect. This row remains visible but is not counted in the summarized vote pattern because the available source text does not explain the practical policy effect.`
5. `Nay. The available source text identifies floor procedure rather than a clear final policy choice. This row remains visible but is not counted in the summarized vote pattern because the available source text does not explain the practical policy effect.`

Does grouping improve scanability: yes. The packet can now show that six rows cluster around the same defense authorization bill/package, while still making clear that amendments and floor-procedure rows are not final policy votes and are excluded when insufficient.

Grouping mistakes or uncertain groups:

- The system can identify a repeated defense bill cluster, but it does not yet distinguish a clean "primary bill row" display label from related amendment/procedure rows for UI presentation.
- The motion-to-commit row is counted only because it is interpreted in the fixture. Procedural rows remain excluded when interpretation status is ambiguous or insufficient.
- The overview still uses existing outcome wording in one place; future copy cleanup should prefer "opposed a measure that passed the House" where supported.

## Tests

Added:

- `frontend/lib/evidenceGrouping.test.mjs`

Coverage:

- grouping repeated rows by stable bill/measure identifier
- not grouping unrelated rows only because they share broad `issue_facet`
- exposing grouping metadata without changing counts or approved overview copy
- preserving high-risk National Security limited treatment

Existing tests still cover:

- approved Valerie / Economy & Taxes overview
- approved Economy card summaries and limited-row caveats
- Justice & Public Safety overview
- generic card summaries
- readiness gating
- compact large-section overview behavior
- banned public phrases

## Verification

```text
node --test frontend/lib/issueOverview.test.mjs
PASS: 11/11 tests

node --test frontend/lib/evidenceGrouping.test.mjs
PASS: 4/4 tests

npm run build
PASS: Next.js production build compiled successfully and generated 4 static pages.
```

## Known Risks

- Group labels currently use the first usable title/description in the group. If an amendment appears before final passage, the group label may be less ideal than the underlying bill title.
- Title-based grouping is deterministic but lower confidence than bill-id grouping. It is used only when stable identifiers are absent.
- No visible grouped-card UI was added in Phase 1. This keeps the PR safe, but the next UI pass still needs to decide how to display the grouping metadata.

## Recommended Next Pass

Add a light UI layer that optionally groups cards by `evidenceGrouping.groups`, with source links and limited-context caveats still visible. Prefer bill-title labels over amendment labels when a final-passage row is available.
