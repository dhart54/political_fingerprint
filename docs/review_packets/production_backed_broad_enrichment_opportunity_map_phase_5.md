# Production-Backed Broad Enrichment Opportunity Map - Phase 5

Date: 2026-06-07

Scope: production read-only scan across loaded officials, issue domains, facets, and weak evidence sections after the procedural-context tier was added.

No production data was written. No import was run. No Supabase rows were modified. No API shape, UI, support/opposition counting, or alignment logic changed.

## Methodology

The scan read production evidence rows with eligible vote classifications and joined:

- loaded officials
- roll calls
- member vote positions
- vote classifications
- current vote interpretations
- vote contexts
- bill metadata

Rows were grouped by official, issue domain, and current facet or measure group. Weak rows were rows whose current interpretation status was missing, `ambiguous`, or `insufficient_evidence`. Procedural rows were detected using the same Phase 4 procedural-context rules: non-interpreted rows with rule, previous-question, agreeing-to-resolution, or providing-for-consideration context.

Local Congress.gov cache coverage was checked without broad fetching. Amendment-like weak rows were also passed through the existing source-packet classifier to separate possible substantive interpretation candidates from rows that remain limited.

Ranking used:

- total row count
- weak row count and share
- procedural-context row count
- local source/cache availability
- likely substantive interpretation value
- likely scroll/value mismatch reduction
- trust risk

Procedural-context candidates are not treated as support/opposition evidence.

## Scan Summary

| Metric | Count |
| --- | ---: |
| Production evidence rows scanned | 26,763 |
| Opportunity sections found | 4,863 |
| Procedural-context candidate sections | 2,163 |
| Substantive interpretation candidate sections | 432 |
| Still-insufficient sections | 2,268 |

The highest-scoring pattern is the same six-row House procedural/floor-rule Justice & Public Safety section repeated across many officials. The top substantive opportunities are mostly one-row amendment candidates, so they are lower value as a bounded batch than the repeated procedural-context pattern.

## Top 20 Opportunities

| Rank | Official | Issue domain | Facet / measure group | Total rows | Interpreted rows | Weak rows | Procedural rows | Not-voting rows | Current readiness | Opportunity type | Expected source availability | Expected value | Risk |
| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 1 | Aaron Bean | Justice & Public Safety | `house_of_representatives` | 6 | 0 | 6 | 6 | 0 | Not enough to summarize | Procedural-context candidate | Strong local cache, 6/6 weak rows | High | Medium |
| 2 | Abraham J. Hamadeh | Justice & Public Safety | `house_of_representatives` | 6 | 0 | 6 | 6 | 0 | Not enough to summarize | Procedural-context candidate | Strong local cache, 6/6 weak rows | High | Medium |
| 3 | Adam Gray | Justice & Public Safety | `house_of_representatives` | 6 | 0 | 6 | 6 | 2 | Not enough to summarize | Procedural-context candidate | Strong local cache, 6/6 weak rows | High | Medium |
| 4 | Adam Smith | Justice & Public Safety | `house_of_representatives` | 6 | 0 | 6 | 6 | 0 | Not enough to summarize | Procedural-context candidate | Strong local cache, 6/6 weak rows | High | Medium |
| 5 | Addison P. McDowell | Justice & Public Safety | `house_of_representatives` | 6 | 0 | 6 | 6 | 0 | Not enough to summarize | Procedural-context candidate | Strong local cache, 6/6 weak rows | High | Medium |
| 6 | Adrian Smith | Justice & Public Safety | `house_of_representatives` | 6 | 0 | 6 | 6 | 0 | Not enough to summarize | Procedural-context candidate | Strong local cache, 6/6 weak rows | High | Medium |
| 7 | Adriano Espaillat | Justice & Public Safety | `house_of_representatives` | 6 | 0 | 6 | 6 | 0 | Not enough to summarize | Procedural-context candidate | Strong local cache, 6/6 weak rows | High | Medium |
| 8 | Al Green | Justice & Public Safety | `house_of_representatives` | 6 | 0 | 6 | 6 | 0 | Not enough to summarize | Procedural-context candidate | Strong local cache, 6/6 weak rows | High | Medium |
| 9 | Alexandria Ocasio-Cortez | Justice & Public Safety | `house_of_representatives` | 6 | 0 | 6 | 6 | 0 | Not enough to summarize | Procedural-context candidate | Strong local cache, 6/6 weak rows | High | Medium |
| 10 | Alma S. Adams | Justice & Public Safety | `house_of_representatives` | 6 | 0 | 6 | 6 | 0 | Not enough to summarize | Procedural-context candidate | Strong local cache, 6/6 weak rows | High | Medium |
| 11 | Ami Bera | Justice & Public Safety | `house_of_representatives` | 6 | 0 | 6 | 6 | 0 | Not enough to summarize | Procedural-context candidate | Strong local cache, 6/6 weak rows | High | Medium |
| 12 | Andrea Salinas | Justice & Public Safety | `house_of_representatives` | 6 | 0 | 6 | 6 | 0 | Not enough to summarize | Procedural-context candidate | Strong local cache, 6/6 weak rows | High | Medium |
| 13 | Andrew Ogles | Justice & Public Safety | `house_of_representatives` | 6 | 0 | 6 | 6 | 0 | Not enough to summarize | Procedural-context candidate | Strong local cache, 6/6 weak rows | High | Medium |
| 14 | Andrew R. Garbarino | Justice & Public Safety | `house_of_representatives` | 6 | 0 | 6 | 6 | 0 | Not enough to summarize | Procedural-context candidate | Strong local cache, 6/6 weak rows | High | Medium |
| 15 | Andrew S. Clyde | Justice & Public Safety | `house_of_representatives` | 6 | 0 | 6 | 6 | 0 | Not enough to summarize | Procedural-context candidate | Strong local cache, 6/6 weak rows | High | Medium |
| 16 | Andre Carson | Justice & Public Safety | `house_of_representatives` | 6 | 0 | 6 | 6 | 0 | Not enough to summarize | Procedural-context candidate | Strong local cache, 6/6 weak rows | High | Medium |
| 17 | Andy Barr | Justice & Public Safety | `house_of_representatives` | 6 | 0 | 6 | 6 | 0 | Not enough to summarize | Procedural-context candidate | Strong local cache, 6/6 weak rows | High | Medium |
| 18 | Andy Biggs | Justice & Public Safety | `house_of_representatives` | 6 | 0 | 6 | 6 | 0 | Not enough to summarize | Procedural-context candidate | Strong local cache, 6/6 weak rows | High | Medium |
| 19 | Andy Harris | Justice & Public Safety | `house_of_representatives` | 6 | 0 | 6 | 6 | 0 | Not enough to summarize | Procedural-context candidate | Strong local cache, 6/6 weak rows | High | Medium |
| 20 | Angie Craig | Justice & Public Safety | `house_of_representatives` | 6 | 0 | 6 | 6 | 0 | Not enough to summarize | Procedural-context candidate | Strong local cache, 6/6 weak rows | High | Medium |

