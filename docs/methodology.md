# Methodology

## Product Scope and Guardrails

This product is a curiosity-led, trust-anchored civic analytics platform focused on observable legislative behavior.

The expanded product north star is documented in `docs/product_north_star.md`:

**Who represents me, how are they acting on the issues I care about, and what can I do next?**

The original MVP scope included:

- behavioral fingerprint
- stability or drift indicator
- plain-language descriptive summary
- ZIP code lookup for one House representative and two senators

The current Product v2 direction adds:

- position by issue
- source-grounded vote interpretation
- user-defined issue preferences
- evidence-based alignment between those preferences and recorded votes
- drilldowns from every high-level read to underlying roll calls and sources
- neutral civic contact paths for current representatives

The current product hierarchy is:

1. Representative Accountability Dashboard
2. Civic Action / Contact Layer
3. Election / Challenger Layer

The election and challenger layer remains secondary to current-representative accountability. Ballot-aware candidate comparison may expand when reliable election data is available, but it must not displace issue evidence, interpreted vote meaning, or neutral civic follow-through for current representatives.

The long-term election context adds ballot-aware candidate comparison:

- upcoming races by ZIP code when reliable election data is available
- incumbent and prior-officeholder comparison based first on recorded governing behavior
- new-candidate coverage based on sourced stated positions when no voting record exists
- explicit evidence-type and caution labels separating recorded behavior from stated positions
- evidence-tiered race pages that make strong, thin, and missing evidence clear

The methodology intentionally does not support:

- corruption claims
- donor-to-vote causal claims
- predictive modeling
- ranking language
- moral judgments
- composite influence scoring
- prescriptive voting advice
- personalized electoral persuasion

The product may say that a recorded voting pattern appears aligned, not aligned, mixed, or insufficiently evidenced relative to preferences the user explicitly selected. It must not tell the user how to vote.

When candidate stated positions are used, the product may say what the candidate claims or lists as a position, with source and date context when available. It must not present stated positions as proven governing behavior.

The product may support neutral contact workflows. Contact surfaces must be user-directed, source-linked when they reference evidence, and separate from all vote interpretation and alignment calculations. The current product shows official contact metadata and evidence context only; ask, thank, track, newsletters, and reminders are deferred until there is a validated need.

## System Principles

Implemented logic follows these repository-wide priorities:

- determinism
- transparency
- reproducibility
- low operational cost
- simplicity

All metric-producing logic must remain a deterministic function of stored inputs.

## Evidence Tiers

Product claims must be tied to an evidence tier.

Tier 1: recorded governing behavior.

- roll-call votes
- signed or vetoed bills
- official executive actions
- source-grounded amendments or sponsorships

Tier 2: institutional record.

- sponsorship and cosponsorship patterns
- committee roles
- attendance and participation records
- previous public office history

Tier 3: sourced stated positions.

- campaign issue pages
- official candidate questionnaires
- debate transcripts
- public candidate statements

Tier 4: insufficient evidence.

- no reliable source found
- source text is too ambiguous
- record is not yet available

Recorded governing behavior should be treated as the highest-confidence evidence. Stated positions may be useful for challengers or first-time candidates, but must be labeled as lower confidence than actual votes or official actions.

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
- `vote_interpretations`

Current repository state uses a database-first read layer for these outputs.

If the database is unavailable in local development, the repository currently falls back to the deterministic fixture-backed precomputed store so local validation remains usable before the seed flow is in place.

The comparison view remains descriptive, but it now uses two deterministic lenses:

- issue focus from precomputed fingerprint shares
- vote-direction context from stored `votes_cast.position` joined to eligible classified domains within the same 730-day fingerprint window

Vote-direction context is limited to per-domain `yea` versus `nay` shares. It does not infer ideology, motives, causal explanations, or the practical meaning of a vote. User-facing summaries must not use raw yea/nay shares alone as a "so what" interpretation.

User-specific alignment is the limited exception to the precomputed-output rule. Because user preferences are session inputs, alignment may be computed at request time as a lightweight comparison between explicit user preferences, stored vote positions, and precomputed vote interpretation records. The API must not classify votes, infer vote meaning, or run heavy aggregation during the request.

## Vote Interpretation Rules

Vote interpretation is the source-grounded record of what a yea or nay vote meant for a roll call when that can be determined.

Allowed inputs:

