# Senate Amendment Fact Model Design And Preflight - Phase 16

Date: 2026-06-12

Scope: design and dry-run preflight for 119th Congress / 2025 Senate amendment vote facts.

No production data was written. No import was run. No `vote_interpretations` rows were created, updated, or deleted. No support/opposition positions were inferred. No UI, API shape, support/opposition counting, or alignment logic changed.

## Current Backlog Summary

Phase 15 showed simple current-Congress Senate bill-centered fact-only coverage is exhausted.

Current 119th Congress / 2025 Senate backlog:

| Category | Count |
| --- | ---: |
| Already loaded in production | 173 |
| PN nominations | 330 |
| Senate amendments with resolvable parent context | 113 |
| Treaty/executive votes | 2 |
| Eligible bill-centered fact-only rows remaining | 0 |

Phase 16 uses the 113 Senate amendment rows as the candidate universe and excludes PN nominations and treaty/executive votes.

## Current Schema And Model Findings

Current relevant production tables:

- `bills`
- `roll_calls`
- `votes_cast`
- `vote_contexts`
- `vote_interpretations`

Current `roll_calls` can store:

- chamber;
- congress;
- session;
- rollcall number;
- vote date;
- question;
- description/title;
- parent `bill_id`;
- source URL.

Current `votes_cast` can store member vote positions.

Current `vote_contexts` can store deterministic member-level vote context:

- vote type;
- member position;
- final result;
- vote margin;
- party totals;
- party-majority and winning-side context;
- context source list.

Current schema cannot safely preserve Senate amendment identity as first-class data. If an amendment vote is represented only through `roll_calls.bill_id` pointing to the parent bill, the product can lose:

- Senate amendment number;
- amendment-to-amendment relationship;
- amendment purpose;
- distinction between a vote on an amendment and a vote on the parent bill;
- whether a row is amendment fact-only and not a substantive parent-bill interpretation.

`vote_contexts.context_source_list` is JSON and could technically carry extra source objects, but it is member-level context rather than roll-level amendment identity. Using it as the sole amendment metadata store would duplicate amendment metadata across every senator's context row and make roll-level audit awkward. It would also leave the public API/UI vulnerable to treating the parent `bill_id` as the primary meaning of the row.

Conclusion:

- Schema migration is required before importing Senate amendment facts safely.
- Adding fields only to `vote_contexts` is not enough.
- Current `vote_contexts` cannot hold amendment metadata without ambiguity and duplication.
- Amendment identity would be lost if represented only through parent bill.
- UI/API handling is required before public display so amendment rows are not mistaken for parent-bill final passage or ordinary parent-bill evidence.

## Senate Amendment XML Findings

The 113 Senate amendment XML rows provide these fields:

- `document/document_type`, usually `S.Amdt.`;
- `amendment/amendment_number`;
- `amendment/amendment_to_amendment_number`, when applicable;
- `amendment/amendment_to_document_number`;
- `amendment/amendment_purpose`;
- `question`;
- `vote_title`;
- `vote_number`;
- `vote_date`;
- `members/member` vote rows;
- official Senate source URL derivable from congress, session, and roll number.

Candidate classification:

| Classification | Count | Treatment |
| --- | ---: | --- |
| Safe amendment fact candidate after schema/model work | 112 | Local dry-run manifest only |
| Amendment candidate needing source packet enrichment | 1 | Deferred |
| Insufficient parent context | 0 | None found |
| Unsupported/malformed | 0 | None found |

Parent bill distribution for the 112 safe future candidates:

| Parent bill type | Count |
| --- | ---: |
| `hr` | 51 |
| `sconres` | 25 |
| `hconres` | 21 |
| `s` | 15 |

The 112 safe future candidates contain 11,197 member vote rows. The roll range is 3-616. One deferred row, roll 344, has parent context but lacks a usable amendment purpose because the XML reports no statement of purpose on file.

## Model Options Considered

### Option A: Existing schema only

Represent amendment rows with `roll_calls.bill_id` pointing to the parent bill and preserve amendment context only in question/description/source URL.

Assessment:

- Correctness: weak; amendment identity is not first-class.
- Risk of misleading users: high; row can look like parent-bill evidence.
- Ease of implementation: easiest.
- Reversibility: moderate.
- Source packets: loses useful structured amendment fields.
- Future interpretations: harder because amendment identity must be recovered from text.
- UI/API impact: likely misleading without additional labels.
- Production migration required: no.

Recommendation: reject.

### Option B: Add amendment columns to `vote_contexts`

Add amendment number, parent bill, purpose, and amendment-to-amendment metadata to `vote_contexts`.

Assessment:

- Correctness: partial; stores the fields but at member-row granularity.
- Risk of misleading users: medium; still easy to confuse roll-level identity with member context.
- Ease of implementation: moderate.
- Reversibility: moderate.
- Source packets: better than option A, but duplicates metadata across roughly 100 rows per roll.
- Future interpretations: usable but awkward.
- UI/API impact: requires API/UI work to surface row-level labels.
- Production migration required: yes.

