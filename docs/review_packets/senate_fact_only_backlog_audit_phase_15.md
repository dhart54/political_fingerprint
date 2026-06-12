# Senate Fact-Only Backlog Completion Audit - Phase 15

Date: 2026-06-08

Scope: 119th Congress / 2025 Senate roll-call facts, audited across known roll numbers 1-618.

No production data was written. No import was run. No additional Senate XML fetch was needed because all roll numbers in the audited 1-618 range were already cached locally after Phase 14. No `vote_interpretations` rows were created, updated, or deleted. No UI, API shape, support/opposition counting logic, or alignment logic changed.

## Why Import Did Not Run

The full current-Congress / 2025 Senate backlog audit found zero remaining absent-from-production rows eligible for fact-only loading under the Phase 15 hard gates.

All cached rows absent from production are deferred or excluded categories:

- PN nominations;
- Senate amendments with resolvable parent context, still deferred because amendment identifiers, parent bills, and amendment purposes are not preserved in the current fact-only storage path;
- treaty/executive votes.

Because no eligible bill-centered legislative rows remained, no Phase 15 manifest was created, no rollback SQL was required, and the pre-approved Phase 15 production import condition was not used.

## Full Backlog Audit Summary

Audited range:

- Senate roll numbers 1-618
- 119th Congress
- calendar year 2025 only

Production/cache state after Phase 14:

| State | Count |
| --- | ---: |
| Total roll numbers in audited range | 618 |
| Loaded production Senate `roll_calls` | 173 |
| Locally cached Senate XML files in range | 618 |
| Uncached roll numbers | 0 |
| Cached but not loaded roll numbers | 445 |
| Missing/unavailable source files | 0 |
| Out-of-scope cached rows | 0 |

Production baseline used for guardrail comparison:

| Check | Count |
| --- | ---: |
| Total `vote_interpretations` | 74 |
| `vote_interpretations` with `support_position` | 48 |
| `vote_interpretations` with `oppose_position` | 48 |
| House `roll_calls` | 339 |
| House `votes_cast` | 146,772 |
| House `vote_contexts` | 146,772 |

## Classification Summary

Classification covered all cached Senate XML rows in the 1-618 audited range.

| Category | Count | Phase 15 treatment |
| --- | ---: | --- |
| Already loaded in production | 173 | No action |
| PN nomination | 330 | Excluded |
| Senate amendment with resolvable parent context | 113 | Deferred |
| Treaty / executive vote | 2 | Excluded |
| Eligible fact-only bill-centered legislative vote | 0 | None available |
| Amendment-only without enough context | 0 | None found |
| Procedural-only | 0 | None found as a separate unsupported category |
| Unsupported reference type | 0 | None found |
| Malformed/unparseable | 0 | None found |
| Out-of-scope congress/year | 0 | None found |

## Already Loaded Production Rolls

Production contains 173 Senate roll calls after Phase 14. These include the earlier production set, the Phase 13 23-roll fact-only package, and the Phase 14 70-roll fact-only package.

Representative examples:

| Roll | Date | Question | Document |
| ---: | --- | --- | --- |
| 1 | 2025-01-09 | On Cloture on the Motion to Proceed | S. 5 |
| 2 | 2025-01-13 | On the Motion to Proceed | S. 5 |
| 5 | 2025-01-17 | On the Cloture Motion | S. 5 |
| 7 | 2025-01-20 | On Passage of the Bill | S. 5 |
| 11 | 2025-01-22 | On Cloture on the Motion to Proceed | S. 6 |

## Excluded And Deferred Backlog

### PN Nominations

Count: 330

Representative examples:

| Roll | Date | Question | Title |
| ---: | --- | --- | --- |
| 8 | 2025-01-20 | On the Nomination | Confirmation: Marco Rubio, of Florida, to be Secretary of State |
| 9 | 2025-01-21 | On the Motion to Proceed | Motion to Proceed to Legislative Session |
| 10 | 2025-01-21 | On the Motion to Proceed | Motion to Proceed to Executive Session to Consider the Nomination of Peter Hegseth to be Secretary of Defense |
| 12 | 2025-01-23 | On the Cloture Motion | Motion to Invoke Cloture: John Ratcliffe to be Director of the Central Intelligence Agency |
| 13 | 2025-01-23 | On the Nomination | Confirmation: John Ratcliffe, of Texas, to be Director of the Central Intelligence Agency |