- chamber
- congress and session
- bill number or document number
- roll call number
- bill title
- bill summary
- bill subjects
- bill lifecycle details, including introduced date, origin chamber, latest action, and public law status when available
- bill text-version metadata
- bill action history
- amendment metadata
- committee activity metadata
- CBO cost-estimate links or descriptions when available
- CRS, JCT, committee-report, or other official explanatory context when available
- roll call question
- roll call description
- final roll call result, when available
- vote margin, when available
- party vote totals, when available
- sponsor party, when available
- whether the member voted with most of their party, when party totals are available
- whether the member voted with the winning side, when final result is available
- official source URL
- stored classification metadata

Stored outputs:

- `roll_call_id`
- `vote_type`, when determinable: final passage, amendment, rule, motion, concurrence, procedural, nomination, appropriations, CRA disapproval, or other
- `what_happened`, when reviewed source text supports it
- `why_it_mattered`, when reviewed source text supports it
- `member_vote_context`, when reviewed source and vote-context baselines support it
- `what_not_to_infer`, required for interpreted public-facing rows
- `support_position`, when determinable
- `oppose_position`, when determinable
- `interpretation_status`
- `interpretation_reason`
- `plain_english_summary`, when reviewed source text supports it
- `yea_meaning`, when reviewed source text supports it
- `nay_meaning`, when reviewed source text supports it
- `policy_effect`, when reviewed source text supports it
- `issue_facet`, when useful and source-grounded
- `confidence`
- `source_basis`
- `interpretation_source_list`, containing the official/source records used for the interpretation
- `uncertainty_note`
- `source_url` or source reference
- `interpretation_version`
- `classification_version`

Rules:

- vote interpretation must be deterministic and auditable
- ambiguous vote meaning must be marked `ambiguous` or `insufficient_evidence`
- ambiguous votes must not count as aligned or not aligned
- public interpretation cards should answer four questions when source context supports them: what happened, why it mattered, what the member's vote meant in context, and what not to infer
- party and result baselines may be surfaced only when computed from stored vote totals: for example, voted with most Democrats, voted against most Republicans, joined a bipartisan majority, broke with most of their party, voted with the winning side, or voted against the final outcome
- party-context language must describe the recorded vote context only; it must not infer motive, pressure, loyalty, ideology, or strategic intent
- LLMs or local/offline models may draft plain-language vote-meaning records for review, but imported records must be cached, source-grounded, schema-validated, neutral, and traceable to official/source fields
- the public application reads cached interpretation records only; it must not call an LLM at request time

Current deterministic interpretation version:

- `interpretation_v1`

Initial rules:

- eligible roll calls with wording such as `on passage`, `on agreeing`, `on adoption`, or `on the bill` are interpreted as `yea` supporting the measure and `nay` opposing the measure
- ineligible roll calls are marked `insufficient_evidence`
- roll calls with amendment or motion wording are marked `ambiguous`
- vague roll call wording is marked `insufficient_evidence`

These rules are intentionally conservative. They prioritize not counting a vote over counting a vote whose yea/nay meaning is unclear.

Manual interpretation batches use `docs/manual_interpretation_workflow.md`. They are designed for the first "DC-speak breakdown" layer without an ongoing API dependency. The importer rejects invalid status values, invalid confidence labels, unsupported support/oppose positions, missing source basis for interpreted records, and persuasive or judgmental language.

Manual interpretation quality is developed through gold slices: one official, one issue domain, reviewed end to end before scaling. The gold-slice standard requires each interpreted vote to explain the practical action, why it mattered, what the member's vote meant in context, and what not to infer. Procedural votes must stay procedural; the product must not translate a motion, amendment, rule, or conference instruction into a final policy effect unless the official packet supports that translation.

Interpretation packets may include a `so_what_context` block assembled from cached Congress.gov subresources. This context is source material for human-reviewed interpretation, not an automatic conclusion engine. It can show bill lifecycle, text versions, recorded actions, amendments, committees, CBO links, and enrichment counts so reviewers can identify the vote type, practical mechanism, direct stakes, and evidence boundary. If those source fields do not support a specific practical read, the interpretation must remain ambiguous or insufficient evidence.

Generalized amendment companion enrichment uses `app.etl.amendment_companion_enrichment` as an offline review workflow. It reads exported manual interpretation packets, identifies amendment-heavy weak sections by issue domain and bill, builds source packets from existing local Congress.gov cache, and drafts review-only candidate interpretations when the roll-call action, member Yea/Nay vote, and matched amendment purpose or description are all present. This workflow does not fetch broad new source data, write production data, import interpretations, or change support/opposition counting. Candidate records from this workflow are review artifacts only until a separate reviewed JSON import is explicitly approved.