## Other Opportunity Types

The scan also found 432 substantive interpretation candidate sections. These are mostly single-row Justice/Public Safety amendment candidates in `administrative_law_and_regulatory_procedures`, with strong local cache coverage. They may be useful cleanup items but are not the best Phase 5 batch because each section is one row.

The scan found 2,268 still-insufficient sections. Those usually have weak source basis, unclear practical effect, or insufficient bill/action context for a reviewable candidate.

## Selected Target Batch

Selected target:

- Official: Aaron Bean
- Issue domain: Justice & Public Safety
- Facet / measure group: `house_of_representatives`
- Rows: six
- Current interpreted rows: zero
- Current weak rows: six
- Current procedural-context rows: six
- Current readiness: Not enough to summarize
- Opportunity type: procedural-context candidate

Why selected:

- It is the highest-scoring pattern in the broad production scan.
- It has multiple rows and strong local source coverage.
- It tests the new procedural-context tier directly.
- It is bounded enough for human review.
- It does not require schema changes or support/opposition counting changes.
- It avoids treating procedural rows as substantive issue-position evidence.

Why not a substantive amendment batch:

- The top substantive candidates are one-row cleanup opportunities.
- They may improve a single evidence card but do not reduce the repeated scroll/value mismatch as much as the six-row procedural pattern.
- No multi-row substantive amendment-heavy weak section outranked the procedural-context pattern.

## Expected Value

If approved later under a contextual import gate, this batch would make six currently weak rows understandable for Aaron Bean and provide a reusable pattern for the repeated House procedural-rule cluster. It would not improve support/opposition counts or alignment labels, and it should not promote issue readiness unless substantive interpreted rows are separately added.

## Risks

- Procedural rows are easy to overread as direct support for or opposition to underlying bills.
- Some House rules bundle multiple bills and issue domains.
- Source packets classify these rows as `still_limited` because existing source-packet classification is amendment-centered and correctly does not promote procedural rule context into substantive interpretation.
- A production import must preserve null support/oppose positions or use an explicitly approved contextual storage model.

## Approval Gate

Do not import anything from this scan without a separate explicit production-write approval.

Any later import must prove:

- procedural-context rows remain excluded from support/opposition counts
- procedural-context rows remain excluded from alignment math
- procedural-context rows remain visibly labeled as procedural context
- rollback instructions exist
- before/after production counts are validated
