# Readiness-First MVP Profile Pass

Date: 2026-06-04

Branch: `readiness-first-mvp-profile-pass`

## Scope

This milestone bundles the next readiness-first representative-profile improvements:

- add a profile-level "Start Here" quick-read action for the clearest reviewed issue read
- add a deterministic "What You Can Learn In 60 Seconds" path
- visually prioritize strong and mixed issue reads above limited/not-ready sections
- explain why limited/not-ready sections are lower priority
- add a grouped-evidence preview for opened issue sections
- add compact evidence confidence labels to vote cards
- separate highest-volume issue focus from the clearest reviewed issue read in Quick Read
- remove alignment framing from no-preference record views
- make issue cards use concise generalized readiness language
- move contact action after opened issue evidence cards
- document the presentation guardrails in methodology
- keep approved Economy & Taxes and Justice & Public Safety issue copy stable

This branch does not add backend interpretation data, curated roll-number summaries, source enrichment, automated LLM interpretation, support/opposition counting changes, alignment changes, or backend/API shape changes.

## Files Changed

- `docs/methodology.md`
- `docs/review_packets/readiness_first_mvp_profile_pass.md`
- `frontend/components/AlignmentPanel.js`
- `frontend/components/ComparisonPanel.js`
- `frontend/components/IssuePreferencePanel.js`
- `frontend/components/PositionByIssue.js`
- `frontend/components/ProfileQuickRead.js`
- `frontend/lib/profileMvpProfile.test.mjs`

Unrelated untracked review artifacts remain outside this PR unless explicitly added later:

- `docs/review_packets/chamber_filtering_data_integrity_audit.md`
- `review_bundle_frontend_data_grounding/`
- `review_bundle_frontend_data_grounding.zip`

## User-Facing Product Improvement

The representative profile now gives the voter a clearer path:

1. Quick Read names what the page can teach in 60 seconds.
2. Start Here points directly to the clearest reviewed issue read.
3. Strong and mixed sections are visually emphasized.
4. Limited/not-ready sections remain visible but are clearly lower priority.
5. Opening an issue shows the issue overview, grouped evidence preview, evidence confidence labels, and source-backed cards.
6. Neutral issue selections are presented as reviewed records, not alignment scores.

When a user opens an issue, the evidence section adds:

- a compact grouped-evidence preview, showing whether rows cluster around repeated bills/measures, limited-context rows, or not-voting rows
- compact evidence confidence labels on each card:
  - `Reviewed meaning`
  - `Limited context`
  - `Needs source support`
  - `Not counted`

These labels describe evidence readiness only. They do not imply motive, ideology, character, corruption, or voting advice.

## Rendered Profile Structure

Top Quick Read:

```text
Quick Read
Start with Economy & Taxes. It has the clearest reviewed vote meaning in this profile.

In 60 seconds, start with Economy & Taxes for reviewed vote meaning. National Security & Foreign Policy has more recorded votes, but the best place to start is the issue with clearer reviewed evidence. 62 votes; drift read: Steady.
```

Start Here panel:

```text
Start Here
Open Economy & Taxes first. It has the clearest reviewed vote meaning; National Security & Foreign Policy has more recorded votes but is not the best first read.
Open Best Read
```

## Before / After Quick Read Behavior

Before:

```text
Valerie P. Foushee's recent record centers on National Security & Foreign Policy. The clearest reviewed issue read is strong evidence in Economy & Taxes.
```

After:

```text
Start with Economy & Taxes. It has the clearest reviewed vote meaning in this profile.
```

Why this changed:

- Highest recorded vote volume can differ from clearest reviewed vote meaning.
- The page should not imply a high-volume limited section is the best place to start.
- The copy is generalized: it compares `topFocus.domain` with `topPosition.domain` for any representative.

## Before / After No-Preference Record Wording

Before:

```text
Your Issues vs This Record
Pick what you want this record checked against.
Record shown
0 aligned / 0 not aligned / 0 mixed / 1 insufficient
```

After:

```text
Selected Issue Records
Choose issue areas to inspect.
Evidence available
1 reviewed record shown / 0 insufficient issues
```

Alignment labels are still available when a user chooses a directional preference. The no-preference state now uses neutral record language.

Position-by-issue guidance:

```text
First Read
The strongest reviewed issue read is Economy & Taxes. Justice & Public Safety is also useful, but the interpreted votes are mixed.

What You Can Learn In 60 Seconds
Start with Economy & Taxes for the clearest reviewed record, then use mixed or limited sections to understand where the evidence gets thinner.

1. Start with Economy & Taxes
This is the clearest reviewed issue read available for this representative.

2. Then compare Justice & Public Safety
This section is useful because reviewed votes point in more than one direction.

3. Use National Security & Foreign Policy as a caution check
This section remains visible, but it should not be read as a stable issue pattern yet.

5 limited sections are lower priority because reviewed vote meaning is thin; 1 section does not have enough reviewed vote meaning to summarize.
```