Current vote-context baseline: the backend stores deterministic member-level vote context in `vote_contexts`. Seeded context derives vote type, final yea/nay result, vote margin, party vote totals, whether the member voted with their party majority, whether the member voted with the winning side, bipartisan winning-side presence, and official roll-call source lists from stored roll-call and member-vote records. Sponsor party remains nullable until a source supplies it. These fields are exposed through position evidence responses and manual interpretation packet export so reviewed "so what" summaries can use context without inferring from raw yea/nay counts alone.

Current reviewed "so what" fields: `vote_interpretations` stores `what_happened`, `why_it_mattered`, `member_vote_context`, and `what_not_to_infer`. Manual interpretation import validates those fields for forbidden persuasive or evaluative language when provided, and the evidence API returns them alongside legacy plain-English fields and deterministic vote context. Public evidence cards should prefer these reviewed fields, falling back to older cached fields only when reviewed fields are not yet loaded.

Current issue-overview layer: the frontend derives a deterministic issue-overview object from the opened evidence rows only. It groups rows by reviewed `issue_facet`, lists practical policy levers from reviewed fields, counts only interpreted yea/nay rows whose position maps to the reviewed measure meaning, explains not-voting rows without counting them as support or opposition, and keeps ambiguous or limited-context rows visible as evidence limits. The overview may compare the member's votes with party-majority and final-outcome context when those deterministic `vote_context` fields are present, but it must not infer motive, ideology, character, corruption, or a voting recommendation.

Issue-overview readiness: public overview copy must become more cautious when the opened slice has too few counted interpreted yea/nay rows or when ambiguous/insufficient rows dominate the slice. In those cases, the overview should describe the limited evidence, preserve the support/opposition counts that are available, and avoid presenting a stable issue pattern. For large issue sections, the overview should keep the measure-group list compact and direct users to the evidence rows below for additional groups rather than rendering a long paragraph.

Evidence grouping: the frontend may derive grouping metadata from opened evidence rows to make repeated bills, amendments, procedural rows, limited-context rows, and not-voting rows easier to review. Grouping must use stable bill or measure identifiers when present, or normalized measure titles when identifiers are unavailable; broad issue facets alone must not group unrelated rows. Grouping is presentation metadata only. It must not change interpretation status, support/opposition counting, alignment math, or whether ambiguous/procedural rows are excluded from the summarized pattern.

Procedural-context tier: procedural or floor-rule rows may be displayed as explanatory context when stored fields identify the row as a rule, procedural motion, concurrence-related step, previous-question vote, rule-resolution vote, conference instruction, motion to commit, or similar floor-process action. This tier is derived from existing evidence fields and does not add a stored interpretation status. Procedural-context rows may explain what the procedural vote was, what bill/package/rule it related to, why it may matter for understanding House floor process, and what not to infer. They must not state that the representative supported or opposed the underlying bill as a substantive policy position, must not create a broad issue-position claim, and must not affect support/opposition counts, alignment labels, confident issue summaries, or readiness promotion. They can reduce scroll/value mismatch by labeling visible weak rows more clearly, while still remaining in the limited/ambiguous burden used by cautious readiness copy.

Supervised enrichment operating model: production-backed enrichment must use a gated loop of production read-only discovery, source-packet construction, candidate classification, review-only candidate packet, import preflight, rollback artifact, explicit approval gate, bounded production import, post-import validation, and PR artifact preservation. Candidate rows are classified as substantive interpretation candidates, procedural-context candidates, or still insufficient. Substantive candidates may count only after source-grounded review and explicit import approval. Procedural-context candidates must keep `support_position` and `oppose_position` null and remain non-counting. Still-insufficient rows must not be promoted from issue facet or bill-level context alone. `app.etl.supervised_enrichment` provides offline validation helpers for these review artifacts; it reads local JSON and does not import or write production data.

Next methodology target: broaden reviewed interpretation records using the new fields and replace remaining aggregate copy with sample-bound language that describes only the votes shown.

## User Alignment Rules

User alignment compares explicit user-selected preferences to interpreted recorded votes.

Allowed labels:

- `aligned`
- `not_aligned`
- `mixed`
- `insufficient_evidence`

Alignment must be based only on:

- the user's explicit issue preference inputs
- eligible classified votes
- stored vote positions
- stored vote interpretations

Alignment must expose evidence counts and underlying vote rows. It must not rank legislators, infer motives, assign moral quality, or tell the user how to vote.

Neutral issue starters use `show_record` preferences. These are not directional alignment inputs. When interpreted vote evidence exists, the UI should label those rows as `Record shown`, exclude them from aligned/not-aligned/mixed counts, and explain that no for/against preference was selected. If interpreted vote evidence is missing, the row remains `insufficient_evidence`.

## Civic Action Rules

Civic action features help users decide what to do next after inspecting evidence about current representatives.

