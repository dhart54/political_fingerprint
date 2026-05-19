# Product North Star

## Purpose

Political Fingerprint helps a voter answer one practical question:

**Who represents me, how are they acting on the issues I care about, and what can I do next?**

The product should make representative accountability feel fast, grounded, and understandable without telling the user what to think. The practical user need is to help someone identify their current representatives, inspect issue-specific evidence, understand what votes meant in plain English, and choose a neutral next action they control.

The long-term experience is ZIP-first and accountability-first:

1. A user enters their ZIP code.
2. The site identifies current representatives first.
3. The user chooses issues they care about.
4. The site shows how those representatives have acted on those issues using interpreted vote evidence.
5. The user can inspect sources and choose a neutral next action: contact, ask, thank, or track.
6. Upcoming election and challenger context appears secondarily when reliable data is available.

## Core Promise

**Current representatives first. Actual behavior first. User judgment always.**

Most political products start with endorsements, ideology, scores, or commentary. This product starts with evidence:

- What did the official vote on?
- What did the vote actually do?
- What did yea and nay mean?
- How did the official vote?
- How much of the record is interpreted versus still unclear?
- What can I ask, thank, contact, or track based on this evidence?
- If a candidate has no voting record, what sourced statements exist and how much confidence should the user place in them?

## Product Hierarchy

### 1. Representative Accountability Dashboard

This is the primary product surface.

For a ZIP-selected current House representative and senators, show:

- issue pattern cards
- interpreted vote meaning
- user-selected issue alignment
- evidence drilldowns
- source links
- coverage and confidence notes

The page should answer the user's current-representation question before introducing election context.

### 2. Civic Action / Contact Layer

This layer turns evidence into neutral civic follow-through.

Allowed actions:

- contact a current representative
- ask about a specific issue or vote
- thank a representative for a recorded action
- track an issue, vote, or representative for later review

Rules:

- the user chooses the action and position
- generated or suggested language must stay neutral and evidence-based
- action history must not affect vote classification, vote interpretation, alignment, or candidate comparison
- the product must not tell the user how to vote or whom to support

### 3. Election / Challenger Layer

Election context remains valuable, but it is secondary.

Use it to answer:

- who is running next
- which candidates have recorded governing behavior
- which candidates only have lower-confidence institutional records or sourced stated positions
- what evidence is missing

Race and challenger views should point back to the strongest available evidence, not displace the current-representative accountability flow.

## Evidence Ladder

All candidate and official reads must identify the evidence tier behind them.

### Tier 1 - Recorded Governing Behavior

Highest confidence.

Examples:

- roll-call votes
- signed or vetoed bills
- executive actions
- official amendments and sponsorships when source-grounded

Use this tier whenever available. It is the primary product differentiator.

### Tier 2 - Institutional Record

Medium confidence.

Examples:

- bill sponsorship and cosponsorship patterns
- committee roles
- attendance and participation records
- official public office history

This can provide useful context but must not be presented as equivalent to a direct vote.

### Tier 3 - Sourced Stated Positions

Lower confidence than governing behavior.

Examples:

- campaign website issue pages
- official questionnaires
- debate transcripts
- public candidate statements
- interviews or written pledges

Use for challengers or new candidates with no voting record. Label clearly as stated position, not demonstrated governing behavior.

### Tier 4 - Insufficient Evidence

When reliable source material is missing, the product should say so plainly.

No guesses. No filler. No pretending a weak source is strong.

## Product Shape

### 1. ZIP Entry

The first user action remains simple: enter a ZIP code.

The response should eventually include:

- current House representative
- current senators
- upcoming federal races
- state-level offices where available
- local races where available and reliable

### 2. Current Officials

For incumbents with voting records, show:

- interpreted issue patterns
- yea/nay record by issue
- evidence drilldowns
- source links
- confidence/coverage notes

### 3. Civic Actions

From an official, issue, or vote evidence row, users should be able to:

- open official contact information when available
- draft their own ask or thank-you anchored to a cited vote
- save an issue or vote to track
- return later to see whether new interpreted evidence has been added

The action layer must preserve source context and avoid persuasive defaults.

### 4. Race Pages

For each upcoming race, show candidates side by side using the evidence ladder:

- incumbent voting record when available
- challenger voting record when they previously held office
- stated positions when no voting record exists
- source and confidence labels for each claim
- issue-by-issue comparison based on the user's selected interests

### 5. User Issues

The user should be able to say:

- I care about this issue.
- I want to see support-side records.
- I want to see oppose-side records.
- I just want the record without an alignment label.

The product may describe alignment to those explicit preferences, but must never become a voting recommendation.

### 6. Plain-English Translation

Every interpreted vote should be able to answer:

- What was this vote about?
- What would a yea vote do?
- What would a nay vote do?
- How did this official vote?
- What source supports that interpretation?
- How confident is this interpretation?

## Feasibility Path

The current product already covers the first layer: current federal officials by ZIP, interpreted congressional votes, user-selected issues, and evidence drilldowns.

The path from here is expansion, not reinvention.

### Federal Accountability Proof

Build the strongest federal version first.

- current congressional officials by ZIP
- congressional roll-call vote interpretation
- contact and tracking actions for current officials
- upcoming federal races
- candidate records and stated positions for federal candidates

### One-State Pilot

After the federal flow is useful, pilot state-level coverage in one state, likely North Carolina.

- state legislative districts
- state legislative voting records where available
- statewide races
- sourced candidate positions

### Broader State Expansion

Add state adapters one by one. Do not assume states share formats.

### Local Coverage

Local races are valuable but should come after the federal and one-state proof.

Local data is fragmented and may require partnerships, manual curation, or third-party data sources.

## Guardrails

The expanded product must still avoid:

- ranking candidates or officials
- telling a user who to vote for
- moral judgments
- motive claims
- corruption claims
- donor-to-vote causal claims
- hidden scoring
- unsupported ideology inference
- treating stated positions as equal to recorded behavior

The product can be useful without being persuasive. Its job is to make the record easier to inspect.

## Success Criteria

The product is working when a user can say:

- I found who represents me.
- I picked issues I care about.
- I saw what the record shows.
- I understood what the votes actually meant.
- I knew what neutral next actions were available.
- I could contact, ask, thank, or track without the site telling me what to think.
- I found who is running next when that context was relevant.
- I could tell when evidence was strong, thin, or missing.
- I did not feel like the site was trying to tell me what to think.
