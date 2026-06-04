# Readiness-First Representative Profile, Phase 1

Date: 2026-06-04

Branch: `codex/readiness-first-profile-phase-1`

## What Changed

- Added a reusable frontend readiness derivation for issue-domain position rows.
- Grouped representative issue domains into:
  - Best issue reads
  - Mixed but interpretable
  - Limited evidence
  - Not enough to summarize
- Updated the representative issue picker so stronger reviewed issue reads appear before limited or not-ready sections.
- Updated the profile quick-read card to point to the best reviewed issue read rather than the highest raw vote-volume issue.
- Kept issue-section overview behavior stable.
- Did not change backend/API behavior, interpretation data, support/opposition counting, alignment logic, or source enrichment.

## Files Changed

- `docs/methodology.md`
- `docs/product_direction_readiness_first_profile.md`
- `docs/review_packets/readiness_first_profile_phase_1.md`
- `frontend/components/PositionByIssue.js`
- `frontend/components/ProfileQuickRead.js`
- `frontend/lib/issueReadiness.mjs`
- `frontend/lib/issueReadiness.test.mjs`

Note: unrelated untracked review artifacts remain outside this PR unless explicitly added later:

- `docs/review_packets/chamber_filtering_data_integrity_audit.md`
- `review_bundle_frontend_data_grounding/`
- `review_bundle_frontend_data_grounding.zip`

## Rendered Representative Profile Summary For Valerie Foushee

Quick read headline:

```text
Valerie P. Foushee's recent record centers on National Security & Foreign Policy. The clearest reviewed issue read is strong evidence in Economy & Taxes.
```

Position-by-issue first-read text:

```text
The strongest reviewed issue read is Economy & Taxes. Justice & Public Safety is also useful, but the interpreted votes are mixed.
```

How-to-read text:

```text
Issue areas are grouped by reviewed evidence strength. Strong and mixed sections come first; limited sections stay visible without being treated as confident summaries. It is descriptive, not a score.
```

## Issue Readiness Grouping Output

```json
[
  {
    "key": "strong_evidence",
    "label": "Best issue reads",
    "readinessLabel": "Strong evidence",
    "count": 1,
    "domains": ["ECONOMY_TAXES"],
    "labels": ["Economy & Taxes"]
  },
  {
    "key": "mixed_but_interpretable",
    "label": "Mixed but interpretable",
    "readinessLabel": "Mixed but interpretable",
    "count": 1,
    "domains": ["JUSTICE_PUBLIC_SAFETY"],
    "labels": ["Justice & Public Safety"]
  },
  {
    "key": "limited_evidence",
    "label": "Limited evidence",
    "readinessLabel": "Limited evidence",
    "count": 5,
    "domains": [
      "NATIONAL_SECURITY_FOREIGN",
      "EDUCATION_WORKFORCE",
      "HEALTH_SOCIAL",
      "ENVIRONMENT_ENERGY",
      "IMMIGRATION_BORDER"
    ],
    "labels": [
      "National Security & Foreign Policy",
      "Education & Workforce",
      "Health & Social Services",
      "Environment & Energy",
      "Immigration & Border Policy"
    ]
  },
  {
    "key": "not_enough_to_summarize",
    "label": "Not enough to summarize",
    "readinessLabel": "Not enough to summarize",
    "count": 1,
    "domains": ["INFRASTRUCTURE_TECH_TRANSPORT"],
    "labels": ["Infrastructure, Tech & Transportation"]
  }
]
```

## Examples By Readiness Label

### Strong Evidence

Economy & Taxes:

- Recorded Yes/No votes: 8
- Reviewed interpreted Yes/No votes: 6
- Pattern: 0 supported measures shown, 6 opposed measures shown
- Treatment: appears under Best issue reads
- Existing approved Economy & Taxes issue overview and vote-card summaries remain unchanged by tests.

### Mixed But Interpretable

Justice & Public Safety:

- Recorded Yes/No votes: 13
- Reviewed interpreted Yes/No votes: 6
- Pattern: 2 supported measures shown, 4 opposed measures shown
- Treatment: appears under Mixed but interpretable
- Existing Justice & Public Safety overview remains stable under tests.

### Limited Evidence

National Security & Foreign Policy:

- Recorded Yes/No votes: 22
- Reviewed interpreted Yes/No votes: 2
- Treatment: appears under Limited evidence
- Reason shown: the section has reviewed evidence, but too little interpreted Yes/No vote meaning for a confident issue read.
- Existing high-risk National Security overview remains limited/cautious under tests.

### Not Enough To Summarize

Infrastructure, Tech & Transportation:

- Recorded Yes/No votes: 0
- Reviewed interpreted Yes/No votes: 0
- Treatment: appears under Not enough to summarize
- Reason shown: no recorded Yes/No votes are loaded for this issue in the current window.

## Existing Slice Stability

- Valerie Foushee / Economy & Taxes approved output remains stable.
- Valerie Foushee / Justice & Public Safety output remains stable.
- High-risk National Security remains limited/cautious.
- Support/opposition counting logic did not change.
- Backend/API shape did not change.
- No new interpretations were added.
- No curated roll-number summaries were added.

## Tests / Build Results

```text
node --test frontend/lib/issueOverview.test.mjs
Result: PASS, 11/11 tests passed.

node --test frontend/lib/evidenceGrouping.test.mjs
Result: PASS, 4/4 tests passed.

node --test frontend/lib/issueReadiness.test.mjs
Result: PASS, 4/4 tests passed.

npm run build
Result: PASS. Next.js compiled successfully and generated 4 static pages.
```

Node emitted the existing module-type warning for `frontend/lib/issueDomains.js` during tests. This warning existed in the current test path and was not changed by this PR.

## Known Limitations

- Phase 1 readiness grouping uses existing position summary counts. It does not inspect all evidence rows up front, so it cannot yet account for every ambiguous/insufficient row before the user opens an issue.
- Readiness labels are presentation labels only. They do not change issue overview readiness, support/opposition counts, alignment math, or backend data.
- Limited evidence remains visible, but Phase 1 does not yet add richer source-enrichment workflows to move rows from limited to strong.
- This does not implement a personalized alignment quiz, broad ideology score, source enrichment, automated LLM interpretation rollout, new backend interpretation data, or broad domain rollout.

## Recommended Next Milestone

Add source-grounding guardrails before source enrichment:

- Add ETL/API checks that prevent chamber/member mismatches from reaching evidence rows.
- Add review-bundle validation so synthetic review rows cannot pair a House member with a Senate roll unless explicitly marked as non-representative fixture data.
- Then plan source enrichment for limited/high-volume slices so rows can move from limited evidence to stronger reviewed issue reads when sources support that.