Current action surface:

- official contact information for the current representative
- selected issue context
- optional selected roll-call reference

Allowed inputs:

- selected current representative
- selected issue domain
- selected roll call or interpreted vote evidence
- source URL or official contact URL when available

Rules:

- actions must be optional and user-initiated
- action UI may show cited evidence context and official contact metadata, but should not generate a message body for the user
- if future action copy is added, it must stay neutral, user-editable, and evidence-based
- actions may summarize cited evidence, but may not tell the user what position to take
- UI-only action states must clearly indicate that the app has not sent, stored, or subscribed the user to anything
- tracking an issue, vote, or official must not alter any computed metric
- action history, if stored, must remain separate from `vote_classifications`, `vote_interpretations`, `fingerprints`, `drift_scores`, `summaries`, and candidate evidence
- contact metadata must be treated as operational context, not evidence of policy behavior
- contact metadata is stored separately in `legislator_contacts` when available
- contact metadata may include official website URL, contact form URL, phone, source URL, source type, and retrieved date
- official contact links help users reach representatives but must not be interpreted as policy evidence
- contact rows are imported through `app.etl.legislator_contacts` from reviewed official-source records keyed by Bioguide ID
- the first reviewed contact seed is `docs/legislator_contacts/nc_federal_contacts_seed.json`

Current CLI example:

- `python -m app.etl.legislator_contacts --input ../docs/legislator_contacts/nc_federal_contacts_seed.json --dry-run`
- `python -m app.etl.legislator_contacts --input ../docs/legislator_contacts/nc_federal_contacts_seed.json`

Forbidden action behavior:

- vote-for or vote-against language
- candidate support or opposition directives
- generated persuasion scripts framed as the product's recommendation
- hidden scoring of representatives based on user actions
- using action history to change alignment labels

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

Interpretation boundary:

- fingerprint is an issue-attention metric
- it shows where eligible votes are concentrated
- it does not show whether the legislator mostly voted `yea` or `nay` inside those domains

## Position by Issue Rules

The product now exposes a deterministic vote-direction view for each legislator.

For the same latest 730-day fingerprint window and `classification_version`:

- join `votes_cast` to eligible `vote_classifications`
- group votes by `primary_domain`
- count `yea`, `nay`, and `other` positions
- compute `yea_share` and `nay_share` using only recorded `yea + nay` votes

Rules:

- `present` and `not_voting` are counted as `other_count`
- `other_count` contributes to `total_votes` but not to `yea_share` or `nay_share`
- if a domain has no recorded `yea` or `nay` votes, both shares are `0.0`
- domains still appear with explicit zeroes

This view is descriptive only. It shows how a legislator voted within issue domains, not ideology or motive.

Frontend presentation:

- domains are grouped by evidence readiness before raw vote volume: `Strong evidence`, `Mixed but interpretable`, `Limited evidence`, and `Not enough to summarize`
- readiness grouping is derived from existing position summary counts; it does not change vote classification, interpretation, support/opposition counting, or alignment math
- limited and not-ready issue sections remain visible, but they are not treated as confident issue summaries
- raw yea/nay shares may be shown as record context, but they must not be presented as broad ideology or "so what" conclusions
- sample-bound labels may be used only for the votes shown:
  - `Mostly Yea in votes shown`
  - `Mostly Nay in votes shown`
  - `Mixed record in votes shown`
  - `Too little interpreted evidence`
- issue summaries should use this bounded form: `The clearest pattern in this evidence is [specific pattern], based on [n] interpreted votes. This is a summary of the votes shown, not a full ideology score.`
- user-facing caution labels should explain the type of caution, such as `Procedural vote`, `Amendment vote`, `Final passage`, `Plain-English interpretation available`, or `Limited source context`; generic confidence labels should not be the primary public label unless they explain evidence type or caution
- stored metrics remain the underlying shares and counts

## Position Evidence Rules

The position-by-issue view supports an evidence drilldown for each legislator and issue domain.

For a selected legislator and domain, the evidence response includes eligible classified votes in the latest 730-day fingerprint window:

- roll call id
- vote date
- chamber
- congress
- roll call number
- recorded vote position
- roll call question
- roll call description
- bill title and summary when available
- classification reason
- classification score breakdown
- source URL when available

The evidence endpoint does not interpret whether a yea or nay vote was substantively aligned with a policy preference. It only exposes the underlying voting record and classification metadata so the user can inspect the basis for higher-level reads.

Frontend presentation:

