# Address-Level Lookup / Ambiguity UI Design Spike V1

## Summary Recommendation

Use a phased hybrid lookup path:

1. Keep ZIP as the first, low-friction entry point.
2. If local/source metadata says the ZIP maps confidently to one current House district and member, allow a clearly labeled result.
3. If the ZIP maps to multiple districts, multiple states, fixture/sample data, stale/unknown source metadata, or uncertain member currentness, do not auto-select a House member.
4. Offer two safe continuations: enter a full address for district resolution, or search manually by representative name.
5. Prototype address-level resolution behind a development flag before any public behavior change.

This is the safest path because ZIP-only lookup is useful for discovery but cannot safely scale nationally as a representative selector. Address-level lookup is needed for precision in split ZIPs, but it introduces privacy, source, terms, rate-limit, and operational concerns that should be handled deliberately.

Recommended source direction:

- Phase 1 should use existing ZIP metadata only and add ambiguity-aware UI states in a future implementation.
- Phase 2 should prototype Census Geocoder server-side behind a dev flag because it is official, supports address-to-geographies lookup, and can return Congressional District geography with explicit benchmark/vintage choices.
- Paid vendors or civic-data vendors should be considered only after privacy/terms review and a source/vendor selection decision.

No public behavior change is recommended in this spike.

## Current Lookup Risk Recap

Current repository findings:

- Backend route `GET /lookup/zip/{zip_code}` calls `get_zip_lookup_response`.
- Backend route `GET /lookup/zips` calls `get_supported_zip_responses`.
- Search route `GET /legislators/search` allows empty `q`, which can expose all loaded legislators.
- Database schema defines `zip_district_map.zip` as `PRIMARY KEY`, with one `state` and one `district`.
- DB lookup reads one ZIP row, then selects one House member by `state + district` using `ORDER BY id LIMIT 1`.
- Fallback lookup uses the first matching fixture ZIP row and first matching House fixture row.
- Senators are selected by state only.
- Frontend auto-runs default ZIP `27701`.
- Frontend copy currently says `ZIP ... maps to ...`.
- Frontend auto-selects the returned House member when `payload.house_rep` is present.
- Supported ZIP copy says "Loaded ZIP Coverage" and "Showing N loaded ZIP mappings from data_source."

Recent report findings:

- ZIP ambiguity report: 9 local mapping rows, 4 unique ZIPs, 9 fixture-only rows, 0 non-fixture rows.
- ZIP `27601` is locally detected as split across `NC-02` and `NC-04`.
- ZIP ambiguity report warns that the one-ZIP-one-district assumption is present in schema and lookup behavior.
- Legislator metadata report warns that fixture/sample rows must not be treated as production coverage.
- Metadata report also warns that currentness, term boundaries, Senate LIS, Senate seat/class, and stale-member checks remain expansion gates.

Product risk:

- The current behavior can make a ZIP-only result look more precise than it is.
- A split ZIP could auto-select the wrong House member.
- A ZIP can resolve to a state where senators are available while the House district remains ambiguous.
- Fixture/sample coverage can be mistaken for production coverage if the UI only says data came from `fixtures`.
- Stale or uncertain member metadata can make a technically resolved district point to the wrong current official.

## Recommended Product Flow

The recommended flow is hybrid and phased:

1. ZIP first

   The first input remains a 5-digit ZIP because it is low-friction and familiar. ZIP lookup should become a coverage and ambiguity check, not always a representative selector.

2. Confidence check

   The backend or client should classify the result into a lookup state:

   - single district with current source/date/member gates passing;
   - multiple districts;
   - multiple states;
   - unsupported ZIP;
   - fixture/sample-only;
   - stale/unknown source;
   - address-required;
   - address-resolution failed;
   - member metadata uncertain.

3. Address only when needed

   Ask for full address only when ZIP-level evidence cannot safely select a House member, or when the user wants to confirm a likely match.

4. Manual fallback always available

   Representative search should remain available for users who do not want to enter a full address or whose address cannot be resolved.

