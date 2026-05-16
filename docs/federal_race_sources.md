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
