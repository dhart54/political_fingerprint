# Senate Current-Congress Coverage Audit - Phase 10

Date: 2026-06-08

Scope: production read-only audit of current Senate roll-call coverage and the safest path to expand current-Congress Senate coverage.

No production data was written. No import was run. No Supabase rows were modified. No UI, API shape, support/opposition counting, or alignment logic changed.

## Current Senate Coverage Summary

Production currently contains Senate roll calls only for the 119th Congress / 2025 data window.

| Measure | Current production value |
| --- | ---: |
| Senate roll calls loaded | 80 |
| Congress | 119 |
| Session stored on production roll calls | `null` |
| Year | 2025 |
| Earliest loaded Senate vote date | 2025-01-09 |
| Latest loaded Senate vote date | 2025-11-10 |
| Loaded roll-number range | 1-618 |
| Missing roll numbers inside loaded range | 538 |
| Vote rows per loaded Senate roll call | min 98 / max 100 / avg 99.9 |

The loaded Senate roll calls are not partial member rows. Each loaded roll call has close to a complete Senate vote roster. The gap is at the roll-call selection layer.

Loaded Senate roll calls by month:

| Month | Loaded rolls | Min roll | Max roll |
| --- | ---: | ---: | ---: |
| 2025-01 | 6 | 1 | 22 |
| 2025-02 | 6 | 58 | 96 |
| 2025-03 | 12 | 100 | 153 |
| 2025-04 | 6 | 160 | 227 |
| 2025-05 | 21 | 229 | 275 |
| 2025-06 | 23 | 305 | 353 |
| 2025-07 | 4 | 354 | 372 |
| 2025-08 | 1 | 480 | 480 |
| 2025-11 | 1 | 618 | 618 |

First missing roll numbers inside the loaded production range:

`3, 4, 6, 8, 9, 10, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 88`

## Loaded Senate Row Shape

Vote types represented in loaded Senate rows:

| Vote type | Roll calls | Vote rows |
| --- | ---: | ---: |
| motion | 58 | 5,796 |
| other | 13 | 1,300 |
| final_passage | 7 | 699 |
| concurrence | 1 | 100 |
| rule | 1 | 100 |

Issue domains represented:

| Domain | Roll calls | Vote rows | Eligible roll calls |
| --- | ---: | ---: | ---: |
| Ineligible / no classification | 64 | 6,395 | 0 |
| Infrastructure / Tech / Transport | 7 | 700 | 7 |
| Economy / Taxes | 4 | 400 | 4 |
| National Security / Foreign | 4 | 400 | 4 |
| Justice / Public Safety | 1 | 100 | 1 |

Interpretation status distribution:

| Interpretation status | Roll calls | Vote rows |
| --- | ---: | ---: |
| No interpretation row | 64 | 6,395 |
| interpreted | 10 | 1,000 |
| ambiguous | 6 | 600 |

Top loaded bill clusters:

| Bill / package | Loaded roll calls | Roll range | Date range | Notes |
| --- | ---: | --- | --- | --- |
| H.R. 1 reconciliation | 21 | 329-372 | 2025-06-28 to 2025-07-01 | Large selected package cluster |
| S.J.Res. 55 hydrogen vehicle rule | 12 | 264-275 | 2025-05-21 | Clustered CRA/disapproval context |
| S. 1582 GENIUS Act | 6 | 240-318 | 2025-05-08 to 2025-06-17 | Selected bill cluster |
| S. 5 Laken Riley Act | 4 | 1-7 | 2025-01-09 to 2025-01-20 | Early selected bill cluster |
| S. 331 HALT Fentanyl Act | 3 | 110-127 | 2025-03-06 to 2025-03-14 | Selected issue cluster |

The loaded production rows appear systematically selected around bills, issue domains, or prior import/review logic. They do not appear randomly incomplete.

## Why Senate Coverage Is Incomplete

The local Senate XML cache contains 374 vote files:

| Local cache measure | Value |
| --- | ---: |
| Cached Senate XML vote files | 374 |
| Cached roll ranges | 1-372, 480, 618 |
| Missing cached files inside 1-618 | 244 |
| Cached files parseable by the current Senate adapter | 80 |
| Cached files skipped by the current Senate adapter | 294 |

The current production count of 80 Senate roll calls matches the 80 cached files that the current adapter can parse into a bill-centered roll call. This indicates the main constraint is not the official Senate source. It is the current adapter/import boundary.

Unsupported cached files by document type:

| Document type | Cached files skipped |
| --- | ---: |
| PN | 192 |
| S.Amdt. | 79 |
| H.J.Res. | 21 |
| H.Con.Res. | 2 |

Unsupported cached files by question type:

| Question type | Cached files skipped |
| --- | ---: |
| On the Nomination | 89 |
| On the Cloture Motion | 87 |
| On the Amendment | 57 |
| On the Motion to Proceed | 26 |
| On the Motion | 20 |
| On the Joint Resolution | 11 |
| Other procedural/concurrent questions | 4 |

The adapter currently parses Senate document references for `S`, `S.Res`, `S.J.Res`, `H.R`, and `H.Res` when a usable document number is present. It skips unsupported references deterministically. This is appropriate for the existing bill-centered ingestion model, but it leaves out:

- nominations (`PN`) that are not ordinary issue-position bill votes;
- Senate amendment votes where the XML stores amendment details under the `<amendment>` node rather than as a bill document number;
- House joint/concurrent resolutions in Senate XML, which likely need added document-reference support before they can be safely loaded;
- later 2025 roll numbers after 372, except cached roll 480 and 618, which are not present in the local cache.

## Current ETL And Source Path Findings

Relevant current code paths:

- `backend/app/etl/fetch_sources.py` can build official Senate XML URLs and fetch selected roll numbers into `backend/data_sources/senate_xml/`.
- `backend/app/etl/senate_xml_adapter.py` parses cached Senate XML into the shared ingest bundle shape.
- `backend/app/etl/live_pipeline.py` fetches Senate member XML and explicitly requested Senate roll numbers, infers bill references from cached XML, fetches Congress.gov bill enrichment, and persists through the same ETL path as House data.
- `backend/app/etl/source_packets.py` can build Congress.gov source packets for rows with bill references and cache coverage.
- `backend/app/etl/supervised_enrichment.py` can validate future Senate candidate batches under the same supervised workflow.

House and Senate use different official roll-call source adapters, but both feed the same downstream classification, interpretation, vote-context, and API read paths.

Current Senate collection is explicit-roll based. There is no current full-range Senate crawler or manifest-based production loader. `live_pipeline` requires `--senate-roll` values and only fetches those explicit rolls.

Current schema can store Senate vote facts already; production contains Senate `roll_calls`, `votes_cast`, `vote_classifications`, `vote_contexts`, and `vote_interpretations`. `roll_calls.bill_id` is nullable in the base schema, so a database migration is not obviously required for a vote-facts expansion. However, current ETL/classification code expects each ingested roll call to carry a `bill_ref`, and the current Senate adapter constructs bill records from document references. Loading nominations or amendment-only rows safely would require adapter/classification policy work before any production import, even if no schema migration is needed.

## Source Availability Audit