5. No raw-address persistence by default

   Address lookup should be server-side. Do not store full address by default. Return and retain only normalized ZIP, state, district, source metadata, and confidence/status fields unless a later privacy decision explicitly approves more.

## Flow-By-Flow UX Table

| Flow | Trigger | House behavior | Senate behavior | Primary action | Draft copy |
| --- | --- | --- | --- | --- | --- |
| ZIP maps confidently to one district | ZIP has one district, source/date/version are known, and current House metadata passes gates | May auto-select House only after gates pass | May show senators with state/currentness caveat | Show result and allow confirmation | We found one likely congressional district for this ZIP. ZIPs are not always precise, so confirm your representative if this looks wrong. |
| ZIP maps to multiple districts | ZIP has more than one House district | Do not auto-select House | May show state-level Senate only if one state is known, with caveat | Ask for address or manual search | This ZIP may include more than one congressional district. To avoid showing the wrong House member, enter your full address or search by representative name. |
| ZIP maps to multiple states | ZIP appears in more than one state | Do not auto-select House | Do not auto-select senators until state is confirmed | Ask for address/state or manual search | This ZIP may cross state lines. Enter your full address, choose your state, or search by representative name so we do not show the wrong officials. |
| ZIP unsupported | ZIP not in loaded map | No House result | No Senate result | Manual search and coverage note | This ZIP is not in the loaded map yet. You can still search by representative name while coverage expands. |
| ZIP is fixture/sample-only | `data_source=fixtures` or report marks source sample | Do not present as production coverage; avoid auto-select outside demo/dev mode | Same | Label sample, offer search | This is sample coverage, not national coverage yet. Search by representative name to inspect loaded records. |
| ZIP resolves to House and senators are state-only | Single state/district result | House result follows House gates | Show senators as state-level records with caveat | Show state caveat near Senate cards | Senators represent the whole state. We show them from the ZIP's state, not from a district-level address match. |
| Lookup source stale or unknown | Missing source date/version/currentness | Do not auto-select House without confirmation | State-level Senate with currentness caveat only | Ask for confirmation/search | We found a possible match, but the lookup source date is not confirmed. Please confirm the representative before relying on this result. |
| Address entered but cannot be resolved | Geocoder returns no match or low-confidence match | No House result | No automatic Senate unless state is confidently known | Retry, simplify address, or search | We could not confidently match that address. Check the address, try again, or search by representative name. |
| Address resolves but member metadata is stale/uncertain | District resolved but local member metadata fails currentness/identity gates | Do not auto-open profile as current representative | Senate caveat if shown | Search and explain coverage | We found the district, but our current representative metadata needs confirmation before we show a profile as your representative. |

## Draft User-Facing Copy

### Initial ZIP prompt

Start with your ZIP. If the ZIP may include more than one district, we will ask for a full address or let you search by representative name.

### Confident single-district ZIP

We found one likely congressional district for this ZIP. ZIPs are not always precise, so confirm your representative if this looks wrong.

### Multi-district ZIP

This ZIP may include more than one congressional district. To avoid showing the wrong House member, enter your full address or search by representative name.

### Multi-state ZIP

This ZIP may cross state lines. Enter your full address, choose your state, or search by representative name so we do not show the wrong officials.

### Unsupported ZIP

This ZIP is not in the loaded map yet. You can still search by representative name while coverage expands.

### Fixture/sample data

This is sample coverage, not national coverage yet.

Longer version:

This result comes from sample data used for development and review. It should not be treated as national ZIP coverage.

### State-only Senate note

Senators represent the whole state. We show them from the ZIP's state, not from a district-level address match.

### Stale or unknown source

We found a possible match, but the lookup source date is not confirmed. Please confirm the representative before relying on this result.

### Address lookup prompt

Enter your full address so we can check the district more precisely. We should not store your full address by default.

### Address lookup third-party disclosure

We use a district lookup service to match your address to a district. We do not store your full address by default.

