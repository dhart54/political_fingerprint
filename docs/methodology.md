# Methodology

## Product Scope and Guardrails

This MVP is a curiosity-led, trust-anchored civic analytics platform focused on observable legislative behavior.

The current product scope is limited to:

- behavioral fingerprint
- stability or drift indicator
- plain-language descriptive summary
- ZIP code lookup for one House representative and two senators

The methodology intentionally does not support:

- corruption claims
- donor-to-vote causal claims
- predictive modeling
- ranking language
- moral judgments
- composite influence scoring

## System Principles

Implemented logic follows these repository-wide priorities:

- determinism
- transparency
- reproducibility
- low operational cost
- simplicity

All metric-producing logic must remain a deterministic function of stored inputs.

## Stack and Deployment Assumptions

The current MVP implementation is built for:

- Python 3.11+ with FastAPI on the backend
- Postgres as the system database
- Next.js with Tailwind CSS on the frontend
- precompute-heavy deployment on Render and Vercel within the locked cost target

## Precomputed Data Rule

API endpoints must read precomputed outputs rather than computing metrics on request.

The authoritative computed outputs are:

- `vote_classifications`
- `fingerprints`
- `chamber_medians`
- `drift_scores`
- `summaries`

Current repository state uses a database-first read layer for these outputs.

If the database is unavailable in local development, the repository currently falls back to the deterministic fixture-backed precomputed store so local validation remains usable before the seed flow is in place.

## Eligibility Rules

Vote eligibility is deterministic.

Procedural votes are excluded before classification, fingerprinting, median calculation, and drift calculation.

The current procedural exclusion rule marks a roll call as procedural when the vote question or description contains any of these case-insensitive keywords:

- `cloture`
- `motion to proceed`
- `quorum`
- `adjourn`
- `rule`
- `tabling`
- `recommit`
- `reconsider`
- `point of order`

If a procedural keyword is present:

- `is_eligible = false`
- `eligibility_reason = "procedural_vote"`

Otherwise:

- `is_eligible = true`
- `eligibility_reason = "policy_vote"`

## Classification Rules

Policy vote classification is deterministic and uses weighted scoring across three signal types:

- committee match: `+3`
- keyword match: `+2` per matched keyword
- subject-tag match: `+2` per matched subject tag

The classifier evaluates all 8 locked issue domains:

- `ECONOMY_TAXES`
- `HEALTH_SOCIAL`
- `EDUCATION_WORKFORCE`
- `ENVIRONMENT_ENERGY`
- `NATIONAL_SECURITY_FOREIGN`
- `IMMIGRATION_BORDER`
- `JUSTICE_PUBLIC_SAFETY`
- `INFRASTRUCTURE_TECH_TRANSPORT`

Inputs:

- committee name
- bill title
- bill summary
- subject tags

Process:

1. Normalize all text to lowercase.
2. Sum weighted committee, keyword, and subject-tag signals for each domain.
3. Select the highest-scoring domain.
4. If the top score is below `3`, mark the vote ineligible with `eligibility_reason = "low_classification_confidence"`.

Stored outputs:

- `primary_domain`
- `score_breakdown`
- `classification_version`

## Fingerprint Rules

Fingerprint calculation is deterministic and uses only eligible classified policy votes.

Window:

- rolling 730 days ending on the computation date

For each legislator and each locked issue domain:

- `vote_count` = count of eligible votes in that domain within the 730-day window
- `total_votes` = count of all eligible votes across all domains within the same window
- `vote_share` = `vote_count / total_votes`

Explicit-zero rule:

- if `vote_count = 0`, the domain row is still stored
- if `total_votes = 0`, then `vote_share = 0.0`

Fingerprint output always includes all 8 domains and never omits a domain row.

## Drift Rules

Drift is deterministic and uses the same 730-day window as the fingerprint.

Window split:

- early window: older 365 days
- recent window: newer 365 days

For each half-window, compute a domain share vector across the 8 locked issue domains.

Formula:

- `drift = 0.5 × sum(abs(P_recent[D] - P_early[D]))`

Constraints:

- `0 <= drift <= 1`
- if total eligible votes in the full 730-day window are fewer than `20`, then:
  - `insufficient_data = true`
  - `drift_value = null`

No estimation or extrapolation is used.

## ETL Order

The ETL pipeline is deterministic, idempotent in design, and versioned through `classification_version`.

Current operation order:

1. ingest fixture source records
2. evaluate procedural eligibility for each roll call
3. classify eligible policy votes into one primary domain
4. build eligible vote records for legislators
5. compute fingerprints
6. compute chamber medians
7. compute drift scores

