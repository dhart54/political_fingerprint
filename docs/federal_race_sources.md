# Federal Race Data Source Notes

## Current Decision

Use FEC candidate summary bulk data for the first federal race ingestion path.

Why:

- official federal source
- available as CSV bulk data
- covers U.S. House, U.S. Senate, and presidential candidates
- includes candidate id, office, state, district, party, and incumbent/challenger/open-seat indicator
- low operating cost because it can be pulled on a batch schedule and cached in Postgres

Important limitation:

FEC candidate summary data is candidate/race context. It does not prove a candidate is certified on a state ballot, and it does not provide issue positions. The product should label FEC-only candidates as insufficient evidence for issue alignment until recorded governing behavior or sourced stated positions are linked.

## Source Tradeoffs

### FEC Candidate Summary Bulk Data

Primary reference: `https://www.fec.gov/campaign-finance-data/candidate-summary-file-description/`

Cost:

- no paid vendor required
- downloadable bulk files and OpenFEC API access are available from FEC.gov
- low runtime cost because ingestion can be batch/cached

License / access:

- official federal source
- intended for public campaign-finance and candidate research workflows
- still requires source URL, source type, cycle, and retrieval date on imported rows

Freshness:

- good for candidate registration and campaign-finance context
- not a real-time ballot-certification feed
- should be refreshed on a scheduled batch cadence during election cycles and before demos

Coverage:

- U.S. House, U.S. Senate, and presidential candidates
- includes candidates registered with the FEC or appearing on an official state ballot, depending on the file row
- does not cover state or local offices
- does not provide issue positions or governing behavior

Decision:

- keep as the primary federal candidate/race context source
- treat FEC-only candidates as `insufficient_evidence` for issue alignment
- link incumbents to voting records only through high-confidence identity matching

### Google Civic Information API

Primary references:

- `https://developers.google.com/civic-information`
- `https://developers.google.com/civic-information/docs/using_api`

Cost:

- no data vendor contract in the current plan, but API-key and quota management are required
- quota limits can affect reliability for public traffic

License / access:

- requires an API key
- tied to Google Developer policies and available election IDs

Freshness:

- useful during supported elections
- depends on elections covered by the Voting Information Project and Google's current data availability

Coverage:

- can provide election, polling place, early vote, candidate, and election-official information during supported elections
- better suited for address-level ballot lookup near an election than for standing race-cache infrastructure

Decision:

- defer until the product needs address-level ballot lookup
- do not use it as the first federal race cache

### Ballotpedia

Primary references:

- `https://developer.ballotpedia.org/dictionaries-and-terms/terms-of-use`
- `https://developer.ballotpedia.org/downloading-bulk-data-via-api`

Cost:

- likely paid/licensed for API or bulk-data use
- not appropriate for the current sub-$50/month operating constraint without a separate agreement

License / access:

- data client terms restrict sharing full data sets
- requires separate source and terms review before any ingestion

Freshness:

- potentially useful for candidate profile coverage and state/local context
- freshness depends on Ballotpedia's editorial/data pipeline and license tier

Coverage:

- broad candidate, office, and election context
- may help with challenger background or local/state coverage later
- should not replace official election-office sources for ballot certification

Decision:

- defer
- use only after a licensing review and only with clear evidence-tier labels

### State Election Offices

Primary reference pattern: state election-office source pages and downloadable candidate/ballot files for the target state.

Cost:

- usually no paid vendor for public files, but formats vary by state
- higher engineering and maintenance cost than FEC because every state is different

License / access:

- authoritative for ballot certification within each state
- terms and file formats must be reviewed state by state

Freshness:

- best source for certified ballot status and state/local races
- update cadence varies by office and filing calendar

Coverage:

- authoritative for that state
- no national normalized schema

Decision:

- use state offices for state pilots and eventual ballot certification
- do not build a national state/local ingestion path until the NC pilot proves source quality and maintenance cost

## Deferred Sources

Google Civic Information API:

- useful near supported elections for voter-specific ballot information
- coverage is election-window dependent
- better suited for later address-level ballot lookup than for the first standing federal race cache

Ballotpedia:

- likely useful for candidate pages and broader state/local coverage
- requires separate source and terms review before ingestion

State election offices:

- authoritative for ballot certification
- formats vary state by state
- better handled after federal proof and North Carolina pilot planning

## Import Boundary

The initial importer:

- reads a local FEC candidate summary CSV
- writes `upcoming_races`
- writes `race_candidates`
- uses `external_candidate_id` for idempotent candidate updates
- marks candidates as `declared_candidate`
- marks FEC-only evidence as `insufficient_evidence`

The importer must not:

- infer candidate issue positions
- link candidate identities to legislators unless confidence is high
- replace state-certified ballot records when those become available
- generate candidate rankings or recommendations
