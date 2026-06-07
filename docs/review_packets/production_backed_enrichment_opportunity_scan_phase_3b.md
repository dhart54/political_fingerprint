# Production-Backed Enrichment Opportunity Scan - Phase 3B

Date: 2026-06-07

Scope: production read-only scan across loaded officials, issue domains, and evidence facets to test whether the amendment/source-packet enrichment workflow can scale beyond Valerie Foushee's remaining single amendment candidate.

No production data was written. No import was run. No Supabase rows were modified. No API shape, UI, support/opposition counting, or alignment logic changed.

## Approval Gate

This packet is for review only.

Do not import any candidate interpretation from this packet unless the user explicitly approves a separate import step. The selected batch also raises a counting-methodology gate: these are procedural rule-context rows, so they should not be imported into the current support/opposition issue pattern unless the product explicitly decides how procedural context should be counted or excluded.

## Discovery Methodology

Read-only production discovery scanned eligible stored rows across:

- loaded officials
- issue domains
- stored `issue_facet` values
- current interpretation status
- member vote position
- vote-context type
- local Congress.gov cache availability

Candidate sections were ranked by:

- total evidence rows
- weak row count and share, where weak means missing, `ambiguous`, or `insufficient_evidence`
- not-voting or present rows
- amendment-like or procedural/rule-like structure
- local Congress.gov cache coverage for weak rows
- likely voter value improvement
- likely scroll/value mismatch reduction

Local source availability was estimated from cached Congress.gov bill records:

- bill detail
- actions
- text versions
- amendments
- committees
- committee reports
- CBO estimates

The scan intentionally did not fetch broad new source data.

## High-Level Finding

The remaining amendment-only opportunity is small:

| Amendment scan metric | Count |
| --- | ---: |
| Amendment-like unique roll calls | 21 |
| Already interpreted amendment roll calls | 19 |
| Weak amendment roll calls | 2 |
| Multi-roll weak amendment-heavy sections | 0 |

The larger scalable opportunity is not a new amendment cluster. It is a repeated procedural-rule context pattern:

| Pattern | Count |
| --- | ---: |
| Officials with Justice/Public Safety `house_of_representatives` weak procedural rows | 434 |
| Officials with the same six-row all-weak pattern | 430 |

This is a major scroll/value mismatch opportunity: the product can show several visible rows in an issue section that are source-backed but not currently understandable to users. It is also a methodology risk because these are procedure votes, not direct final policy votes.

## Top Candidate Sections

The top ranked sections are the same six-row Justice/Public Safety procedural-rule pattern repeated across many officials. The table lists the first 10 production sections by deterministic scan order.

| Rank | Official | Issue domain | Facet / measure group | Total rows | Interpreted rows | Weak rows | Not-voting rows | Current readiness | Why targetable | Expected source availability |
| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| 1 | Aaron Bean | Justice & Public Safety | `house_of_representatives` | 6 | 0 | 6 | 0 | Not enough to summarize | Six weak procedural/rule rows; likely scroll/value mismatch | 6/6 weak rows have strong local Congress.gov cache |
| 2 | Abraham J. Hamadeh | Justice & Public Safety | `house_of_representatives` | 6 | 0 | 6 | 0 | Not enough to summarize | Same six-row procedural pattern | 6/6 weak rows have strong local Congress.gov cache |
| 3 | Adam Gray | Justice & Public Safety | `house_of_representatives` | 6 | 0 | 6 | 2 | Not enough to summarize | Same six-row procedural pattern; two not-voting rows lower member-specific value | 6/6 weak rows have strong local Congress.gov cache |
| 4 | Adam Smith | Justice & Public Safety | `house_of_representatives` | 6 | 0 | 6 | 0 | Not enough to summarize | Same six-row procedural pattern | 6/6 weak rows have strong local Congress.gov cache |
| 5 | Addison P. McDowell | Justice & Public Safety | `house_of_representatives` | 6 | 0 | 6 | 0 | Not enough to summarize | Same six-row procedural pattern | 6/6 weak rows have strong local Congress.gov cache |
| 6 | Adrian Smith | Justice & Public Safety | `house_of_representatives` | 6 | 0 | 6 | 0 | Not enough to summarize | Same six-row procedural pattern | 6/6 weak rows have strong local Congress.gov cache |
| 7 | Adriano Espaillat | Justice & Public Safety | `house_of_representatives` | 6 | 0 | 6 | 0 | Not enough to summarize | Same six-row procedural pattern | 6/6 weak rows have strong local Congress.gov cache |
| 8 | Al Green | Justice & Public Safety | `house_of_representatives` | 6 | 0 | 6 | 0 | Not enough to summarize | Same six-row procedural pattern | 6/6 weak rows have strong local Congress.gov cache |
| 9 | Alexandria Ocasio-Cortez | Justice & Public Safety | `house_of_representatives` | 6 | 0 | 6 | 0 | Not enough to summarize | Same six-row procedural pattern | 6/6 weak rows have strong local Congress.gov cache |
| 10 | Alma S. Adams | Justice & Public Safety | `house_of_representatives` | 6 | 0 | 6 | 0 | Not enough to summarize | Same six-row procedural pattern | 6/6 weak rows have strong local Congress.gov cache |