| Source | Availability | Fields available | Mapping fit | Gaps / risks | Automation readiness |
| --- | --- | --- | --- | --- | --- |
| Senate roll-call XML | Strong for roll-call vote facts. Local cache already has rolls 1-372 plus 480 and 618. Official URL pattern is implemented. | Congress, session, vote number, date, question, title, result text, document type/number/name/title, amendment details, member votes, LIS ids, party/state, yea/nay/present/not voting. | Strong for vote facts and member votes. Good for bill-linked roll calls already supported. | Amendment-only rows need amendment-node parsing and underlying-bill mapping. Nominations are not ordinary issue-position evidence. Later rolls 373-479 and 481-617 need source fetch/caching. | Safe to automate for local cache validation and explicit bounded fetches. Not safe for production import without staging and review. |
| Congress.gov bill cache | Medium to strong for bill context where bill refs exist. Local cache has bill metadata plus enrichment subresources. | Bill title, summary, subjects, actions, text versions, amendments, committees, reports, CBO links when available. | Strong for bill-linked source packets and interpretation review. | Does not by itself explain every Senate motion, cloture vote, or amendment vote. Nominations need a different source/model. | Safe for source-packet construction. Not a support/oppose decision source by itself. |
| GovInfo / official bill text context | Useful as supporting context when already represented through Congress.gov text/action links or local cache. | Text versions, public-law text, reports where available. | Good for review packets and source basis. | Not currently a standalone Senate roll-call importer. | Use as source support after roll facts are loaded/cached; do not automate interpretation from it. |
| Existing local cache | Strong for near-term audit and local validation. | 374 Senate XML vote files; 404 Congress.gov cache files across bill/enrichment directories. | Strong for offline validation and staged expansion planning. | Cache does not cover every missing roll inside production range, and 294 cached files require adapter policy changes before import. | Best first step for no-write validation. |

## Coverage Expansion Options

| Option | Product value | Data volume impact | Interpretation burden | Source availability | Trust / UI risk | Recommendation |
| --- | --- | --- | --- | --- | --- | --- |
| A. Load all missing 2025 Senate roll calls | Highest raw completeness | Up to 538 additional roll calls inside production range, about 53,800 additional vote rows at current roster size | Very high | Partial local cache plus additional fetches needed | High, because nominations/procedure/amendments could flood weak evidence | Do not start here in production |
| B. Load only legislative/eligible Senate roll calls | High value with lower clutter | Unknown until local classification, but much smaller than 538 rolls | Medium to high | Strong for bill-linked XML and Congress.gov cache | Medium | Preferred production direction after local validation |
| C. Load current session/current range first | Useful staging frame | Cached 1-372 plus later bounded ranges; current production already has sparse selected rows through 618 | Medium | Strong for cached 1-372, weaker for later missing ranges | Medium | Good staging boundary |
| D. Load vote facts first, interpretations later | Strong foundation and safer than simultaneous interpretation | Facts expansion can be measured before interpretation import | Defers interpretation burden | Strong for Senate XML | Medium if UI/readiness impact is staged | Preferred workflow |
| E. Enrich source packets before importing interpretations | High trust value | No raw-data expansion by itself | Medium | Strong where bill refs and cache exist | Low | Required before any substantive Senate interpretation import |

## Recommended Expansion Path

Recommended path: staged vote-facts expansion for legislative Senate roll calls, then supervised enrichment.

1. Run a local no-write Senate cache validation for all cached rolls 1-372, 480, and 618.
2. Extend the Senate adapter only as needed for safe legislative references:
   - add `H.J.Res` and `H.Con.Res` document-reference support if the current bill schema accepts those bill types in production;
   - add Senate amendment-node parsing only when the underlying bill and amendment purpose can be mapped source-groundedly;
   - keep nominations out of ordinary issue-position evidence.
3. Build a local manifest classifying each cached roll as:
   - already loaded;
   - legislative bill-linked fact candidate;
   - amendment candidate needing source-packet review;
   - procedural-context candidate;
   - nomination or other non-issue-position row;
   - unsupported/still insufficient.
4. Only after the local manifest is reviewed, import a bounded fact-only batch if explicitly approved.
5. Generate supervised interpretation candidates later from the loaded facts and source packets.

This means vote facts should be loaded before interpretations, but only after a local validation manifest and explicit import approval. Interpretations should not be imported with the fact load.

Estimated expansion sizes:

- Full current production range: 538 missing Senate roll calls inside 1-618, roughly 53,800 additional vote rows.
- Existing local cache gap: 294 cached-but-skipped roll calls, roughly 29,400 vote rows, plus 244 uncached roll calls inside 1-618.
- Initial safe legislative fact batch: likely much smaller than 538, pending local manifest classification. The clearest first candidate set is bill-linked joint/concurrent resolutions and source-grounded amendment rows, not nominations.

