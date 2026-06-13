# Post-Expansion Senate Value Enrichment Package - Phase 20

Date: 2026-06-12

Scope: production read-only audit and review-only candidate generation after the Phase 14 Senate bill-centered fact import and Phase 19A Senate amendment fact import.

No production data was written in Phase 20. No `vote_interpretations` rows were inserted, updated, or deleted. No support/opposition counting logic, alignment logic, UI behavior, or API shape changed.

## Production Coverage Snapshot

Read-only production query baseline:

| Metric | Count |
| --- | ---: |
| Legislators | 548 |
| Senate legislators | 102 |
| Total roll calls | 624 |
| House roll calls | 339 |
| Senate roll calls | 285 |
| Total votes_cast | 175,264 |
| Senate votes_cast | 28,492 |
| Senate vote_contexts | 28,492 |
| Total vote_interpretations | 74 |
| vote_interpretations with support_position | 48 |
| vote_interpretations with oppose_position | 48 |
| Senate amendment references | 112 |

Senate production rows by fact type:

| Fact type | Roll calls | Vote rows | Interpreted rolls | Classified rolls |
| --- | ---: | ---: | ---: | ---: |
| Senate amendment fact | 112 | 11,197 | 0 | 0 |
| Senate bill/other fact | 173 | 17,295 | 16 | 80 |

Senate interpretation distribution:

| Status | Roll calls | Vote rows |
| --- | ---: | ---: |
| no_interpretation | 269 | 26,892 |
| interpreted | 10 | 1,000 |
| ambiguous | 6 | 600 |

## Amendment API/Data Verification

Phase 19A successfully preserved amendment identity in production:

- `senate_amendment_references` rows: 112
- amendment vote rows: 11,197
- amendment rows with `vote_interpretations`: 0

However, the currently imported amendment fact rows have no `vote_classifications`:

| Check | Count |
| --- | ---: |
| Amendment roll calls | 112 |
| Amendment roll calls with vote_classifications | 0 |
| Amendment roll calls with vote_interpretations | 0 |
| Amendment vote rows | 11,197 |

The API evidence serializer can label rows as `senate_amendment_fact` when amendment references are present, but the position evidence query reaches evidence through eligible `vote_classifications`. As a result, the 112 imported amendment facts are preserved in production but are not yet issue-evidence rows in the accountability profile. A substantive amendment enrichment package would require a separate classification/evidence-readiness milestone before interpretation import can create user-visible value.

## Opportunity Scan Methodology

The scan used production read-only SQL with the following ranking factors:

- affected roll-call count;
- affected vote-row count;
- whether rows are eligible issue evidence today;
- whether rows already have `vote_interpretations`;
- whether rows are bill-centered, amendment facts, or procedural floor/process rows;
- source availability from official Senate XML and production bill/amendment references;
- likely voter value if enriched;
- trust risk and likelihood of overclaiming;
- whether enrichment would require classification, API, counting, or alignment changes.

Rows were not imported, reclassified, or modified.

## Top Opportunities Found

| Rank | Opportunity | Roll calls | Vote rows | Current evidence readiness | Opportunity type | Expected source availability | Value | Risk |
| ---: | --- | ---: | ---: | --- | --- | --- | --- | --- |
| 1 | H.R. 1 reconciliation package, Senate bill-centered and amendment-adjacent votes | 43 | 4,300 | mostly ineligible or unclassified; 21 low-confidence/non-eligible classifications | mixed substantive/procedural candidate after classification work | strong Senate XML; bill context available; amendment context partial | high, because it covers a major package across all senators | high unless classification/readiness is solved first |
| 2 | Senate amendment facts on S.Con.Res. 7 | 25 | 2,500 | amendment references preserved; no issue classifications | amendment fact/value candidate after evidence-readiness work | strong Senate XML and amendment reference rows | high for explaining budget-resolution amendment activity | high if treated as issue-position evidence too early |
| 3 | Senate amendment facts on H.Con.Res. 14 | 21 | 2,100 | amendment references preserved; no issue classifications | amendment fact/value candidate after evidence-readiness work | strong Senate XML and amendment reference rows | high for budget/reconciliation process comprehension | high without classification and display policy |
| 4 | H.R. 5371 continuing appropriations package | 18 | 1,800 | one eligible/interpreted roll; remaining rows mostly unclassified | mixed substantive/procedural candidate after classification work | strong Senate XML; bill context available | medium-high for appropriations context | medium-high because many rows are not evidence-ready |
| 5 | S.J.Res. 55 hydrogen-vehicle safety CRA floor-process rows | 6 weak eligible rows plus 1 interpreted final resolution vote | 600 weak vote rows | eligible issue evidence today; ambiguous procedural rows | procedural-context candidate | strong Senate XML and production bill title | medium, reduces scroll/value mismatch in current API surface | low if kept non-counting |