Issue picker hierarchy:

```text
Best issue reads
Economy & Taxes
Strong evidence
Best place to start

Mixed but interpretable
Justice & Public Safety
Mixed but interpretable
Useful comparison read

Limited evidence
National Security & Foreign Policy
Limited evidence
Lower priority: read cautiously

Not enough to summarize
Infrastructure, Tech & Transportation
Not enough to summarize
Evidence visible, not ready to summarize
```

Issue-card wording examples:

```text
Strong evidence
6 reviewed Yes/No votes out of 8 recorded votes.
Best place to start.

Mixed but interpretable
5 reviewed Yes/No votes out of 13 recorded votes.
Reviewed votes point in more than one direction. Useful comparison read.

Limited evidence
2 reviewed Yes/No votes out of 22 recorded votes.
Reviewed vote meaning is thin. Read cautiously.

Not enough to summarize
No reviewed Yes/No vote meaning is available yet out of 3 recorded votes.
Evidence may still be visible, but this issue is not ready for a confident summary.
```

## Representative Profile Readiness Grouping

Current Valerie Foushee grouping remains:

```json
[
  {
    "label": "Best issue reads",
    "domains": ["Economy & Taxes"]
  },
  {
    "label": "Mixed but interpretable",
    "domains": ["Justice & Public Safety"]
  },
  {
    "label": "Limited evidence",
    "domains": [
      "National Security & Foreign Policy",
      "Education & Workforce",
      "Health & Social Services",
      "Environment & Energy",
      "Immigration & Border Policy"
    ]
  },
  {
    "label": "Not enough to summarize",
    "domains": ["Infrastructure, Tech & Transportation"]
  }
]
```

## Slice 1: Valerie Foushee / Economy & Taxes

Readiness status: safe / strong evidence.

Profile treatment:

- appears under `Best issue reads`
- gets `Best place to start` priority copy
- is the Start Here target
- opened evidence shows grouped budget, appropriations, continuing-funding, limited-context, and not-voting clusters

Approved overview remains stable:

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

Grouped evidence preview:

```text
9 evidence rows shown across 5 bill or measure groups; 3 repeated groups detected; 2 limited-context rows kept separate; 1 not-voting row not counted as support or opposition.
Repeated bill groups help show when several rows are about the same package. Limited-context and not-voting rows remain visible without being counted as support or opposition.
```

Grouped preview labels now use safer voter-facing category labels where existing row text supports them, such as:

- `Budget framework / reconciliation setup`
- `SBA loan eligibility`
- `Military construction and VA funding`
- `Temporary funding / shutdown package`
- `SBA regulatory-cost cap`

If a group cannot be safely mapped, it falls back to cautious generic labels such as `Primary measure`, `Related amendments`, `Related procedural votes`, `Limited context`, or `Not voting`.

Representative groups:

- Budget framework group: rolls 50 and 100, counted Yes/No rows.
- Military construction / Veterans Affairs appropriations group: rolls 180, 182, and 263, with limited-context rows kept separate.
- Continuing appropriations group: rolls 281 and 285, counted Yes/No rows.
- Small Business Regulatory Reduction Act: roll 310, not-voting row, not counted as support or opposition.

First five default-visible card summaries remain approved:

1. `Nay. The House adopted a budget blueprint that helped start a fast-track reconciliation process for later tax, spending, deficit, and debt-limit legislation. Foushee voted against adopting that framework, matching most Democrats. The measure passed narrowly.`
2. `Nay. The House agreed to the Senate-amended budget framework, keeping the reconciliation process moving for later tax, spending, deficit, and debt-limit legislation. Foushee voted against agreeing to that framework, matching most Democrats. The measure passed narrowly.`
3. `Nay. The House passed a bill that would restrict SBA 7(a) and 504 loan eligibility based on citizenship or lawful-permanent-residency status. Foushee voted against adding those eligibility restrictions, matching most Democrats. The bill passed the House.`
4. `Limited-context row. This was an en bloc appropriations amendment, but the available source text does not explain the full practical change. It remains visible below but is not counted in the summarized vote pattern.`
5. `Nay. The House passed an FY2026 funding bill for military construction, military housing, veterans benefits, Veterans Affairs programs, and related agencies. Foushee voted against passing that funding bill, matching most Democrats. The measure passed the House.`

## Slice 2: Valerie Foushee / Justice & Public Safety

Readiness status: safe / mixed but interpretable.

Profile treatment:

- appears under `Mixed but interpretable`
- gets `Useful comparison read` priority copy
- is the second 60-second path step
- opened evidence shows separate primary measure groups and keeps limited-context rows separate

Approved overview remains stable:

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

Grouped evidence preview:

```text
7 evidence rows shown across 7 bill or measure groups; 2 limited-context rows kept separate.
Repeated bill groups help show when several rows are about the same package. Limited-context and not-voting rows remain visible without being counted as support or opposition.
```