In the current fixture-backed implementation, ingestion loads:

- legislators
- bills
- roll calls
- votes cast
- subject tags
- ZIP mappings

The repository now also includes a deterministic local database seed path:

- `python -m app.etl.run_all --fixtures`

Current seed behavior:

- rebuilds the local database from fixtures
- writes source tables plus precomputed outputs
- uses stable integer ids derived from fixture order
- fully replaces previously seeded rows so repeated runs are idempotent for local development

The ETL runner also supports a compute-only mode for local inspection without database writes:

- `python -m app.etl.run_all --fixtures --compute-only`

## Fixture Dataset

The local fixture dataset lives under `backend/fixtures/` and is the authoritative development dataset before live ingestion is introduced.

Current fixture implementation includes:

- 3 legislators
- 12 bills
- 14 roll calls
- 10 policy roll calls
- 2 procedural roll calls
- 2 low-confidence roll calls
- 2 ZIP mappings

The ETL fixture runner loads the fixture files, classifies roll calls deterministically, builds eligible votes, and computes fingerprints, chamber medians, and drift results in a local deterministic pass.

For this repository state, fixture design prioritizes the `10` policy roll call requirement. Under the locked drift threshold of `20` total eligible votes, that means fixture drift outputs remain `insufficient_data` for all three legislators.

## Live Source Adapters

The repository now includes non-fixture ingestion adapters through:

- `source="congress_sample"`
- `source="house_clerk_sample"`
- `source="house_clerk_cache"`
- `source="senate_xml_sample"`
- `source="senate_xml_cache"`

Current source assumptions:

- `congress_sample` input records are official-style Congress JSON exports stored locally
- `congress_sample` member records provide `bioguideId`, display name, chamber, state, district, and party code
- `congress_sample` bill records provide congress, bill type, bill number, title, summary, committee, and subjects
- `congress_sample` roll call records provide chamber, congress, roll number, ISO vote date, question, description, bill reference, and source URL
- `congress_sample` vote records provide chamber, roll number, member display name, and vote position
- `house_clerk_sample` input records are official-style House Clerk member XML and roll call XML samples stored locally
- `house_clerk_cache` reads downloaded House Clerk roll call XML from `backend/data_sources/house_clerk/`
- `house_clerk_sample` bill metadata is enriched from local Congress.gov-style bill JSON keyed by congress, bill type, and bill number
- `house_clerk_sample` member records provide `bioguideID`, official display name, party, state postal code, and state-district code
- `house_clerk_sample` roll call records provide congress, session, roll call number, `legis-num`, `vote-question`, `vote-desc`, and action date
- `house_clerk_sample` votes are matched to legislators by `bioguide-id`
- `senate_xml_sample` input records are official-style Senate roll call XML and local Senate member XML samples stored locally
- `senate_xml_cache` reads downloaded Senate roll call XML from `backend/data_sources/senate_xml/`
- `senate_xml_sample` bill metadata is enriched from local Congress.gov-style bill JSON keyed by congress, bill type, and bill number
- `senate_xml_sample` member records provide `lis_member_id`, `bioguide_id`, display name, state, and party
- `senate_xml_sample` roll call records provide congress, session, vote number, vote date, question, vote title, and document number
- `senate_xml_sample` votes are matched to legislators by `lis_member_id`

Current adapter behavior:

- normalizes official-style fields into the existing ingest bundle shape
- derives stable internal ids for legislators, bills, and roll calls
- for House Clerk samples, derives bill identity from `legis-num` and enriches title, summary, committee, and subjects from matching Congress-style metadata when available
- for House Clerk cache ingestion, downloaded roll call XML can be used directly while bundled sample metadata files remain the fallback for members, bill metadata, and ZIP mappings until those fetch layers are added
- for Senate XML samples, derives bill identity from the document number and enriches title, summary, committee, and subjects from matching Congress-style metadata when available
- for Senate XML cache ingestion, downloaded roll call XML can be used directly while bundled sample metadata files remain the fallback for members, bill metadata, and ZIP mappings until those fetch layers are added
- for Senate XML cache ingestion, vote files that reference senators missing from the current member roster snapshot synthesize deterministic fallback legislator records from the vote payload instead of aborting the import
- for larger live-source imports, unsupported non-bill references and House rolls without a usable bill reference are skipped deterministically rather than failing the whole chamber import
- reuses the same downstream classification, metric, ETL write, and API read paths as fixture ingestion