Why these are not immediately import-ready:

- They are procedural House rule votes.
- Source packets provide bill actions, text versions, committees, and committee reports, but no CRS summaries for the House resolutions.
- They can explain what procedural step happened and what measures were made eligible for consideration.
- They should not be collapsed into direct support/opposition on the underlying bills.

## Selected Target Batch

Selected target:

- Official: Valerie P. Foushee
- Issue domain: Justice & Public Safety
- Facet / measure group: `house_of_representatives`
- Rows: six weak procedural House-resolution rows
- Current status: all six are `insufficient_evidence`

Why selected:

- It is the same high-scoring pattern found across 430 officials, so review work here is reusable.
- It is in the already reviewed Valerie profile path, which makes product impact easier to evaluate.
- It is large enough to matter: six rows, not a one-row amendment candidate.
- All six rows have local Congress.gov cache with official actions, text versions, committees, committee reports, and House Clerk roll-call context.
- The batch directly tests whether source-packet enrichment can improve procedural context without changing issue alignment or vote counting.

Why higher/lower candidates were rejected:

- Higher-ranked candidates have the same row pattern, but selecting the first alphabetic official would not add product-learning value beyond Valerie.
- Amendment-only candidates were rejected for Phase 3B because only one strong amendment candidate remains and Phase 3 already documented it.
- The H.R. 3944 en bloc amendment was rejected because the source packet could not match amendment-specific text.

Expected product value:

- Reduces scroll/value mismatch in issue evidence by explaining why rule rows are visible.
- Helps users distinguish procedural floor-control votes from final policy votes.
- Creates a reusable template for hundreds of similar rows.

Expected readiness impact:

- If kept as procedural context only: readiness label does not change, but evidence comprehension improves.
- If imported under the current interpreted support/opposition model: interpreted count would rise from 6 to 12 in Valerie / Justice, but that would risk treating procedural floor votes like direct policy positions.
- Recommended path: do not import these into current support/opposition counting until procedural interpretation display and counting boundaries are explicit.

## Selected Batch Baseline

Valerie P. Foushee / Justice & Public Safety current production baseline:

| Metric | Current |
| --- | ---: |
| Recorded eligible rows | 13 |
| Interpreted rows | 6 |
| Ambiguous rows | 1 |
| Insufficient-evidence rows | 6 |
| Missing interpretation rows | 0 |
| Current readiness | Mixed but interpretable |

Selected six-row procedural batch:

| Roll | Bill | Question | Current status | Foushee vote | Source-packet result |
| ---: | --- | --- | --- | --- | --- |
| 160 | `119:hres:489` | On Ordering the Previous Question | `insufficient_evidence` | Nay | `still_limited` |
| 161 | `119:hres:489` | On Agreeing to the Resolution | `insufficient_evidence` | Nay | `still_limited` |
| 267 | `119:hres:707` | On Ordering the Previous Question | `insufficient_evidence` | Nay | `still_limited` |
| 268 | `119:hres:707` | On Agreeing to the Resolution | `insufficient_evidence` | Nay | `still_limited` |
| 290 | `119:hres:879` | On Ordering the Previous Question | `insufficient_evidence` | Nay | `still_limited` |
| 291 | `119:hres:879` | On Agreeing to the Resolution | `insufficient_evidence` | Nay | `still_limited` |

## Source Packet Coverage

All six selected rows have:

- House Clerk roll-call URL
- Congress.gov bill detail URL
- Congress.gov actions
- Congress.gov text versions
- Congress.gov committee records
- Congress.gov committee report links

All six selected rows lack:

- CRS bill summary text for the House resolution
- amendment records
- CBO cost estimates

Source-packet classification is `still_limited` for all six because the existing source-packet classifier is amendment-centered and does not promote procedural rule context. That is the correct conservative result.

## Review-Only Candidate Interpretation Table

These candidates are contextual procedural interpretations, not import-ready policy-position interpretations.

