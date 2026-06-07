# Production-Backed Candidate Batch - Phase 5

Date: 2026-06-07

Scope: review-only candidate batch selected from the Phase 5 broad production read-only opportunity map.

No production data was written. No import was run. No Supabase rows were modified. No API shape, UI, support/opposition counting, or alignment logic changed.

## Selected Batch

Selected target:

- Official: Aaron Bean
- Bioguide ID: `B001314`
- Issue domain: Justice & Public Safety
- Facet / measure group: `house_of_representatives`
- Candidate count: six
- Candidate split: zero substantive, six procedural-context, zero insufficient

Current production baseline for this section:

| Metric | Current |
| --- | ---: |
| Total rows | 6 |
| Interpreted rows | 0 |
| Weak rows | 6 |
| Procedural-context rows | 6 |
| Not-voting rows | 0 |
| Current readiness | Not enough to summarize |

## Source Coverage

All six candidates have local Congress.gov cache hits with:

- bill detail URL
- action records
- text-version metadata
- committee records
- committee report links
- Congress.gov source URLs

All six lack:

- CRS bill summary text for the House resolution
- amendment records
- matched amendment purpose or description
- CBO cost estimates

The existing source-packet classifier returns `still_limited` for all six, which is the correct conservative result for procedural rows. The proposed category is procedural-context, not substantive interpretation.

## Candidate Table

| Roll call ID | Roll | Official / domain / facet | Vote type | Candidate category | Source basis | Proposed summary | Why it mattered | What not to infer | Would count if later approved/imported? | Confidence | Remaining risks |
| ---: | ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 145 | 160 | Aaron Bean / Justice & Public Safety / `house_of_representatives` | Motion / previous question | Procedural-context | House Clerk roll context; Congress.gov H. Res. 489 bill detail, actions, text versions, committees, H. Rept. 119-151 | The House voted on ordering the previous question for H. Res. 489, a procedural step tied to floor consideration of H.R. 884, H.R. 2056, H.R. 2096, and S. 331. Bean voted Yea. | The vote affected whether the House moved forward procedurally toward adopting the rule for considering those measures. | Do not treat this as final passage of any listed bill or as direct support for every policy included in the rule. | No. It should be visible context only, not support/opposition evidence. | Contextual | Rule bundled multiple measures; source packet remains `still_limited` for substantive policy effect. |
| 146 | 161 | Aaron Bean / Justice & Public Safety / `house_of_representatives` | Rule resolution | Procedural-context | House Clerk roll context; Congress.gov H. Res. 489 bill detail, actions, text versions, committees, H. Rept. 119-151 | The House voted on agreeing to H. Res. 489, which set terms for considering H.R. 884, H.R. 2056, H.R. 2096, and S. 331. Bean voted Yea. | The vote decided whether that floor rule would be adopted. | Do not treat this as final passage of the listed bills or as a broad Justice/Public Safety position. | No. It should be visible context only, not support/opposition evidence. | Contextual | Rule bundled multiple measures; source packet remains `still_limited` for substantive policy effect. |
| 246 | 267 | Aaron Bean / Justice & Public Safety / `house_of_representatives` | Motion / previous question | Procedural-context | House Clerk roll context; Congress.gov H. Res. 707 bill detail, actions, text versions, committees, H. Rept. 119-298 | The House voted on ordering the previous question for H. Res. 707, a procedural step tied to floor consideration of several D.C. justice/public-safety bills and several energy-related measures. Bean voted Yea. | The vote affected whether the House moved forward procedurally toward adopting the rule. | Do not treat this as final passage of any listed bill or as direct support for every measure included in the rule. | No. It should be visible context only, not support/opposition evidence. | Contextual | Rule includes measures from more than one issue area; source packet remains `still_limited` for substantive policy effect. |
| 247 | 268 | Aaron Bean / Justice & Public Safety / `house_of_representatives` | Rule resolution | Procedural-context | House Clerk roll context; Congress.gov H. Res. 707 bill detail, actions, text versions, committees, H. Rept. 119-298 | The House voted on agreeing to H. Res. 707, which set terms for considering several D.C. justice/public-safety bills and several energy-related measures. Bean voted Yea. | The vote decided whether that floor rule would be adopted. | Do not treat this as final passage of the listed bills or as a direct policy position on every measure included in the rule. | No. It should be visible context only, not support/opposition evidence. | Contextual | Rule includes measures from more than one issue area; source packet remains `still_limited` for substantive policy effect. |
| 269 | 290 | Aaron Bean / Justice & Public Safety / `house_of_representatives` | Procedural / previous-question or concurrence context | Procedural-context | House Clerk roll context; Congress.gov H. Res. 879 bill detail, actions, text versions, committees, H. Rept. 119-380 | The House voted on a procedural step for H. Res. 879, a rule covering several Congressional Review Act resolutions, energy measures, a D.C. policing bill, and other measures. Bean voted Yea. | The vote affected whether the House moved forward procedurally toward adopting the rule context. | Do not treat this as final passage of any listed resolution or bill, or as support for every bundled measure. | No. It should be visible context only, not support/opposition evidence. | Contextual | Rule bundles multiple issue areas; source packet remains `still_limited` for substantive policy effect. |
| 270 | 291 | Aaron Bean / Justice & Public Safety / `house_of_representatives` | Rule resolution | Procedural-context | House Clerk roll context; Congress.gov H. Res. 879 bill detail, actions, text versions, committees, H. Rept. 119-380 | The House voted on agreeing to H. Res. 879, which set terms for considering several Congressional Review Act resolutions, energy measures, D.C. policing/public-safety measures, and other measures. Bean voted Yea. | The vote decided whether that floor rule would be adopted. | Do not treat this as final passage of the listed measures or as direct support for each included issue. | No. It should be visible context only, not support/opposition evidence. | Contextual | Rule bundles multiple issue areas; source packet remains `still_limited` for substantive policy effect. |

## Expected Impact If Later Approved

Expected product value:

- Six currently weak rows become understandable procedural context.
- The section still does not receive substantive support/opposition counts.
- Alignment labels remain unchanged.
- Readiness should remain cautious unless substantive interpreted Yes/No rows are separately added.
- The same review pattern can scale to the repeated House procedural-rule cluster.

Expected readiness impact:

- Before: Not enough to summarize, six weak rows.
- After contextual approval/import: still not a substantive issue-position summary, but six rows can display as procedural context.

## Import Recommendation

Do not import this batch automatically.

The first bounded import batch, if approved later, should be this six-row Aaron Bean procedural-context batch or the already reviewed Valerie analog, but only under a production-write approval gate that explicitly preserves contextual/no-count behavior.

Required approval gate before any production write:

- confirm the storage model for procedural-context records
- confirm support_position and oppose_position remain null or otherwise cannot affect counts
- confirm alignment payloads are unchanged before and after import
- confirm issue overview/readiness behavior remains cautious
- prepare rollback instructions
- validate row-level source basis and `what_not_to_infer`

## Final Recommendation

The broad API/source sweep is ready for supervised batch review, not unsupervised imports.

Next work should prioritize a bounded procedural-context production import only after the storage/counting approval gate is accepted. Coverage expansion can continue in parallel for substantive interpretation rows, but the production write path should remain gated.