## Official File Fetch Layer

The repository now includes a cached XML download utility in `app.etl.fetch_sources`.

Current supported fetch targets:

- House Clerk current member XML
- House Clerk roll call XML by calendar year and roll number
- Senate current member XML
- Senate roll call XML by congress, session, and roll number
- Congress.gov bill metadata JSON by congress, bill type, and bill number

Current fetch behavior:

- downloads official XML files into a caller-specified local directory
- downloads Congress.gov bill metadata JSON into `backend/data_sources/congress/bills/`
- uses deterministic official URL patterns for House Clerk and Senate XML vote files
- uses the Congress.gov v3 bill endpoint with an API key and JSON format parameter
- skips existing files unless `--overwrite` is provided
- writes downloads atomically through a temporary file replacement step

Current CLI examples:

- `python -m app.etl.fetch_sources house --year 2025 --roll 1 --output-dir ./tmp/house`
- `python -m app.etl.fetch_sources house-members`
- `python -m app.etl.fetch_sources senate --congress 119 --session 1 --roll 1 --output-dir ./tmp/senate`
- `python -m app.etl.fetch_sources senate-members`
- `python -m app.etl.fetch_sources congress-bill --congress 119 --bill-type hr --bill-number 120 --api-key YOUR_KEY`

## Live Pipeline Orchestration

The repository now includes a single orchestration entry point in `app.etl.live_pipeline`.

Current orchestration behavior:

- fetches House member XML before House roll call downloads when House roll numbers are requested
- fetches Senate member XML before Senate vote downloads when Senate roll numbers are requested
- infers bill references from downloaded House `legis-num` fields and Senate `document` fields when possible
- fetches Congress.gov bill metadata for the union of explicitly requested bill references and inferred bill references
- skips only `404 Not Found` Congress bill metadata responses deterministically so unresolved official bill references do not abort the whole import
- runs persistent ETL immediately after the fetch step
- persists a combined mixed-source seed bundle when both House and Senate cache inputs are present in the same run

Current CLI example:

- `python -m app.etl.live_pipeline --house-year 2025 --house-roll 1 --bill 119:hr:120 --congress-api-key YOUR_KEY`
- `python -m app.etl.live_pipeline --house-year 2025 --house-roll 1 --senate-congress 119 --senate-session 1 --senate-roll 1 --bill 119:hr:120 --bill 119:s:210 --congress-api-key YOUR_KEY`

## Starter Real-Data Run

The repository now includes a convenience starter script in `scripts/run_real_data_starter.py`.

Current starter behavior:

- targets one verified House example roll and one verified Senate example roll
- fetches the corresponding chamber member rosters
- fetches the related Congress.gov bill metadata
- runs the mixed House+Senate live pipeline into Postgres
- is intended as the fastest reproducible path to seeing non-sample stored data in the frontend

The repository also includes an expanded convenience script in `scripts/run_real_data_expanded.py`.

Current expanded-batch behavior:

- targets a larger curated set of recent House and Senate bill votes
- relies on live pipeline bill-reference inference from downloaded vote XML instead of a hand-maintained bill list
- broadens the stored real-data coverage so the frontend shows fewer zero-state legislator profiles

The repository also includes a bulk range import script in `scripts/run_real_data_bulk.py`.

Current bulk-script behavior:

- accepts explicit House and Senate roll numbers and inclusive roll ranges
- expands those ranges deterministically into sorted roll lists
- relies on the same live pipeline bill-reference inference from downloaded vote XML
- is intended for much larger real-data backfills than the starter or expanded scripts

## Fingerprint API

The fingerprint endpoint returns precomputed fingerprint rows only.

Default overlay behavior:

- chamber median overlay uses the `ALL` party grouping by default

Supported overlay toggle:

- `comparison_party=ALL`
- `comparison_party=D`
- `comparison_party=R`

The party toggle changes only the overlay median values. It does not change the legislator fingerprint itself.

## Drift API

The drift endpoint returns precomputed drift rows only.

Returned fields include:

- full 730-day window bounds
- early and recent half-window bounds
- total vote counts
- insufficient-data flag
- drift value

If a legislator is below the locked minimum vote threshold, the endpoint returns:

- `insufficient_data = true`
- `drift_value = null`

## Summary API

The summary endpoint returns cached summary text.

Current behavior:

- on first request, a deterministic fallback summary is generated from precomputed fingerprint and drift outputs when no stored summary row exists
- generated summaries are written to the `summaries` table and reused on later requests
- the cache key is based on legislator, window end, and classification version