| Roll | Confidence | Vote type | Recommendation | Support position | Oppose position | Plain-English summary | Why it mattered | What not to infer | Source basis | Should count if approved/imported later? |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 160 | Contextual | Motion / previous question | Contextual only; counting gate required | Yea supported ordering the previous question | Nay opposed ordering the previous question | The House voted on ordering the previous question for H. Res. 489, a procedural step tied to floor consideration of H.R. 884, H.R. 2056, H.R. 2096, and S. 331. Foushee voted Nay. | The vote affected whether the House moved forward procedurally toward adopting the rule for considering those measures. | Do not treat this as final passage of any listed bill or as a direct position on every issue named in the rule. | House Clerk Roll 160; Congress.gov H. Res. 489 title, actions, text versions, and committee report link. | No, not as direct issue support/opposition under current counting. |
| 161 | Contextual | Rule resolution | Contextual only; counting gate required | Yea supported agreeing to the rule resolution | Nay opposed agreeing to the rule resolution | The House voted on agreeing to H. Res. 489, which set terms for considering H.R. 884, H.R. 2056, H.R. 2096, and S. 331. Foushee voted Nay. | The vote decided whether that floor rule would be adopted. | Do not treat this as final passage of the listed bills or as a broad Justice/Public Safety position. | House Clerk Roll 161; Congress.gov H. Res. 489 title, actions, text versions, and committee report link. | No, not as direct issue support/opposition under current counting. |
| 267 | Contextual | Motion / previous question | Contextual only; counting gate required | Yea supported ordering the previous question | Nay opposed ordering the previous question | The House voted on ordering the previous question for H. Res. 707, a procedural step tied to floor consideration of several D.C. justice/public-safety bills and energy-related measures. Foushee voted Nay. | The vote affected whether the House moved forward procedurally toward adopting the rule. | Do not treat this as final passage of any listed bill or as a position on every measure included in the rule. | House Clerk Roll 267; Congress.gov H. Res. 707 title, actions, text versions, and committee report link. | No, not as direct issue support/opposition under current counting. |
| 268 | Contextual | Rule resolution | Contextual only; counting gate required | Yea supported agreeing to the rule resolution | Nay opposed agreeing to the rule resolution | The House voted on agreeing to H. Res. 707, which set terms for considering several D.C. justice/public-safety bills and energy-related measures. Foushee voted Nay. | The vote decided whether that floor rule would be adopted. | Do not treat this as final passage of the listed bills or as a direct policy position on all measures included in the rule. | House Clerk Roll 268; Congress.gov H. Res. 707 title, actions, text versions, and committee report link. | No, not as direct issue support/opposition under current counting. |
| 290 | Contextual | Procedural / previous question or concurrence context | Contextual only; counting gate required | Yea supported moving forward procedurally on the rule context | Nay opposed moving forward procedurally on the rule context | The House voted on a procedural step for H. Res. 879, a rule covering several Congressional Review Act resolutions, an energy bill, a D.C. policing bill, and other measures. Foushee voted Nay. | The vote affected whether the House moved forward procedurally toward adopting the rule context. | Do not treat this as final passage of any listed resolution or bill. | House Clerk Roll 290; Congress.gov H. Res. 879 title, actions, text versions, and committee report link. | No, not as direct issue support/opposition under current counting. |
| 291 | Contextual | Rule resolution | Contextual only; counting gate required | Yea supported agreeing to the rule resolution | Nay opposed agreeing to the rule resolution | The House voted on agreeing to H. Res. 879, which set terms for considering several Congressional Review Act resolutions, energy measures, and D.C. policing/public-safety measures. Foushee voted Nay. | The vote decided whether that floor rule would be adopted. | Do not treat this as final passage of the listed measures or as a direct position on each included issue. | House Clerk Roll 291; Congress.gov H. Res. 879 title, actions, text versions, and committee report link. | No, not as direct issue support/opposition under current counting. |

## Rows Left Insufficient

All six selected rows should remain insufficient for production import under the current model unless a procedural-context display/counting rule is approved.

Reason:

- They are meaningful procedural context.
- They are not direct final policy votes.
- Current support/opposition issue counts do not distinguish direct policy support from procedural floor-control support.
- Importing them as ordinary interpreted rows could inflate issue pattern counts and confuse alignment.

## Expected Before / After Impact

Recommended after state without import:

- Production remains unchanged.
- Review packet provides a reusable procedural interpretation standard.
- Readiness label remains Mixed but interpretable for Valerie / Justice because no production data changes.

Hypothetical after approved procedural-context implementation:

- Six currently insufficient procedural rows could become understandable in the UI.
- They should remain separated from direct support/opposition issue pattern math.
- Voter value improves by explaining why the rows are visible and what they do not prove.

## Risks

- Procedural rows are easily overread as direct policy positions.
- Existing source-packet classification correctly stays `still_limited`; a separate procedural review standard is needed before import.
- The same pattern appears across hundreds of officials, so a mistake would scale broadly.
- Some House rules bundle measures from multiple issue domains, increasing classification and display risk.
- Current alignment logic may treat interpreted support/oppose positions as issue-position evidence, so these should not be imported until counting boundaries are explicit.

## Recommended Next Step

Do not import this batch.

Recommended next milestone:

1. Define a procedural-context interpretation tier that can be displayed but excluded from support/opposition and alignment math.
2. Add tests proving procedural interpretations do not change issue pattern counts or alignment labels.
3. Then pilot these six Valerie rows as contextual evidence only.