- evidence rows remain roll-call level because amendments and related actions can be meaningful
- the UI groups rows by bill title or measure label when available
- the UI surfaces both roll-call count and distinct bill-or-measure count so repeated actions on one bill are not presented as unrelated votes
- the UI may show a compact grouped-evidence preview using derived metadata only; this preview must not change support/opposition counts or upgrade limited rows into interpreted rows
- the representative page may show a deterministic 60-second path that points users to the strongest reviewed issue read first and marks limited/not-ready sections as lower priority
- the representative page must not imply that the issue domain with the most recorded votes is the best place to start when another domain has clearer reviewed vote meaning
- when a user selects issues without a directional preference, public copy should describe selected records or evidence available rather than alignment or non-alignment
- the UI may show a deterministic issue overview for the opened issue using only the evidence rows already returned by the endpoint
- that issue overview may count interpreted votes with yea/nay positions, rows without yea/nay positions, and ambiguous or insufficient-evidence rows
- that issue overview may say whether the representative's interpreted votes with yea/nay positions in the opened issue slice were for, against, mostly for, mostly against, or split across the interpreted measures
- that issue overview may group source-grounded issue facets from cached `vote_interpretations` into short practical measure descriptions, such as budget-reconciliation instructions, loan-eligibility restrictions, or temporary funding packages
- issue-overview language must be domain-aware: Economy & Taxes may use fiscal/tax language, Justice & Public Safety may use public-safety and legal-policy language, and other domains should fall back to neutral "policy questions" or "reviewed measures" language
- issue-overview measure groups may use a small reviewed mapping from `issue_facet` values to voter-facing labels; if no mapping exists, fallback text must still be neutral and source-grounded
- that issue overview must state its scope, including interpreted vote count, total roll-call rows shown, rows without yea/nay positions, and ambiguous/procedural rows left outside the summarized pattern
- issue sections with only one interpreted vote with a yea/nay position must be framed as a limited read and treated as a narrow signal until more interpreted votes are loaded
- it must not infer motive, ideology, causality, rank, or recommend an electoral action
- it must describe only the opened evidence section, not a broad issue ideology
- this grouping is explanatory only and does not change stored metrics or alignment calculations

Vote-card UX rules:

- the default visible layer must explain the vote in plain English before showing audit or methodology details
- default-visible cards should prioritize roll date, roll number, recorded vote, vote summary, why it mattered, and source access
- source links must remain available without opening an expandable details section
- the expandable details layer is for audit, methodology, source-basis chips, interpretation/status badges, eligibility notes, and reference-vote actions
- source-basis and methodology details should not be visible by default
- ambiguous or limited-context votes must show their caveat plainly and must not be over-interpreted into a support/opposition pattern
- rows where the member was recorded as not voting may explain the bill or measure, but must never be counted as support or opposition
- generic vote-card summaries should use the representative's available display name rather than "this representative" when a name is available
- default-visible cards may show compact evidence confidence labels such as `Reviewed meaning`, `Limited context`, `Needs source support`, or `Not counted`; these labels describe evidence readiness and must not imply ideology or motive

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

Interpretation boundary:

- drift measures change in issue emphasis over time
- it does not measure ideological moderation, extremity, or consistency of beliefs

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
- `python -m app.etl.fetch_sources congress-bill --congress 119 --bill-type hr --bill-number 120 --include-enrichment`

When `--include-enrichment` is used, the Congress.gov pull stores the bill detail payload plus bill summaries, bill subjects, bill actions, bill text-version metadata, bill amendments, and bill committees in separate cache directories. The ETL merges those companion payloads deterministically before classification, so interpretation packets can use CRS summary text, official subject terms, lifecycle/action context, text-version links, amendment context, committee activity, CBO links, and public-law status when Congress.gov provides them.

These Congress.gov enrichment records improve interpretation packets but do not by themselves decide support/oppose meaning. The reviewed interpretation must still cite the specific source basis and must mark the row ambiguous or insufficient when the bill/action/amendment context does not justify a plain-English practical effect.

## Interpreted Issue Patterns

The position endpoint now includes neutral interpreted-pattern counts for each issue domain.

These counts are derived only from stored `vote_interpretations` rows where:

- `interpretation_status = interpreted`
- the interpretation classification version matches the vote classification version
- the legislator's recorded vote matches the stored `support_position` or `oppose_position`, or is counted separately as another interpreted position

The frontend renders these as issue pattern cards. The cards may say that interpreted votes were recorded on the for side, against side, or split between those sides. They must also show coverage language, such as how many recorded yea/nay votes have cached vote meanings. These cards are descriptive only; they do not rank officials, infer motives, or recommend electoral action.

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

