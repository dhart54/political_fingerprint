# North-Star Action Plan

## Destination

Build Political Fingerprint into a ZIP-first civic product that helps users quickly inspect who represents their interests at the national and state level.

The product should answer:

**Who represents me, who is running next, and what does the evidence show about how they act on the issues I care about?**

The product must keep its trust posture:

- actual governing behavior first
- sourced stated positions only when no governing record exists
- confidence labels everywhere evidence quality changes
- no candidate rankings
- no voting recommendations
- every claim traceable to source material

## Current State

What exists now:

- ZIP lookup for current federal representation
- current House representative and senators
- interpreted congressional vote records for a first manual batch
- issue preference selection
- alignment labels against interpreted votes
- evidence drilldowns with source links
- interpreted issue pattern cards
- Render/Vercel staging path

Important current limitations:

- no upcoming race data
- no candidate roster data
- no challenger or first-time candidate stated-position records
- no state legislative voting records
- no state election coverage
- no local election coverage
- interpretation coverage is still thin outside the first high-impact batch

## Guiding Architecture

Use an evidence-ladder architecture.

### Tier 1: Recorded Governing Behavior

Use for incumbents and prior officeholders whenever available.

Data examples:

- congressional roll-call votes
- state legislative roll-call votes
- signed or vetoed bills
- official executive actions

Product output:

- issue pattern cards
- vote drilldowns
- yea/nay meaning
- alignment against explicit user preferences

### Tier 2: Institutional Record

Use as supporting context, not as direct issue alignment unless methodology supports it.

Data examples:

- bill sponsorship and cosponsorship
- committee roles
- public-office history
- attendance or participation records

Product output:

- candidate context
- evidence notes
- optional issue indicators only when source-grounded

### Tier 3: Sourced Stated Positions

Use for candidates with no voting record.

Data examples:

- campaign issue pages
- official questionnaires
- debate transcripts
- public candidate statements

Product output:

- stated-position cards
- lower-confidence labels
- source URLs and retrieved dates
- separate display from recorded vote behavior

### Tier 4: Insufficient Evidence

Use whenever the source trail is weak, missing, or ambiguous.

Product output:

- explicit insufficient-evidence state
- no inferred stance
- no filler claims

## Phase A - Stabilize The Federal Current-Official Proof

Goal: make the current federal product compelling enough to prove the core value before adding ballot complexity.

Deliverables:

- expand cached vote interpretations across more high-visibility federal votes
- prioritize records surfaced by common ZIP demos and starter issue bundles
- improve plain-English summaries where official titles are too vague
- keep all interpretations cached and source-grounded
- add coverage indicators showing interpreted versus uninterpreted records per issue

Acceptance criteria:

- a user entering a loaded ZIP can find at least several meaningful DC-speak breakdowns
- issue pattern cards show useful coverage instead of mostly empty states
- every interpretation links to source material
- no copy tells the user what to think

## Phase B - Federal Ballot Data Spike

Goal: decide how upcoming federal races and candidate rosters will enter the system.

Research tasks:

- identify candidate/race data sources for upcoming federal elections
- evaluate source cost, license, freshness, API reliability, and coverage
- determine whether race data can be stored within the current cost target
- document source update cadence and failure modes

Likely data categories:

- election cycle
- office
- state
- district
- election date
- candidate name
- party when available
- incumbent/challenger flag when available
- source URL
- source retrieved date

Deliverables:

- data source decision memo
- schema proposal for races and candidates
- update cadence recommendation
- ingestion plan with dry-run mode

Acceptance criteria:

- one preferred federal race data source or source combination is chosen
- licensing and cost are understood
- candidate identity matching risk is documented
- no implementation begins until source terms are acceptable

## Phase C - Federal Race Schema And API

Goal: add upcoming federal races without changing the trust model.

Backend deliverables:

- `upcoming_races` table
- `race_candidates` table
- candidate-to-legislator linkage field for incumbents and prior officeholders
- source provenance fields
- migration tests
- seed fixtures
- `GET /lookup/zip/{zip}/races` or equivalent
- API tests for loaded, empty, and unknown ZIP states

Frontend deliverables:

- "Your Upcoming Federal Races" section after ZIP lookup
- neutral race cards
- race status labels such as upcoming, active, or past
- empty states for unavailable race data

Acceptance criteria:

- ZIP lookup can show current officials and upcoming federal races separately
- candidates are not ranked
- candidate cards expose source and confidence state
- the experience remains useful when race data is missing

## Phase D - Candidate Evidence Tiers

Goal: compare candidates by the strongest available evidence.

Backend deliverables:

- `candidate_evidence` table
- evidence tier enum
- issue domain mapping
- source URL
- source type
- source retrieved date
- confidence label
- statement or record summary
- candidate evidence endpoint

Rules:

- incumbent candidate cards should link to existing legislator voting records
- prior officeholders may link to prior recorded behavior when identity matching is reliable
- first-time candidates may show sourced stated positions only
- stated positions must never be counted as equivalent to votes

Frontend deliverables:

- evidence tier badges
- "Recorded votes" section
- "Stated positions" section
- "Insufficient evidence" state
- source expansion for every claim

Acceptance criteria:

- at least one incumbent-versus-challenger federal race can render with mixed evidence tiers
- users can tell which claims come from votes and which come from statements
- tests prove stated positions do not feed vote-based alignment math

## Phase E - Race Comparison Experience

Goal: turn the product from current-official inspection into ballot-aware comparison.

User flow:

1. enter ZIP
2. select issues
3. see current officials
4. see upcoming federal races
5. open a race
6. compare candidates by evidence tier and issue

UI deliverables:

- race panel or race page
- candidate columns or stacked mobile cards
- issue-by-issue comparison
- evidence strength labels
- source drilldowns
- no aggregate candidate score

Acceptance criteria:

- user can compare an incumbent with voting history to a challenger with stated positions
- the UI does not imply the two evidence types are equally strong
- all comparison claims are expandable to sources
- missing evidence feels intentional, not broken

## Phase F - North Carolina State Pilot

Goal: prove state-level feasibility in one state before national state coverage.

Research tasks:

- identify NC election data source for state races
- identify NC legislative roll-call source
- identify NC district mapping requirements
- document source format, update cadence, and reliability

Backend deliverables:

- state office model extension if needed
- NC race ingestion prototype
- NC state legislative vote ingestion prototype if feasible
- source-specific methodology notes

Frontend deliverables:

- state race cards under ZIP lookup
- evidence labels that distinguish federal and state data sources

Acceptance criteria:

- one NC state race or office can be shown from source-backed data
- methodology clearly explains any differences from federal data
- source quality is good enough to justify continuing state expansion

## Phase G - Broader State And Local Expansion

Goal: scale only after the federal and NC pilot flows prove useful.

State expansion rules:

- add states one at a time
- document each source adapter
- avoid assuming shared formats
- require source provenance and update cadence

Local expansion rules:

- treat local coverage as a separate product tier
- evaluate data vendor or civic-data partnership options
- avoid hand-maintaining local data at national scale without a clear workflow

Acceptance criteria:

- state adapters are repeatable
- source-quality labels remain visible
- local coverage does not degrade trust in federal/state coverage

## Immediate Next Tasks

1. Confirm deployed staging includes the latest interpreted issue pattern cards.
2. Expand manual federal vote interpretations for the most visible demo paths.
3. Run a data-source spike for upcoming federal races. Initial decision: use FEC candidate summary data for declared federal candidate/race context, while labeling it separately from ballot certification and issue evidence.
4. Review and refine the fixture-backed race/candidate schema now present in migration `0004_upcoming_races.sql`.
5. Smoke-test the fixture-backed "Upcoming Federal Races" section for ZIP `27701`.
6. Add source-research notes before wiring live race data.
7. Wire the initial FEC candidate-summary importer into Supabase with a dry-run first.
8. Add candidate-to-legislator matching only when identity confidence is high enough to avoid false voting-record links.

## Decision Rules

Prefer a narrower feature when:

- the source is official or highly reliable
- the evidence tier is clear
- the user can inspect source material
- the feature helps the user reach a useful answer faster

Reject or defer a feature when:

- it requires ranking candidates
- it hides source quality
- it treats statements like votes
- it makes unsupported ideology or motive claims
- it would create large maintenance burden before the federal proof is compelling