## Readiness And Enrichment Implications

Senate expansion should happen before broad new House enrichment if the goal is current-official coverage parity. Current House roll-call coverage is far broader within the loaded 2025 range, while Senate coverage is clearly sparse and adapter-filtered. Existing House candidate imports can still proceed one at a time only after explicit approval, but the next coverage milestone should focus on Senate fact completeness.

Existing candidate classification and supervised enrichment tooling can be reused for Senate rows, but Senate-specific guardrails are needed:

- cloture, motion-to-proceed, motion-to-table, and nomination votes must not be treated as ordinary support/opposition evidence by default;
- Senate amendment votes need the amendment purpose, underlying bill, vote action, and member position before substantive interpretation;
- procedural-context tier can apply to Senate procedure, but Senate procedure should have its own reviewed examples before any automated production import;
- not-voting and present handling can stay non-counting under the existing vote-position treatment;
- nominations should not be added to issue-position summaries without a separate product decision and methodology, because they are personnel confirmation votes rather than bill-policy votes.

Senate expansion changes the autonomous procedural-context roadmap. House procedural-context import has been validated for a specific House floor-rule pattern. Senate procedural-context import should remain supervised until Senate-specific procedural categories are reviewed and tested.

## What Should Not Be Automated Yet

Do not automate:

- production import of all missing Senate roll calls;
- production import of nominations into ordinary issue domains;
- substantive interpretation of Senate amendment votes from amendment purpose alone;
- support/opposition assignment for cloture, motion-to-proceed, or procedural votes without reviewed source basis;
- procedural-context imports for Senate categories without explicit Senate-specific examples and approval;
- broad source scraping beyond the existing official Senate XML and Congress.gov/GovInfo cache paths.

## Risks

- Loading all Senate votes at once would substantially increase weak/procedural rows and could worsen scroll/value mismatch before interpretation/context catches up.
- Nominations are numerous in the local cache and need a separate product/methodology treatment if ever surfaced.
- Senate amendment XML contains useful amendment fields, but the current adapter does not map them into source packets; treating those rows as substantive without amendment review would weaken trust.
- The production schema can store Senate facts, but the current ETL assumes a bill reference. Adapter changes should be validated locally before any production write.
- Current production uses Supabase as the working database, so every import still needs explicit approval, a rollback artifact, and post-import validation.

## Next Milestone Recommendation

Recommended next milestone: Senate Legislative Vote-Facts Expansion Preflight.

Scope should be preflight only:

- build a local manifest for cached Senate rolls 1-372, 480, and 618;
- classify cached rows into loaded, bill-linked legislative, amendment-needs-review, procedural-context, nomination, and unsupported buckets;
- identify the first bounded fact-only import batch;
- produce an import preflight and rollback artifact;
- stop before production import approval.

Do not begin with broad interpretation import. The safest sequence is source/fact coverage first, then source packets, then supervised interpretation batches.

## Validation Performed

Production read-only queries were run with `default_transaction_read_only = on` for:

- Senate coverage by Congress/session/year;
- loaded roll-number range and missing roll count;
- loaded rolls by month;
- vote-type distribution;
- issue-domain distribution;
- interpretation status distribution;
- vote rows per loaded Senate roll call;
- top loaded bill clusters.

Local source/code audit covered:

- Senate fetch URL and member-source support in `backend/app/etl/fetch_sources.py`;
- Senate XML parsing and skip behavior in `backend/app/etl/senate_xml_adapter.py`;
- explicit-roll live pipeline behavior in `backend/app/etl/live_pipeline.py`;
- source-packet support in `backend/app/etl/source_packets.py`;
- vote-context vote-type support in `backend/app/etl/vote_context.py`;
- schema support in `backend/migrations/0001_initial_schema.sql` and `backend/migrations/0008_vote_contexts.sql`;
- methodology source-adapter documentation in `docs/methodology.md`.
