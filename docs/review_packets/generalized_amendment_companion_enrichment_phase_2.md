# Generalized Amendment Companion Enrichment - Phase 2

Date: 2026-06-07

Scope: generalize the NDAA amendment enrichment pattern into a repeatable offline workflow. This phase finds amendment-heavy weak sections, builds source packets from already exported review packets and cached Congress.gov companion data, and produces review-only candidate interpretations.

No production data import, Supabase write, API behavior change, frontend change, counting change, or alignment change is included.

## Workflow Boundary

This phase stops before production import.

Allowed:

- read exported manual interpretation packet JSON
- read existing local Congress.gov cache
- identify weak amendment-heavy sections
- build deterministic source packets
- draft candidate interpretation JSON for human review
- write local review artifacts to caller-specified paths

Not allowed without explicit approval:

- broad autonomous data collection
- source enrichment ingestion
- production Supabase writes
- `manual_interpretations import`
- support/opposition counting changes
- API or frontend behavior changes

## New Helper

`backend/app/etl/amendment_companion_enrichment.py`

Commands:

```powershell
cd backend
.\.venv_win\Scripts\python.exe -m app.etl.amendment_companion_enrichment discover --packets ..\docs\interpretation_batches\<batch>_packets.json --output ..\docs\review_packets\<batch>_amendment_sections.json
```

```powershell
cd backend
.\.venv_win\Scripts\python.exe -m app.etl.amendment_companion_enrichment build-review-batch --packets ..\docs\interpretation_batches\<batch>_packets.json --output ..\docs\interpretation_batches\<batch>_amendment_review_candidates.json
```

## Discovery Rule

The discovery step groups rows by:

- primary domain
- bill congress
- bill type
- bill number

A row is included only when:

- the current interpretation status is missing, `ambiguous`, or `insufficient_evidence`
- and the roll-call question, vote context, or House amendment hint indicates an amendment vote

By default, a section must have at least three weak amendment rows to appear in the discovery output.

The output is a prioritization aid only. It does not imply that the rows are import-ready or that a public issue pattern exists.

## Review Batch Rule

The review batch step:

1. Converts weak amendment packets into `SourcePacketTarget` rows.
2. Builds Congress.gov source packets with existing deterministic source-packet logic.
3. Drafts candidate interpretations only when all of these are true:
   - the roll-call action clearly says the vote was on agreeing to an amendment
   - the selected member has a Yea or Nay vote in the packet
   - the matched Congress.gov amendment has purpose or description text
4. Marks the candidate `insufficient_evidence` when any of those requirements are missing.

Candidate interpretations use `interpretation_status_recommendation = review_candidate_only`. They are not production records and must not be imported until separately reviewed and explicitly approved.

## Guardrails

Candidate copy must:

- say the vote was on whether to agree to an amendment
- say it was not final passage of the bill
- tie Yea/Nay meaning only to agreeing to the amendment
- avoid motive, ideology, character, corruption, ranking, or voting-recommendation claims
- cite official roll-call context and matched Congress.gov amendment purpose/description

## Tests

Targeted test file:

```powershell
cd backend
.\.venv_win\Scripts\python.exe -m pytest tests\test_amendment_companion_enrichment.py tests\test_source_packets.py tests\test_ndaa_amendment_interpretations.py
```

## Files Added

- `backend/app/etl/amendment_companion_enrichment.py`
- `backend/tests/test_amendment_companion_enrichment.py`
- `docs/review_packets/generalized_amendment_companion_enrichment_phase_2.md`

