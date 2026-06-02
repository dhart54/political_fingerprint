# North Carolina State Pilot Source Plan

This note scopes a cautious North Carolina state-level pilot. It should not be treated as approval for broad state expansion.

## Pilot Goal

Prove one state-level accountability path for a loaded North Carolina ZIP:

1. identify the user's current NC House and NC Senate districts
2. show current state legislators when source-backed identity data is available
3. ingest a small, reviewed set of NC General Assembly roll-call votes
4. keep state race context secondary and clearly separate from federal records

Do not mix state records into federal fingerprints until state methodology, source fields, and chamber-specific vote rules are documented.

## Source Inventory

### State Election / Candidate Data

Primary source: North Carolina State Board of Elections candidate lists.

Useful fields:

- election date
- county
- contest name
- candidate name and ballot name
- filing date
- party
- contest term and vote-for count
- candidate contact fields where included by file type

Access method:

- download CSV candidate spreadsheet for the election year
- use PDF candidate-by-contest lists only as review/audit material
- filter contests to `NC Senate` and `NC House` for the first pilot

Reliability:

- official state election source
- available at the start of candidate filing periods
- updated daily during filing periods and as needed before an election

Limitations:

- candidate lists are not always final
- 2026 general lists may be temporarily incomplete while county boards add candidates
- candidate rows do not provide issue positions
- source files may include personal/contact fields, so store only fields needed for product display and provenance

Recommended cadence:

- daily during filing periods for the target election
- weekly after filing closes until certification stabilizes
- manual review before any public demo

### Legislative Voting Data

Primary source: North Carolina General Assembly bill/vote pages and NCGA web services.

Useful fields:

- bill number and session
- bill title
- chamber
- roll-call number or RCS number when available
- vote date
- vote subject
- aye/no/not-voting/excused counts
- individual member votes
- bill history/action links

Access method:

- begin with NCGA bill pages and the `Votes on Bills` surface for one reviewed bill
- prefer NCGA web services where an endpoint exposes the required bill/vote records
- if an endpoint does not expose per-member vote details cleanly, keep the first pilot as a reviewed/manual packet workflow rather than a broad crawler

Reliability:

- official legislative source
- Legislative Library states individual member voting reports are available online from 1997-present
- roll-call votes are electronically recorded for each member; voice votes are not member-level roll calls

Limitations:

- voice votes should be excluded from behavior fingerprints because they do not provide member-level positions
- amendment, motion, second-reading, concurrence, veto-override, and procedural subjects need state-specific interpretation rules
- NCGA source pages may expose data through HTML and web services in different shapes than Congress.gov/House Clerk/Senate XML
- committee votes and archived audio are out of scope for the first pilot

Recommended cadence:

- nightly during active legislative sessions once an adapter exists
- manual reviewed interpretation batches before any public-facing state vote meaning
- rerun after session adjournment to stabilize late corrections

### District Mapping

Primary sources:

- NCSBE voting maps/redistricting geospatial folders
- NCGA redistricting maps, shapefiles, block assignment files, and reports

Useful fields:

- NC House district boundaries
- NC Senate district boundaries
- district plan name and election-use status
- source year / enactment status
- block assignment or shapefile path

Access method:

- use current NCSBE NC House and NC Senate district shapefile folders for election-facing district maps
- use NCGA redistricting pages to confirm plan status and access block assignment files
- use geocoded address or ZCTA/precinct approximation only as a separate, confidence-labeled mapping layer

Reliability:

- official state election and legislative map sources
- NCSBE links current and past geospatial files for precincts, legislative districts, and congressional districts
- NCGA publishes historical/current plan files, including shapefiles and block assignment files

Limitations:

- ZIP code alone is not sufficient for reliable state legislative district lookup
- a ZIP can cross multiple NC House or NC Senate districts
- NCGA's public `Find Your Legislators` tool is address-based and notes results reflect an address point returned by a commercial geocoder
- for product accuracy, state district lookup should require address-level geocoding or clearly label ZIP-only results as approximate/multiple-district coverage

Recommended cadence:

- update when NCSBE or NCGA publishes a new district plan for an election cycle
- do not assume congressional, NC House, and NC Senate maps change together
- preserve plan name/effective election year with every mapping import

## Recommended Pilot Shape

Start with a source-backed but narrow NC pilot:

1. Pick one loaded NC ZIP that already matters to the federal demo, such as `27701`.
2. Do not infer state districts from ZIP alone. First show a "state coverage requires address-level lookup" note, or use a reviewed single-address fixture for the pilot.
3. Add state-specific tables only after the source packet shape is proven:
   - `state_legislators`
   - `state_roll_calls`
   - `state_votes_cast`
   - `state_vote_interpretations`
   - `state_district_maps`
   - optional `state_races` and `state_race_candidates`
4. Keep state evidence visually labeled as `NC General Assembly`, not federal.
5. Keep state race cards below the current official accountability flow.

## First Adapter Tasks

1. Download and inspect the current NCSBE candidate CSV layout.
2. Download current NC House and NC Senate district shapefiles or block assignment files.
3. Pick one NCGA bill page with multiple roll calls and verify whether the web services surface exposes enough structured data.
4. Draft a manual state vote packet format before writing a broad ingestion job.
5. Add methodology notes for NC-specific vote subjects:
   - second reading
   - third reading
   - concurrence
   - conference report
   - veto override
   - amendments
   - motion to table
   - previous question / procedural motions

## Go / No-Go Criteria

Go if:

- current district mapping can be made address-accurate or clearly labeled as approximate
- NCGA roll-call pages or web services expose member-level votes with stable identifiers
- candidate lists include enough contest metadata to show state races neutrally
- source provenance can be stored for every displayed row

No-go or defer if:

- only ZIP-level district mapping is available for state legislators
- member-level vote records require fragile scraping with no stable identifiers
- candidate files are incomplete for the target election
- state vote interpretation would require guessing procedural meaning

## Product Boundaries

- State records must not be merged into federal issue counts.
- State candidate rows must not be ranked.
- State stated positions, if added later, remain lower confidence than state roll-call votes.
- Voice votes, committee audio, and unverifiable summaries stay out of alignment math.
- Any state pilot UI must tell the user when evidence is state-level rather than federal-level.