Representative groups:

- Five primary bill/measure groups are counted in the summarized Yes/No pattern.
- Two limited-context singleton groups remain visible and excluded.
- No repeated bill/measure group is detected in the current fixture.

First five default-visible card summaries remain stable:

1. `Nay. The House passed the HALT Fentanyl Act, which would permanently place fentanyl-related substances as a class into Schedule I and apply fentanyl-analogue penalty thresholds, while creating or revising research-registration paths. Foushee voted against passing the bill, matching most Democrats. The bill passed the House.`
2. `Nay. The House passed a bill directing GSA to create a process for federal law-enforcement officers to buy retired agency-issued firearms. Foushee voted against passing the bill, matching most Democrats. The bill passed the House.`
3. `Yea. The House passed a bill requiring DOJ reports on targeted attacks against law-enforcement officers, reporting-system feasibility, and officer mental-health resources. Foushee voted to pass the bill, matching most Democrats. The bill passed the House.`
4. `Nay. The House passed a bill changing D.C. police pursuit rules by removing current restrictions and adding a general pursuit requirement with listed exceptions. Foushee voted against passing the bill, matching most Democrats. The bill passed the House.`
5. `Nay. The House passed a bill that would repeal D.C.'s 2022 policing and justice reform act, including provisions related to neck restraints, body-worn cameras, and police disciplinary records. Foushee voted against passing the bill, matching most Democrats. The bill passed the House.`

## Slice 3: High-Risk National Security & Foreign Policy

Readiness status: limited.

Profile treatment:

- appears under `Limited evidence`
- gets `Lower priority: read cautiously` priority copy
- is used as the 60-second caution-check example
- opened evidence remains limited/cautious and does not become a stable issue pattern

Rendered overview remains cautious:

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

Grouped evidence preview example:

```text
2 evidence rows shown across 2 bill or measure groups; 1 limited-context row kept separate.
Repeated bill groups help show when several rows are about the same package. Limited-context and not-voting rows remain visible without being counted as support or opposition.
```

Representative groups:

- Foreign military sale row: interpreted but still part of a limited slice because interpreted evidence is thin.
- Defense authorization amendment row: limited/insufficient, visible below, not counted in the summarized pattern.

First two default-visible card summaries:

1. `Nay. The Senate voted on whether to allow a specific foreign military sale to proceed. Foushee voted against allowing that foreign military sale to proceed, matching most Democrats. The measure passed.`
2. `Nay. The available source text identifies an amendment but does not explain the full practical policy effect. This row remains visible but is not counted in the summarized vote pattern because the available source text does not explain the practical policy effect.`

Known data-review note: a separate chamber-filtering audit was created for the National Security fixture concern where a House member appears with Senate wording. That audit remains outside this PR unless separately requested. This milestone does not modify backend data or chamber filtering.

## Evidence Confidence Labels

Default-visible card labels now map to row readiness:

- `Reviewed meaning`: interpreted rows where the card can explain vote meaning.
- `Limited context`: ambiguous rows that stay visible but should not be forced into the pattern.
- `Needs source support`: insufficient-evidence rows that need stronger source grounding before confident interpretation.
- `Not counted`: not-voting rows that may explain bill meaning but cannot count as support or opposition.

Source buttons remain visible outside collapsed details. Audit/methodology details remain in the details layer.

## Opened Issue Order

Preferred order is now reflected in the component:

1. issue overview
2. grouped evidence preview
3. vote cards
4. Contact this office

The contact panel was moved after the vote cards so it no longer interrupts the evidence-reading flow.

## Tests / Build Results

```text
node --test frontend/lib/issueOverview.test.mjs
PASS: 11/11 tests

node --test frontend/lib/evidenceGrouping.test.mjs
PASS: 4/4 tests

node --test frontend/lib/issueReadiness.test.mjs
PASS: 4/4 tests

node --test frontend/lib/profileMvpProfile.test.mjs
PASS: 6/6 tests

npm run build
PASS: Next.js production build compiled successfully and generated 4 static pages.
```

Node emitted the existing module-type warning for `frontend/lib/issueDomains.js` during tests. This warning was present in earlier test paths and is not introduced by this milestone.

## Known Risks

- The grouped preview is intentionally light. It improves scanning but does not yet provide full grouped-card layout.
- Group labels still depend on available title/description fields; amendment-first groups may still need a future display-label preference for final-passage or bill-title rows.
- National Security remains limited and should not be treated as a stable issue read without source/data cleanup.
- Readiness and confidence labels are presentation guardrails. They do not enrich source data or change interpretations.

## Merge Recommendation

Merge-ready if the final build passes. This is a coherent MVP profile increment: readiness-first ordering stays in place, opened issue sections are easier to scan, evidence confidence is more visible, and the review packet covers Economy, Justice, and high-risk National Security without changing backend data or vote-counting logic.
