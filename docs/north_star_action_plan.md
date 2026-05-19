# North-Star Action Plan

## Destination

Build Political Fingerprint into a ZIP-first accountability product that helps users quickly inspect current representatives, understand how they are acting on personally important issues, and choose a neutral next action.

The product should answer:

**Who represents me, how are they acting on the issues I care about, and what can I do next?**

The product must keep its trust posture:

- actual governing behavior first
- current representatives before election context
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
- federal race and candidate context through FEC candidate-summary imports
- first candidate evidence seed for a challenger
- Render/Vercel staging path

Important current limitations:

- no civic action or contact layer
- no ask, thank, or track workflow
- limited contact metadata for current officials
- thin interpretation coverage outside the first high-visibility slices
- limited challenger or first-time candidate stated-position records
- no state legislative voting records
- no state election coverage
- no local election coverage

## Frontend Structure Review

The current frontend already supports most of the accountability-first direction:

- `frontend/app/page.js` opens with ZIP lookup, then current profile, quick read, issue preferences, alignment, vote evidence, and comparison.
- `ProfileQuickRead`, `AlignmentPanel`, and `PositionByIssue` are the strongest accountability surfaces.
- `PositionByIssue` now includes the best interpreted evidence card pattern: `Why this mattered`, `What this vote was`, and `Their vote`.
- `ZipLookupPanel` now fetches race context but the home page renders `UpcomingRacePanel` below the representative accountability, evidence, action, and comparison flow.
- `PositionByIssue` now includes a UI-only contact/action panel with editable contact, ask, thank, and session-only track states.

Recommended structure:

1. Keep ZIP lookup and current representative cards first.
2. Keep current profile, quick read, user issues, alignment, and interpreted evidence as the main body.
3. Add a new action layer after evidence, where the user can contact, ask, thank, or track from a specific official/issue/vote.
4. Keep upcoming race context below the accountability flow and collapsed behind a secondary section after current-representative evidence.
5. Keep comparison framed around current officials and selected issues unless the user explicitly opens election context.

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

## Civic Action Model

The action layer should be evidence-linked but not persuasive.

Allowed action types:

- `contact`: open official contact paths and preserve the related evidence context
- `ask`: help the user ask a representative about a vote, issue, or missing evidence
- `thank`: help the user reference a recorded vote or action they appreciate
- `track`: save an issue, official, race, or vote for later review

Action rules:

- actions are user-directed and optional
- suggested text must be neutral, editable, and tied to cited evidence
- no action can imply a voting recommendation
- no action can change alignment math or evidence tiers
- contact metadata should be stored separately from vote and candidate evidence

## Phase A - Representative Accountability Dashboard

Goal: make the current federal representative product compelling enough to prove the core value before adding more election complexity.

Deliverables:

- expand cached vote interpretations across more high-visibility federal votes
- prioritize records surfaced by common ZIP demos and starter issue bundles
- improve plain-English summaries where official titles are too vague
- keep all interpretations cached and source-grounded
- add coverage indicators showing interpreted versus uninterpreted records per issue
- make the current representative dashboard the obvious primary screen after ZIP lookup
- demote upcoming races to a secondary section below the accountability flow

Acceptance criteria:

- a user entering a loaded ZIP can find at least several meaningful DC-speak breakdowns
- issue pattern cards show useful coverage instead of mostly empty states
- every interpretation links to source material
- no copy tells the user what to think

## Phase B - Civic Action / Contact Layer

Goal: let users move from evidence inspection to a neutral next action with their current representatives.

Backend deliverables:

- contact metadata model or read adapter for current legislators
- stored action-intent schema if tracking is implemented server-side
- action type enum: contact, ask, thank, track
- source/evidence reference fields for actions tied to votes or issues
- tests proving actions do not affect alignment, vote interpretation, or candidate evidence

Frontend deliverables:

- action entry points from representative profile, issue pattern cards, and evidence rows
- contact card for official phone/site/contact-form links when available
- ask/thank affordance that keeps the cited vote and source visible
- track affordance for issue, official, or vote
- neutral empty states when contact metadata is missing

Acceptance criteria:

- user can open a current representative's contact path from the accountability dashboard
- user can start an ask or thank flow from a specific interpreted vote
- user can track an issue or vote without creating a score, ranking, or recommendation
- all action copy remains neutral and user-directed

## Phase C - Interpretation Coverage Expansion

Goal: scale the gold-slice interpretation standard before adding more surface area.

Deliverables:

- visually review the Valerie Foushee / `ECONOMY_TAXES` gold slice
- replicate the standard to the next visible Valerie issue domain
- expand to the NC senators' highest-visible starter issue gaps
- add coverage metadata that distinguishes reviewed, interpreted, ambiguous, and insufficient-evidence rows
- update manual interpretation workflow examples as quality patterns improve

Acceptance criteria:

- the most common loaded ZIP path has multiple issue domains with practical vote meaning
- procedural or unclear rows remain explicit evidence-boundary cases
- frontend cards avoid generic bill-passage language in reviewed slices

## Phase D - Federal Election Context As Secondary

Goal: keep federal race and challenger context useful without making it the primary journey.

Current status:

- FEC candidate-summary race context is imported to Supabase.
- High-confidence incumbent linkage is available for current federal legislators.
- The frontend can render upcoming federal races and candidate evidence rows.
- Remaining work is mostly hierarchy, source documentation, and evidence-tier polish.

Deliverables:

- keep FEC candidate-summary race context as secondary election data
- document cost, license, freshness, and coverage tradeoffs for FEC and any supplemental sources
- keep upcoming races visually separate from current representative evidence
- add another reviewed candidate evidence seed only after the accountability/action layer has a clear path

Acceptance criteria:

- the user can ignore election context and still complete the accountability flow
- one preferred federal race data source or source combination is documented
- licensing and cost are understood
- candidate identity matching risk is documented
- challenger evidence remains clearly lower confidence than recorded votes

## Phase E - Federal Race Schema And API

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

## Phase F - Candidate Evidence Tiers

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

## Phase G - Race Comparison Experience

Goal: support ballot-aware comparison after the current-representative accountability and action flow is solid.

User flow:

1. enter ZIP
2. select issues
3. see current officials
4. inspect evidence and choose any current-representative action
5. optionally see upcoming federal races
6. open a race
7. compare candidates by evidence tier and issue

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

## Phase H - North Carolina State Pilot

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

## Phase I - Broader State And Local Expansion

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

1. Define the minimal contact metadata source/update workflow for current federal officials beyond the NC pilot rows.
2. Expand manual federal vote interpretations for the next most visible current-official issue domain.
3. Add action-layer tests proving UI-only action state does not change alignment labels, vote interpretation, or evidence tiers.
4. Keep newsletter/email tracking out of scope until users validate that persistent reminders are actually needed.
5. Keep race/candidate work to maintenance and neutral evidence-tier cleanup until the accountability/action path is coherent.

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