## Candidate Batch Generated

Created review-only procedural-context batch:

- `docs/interpretation_batches/batch_015_senate_sjres55_procedural_context_candidates.json`

Candidate split:

| Batch | Substantive | Procedural context | Still insufficient | Import status |
| --- | ---: | ---: | ---: | --- |
| batch_015_senate_sjres55_procedural_context_candidates | 0 | 6 | 0 | review-only; no import approval in this milestone |

The batch covers Senate Roll 266-271 on S.J.Res. 55. These rows are floor-process motions connected to a Congressional Review Act disapproval resolution. They should remain visible only as procedural context, with `support_position = null`, `oppose_position = null`, and no support/opposition or alignment effect.

## Why No Substantive Package Was Selected

Phase 20 did not produce a selected substantive import preflight because no sufficiently bounded, user-visible substantive Senate package passed the guardrails.

The largest post-expansion opportunities are real, but they are not safe substantive import targets yet:

- the 112 Senate amendment facts have no issue classifications, so they are not currently issue-evidence rows;
- H.R. 1 has many rows, but the classified rows are ineligible or low-confidence rather than eligible issue evidence;
- many newly imported bill-centered rows are fact-complete but unclassified;
- importing `vote_interpretations` for unclassified rows would not reliably improve the current position-by-issue surface;
- turning those rows into user-visible evidence requires a separate classification/evidence-readiness decision, not an interpretation-only import.

This is a true Phase 20 blocker for the requested substantive package and rollback preflight. Proceeding anyway would risk creating interpretations that either remain invisible or imply issue evidence before the classification layer has approved the row.

## Expected Readiness And Value Impact

Procedural batch if later approved:

- affects 6 roll calls and 600 senator vote rows;
- can reduce unexplained-row burden for the existing S.J.Res. 55 Infrastructure/Transportation section;
- should not promote issue readiness to Strong or Mixed by itself;
- should not add substantive support/opposition counts;
- should not change alignment.

Deferred substantive opportunities:

- H.R. 1 and Senate amendment packages could materially increase Senate profile value after classification/evidence-readiness work;
- likely impact is high because these packages affect all senators and cover major current-Congress legislative activity;
- readiness impact cannot be counted yet because the rows are not eligible issue evidence today.

## Expected Support/Opposition And Alignment Impact

For the generated procedural batch:

- support_position: null
- oppose_position: null
- support/opposition impact: 0
- alignment impact: 0
- vote_interpretations write approval: not requested

For deferred substantive packages:

- impact is not estimated for import approval because no substantive package was selected;
- any future substantive import must include exact roll_call_ids, support/oppose positions, baseline counts, alignment spot checks, and rollback SQL.

## Rows Rejected Or Deferred

| Category | Count | Reason |
| --- | ---: | --- |
| Senate amendment facts | 112 roll calls | Amendment identity is preserved, but rows lack issue classifications and are not current issue-evidence rows. |
| H.R. 1 low-confidence/ineligible classified rows | 21 roll calls | Classification layer does not currently mark these as eligible issue evidence. |
| H.R. 1 unclassified amendment/floor rows | 22 roll calls | Need classification/readiness work before interpretation candidates. |
| Other bill-centered unclassified Senate rows | 93 roll calls | Fact coverage exists, but interpretation import would not reliably surface without classification. |
| PN nominations | not scanned for candidates | Explicitly out of scope. |
| Treaty/executive votes | not scanned for candidates | Explicitly out of scope. |

## Approval Gates

No substantive approval phrase is recommended from Phase 20 because no substantive package passed the hard gates.

If the procedural S.J.Res. 55 batch is reviewed later, the required approval phrase should be:

> Approve production import of batch_015 Senate S.J.Res. 55 procedural-context rows, with support_position and oppose_position null and no support/opposition or alignment counting changes.

Before any substantive Senate import, run a separate classification/evidence-readiness milestone and then a fresh supervised import preflight.

## Recommended Next Action

Run a Senate classification and evidence-readiness preflight before any substantive interpretation import.

That milestone should:

- classify newly imported Senate bill-centered and amendment fact rows into eligible issue evidence, procedural context, still insufficient, or out of scope;
- verify how `senate_amendment_fact` rows appear in the API after classification;
- avoid support/opposition and alignment changes until a bounded substantive interpretation preflight is created;
- produce a new top opportunity map after evidence readiness, then select a substantive package only if it is visible, source-grounded, and count-impact validated.

Do not import the H.R. 1, Senate amendment, or other substantive packages until that classification/evidence-readiness step is complete.