The Senate fact-only helper is separate from the persistent ETL path. `app.etl.senate_fact_import` reads an explicit Senate manifest, parses cached Senate XML vote facts, optionally validates production state with read-only queries, and reports planned `bills`, `roll_calls`, `votes_cast`, and `vote_contexts` inserts. It does not call the persistent seed path and must not create, update, or delete `vote_interpretations`. Production fact imports require a bounded approval gate and rollback artifact before any write. Phase 14 package imports are limited to 119th Congress / 2025 Senate roll calls, capped at 75 roll calls and 7,500 `votes_cast` rows, and exclude PN nominations, Senate amendments, treaty/executive votes, unsupported references, malformed XML, rows with existing `vote_interpretations`, and rows outside the current-Congress/year scope. Fact-only imports do not change support/opposition counting, alignment, issue readiness, or substantive interpretation coverage until separately reviewed `vote_interpretations` are approved.

Senate amendment reference handling keeps amendment facts separate from parent-bill final passage evidence. `app.etl.senate_amendment_facts` reads cached 119th Congress / 2025 Senate XML and builds local review manifests that preserve amendment number, parent bill, amendment purpose, roll question/title, source URL, and member vote-row counts. Phase 17 adds a local migration for `senate_amendment_references`, keyed one-to-one to `roll_calls`, so a Senate amendment row can point at its parent bill while still preserving amendment identity. Amendment rows remain fact-only and non-interpreted: they must not create `vote_interpretations`, assign `support_position` or `oppose_position`, alter alignment, or be summarized as parent-bill final passage. Production amendment fact import still requires applying the migration in production, a bounded production-aware dry-run, rollback artifact, explicit approval, and post-import validation.

Senate amendment import preflight remains dry-run only until explicitly approved. Phase 18 uses the same `app.etl.senate_amendment_facts` helper to convert safe amendment candidates into a bounded import manifest, validate the local migration against production metadata with read-only queries, and plan future writes to `bills`, `roll_calls`, `votes_cast`, `vote_contexts`, and `senate_amendment_references`. The preflight must plan zero `vote_interpretations` inserts, updates, or deletes, zero support/opposition inference, and zero alignment impact. A future import must have rollback SQL scoped only to the target amendment roll calls and must not proceed without an explicit approval phrase covering the schema and data boundaries.

Phase 19 applied the `senate_amendment_references` migration and imported the approved 112-row Senate amendment fact-only package. The import added only parent bill, roll-call, member vote, vote-context, and amendment-reference facts. It did not create `vote_interpretations`, did not infer support/opposition, did not change alignment inputs, and did not handle PN nominations, treaty/executive votes, or the deferred roll 344.

Phase 20B adds deterministic Senate evidence classification for fact-only Senate rows that were already loaded into production. The helper in `app.etl.senate_evidence_classification` builds an explicit manifest from 119th Congress / 2025 Senate roll calls, classifies Senate amendment facts from amendment purpose and identity first, and treats parent bill context as supporting context only. Bill-centered Senate rows continue to use bill title, roll question, description, summary, and subjects. Rows with missing or generic amendment purpose, procedural-only bill-centered questions, PN nominations, treaty/executive votes, unsupported rows, and rows outside the current-Congress/year scope remain deferred. This classification step may create or update `vote_classifications` only under an explicit approval phrase and rollback artifact; it must not create `vote_interpretations`, infer `support_position` or `oppose_position`, or change alignment logic. The Phase 20B production write uses active classification version `v1` so the existing evidence API can see the classified rows, but it still leaves every row fact-only until a separate supervised interpretation import is approved.

Phase 21 scales the same Senate enrichment loop across the strongest loaded 119th Congress / 2025 Senate evidence families. The helper in `app.etl.senate_enrichment_phase21` builds a bounded manifest for priority families, writes only deterministic missing `vote_classifications` after rollback generation, and generates separate substantive and procedural interpretation batches. Amendment votes remain controlled by amendment purpose and identity, final-passage rows must describe final passage without implying support for every provision, and procedural rows remain non-counting with null support/opposition positions. Phase 21 imports are capped, rollback-scoped, source-grounded, and must validate support/opposition impact, not-voting exclusions, serialization, alignment, House invariance, and idempotency after production writes.

Phase 22 is a presentation-only evidence-density pass for the accountability profile. The frontend should lead with the clearest reviewed issue read, keep official identity and the quick read compact, show issue summaries before detailed proof, and make vote rows compact by default with source basis, caveats, and secondary metadata behind expansion. Evidence display order may prioritize source-grounded substantive interpreted rows ahead of procedural, limited-context, and not-voting rows, but this is a UI ordering rule only. It must not change support/opposition counting, alignment logic, readiness thresholds, vote interpretation storage, amendment/final-passage meaning, or procedural-context non-counting treatment.