### Address cannot be resolved

We could not confidently match that address. Check the address, try again, or search by representative name.

### District found but member uncertain

We found the district, but our current representative metadata needs confirmation before we show a profile as your representative.

### Manual representative search fallback

Prefer not to enter an address? Search by representative name and inspect any loaded record directly.

## Data / Source Option Matrix

| Option | Expected accuracy | Cost / terms risk | Privacy implications | Operational complexity | Rate limits | Server-side use | Store raw address? | House + Senate support | Sensitive data concerns |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ZIP-only with ambiguity UI | Low to moderate. Safe only when ZIP metadata proves one district; cannot resolve split ZIPs by itself. | Low if using owned data, but national ZIP dataset still needs source/date/version rights. | Lowest if no address collected. | Low for Phase 1, but requires ambiguity states and tests. | None beyond app traffic. | Yes. | No. | House only when unambiguous; senators by state if state is known. | Low, but risk of wrong representative if auto-select is allowed. |
| Census Geocoder | Moderate to high for address-to-geography when matched; based on MAF/TIGER address ranges, not address validation. | Low monetary cost; official service. Must manage benchmark/vintage changes. | Full address is sent to Census if used live. No raw storage should be default. | Moderate. Needs server-side proxy, match confidence handling, benchmark/vintage logging, and district parsing. | Batch docs state 10,000 records per batch; no public app quota was confirmed in docs checked. | Yes; server-side is preferred because docs say CORS is not supported. | No by default. Retain only district, source, benchmark/vintage, and non-identifying status. | Can return Congressional District geographies; senators still need state/member metadata lookup. | Yes: full address is personal location data and must be redacted from logs. |
| Google Civic Information API | Moderate for political division lookup; current docs expose Divisions and Elections, not a safe new dependency on legacy representative lookup. | Medium. Bound to Google API terms and availability. | Full address is sent to Google if using `divisionsByAddress` or `voterinfo`. | Moderate. Needs API key, quota review, terms review, response mapping, and fallback handling. | Not confirmed from official docs checked; must review in Google Cloud Console before implementation. | Yes, and API key should stay server-side. | No by default. | Divisions can identify political geography; voter info is election-focused. Not recommended as primary representative source without further review. | Yes: full address to Google and Google API data-use requirements. |
| Smarty / address validation vendors | High for address standardization and geocoding when subscription supports rooftop/parcel precision. | Medium to high. Commercial pricing, subscription features, and terms review required. | Full address is sent to vendor and processed under vendor privacy/contract terms. | Moderate to high. Needs account, secrets, billing, retries, vendor status, and precision gating. | Vendor/account dependent. | Yes; secrets must stay server-side. | No by default. | Can provide coordinates/metadata; House district may require returned congressional district metadata or separate boundary lookup. Senators still need state/member metadata. | High: commercial third-party processing of full addresses. |
| State/district shapefiles plus geocoding | Potentially high if geocoding is accurate and boundaries are current. | Low if using public official shapefiles; geocoding source may add terms/cost. | Depends on geocoder. If geocoding is external, address leaves system; if local, storage/cache risks remain. | High. Needs geospatial pipeline, boundary versioning, point-in-polygon, updates after redistricting, and QA. | None for local boundary lookup; geocoder-dependent. | Yes. | No by default. | Can resolve House and state legislative districts if boundary layers are maintained; senators by state. | Medium to high depending on geocoder and logs. |
| Cicero or civic-data vendors | High for address-to-district and elected official lookup if vendor coverage is current. | Medium to high. Paid credits, terms, and vendor lock-in. Cicero page lists pricing and asks API users to limit calls to 200/minute. | Full address is sent to vendor. Vendor may also return official/contact data that must be reconciled with app metadata. | Moderate. Easier than building geospatial stack, but requires contracts, secrets, monitoring, and reconciliation. | Cicero official FAQ asks users to limit API calls to 200 per minute. | Yes; credentials should be server-side. | No by default. | Strongest vendor option for House, state/local districts, and elected officials, but app should still reconcile to internal records. | High: third-party address and civic-profile processing. |
| Manual representative search fallback | Depends on user knowing or finding the representative. It avoids false precision from location data. | Low. Uses existing search. | Low. No address required. | Low to moderate. Search UX and labels need tightening. | App traffic only. | Yes. | No. | Supports any loaded legislator; does not prove "my representative." | Low, but copy must avoid implying the selected person represents the user. |