Reason excluded:

- PN nomination semantics are not approved for the current fact-only product model.
- The existing fact importer expects bill-centered references for storage through the current `bills` / `roll_calls` path.
- PN loading should wait for a separate product/methodology decision about nomination records, evidence surfaces, and any needed schema/storage shape.

### Senate Amendments With Resolvable Parent Context

Count: 113

Representative examples:

| Roll | Date | Question | Title |
| ---: | --- | --- | --- |
| 3 | 2025-01-15 | On the Amendment | Cornyn Amdt. No. 14 |
| 4 | 2025-01-15 | On the Amendment | Coons Amdt. No. 23 |
| 6 | 2025-01-20 | On the Amendment | Ernst Amdt No. 8, As Amended |
| 62 | 2025-02-20 | On the Motion | Motion to Waive All Applicable Budgetary Discipline Re: Schumer Amdt. No. 454 |
| 63 | 2025-02-20 | On the Motion | Motion to Waive All Applicable Budgetary Discipline Re: Klobuchar Amdt. No. 494 |

Reason deferred:

- Senate amendment handling remains explicitly out of scope for Phase 15.
- Although many amendment rows include parent context, the fact-only path does not yet preserve amendment identifiers, amendment-to-amendment relationships, parent bill references, amendment purpose text, and other context needed to keep these rows auditable.
- Loading amendment rows through only parent `bill_id` would blur the distinction between amendment facts and bill-level votes.

### Treaty / Executive Votes

Count: 2

| Roll | Date | Question | Title |
| ---: | --- | --- | --- |
| 422 | 2025-07-22 | On the Motion to Proceed | Motion to Proceed to Executive Session to consider Emil J. Bove III |
| 511 | 2025-09-09 | On the Motion to Proceed | Motion to Proceed to Executive Session to consider S.Res. 377 |

Reason excluded:

- Treaty/executive vote semantics are outside the current fact-only legislative vote path.
- These rows should wait for a separate source/model decision before any production import.

## Fetch/Cache Result

No additional fetch was run because local cache inspection showed all audited roll numbers 1-618 were already present under `backend/data_sources/senate_xml/`.

| Fetch/cache category | Count |
| --- | ---: |
| Audited roll numbers | 618 |
| Cached locally before Phase 15 audit | 618 |
| Newly fetched in Phase 15 | 0 |
| Already cached | 618 |
| Missing/unavailable | 0 |
| Failed fetches | 0 |
| Out-of-scope cached files | 0 |

## Import Decision

No Phase 15 import was run.

Reasons:

- eligible fact-only bill-centered rows remaining: 0;
- no manifest was created;
- no rollback artifact was required;
- running an import would have required handling one of the explicitly excluded/deferred categories.

## Guardrail Confirmation

Phase 15 did not:

- import production data;
- write Supabase data;
- create, update, or delete `vote_interpretations`;
- change support/opposition inputs;
- change alignment inputs;
- modify House rows;
- handle Senate amendments;
- handle PN nominations;
- handle treaty/executive votes;
- add interpretations;
- change UI/API/counting/alignment logic.

## Remaining Backlog

Remaining absent-from-production current-Congress Senate rows are:

- 330 PN nomination rows;
- 113 Senate amendment rows with resolvable parent context;
- 2 treaty/executive rows.

These rows should remain outside the fact-only bill-centered import path until separate storage, product semantics, and rollback/validation gates are defined.

## Next Recommended Action

Recommended next milestone:

- Senate amendment fact-model preflight.

That milestone should decide whether amendment facts can be safely stored without interpretation by preserving:

- Senate amendment number;
- amendment purpose;
- parent bill or parent amendment;
- amendment-to-amendment relationships;
- source XML path/URL;
- vote question/title;
- member vote positions;
- explicit non-counting interpretation boundary.

PN nominations should remain excluded until there is a product and methodology decision about whether nominations belong in this civic behavior surface and how they should be displayed without being conflated with bill votes.