Phase 23 restores profile evidence integrity and compresses the mobile accountability profile without changing civic semantics. API reads for positions, evidence rows, and alignment should join `vote_interpretations` by the `roll_call_id` primary-key relationship rather than hiding approved interpretations behind a matching classification-version string. The frontend may defensively fill missing position-summary interpretation counts from the domain evidence endpoint when a deployed API omits those summary fields; this fallback counts only rows whose stored `interpretation_status` is `interpreted` and whose member vote matches the stored support or opposition position. It must not infer support/opposition, promote procedural rows, change readiness thresholds, or alter alignment math. Profile layout should keep the post-ZIP shell, quick read, issue selector, empty states, and weak issue lists compact so source-backed evidence appears earlier on mobile while limited, procedural, and not-voting rows remain inspectable.

Current CLI example:

- `python -m app.etl.live_pipeline --house-year 2025 --house-roll 1 --bill 119:hr:120 --congress-api-key YOUR_KEY`
- `python -m app.etl.live_pipeline --house-year 2025 --house-roll 1 --senate-congress 119 --senate-session 1 --senate-roll 1 --bill 119:hr:120 --bill 119:s:210 --congress-api-key YOUR_KEY`

## Federal Race And Candidate Context

The repository includes an initial federal race importer in `app.etl.federal_races`.

Current source:

- FEC candidate summary bulk data

Current source boundary:

- FEC candidate summary rows establish federal candidate/race context.
- They do not establish ballot qualification in every state.
- They do not establish issue positions.
- They do not count as recorded governing behavior.

Current importer behavior:

- reads FEC candidate summary CSV exports from a local file
- keeps House and Senate rows only
- groups House candidates by cycle, state, and district
- groups Senate candidates by cycle and state
- writes deterministic `upcoming_races` and `race_candidates` rows
- sets race status from election date and importer `as_of` date, currently `upcoming` before or on election day and `past` after election day
- uses `source_type = fec_candidate_summary`
- stores the FEC candidate id as `external_candidate_id` for idempotent re-imports
- marks FEC-only candidate rows as `candidate_status = declared_candidate`
- marks FEC-only candidate evidence as `insufficient_evidence`
- links an incumbent candidate to an existing legislator only when office, state, district, party, incumbent flag, and candidate name match a current in-office legislator record
- links a non-incumbent prior officeholder only when the same office, state, district, party, and candidate name match a stored legislator record that is no longer in office
- upgrades matched incumbent or prior-officeholder candidate evidence to `recorded_governing_behavior`
- includes a compact voting summary for linked incumbents using existing precomputed rows: eligible vote count, interpreted vote count, top issue domains, computation window, and classification version

Candidate issue alignment must not be computed from FEC candidacy rows. A candidate needs linked recorded governing behavior or separate sourced stated-position records before issue comparison can show more than insufficient evidence.

Race-card selected-issue comparison is evidence coverage only. For each user-selected issue, the UI may show that a candidate has linked recorded-vote evidence, reviewed institutional or stated-position records, or insufficient evidence. It must not aggregate those rows into a candidate score, winner, rank, or vote recommendation.

The race panel may limit visible candidates when a race has many low-signal rows. The visible order should prefer linked recorded-vote records, then reviewed candidate evidence, then other non-insufficient evidence tiers, then FEC-only insufficient-evidence rows. Any cap must be disclosed in the UI and must not imply that hidden candidates are worse or less legitimate; it only preserves the product hierarchy where election context is secondary to the current representative record.

Current CLI example:

- `python -m app.etl.federal_races --fec-candidate-summary ./backend/data_sources/fec/candidate_summary_2026.csv --cycle 2026 --dry-run`
- `python -m app.etl.federal_races --fec-candidate-summary ./backend/data_sources/fec/candidate_summary_2026.csv --cycle 2026 --as-of 2026-05-17 --dry-run`

## State-Level Expansion Boundary

State records must use a separate methodology from federal records until the source shape, district lookup, vote subjects, candidate data, and interpretation rules are proven for that state. A state pilot may reuse product principles, but it must not reuse federal assumptions blindly.

State-level expansion must pass `docs/state_adapter_checklist.md` before adding public UI or broad ETL. The checklist requires official district mapping, current official identity, member-level roll-call data, state-specific vote interpretation rules, source-backed candidate context, separate state storage, and clear UI labels.

ZIP-only state district lookup is not sufficient to auto-select a state representative unless the ZIP maps unambiguously to one district. When a ZIP crosses districts, the UI must require address-level lookup or show an approximate/multiple-district state.

