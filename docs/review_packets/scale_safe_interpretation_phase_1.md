# Scale-Safe Interpretation Expansion, Phase 1

Scope: milestone-sized frontend safety pass for issue overviews and generic vote-card summaries. This branch does not add backend interpretation data, does not change API shape, does not add curated roll-number summaries, and does not broaden low-confidence domains as high-confidence.

## What Changed

- Added issue-overview readiness gating in `frontend/lib/issueOverview.mjs`.
- Added compact overview behavior for slices with more than five interpreted measure groups.
- Added generic facet-based vote-card summaries for additional high-confidence interpreted facets.
- Added regression tests for approved Economy & Taxes output, Justice & Public Safety output, readiness gating, compact large-section behavior, generic summaries, limited/procedural rows, and banned public phrases.
- Added a small methodology note describing readiness gating and compact overview behavior.

Counting/alignment logic changed: no. Existing support/opposition counting is preserved. The new logic changes only how confidently the overview copy describes a slice.

## Files Changed

- `frontend/lib/issueOverview.mjs`
- `frontend/lib/voteCardSummary.mjs`
- `frontend/lib/issueOverview.test.mjs`
- `docs/methodology.md`
- `docs/review_packets/scale_safe_interpretation_phase_1.md`

## Representative Slices Tested

### 1. Strong Economy & Taxes Slice

Status: safe.

Counts:

- total rows: 9
- counted interpreted Yes/No rows: 6
- ambiguous/limited rows: 2
- not-voting rows: 1
- interpreted measure groups shown in overview: 5 of 5

Rendered overview:

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

First five default-visible card summaries, using approved Valerie Economy UI copy:

1. `Nay. The House adopted a budget blueprint that helped start a fast-track reconciliation process for later tax, spending, deficit, and debt-limit legislation. Foushee voted against adopting that framework, matching most Democrats. The measure passed narrowly.`
2. `Nay. The House agreed to the Senate-amended budget framework, keeping the reconciliation process moving for later tax, spending, deficit, and debt-limit legislation. Foushee voted against agreeing to that framework, matching most Democrats. The measure passed narrowly.`
3. `Nay. The House passed a bill that would restrict SBA 7(a) and 504 loan eligibility based on citizenship or lawful-permanent-residency status. Foushee voted against adding those eligibility restrictions, matching most Democrats. The bill passed the House.`
4. `Limited-context row. This was an en bloc appropriations amendment, but the available source text does not explain the full practical change. It remains visible below but is not counted in the summarized vote pattern.`
5. `Nay. The House passed an FY2026 funding bill for military construction, military housing, veterans benefits, Veterans Affairs programs, and related agencies. Foushee voted against passing that funding bill, matching most Democrats. The measure passed the House.`

Treatment:

- Not-voting row is explained below the overview and excluded from support/opposition.
- Ambiguous/limited rows remain visible and excluded.
- Approved gold-slice overview and card copy remain stable.

### 2. Justice & Public Safety Generalization Slice

Status: safe.

Counts:

- total rows: 7
- counted interpreted Yes/No rows: 5
- ambiguous/insufficient rows: 2
- not-voting rows: 0
- interpreted measure groups shown in overview: 5 of 5

Rendered overview:

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

First five default-visible card summaries:

1. `Nay. The House passed the HALT Fentanyl Act, which would permanently place fentanyl-related substances as a class into Schedule I and apply fentanyl-analogue penalty thresholds, while creating or revising research-registration paths. Foushee voted against passing the bill, matching most Democrats. The bill passed the House.`
2. `Nay. The House passed a bill directing GSA to create a process for federal law-enforcement officers to buy retired agency-issued firearms. Foushee voted against passing the bill, matching most Democrats. The bill passed the House.`
3. `Yea. The House passed a bill requiring DOJ reports on targeted attacks against law-enforcement officers, reporting-system feasibility, and officer mental-health resources. Foushee voted to pass the bill, matching most Democrats. The bill passed the House.`
4. `Nay. The House passed a bill changing D.C. police pursuit rules by removing current restrictions and adding a general pursuit requirement with listed exceptions. Foushee voted against passing the bill, matching most Democrats. The bill passed the House.`
5. `Nay. The House passed a bill that would repeal D.C.'s 2022 policing and justice reform act, including provisions related to neck restraints, body-worn cameras, and police disciplinary records. Foushee voted against passing the bill, matching most Democrats. The bill passed the House.`

Treatment:

- Two limited/insufficient rows remain visible below and are excluded from the summarized support/opposition pattern.
- Justice-specific public language remains domain-aware and does not use tax wording.

### 3. High-Risk National Security & Foreign Policy Slice

Status: limited.

Counts:

- total rows: 2
- counted interpreted Yes/No rows: 1
- ambiguous/insufficient rows: 1
- not-voting rows: 0
- interpreted measure groups shown in overview: 1 of 1

Rendered overview:

```text
What these votes were about
This National Security & Foreign Policy sample has limited interpreted evidence. The rows that can be summarized concern whether to allow or disapprove specific foreign military sales. Only 1 reviewed Yes/No vote could be interpreted, so the section should not be read as a stable pattern. One additional row remains visible below but is not counted because the available source text does not clearly explain the practical policy effect.

What Foushee did
Of the 1 reviewed Yes/No vote that could be interpreted, 0 supported the measures shown and 1 opposed them. All of those votes matched most Democrats. All opposed measures that passed the House.

What pattern that creates
This section is best read as limited evidence, not a stable issue pattern, because the interpreted evidence is still thin.

How a voter might read that
A voter can use these rows as source-backed examples of what was reviewed, but should look at the individual evidence cards before drawing a broader issue-area conclusion. The vote record alone does not show her motive.

What not to infer
Do not infer motive, ideology, character, corruption, or a voting recommendation from this section. The rows show recorded votes and reviewed bill meaning for this sample, not her full record in this issue area. Not-voting and limited-context rows remain visible below, but they are not forced into the pattern.
```

First two default-visible card summaries:

1. `Nay. The Senate voted on whether to allow a specific foreign military sale to proceed. Foushee voted against allowing that foreign military sale to proceed, matching most Democrats. The measure passed.`
2. `Nay. The available source text identifies an amendment but does not explain the full practical policy effect. This row remains visible but is not counted in the summarized vote pattern because the available source text does not explain the practical policy effect.`

Treatment:

- This slice is not presented as a stable pattern.
- The insufficient-evidence defense authorization amendment remains visible and excluded from support/opposition.

## Large-Section Behavior

When a safe slice has more than five interpreted measure groups, the overview lists the top five groups and adds a compact sentence such as:

```text
One additional measure group is shown in the evidence below.
```

The full evidence rows and full `measureGroups` object remain available; the compact behavior only limits overview paragraph length.

## Before/After Examples

### Readiness gating

Before:

```text
Foushee consistently opposed the measures reviewed in this sample.
```

After, for thin evidence:

```text
This section is best read as limited evidence, not a stable issue pattern, because the interpreted evidence is still thin.
```

### Large sections

Before:

```text
The overview could list every measure group in one long sentence.
```

After:

```text
The overview lists five measure groups and directs users to additional evidence below.
```

### Generic card summaries

New or improved templates include:

- `dc_policing_reform_repeal`: D.C. policing and justice reform repeal.
- `school_foreign_influence_parent_notifications`: parent notifications about foreign-influence issues in schools.
- `health_insurance_premium_assistance`: health insurance premium assistance and affordability rules.
- `defense_authorization`: defense and national-security authorization legislation.
- `natural_gas_pipeline_and_lng_review_coordination`: federal review coordination for natural gas pipeline and LNG projects.
- `federal_employee_collective_bargaining`: federal employee collective-bargaining rules.

## High-Confidence Slices Improved

- Justice & Public Safety: clearer generic card summaries for law-enforcement and D.C. policing facets.
- Education & Workforce: clearer school foreign-influence/funding and federal employee bargaining facets.
- Health & Social Services: clearer health insurance premium assistance and Medicaid payment-rule facets.
- National Security & Foreign Policy: clearer foreign military sales and defense authorization facets, with readiness gating for thin/high-risk slices.
- Environment & Energy: clearer natural gas pipeline and LNG review coordination facet.

## Unsafe or Limited Slices Still Blocked

- Slices with fewer than three counted interpreted Yes/No rows are marked limited.
- Slices where ambiguous or insufficient rows dominate are marked limited.
- Procedural/floor-rule rows remain limited unless source text supports a practical policy effect.
- The branch does not add source enrichment or new interpretation records.

## Tests / Build Results

```text
node --test frontend/lib/issueOverview.test.mjs
PASS: 11/11 tests

npm run build
PASS: Next.js production build compiled successfully and generated 4 static pages.
```

## Known Risks

- Readiness thresholds are intentionally simple: fewer than three counted interpreted Yes/No rows, or limited/ambiguous rows dominating the slice. These are frontend copy gates, not scoring changes.
- Compact measure-group selection uses row count and original order. That is deterministic, but future scaling may need better grouping if many related roll calls repeat the same bill.
- Some generic templates still rely on facet mappings. Additional high-volume facets may need future label/template cleanup before public rollout.

## Recommended Next Pass

Review another milestone branch focused on source enrichment and grouping repeated roll calls for large issue sections. Do not broaden rollout until more slices have enough interpreted rows and voter-facing facet labels.