Recommendation: not preferred.

### Option C: Add amendment reference table

Add a dedicated amendment reference table keyed by `roll_call_id`, preserving:

- amendment number;
- amendment type;
- amendment-to-amendment number;
- parent bill type;
- parent bill number;
- parent bill display;
- amendment purpose;
- source URL/path or source reference;
- fact-only status/version.

Assessment:

- Correctness: strongest.
- Risk of misleading users: lowest when paired with UI/API labels.
- Ease of implementation: moderate.
- Reversibility: good; rollback can delete amendment reference rows with target roll calls.
- Source packets: strong; source packet construction can read structured amendment identity.
- Future interpretations: strong; interpretation review can cite exact amendment metadata.
- UI/API impact: required before public display/import.
- Production migration required: yes.

Recommendation: preferred.

### Option D: Defer database changes and keep amendment rows out of production

Do not import Senate amendment facts until amendment identity storage and display semantics are approved.

Assessment:

- Correctness: safe.
- Risk of misleading users: lowest short-term.
- Ease of implementation: easiest now.
- Reversibility: not applicable.
- Source packets: no production benefit yet.
- Future interpretations: delayed.
- UI/API impact: none now.
- Production migration required: no now.

Recommendation: current stop state until Option C is implemented.

## Recommended Amendment Fact Model

Use Option C: a dedicated amendment reference table keyed to `roll_calls`.

Recommended future table shape, conceptually:

- `roll_call_id`
- `amendment_number`
- `amendment_type`
- `amendment_to_amendment_number`
- `parent_bill_type`
- `parent_bill_number`
- `parent_bill_display`
- `amendment_purpose`
- `source_url`
- `source_xml_path`
- `fact_status`, such as `fact_only_uninterpreted`
- `source_version`

Future import could then write:

- parent bill row in `bills`, if missing;
- roll-call metadata in `roll_calls`;
- member votes in `votes_cast`;
- deterministic context in `vote_contexts`;
- amendment identity in the new amendment reference table.

Future import must not write `vote_interpretations` unless separately reviewed and approved.

## Required Changes Before Import

Schema migration required:

- yes.

UI/API changes required:

- yes, before public display/import is considered safe.

Reason:

- API evidence rows must identify amendment fact-only rows clearly and distinguish them from parent-bill final passage or generic parent-bill evidence.
- UI labels must say amendment fact/context, not substantive parent-bill support/opposition.
- Support/opposition and alignment logic must continue to ignore these rows unless a later source-grounded `vote_interpretation` is separately approved.

## Dry-Run Manifest

Local manifest:

- `docs/review_packets/senate_amendment_fact_model_manifest_phase_16.json`

Dry-run validation result:

| Check | Result |
| --- | ---: |
| Candidate rows | 112 |
| Deferred rows | 1 |
| Planned `vote_interpretations` inserts | 0 |
| Planned `vote_interpretations` updates | 0 |
| Planned `vote_interpretations` deletes | 0 |
| Validation errors | 0 |
| Safe to request import approval | false |

The manifest is local/preflight only. It is not an import manifest and does not approve production writes.

Validation confirmed:

- all candidate rows are Congress 119;
- all candidate rows are calendar year 2025;
- all candidate rows are Senate rows;
- all candidate rows have resolvable amendment identifiers;
- all candidate rows have resolvable parent bill context;
- all candidate rows have member vote rows;
- no `vote_interpretations` are planned;
- no support/oppose positions are inferred;
- no alignment impact is possible;
- no PN nominations are included;
- no treaty/executive votes are included;
- amendment identity is not collapsed into generic parent-bill evidence in the manifest.

## Expected Production Impact If Later Imported

Only after a schema/model milestone and explicit approval, a future fact-only import would likely affect:

- `bills`;
- `roll_calls`;
- `votes_cast`;
- `vote_contexts`;
- a new amendment reference table.

Expected support/opposition/alignment impact:

- none for fact-only amendment rows;
- no `vote_interpretations` writes;
- no `support_position` or `oppose_position` values;
- no alignment changes.

## Excluded Or Deferred Rows

Deferred:

- roll 344: parent context exists, but no statement of purpose is available in the Senate XML.

Excluded by milestone scope:

- 330 PN nominations;
- 2 treaty/executive votes.

## Risks

- Importing amendment facts without first-class amendment identity would mislead users by making amendment votes look like parent-bill votes.
- Storing amendment metadata only in `vote_contexts` would duplicate roll-level amendment facts across member rows and complicate source-packet generation.
- UI/API must distinguish amendment fact rows from interpreted substantive evidence before these rows are displayed publicly.
- Amendment votes should remain fact-only until separately reviewed source packets support any practical meaning.

## Next Milestone Recommendation

Recommended next milestone:

- Senate amendment reference schema and API preflight.

That milestone should:

- design the amendment reference migration;
- decide API evidence shape for fact-only amendment rows;
- preserve non-counting/non-alignment behavior;
- create rollback and validation plans;
- stop before production import approval.