## Official Source Notes

- Census Geocoder docs say the service accepts single record and batch requests, can return geographies, uses benchmark/vintage parameters, and includes Congressional Districts among default geography layers when available. The same docs state CORS is not supported, favoring a server-side proxy. Source: https://geocoding.geo.census.gov/geocoder/Geocoding_Services_API.html
- Census TIGER/Line Shapefiles are official boundary files. The 2025 page states legal boundaries and names are as of January 1, 2025, and that core files contain geographic entity codes but not demographic data. Source: https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html
- Google Civic Information API current reference lists Elections and Divisions resources. `divisionsByAddress` looks up political geographic divisions for one address; `voterinfo` is election/voter-information oriented. The API terms page binds use to Google APIs Terms of Service. Sources: https://developers.google.com/civic-information/docs/v2/ and https://developers.google.com/civic-information/docs/v2/divisions/divisionsByAddress
- Smarty docs describe US address verification, geocoding products, and precision levels including ZIP-level, street, parcel, and rooftop with subscription requirements. Smarty privacy policy says it may collect/store/process personal information provided through services. Sources: https://www.smarty.com/docs/apis/us-street-api/reference and https://www.smarty.com/legal/privacy-policy
- Cicero describes address-to-district matching and elected official lookup, lists credit pricing, offers a free trial, and asks API users to limit calls to 200 per minute. Source: https://www.cicerodata.com/api/

## Privacy Posture

Default recommendation: minimize address handling.

- Do not store full addresses by default.
- Do not send addresses to third-party APIs from the browser.
- Use a backend route or server action for any future address lookup so API keys stay server-side and logging can be controlled.
- Redact or suppress raw address strings in application logs, analytics, error traces, and telemetry.
- Return only the fields needed for the product flow: normalized ZIP, state, district, source, benchmark/vintage/version, confidence/status, and whether the result is ambiguous.
- If a third-party lookup service is used, tell the user before or at the point of address entry.
- Do not retain raw address in database tables unless a later privacy review explicitly approves a bounded, user-visible use.
- Do not use address input for profile personalization, analytics enrichment, campaign targeting, or any purpose outside district lookup.
- Cache only non-identifying results when possible, such as `ZIP + district ambiguity metadata` or provider/source metadata, not household-level addresses.
- Treat full address as sensitive user location data even if it is not classified as special-category data.

Recommended disclosure pattern:

> We use your address only to find the correct district. We do not store your full address by default.

For third-party lookup:

> This lookup sends your address to [provider] to identify the district. We do not store your full address by default.

## Phased Implementation Plan

### Phase 1: UI ambiguity handling using existing ZIP data and manual search fallback

Goal: make current ZIP evidence honest without changing data sources.

Implementation shape for a future PR:

- Add lookup states for single district, ambiguous ZIP, multi-state ZIP, unsupported ZIP, fixture/sample-only, and stale/unknown source.
- Stop auto-selecting House member for ambiguous, fixture/sample-only, stale, or unknown-source ZIP states.
- Keep manual representative search visible as a fallback.
- Label fixture/sample results clearly.
- Add rendered tests for all ZIP lookup states.
- Keep public behavior changes behind explicit product approval.

Acceptance gate:

- Ambiguous ZIP never auto-selects a House member.
- Fixture/sample result is visibly labeled.
- Unsupported ZIP gives a manual search path.

### Phase 2: Address-level design/prototype behind dev flag

Goal: test address-to-district resolution without public rollout.

Implementation shape for a future PR:

- Add a dev-flagged address lookup prototype using Census Geocoder first.
- Route requests server-side; do not call the provider from the browser.
- Store no raw address by default.
- Capture source metadata: provider, benchmark, vintage, request date, and district layer.
- Normalize provider responses into internal states: resolved, no match, multiple matches, low confidence, stale source, provider error.
- Reconcile district result to app House member metadata and currentness gates.

Acceptance gate:

- Address lookup can resolve a known split-ZIP fixture scenario in a deterministic test harness.
- Raw address is absent from logs and persistent storage by default.

### Phase 3: Source/vendor selection and production-readiness review

Goal: choose whether to use Census, vendor, shapefile stack, or a layered approach.

Tasks:

- Compare Census prototype match quality with a reviewed set of synthetic and real non-sensitive test addresses.
- Review privacy, security, rate limits, terms, uptime, and cost for any third-party provider.
- Decide if a paid address validation layer is needed before Census/geographic lookup.
- Decide if app-owned shapefile point-in-polygon is worth the operational cost.
- Define source freshness SLA and redistricting update procedure.

Acceptance gate:

- Provider/source choice is documented with source/date/version metadata requirements and privacy review.

### Phase 4: National ZIP/district rollout gates

Goal: allow national lookup only when ambiguity and metadata gates are enforceable.

Required gates:

- National ZIP/district source has source, retrieval date, effective date, and version metadata.
- ZIPs with multiple districts or states return ambiguity states.
- Address-level lookup or manual fallback is available for ambiguous ZIPs.
- Current House member metadata has identity/currentness gates.
- Senate state results carry currentness/seat caveats.
- Rendered tests cover all lookup states.
- Production rollout includes monitoring for provider errors, unsupported ZIPs, ambiguous ZIPs, and no-match addresses.

## Acceptance Criteria For Future Implementation

- Ambiguous ZIP never auto-selects a House member.
- Multi-state ZIP never auto-selects House or Senate until state/address is confirmed.
- Single-district ZIP may auto-select only when source/date/version and currentness gates pass.
- Unsupported ZIP gets clear fallback copy and manual representative search.
- Fixture/sample data is visibly labeled and cannot appear as national coverage.
- Address lookup does not store raw address by default.
- Third-party address lookup is disclosed to the user before or at address entry.
- Address lookup runs server-side; provider keys are never exposed to the browser.
- Logs, analytics, and error traces do not include raw full addresses.
- Address lookup returns explicit states for no match, multiple match, low confidence, and provider unavailable.
- No public behavior change ships without unit and rendered tests for all lookup states.
- Production rollout has source/date/version metadata, provider status monitoring, and rollback instructions.
- District match is not treated as a current member match unless legislator metadata gates pass.
- Senate results are labeled as state-level and carry currentness/seat caveats until Senate metadata is hardened.

## No-Go Items

- No national ZIP rollout with one-ZIP-one-district auto-selection.
- No ambiguous ZIP auto-selecting a House member.
- No third-party address API without privacy/terms review.
- No storing raw addresses by default.
- No unlabeled fixture/sample lookup result.
- No Senate/state result without currentness caveat.
- No public behavior change without rendered tests.
- No client-side third-party address API calls that expose provider keys.
- No address-derived analytics or profiling beyond district lookup.
- No vendor lock-in before source metadata, costs, rate limits, and rollback path are documented.

## Recommended Next Implementation Milestone

**ZIP Lookup Ambiguity UI States V1**

Scope:

- Implement state modeling and copy for existing ZIP lookup only.
- Add UI states for single-district, ambiguous ZIP, multi-state ZIP, unsupported ZIP, fixture/sample-only, and stale/unknown source.
- Stop House auto-select for ambiguous, stale, unknown, or sample-only states.
- Keep manual representative search fallback visible.
- Add unit and rendered tests for all lookup states.
- Do not add address lookup yet.
- Do not add new production data yet.

This should come before any address-provider integration because it fixes the most immediate trust problem with the least privacy and operational risk.
