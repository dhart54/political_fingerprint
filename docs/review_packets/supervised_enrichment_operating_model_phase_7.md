# Supervised Enrichment Operating Model - Phase 7

Date: 2026-06-07

Scope: define the repeatable workflow for safe, production-backed enrichment batches.

This milestone did not import data, write Supabase, modify production records, change UI, change API shape, change support/opposition counting, or change alignment logic.

## Why Phase 7 Exists

The product now has two proven enrichment paths:

- NDAA amendment enrichment showed that source-grounded amendment records can turn weak rows into substantive interpreted votes when the roll-call action, member vote, and matched amendment purpose are all clear.
- Procedural-context enrichment showed that repeated House floor-rule rows can become useful explanatory context without becoming support/opposition or alignment evidence.

Phase 7 turns those lessons into an operating model so future batches can be selected, reviewed, validated, approved, imported, and preserved without weakening the product's evidence boundary.

## Lessons From NDAA Substantive Import

Substantive enrichment is appropriate when:

- the vote is directly tied to a source-grounded action, such as agreeing to a matched amendment;
- the member's Yea/Nay position is available;
- official source context explains the practical effect of the vote;
- `support_position` and `oppose_position` can be assigned without using broad bill context alone;
- the candidate explains what not to infer, including motive, ideology, character, or a voting recommendation.

The NDAA pattern is valuable because it can improve support/opposition evidence and issue readiness. It is also higher risk because imported interpreted records can affect counts and alignment. It therefore requires a stricter preflight: exact rows, source basis, count impact, alignment impact, rollback artifact, and explicit substantive import approval.

## Lessons From Procedural-Context Import

Procedural-context enrichment is appropriate when:

- the vote explains floor process, rule adoption, previous-question steps, concurrence posture, amendment availability, or similar procedural context;
- the row is useful to understand what the user is seeing;
- the row does not establish a direct substantive policy position on the underlying bill or package.

The Phase 6 production import updated six existing House rules rows while keeping:

- `interpretation_status = insufficient_evidence`;
- `support_position = null`;
- `oppose_position = null`;
- support/opposition counts unchanged;
- alignment unchanged.

The procedural-context pattern is valuable because it reduces scroll/value mismatch across repeated weak rows. It must stay non-counting.

## Supervised Enrichment Workflow

Standard loop:

1. Production read-only discovery
2. Source-packet construction
3. Candidate classification
4. Review-only candidate packet
5. Import preflight
6. Rollback artifact
7. Explicit approval gate
8. Bounded production import
9. Post-import validation
10. PR artifact preservation

Only step 8 writes production data. It must not run without the exact explicit approval phrase for the relevant batch type.

## Candidate Type Definitions

### A. Substantive Interpretation Candidate

A substantive candidate is source-grounded and may become countable after approval/import.

Requirements:

- `interpretation_status = interpreted`
- source basis includes official roll-call context and practical-effect source context
- `support_position` and `oppose_position` are non-null and different
- not procedural/floor-rule-only
- includes plain-English summary, what happened, why it mattered, member vote context, and what not to infer

Can count later only after human review and explicit production import approval.

### B. Procedural-Context Candidate

A procedural-context candidate explains floor process or procedural posture.

Requirements:

- `interpretation_status` remains non-interpreted, preferably `insufficient_evidence`
- `support_position = null`
- `oppose_position = null`
- explicit procedural source signal, not `issue_facet` alone
- explains what the vote was procedurally and what not to infer

It remains visible context only. It must not count toward support/opposition, alignment, confident issue-position summaries, or readiness promotion.

### C. Still Insufficient

A still-insufficient row lacks enough source-grounded context for either substantive interpretation or procedural-context explanation.

Common reasons:

- missing source packet;
- bill-level context does not explain the specific amendment or vote;
- rule package is too broad to connect to a practical effect;
- member vote is not Yea/Nay;
- source text does not support a clear summary;
- `issue_facet` alone is the only clue.

These rows remain limited/ambiguous/insufficient and should not be imported as enriched records.

## Production-Read Versus Production-Write Rules

Allowed without production-write approval:

- read production evidence data;
- rank weak sections;
- inspect current interpretation status and source coverage;
- build local source packets from supported tools and cache;
- draft review-only candidates;
- validate candidate types;
- create preflight and rollback artifacts.

Not allowed without explicit approval:

- import any interpretation batch;
- update `vote_interpretations`;
- change support/opposition positions;
- modify Supabase data;
- broaden source ingestion beyond supported tools;
- run a production write hidden inside discovery or validation.