State records must not be merged into federal fingerprints, chamber medians, drift scores, federal summaries, or federal vote interpretations. Cross-level comparison is deferred until there is a documented methodology for mixed federal/state evidence.

## Candidate Evidence Records

Candidate evidence records are the lower-confidence companion to recorded governing behavior.

Stored candidate evidence may include:

- institutional records
- sourced stated positions
- explicit insufficient-evidence records

Rules:

- candidate evidence is stored in `candidate_evidence`
- each row must link to one `race_candidates` row
- sourced stated positions must include a source URL
- sourced stated positions may use `low` or `medium` confidence, but not `high`
- stated positions must remain separate from vote-based alignment math
- candidate evidence may describe what a source says, but it must not tell users how to vote
- missing candidate evidence should render as an intentional not-loaded state, not as a negative claim about the candidate

The candidate evidence endpoint returns stored source records only. It does not infer issue positions from FEC candidacy rows and does not generate summaries at request time.

Initial reviewed seed:

- Nida Allam, FEC candidate id `H2NC06098`
- source: Justice Democrats candidate profile, retrieved May 17, 2026
- evidence tier: `institutional_record`
- issue domains: `ECONOMY_TAXES`, `EDUCATION_WORKFORCE`, `HEALTH_SOCIAL`
- confidence: `medium`

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

The ZIP lookup endpoint returns loaded legislator mappings for the requested ZIP code. It reads from `zip_district_map` when the database is available and falls back to fixture mappings in local development.

Returned data includes:

- ZIP code
- state
- congressional district
- House representative for that district
- both senators for that state

The `/lookup/zips` endpoint returns a deterministic list of loaded ZIP mappings for the UI to suggest. This avoids hard-coded demo-only ZIP prompts and lets the frontend reflect whichever mappings are present in Supabase or fixtures.

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

## Coverage Metadata API

The `/coverage/metadata` endpoint exposes lightweight first-viewport context. The original `/metadata/coverage` route remains available for local/backward compatibility when the hosting layer permits it:

- data source used by the response (`database` or `fixtures`)
- current fingerprint window start and end
- classification version
- loaded legislator count
- total roll call count
- eligible roll call count
- count and share of roll calls with source URLs

The endpoint reads from precomputed database tables when available. If the database is unavailable in local development, it falls back to the deterministic fixture bundle and fixture-derived computed outputs.

Coverage metadata is descriptive only. It does not score quality, rank officials, infer completeness beyond stored counts, or change any alignment calculation.

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
- requests `GET /lookup/zips` for loaded ZIP suggestions
- renders the returned district, House representative, and both senators
- shows clickable loaded ZIP suggestions instead of hard-coded demo copy
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

## Profile Narrative And Guided Alignment

The accountability profile uses a three-layer presentation model:

1. The answer: one compact record summary near the top of the loaded profile.
2. The explanation: reviewed issue patterns, concrete policy themes, and guided preference prompts.
3. The proof: full roll-call evidence, official titles, source basis, procedural context, and caveats behind disclosure controls.

The top-level record summary is deterministic. It is derived from interpreted support/opposition counts, readiness labels, recorded vote counts, chamber, and party metadata already returned by the read API. It may say that a reviewed sample is strong, mixed, limited, or not ready to summarize. It may use chamber and party context only as orientation when the profile has the supporting metadata. It must not infer motive, ideology, character, corruption, or voting recommendation.

Reviewed issue patterns appear immediately under the top summary. Each pattern shows the issue name, readiness, interpreted support/opposition counts, and a concise policy-theme line. These pattern rows use stored interpretation counts only; procedural-context rows, not-voting rows, ambiguous rows, and insufficient-evidence rows do not become support/opposition evidence.

Guided alignment prompts are concrete prompts about reviewed measures, not broad questions about whether a user is "for" or "against" an issue domain. Prompt options are:

- generally favored the reviewed measures
- generally favored opposing them
- views differ by measure
- not sure

Only the first two options are directional and may call the existing alignment endpoint. `views differ by measure` and `not sure` are intentionally non-counting UI choices; they do not produce a personalized alignment label. The descriptive official-record summary remains unchanged regardless of user preference.

Sparse profiles or issue areas with fewer than three reviewed Yes/No meanings do not receive a concrete alignment prompt. They remain inspectable as evidence, but the UI should not force a confident issue read or personalized alignment claim.

For deployment drift protection, the repository includes a post-merge backend smoke workflow. When a Render deploy hook secret is configured, backend changes on `main` can trigger a Render deployment and verify that the public backend exposes `/health`, Valerie position `interpreted_total`, and evidence `interpretation_status`. The workflow must not store secrets in the repository.