The fallback summary is descriptive only and includes:

- vote volume
- the largest fingerprint emphasis areas
- drift availability or the insufficient-data condition

The summary layer must remain neutral:

- no causal claims
- no ranking language
- no motive inference
- no forbidden terms such as `corrupt`, `extreme`, `radical`, `worst`, `best`, `biased`, or `bought`

## ZIP Lookup API

The ZIP lookup endpoint returns fixture-backed legislator mappings for the requested ZIP code.

Returned data includes:

- ZIP code
- state
- congressional district
- House representative for that district
- both senators for that state

## Legislator Search API

The legislator search endpoint returns fixture-backed legislator records for frontend discovery.

Current behavior:

- supports case-insensitive substring matching against `name_display`
- returns all available legislators when the query is empty
- sorts results deterministically by display name, then legislator id
- returns stable identity and display fields for selection flows

## Frontend API Connectivity

The frontend home page performs a client-side health check against `NEXT_PUBLIC_API_BASE_URL`.

Current behavior:

- requests `GET /health`
- renders connected, checking, or unavailable status in the UI
- displays the configured API base URL so the active backend target is visible

## Fingerprint Radar UI

The frontend radar chart renders:

- the legislator fingerprint polygon from `vote_share`
- the chamber median overlay polygon from `median_share`

Current UI behavior:

- overlay defaults to `ALL`
- the user can toggle overlay comparison between `ALL`, `D`, and `R`
- the toggle changes only the median overlay, not the fingerprint values

## Drift Indicator UI

The frontend drift indicator renders the drift API result directly.

Current UI behavior:

- shows the deterministic drift value when available
- shows the insufficient-data state explicitly when the backend returns `insufficient_data = true`
- surfaces early and recent vote totals alongside the indicator

## Summary UI

The frontend summary panel renders the cached summary endpoint response directly.

Current UI behavior:

- displays the summary text returned by the backend
- surfaces generation method, window end, classification version, and created timestamp
- does not generate or rewrite summary text on the client

## ZIP Lookup UI

The frontend ZIP lookup panel calls the ZIP lookup API directly from the home page.

Current UI behavior:

- defaults to fixture ZIP `27701` for local verification
- requests `GET /lookup/zip/{zip}`
- renders the returned district, House representative, and both senators
- surfaces request failures explicitly instead of inferring fallback data on the client

## Legislator Selection UI

The frontend legislator picker uses the legislator search endpoint to drive the analysis panels.

Current UI behavior:

- loads available legislators from `GET /legislators/search`
- supports client-side search input backed by server search results
- updates fingerprint, drift, and summary panels together when a legislator is selected
- keeps ZIP lookup independent from the currently selected legislator

## Provenance UI

The frontend now surfaces provenance details near both the fingerprint and summary sections.

Current UI behavior:

- fingerprint UI shows last updated time, computation window end, and classification version
- summary UI shows last updated time, computation window end, and classification version
- both sections include a concise on-page methodology explainer instead of relying on hidden implementation details

## Summary UX

The frontend summary section keeps the stored summary text intact but presents it in a more scannable layout.

Current UI behavior:

- splits the returned summary into short insight blocks for faster reading
- keeps metadata visible but visually secondary to the narrative
- does not rewrite, rank, or reinterpret the stored summary text on the client

## Error and Empty States

The frontend now uses explicit user-facing empty and error states across the main product surfaces.

Current UI behavior:

- backend connectivity errors explain that the API may not be running
- legislator search errors avoid raw technical failure text
- fingerprint, drift, and summary failures show plain recovery guidance
- ZIP lookup validates 5-digit input before requesting data
- empty summary and fingerprint states are rendered explicitly instead of leaving blank sections

## Comparison API

The comparison endpoint bundles two legislators into one side-by-side response without changing single-legislator endpoints.

Current behavior:

- `GET /compare/legislators`
- requires `left_legislator_id` and `right_legislator_id`
- supports the same `comparison_party` overlay toggle as the fingerprint endpoint
- returns legislator metadata plus each side's fingerprint, drift, and summary payload
- does not add ranking, winner labels, or evaluative comparison language

## Comparison UI

The frontend comparison section uses the comparison endpoint to render two legislators side by side.

Current UI behavior:

- supports choosing a left and right legislator independently
- uses the same `ALL`, `D`, and `R` overlay context as the fingerprint comparison
- shows top fingerprint emphasis, drift state, and summary preview for each side
- labels both sides explicitly and avoids winner framing or ranked language