## Batch Selection Rules

Rank future opportunities by:

- total weak rows;
- number of affected officials and issue sections;
- source availability;
- likely voter value;
- ability to reduce scroll/value mismatch;
- trust risk;
- whether the batch is substantive, procedural-context, or mixed;
- whether schema changes would be required.

Guardrails:

- avoid one-row cleanup as a milestone unless it is high-value or unblocks a repeated pattern;
- avoid broad imports without batch review;
- avoid counting procedural rows;
- avoid using `issue_facet` alone as source meaning;
- avoid promoting readiness based only on procedural context;
- stop and report if schema changes would be required.

## Review Packet Templates

### A. Opportunity Map

Include:

- scan date and production-read-only scope;
- source tables read;
- ranking method;
- top opportunities table;
- candidate type;
- source availability;
- expected value;
- risk level;
- selected target and rejected alternatives.

### B. Candidate Batch

Include one row per candidate:

- `roll_call_id`;
- roll number;
- official/domain/facet;
- vote type;
- candidate type;
- current status;
- recommended status;
- support/oppose positions, if any;
- source basis;
- proposed summary;
- why it mattered;
- what not to infer;
- confidence;
- whether it would count if approved/imported.

### C. Production Import Preflight

Include:

- exact batch file;
- exact target `roll_call_id` list;
- current production status for every target row;
- insert/update behavior;
- before counts/readiness;
- expected after behavior;
- support/opposition impact;
- alignment impact;
- tests run;
- rollback artifact path;
- required approval phrase.

### D. Rollback Artifact

Include:

- transaction boundary;
- exact target rows only;
- previous values for all updated fields;
- insert rollback behavior, if inserts are expected;
- comment stating it must not run unless validation fails or rollback is explicitly requested.

### E. Post-Import Validation

Include:

- import command;
- `imported_count` and errors;
- rows changed;
- status/support/oppose after import;
- support/opposition counts after import;
- alignment spot checks after import;
- tests and validation run;
- whether rollback was needed.

## Approval Gates

Substantive import approval phrase:

`Approve production import of [batch_id] substantive interpretation rows, with reviewed support_position and oppose_position values and confirmed support/opposition and alignment impact.`

Procedural-context import approval phrase:

`Approve production import of [batch_id] procedural-context rows, with support_position and oppose_position null and no support/opposition or alignment counting changes.`

Before any production write, confirm:

- exact rows;
- current production state;
- insert/update behavior;
- rollback artifact exists;
- support/opposition impact;
- alignment impact;
- target batch file;
- tests/validation are current;
- no import runs before explicit approval.

## Offline Tooling Added

Phase 7 adds `backend/app/etl/supervised_enrichment.py`, an offline/review-only helper that:

- classifies candidates as substantive interpretation, procedural context, or still insufficient;
- validates supervised batch artifacts;
- rejects procedural-context candidates with non-null support/oppose positions;
- rejects substantive candidates that carry procedural-only source signals;
- warns when `issue_facet` alone is being treated as source meaning;
- emits approval-gate checklist text.

CLI examples:

```powershell
cd backend
.\.venv_win\Scripts\python.exe -m app.etl.supervised_enrichment validate-batch --input ..\docs\interpretation_batches\batch_004_procedural_context_house_rules_justice.json
.\.venv_win\Scripts\python.exe -m app.etl.supervised_enrichment approval-checklist --input ..\docs\interpretation_batches\batch_004_procedural_context_house_rules_justice.json
```

These commands read local JSON only and do not write production data.

## Recommended Next Batch Strategy

Next supervised batch should start with a read-only opportunity map and prefer one of:

- a multi-row substantive amendment batch where Congress.gov amendment purpose/description is available for each row;
- a compact procedural-context batch that repeats across many officials and already has source coverage;
- a mixed batch only if each row is clearly classified and the import artifact separates countable and non-counting records.

Avoid a one-row cleanup unless it unlocks a repeated pattern or fixes a high-visibility weak card.

## What Should Not Be Automated Yet

Do not automate:

- production imports;
- approval decisions;
- support/opposition assignment for ambiguous rows;
- procedural-to-substantive promotion;
- readiness promotion based only on procedural context;
- broad source scraping;
- LLM interpretation import;
- rollback execution without explicit direction.

The supervised loop should remain human-gated until repeated batches prove that discovery, source packets, candidate classification, import preflight, rollback, and post-import validation are reliable.
