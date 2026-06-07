# Congress.gov Source Packet Enrichment - Phase 1

Date: 2026-06-05

Branch: `codex/evidence-depth-coverage-expansion-plan`

Scope: bounded backend/source-packet implementation and review packet. No UI change, database write, interpretation promotion, alignment/counting change, curated roll-number summary, source scraping, or PR creation is included.

## What Already Existed

The repo already had substantial Congress.gov support:

- `backend/app/etl/fetch_sources.py`
  - builds official Congress.gov v3 bill URLs
  - fetches bill detail, summaries, subjects, actions, text versions, amendments, and committees
  - supports `congress-bill --include-enrichment`
- `backend/app/etl/congress_adapter.py`
  - normalizes Congress.gov bill records
  - merges companion cache files from `bill_summaries`, `bill_subjects`, `bill_actions`, `bill_texts`, `bill_amendments`, and `bill_committees`
- `backend/app/etl/live_pipeline.py`
  - infers bill refs from House/Senate roll-call cache
  - fetches Congress.gov enrichment for inferred or explicit bill refs
- `backend/app/etl/manual_interpretations.py`
  - exports manual interpretation packets
  - enriches packets with `so_what_context` when cached Congress.gov data is available
- Tests already covered Congress.gov URL construction, cache merging, and manual packet enrichment.

What was missing for this milestone:

- a deterministic source-packet structure focused on review classification rather than interpretation promotion
- preservation of unfetched Congress.gov subresource references, such as "amendments count/url exists, but the companion amendment records are not cached"
- a review-only classification for whether enriched context looks upgradeable or should remain limited

## What Changed

Implemented a new review-only backend helper:

```text
backend/app/etl/source_packets.py
```

It builds deterministic Congress.gov source packets for target rows and classifies enrichment as:

- `likely_upgrade_candidate`
- `still_limited`
- `no_useful_context_found`
- `source_missing_or_unavailable`

It does not:

- write to the database
- change `interpretation_status`
- change support/opposition counts
- change alignment logic
- expose new UI behavior
- call an LLM
- fetch new sources

Also extended `backend/app/etl/congress_adapter.py` to preserve `source_subresources` metadata from Congress.gov bill detail payloads. This means a packet can now say that Congress.gov advertises amendment/action/text/committee subresources even when the companion cache files have not been fetched yet.

## Source Packet Shape

The source packet includes:

- `roll_call_id`
- `rollcall_number`
- chamber/congress
- vote question and description
- vote source URL
- primary domain
- current interpretation status
- issue facet
- vote type
- bill id / congress / type / number
- bill title
- bill summary
- latest action
- legislation URL
- amendment hint parsed from the roll description
- matched amendment record when available
- actions
- text versions
- amendment records
- committees
- committee reports
- CBO cost estimates
- Congress.gov source URLs
- cache metadata
- source availability flags
- review classification
- review notes

## Target Rows Selected

Target: National Security & Foreign Policy / defense authorization amendment rows.

Query boundary:

- `primary_domain = NATIONAL_SECURITY_FOREIGN`
- `issue_facet = Defense authorization amendment`
- `interpretation_status in (insufficient_evidence, ambiguous)`

Rows found: 17 distinct roll calls.

All target rows are House amendment votes on:

```text
119:hr:3838
Streamlining Procurement for Effective Execution and Delivery and National Defense Authorization Act for Fiscal Year 2026
```

Rolls selected:

```text
244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255, 256, 257, 258, 259, 260
```

## Before / After Source Packet Examples

### Before

Roll 244 evidence had:

```json
{
  "roll_call_id": 224,
  "rollcall_number": 244,
  "question": "On Agreeing to the Amendment",
  "description": "Meeks of New York Part A Amendment No. 34",
  "bill": "119:hr:3838",
  "bill_summary": "",
  "interpretation_status": "insufficient_evidence",
  "issue_facet": "Defense authorization amendment",
  "interpretation_reason": "Manual review found insufficient amendment detail for a source-grounded yea/nay interpretation."
}
```

The row identified the amendment vote but did not expose enough bill/amendment source context to evaluate practical effect.

### After

Roll 244 source packet now includes:

```json
{
  "roll_call_id": 224,
  "rollcall_number": 244,
  "vote_description": "Meeks of New York Part A Amendment No. 34",
  "bill": {
    "bill_id": "119:hr:3838",
    "title": "Streamlining Procurement for Effective Execution and Delivery and National Defense Authorization Act for Fiscal Year 2026",
    "summary": "Congress.gov summary available for the FY2026 defense authorization bill.",
    "legislation_url": "https://www.congress.gov/bill/119th-congress/house-bill/3838",
    "latest_action": {
      "action_date": "2025-09-30",
      "text": "Received in the Senate."
    }
  },
  "amendment": {
    "amendment_number": "34",
    "amendment_label": "Part A Amendment No. 34",
    "sponsor_text": "Meeks of New York",
    "purpose": null,
    "description": null,
    "matched_from_roll_description": false
  },
  "source_availability": {
    "bill_cache_hit": true,
    "bill_summary": true,
    "actions": true,
    "text_versions": false,
    "amendment_records": false,
    "amendment_subresource_reference": true,
    "matched_amendment": false,
    "committee_reports": true,
    "cbo_cost_estimates": true,
    "congressgov_source_urls": true
  },
  "review_classification": "still_limited"
}
```

The source packet is richer, but it still does not contain amendment-specific purpose text. That is why the row remains `still_limited`.

## Source Fields Found

For all 17 target rows:

| Source field | Rows available |
|---|---:|
| Congress.gov bill cache hit | 17 |
| Bill summary | 17 |
| Latest action / action context | 17 |
| Amendment subresource reference URL | 17 |
| Committee report reference | 17 |
| CBO cost estimate | 17 |
| Congress.gov source URLs | 17 |
| Fetched amendment records | 0 |
| Matched amendment purpose/description | 0 |
| Fetched text-version records | 0 |
| Fetched committee records | 0 |

## Review Classification Results

| Classification | Rows |
|---|---:|
| `likely_upgrade_candidate` | 0 |
| `still_limited` | 17 |
| `no_useful_context_found` | 0 |
| `source_missing_or_unavailable` | 0 |

This is a useful Phase 1 result: Congress.gov bill-level context exists, and the bill detail points to amendment subresources, but the currently cached data does not include fetched amendment detail. The rows should not be promoted yet.

## Why Congress.gov Helped

Congress.gov helped by confirming:

- the target rows belong to the FY2026 defense authorization bill
- bill-level summary is available
- the bill has amendment records available through a Congress.gov subresource
- the bill has a committee report reference
- the bill has a CBO estimate
- the bill has official source URLs that can support the next enrichment step

This gives the next milestone a specific source path instead of a vague "find better context" task.

## Why Congress.gov Did Not Yet Fully Help

The currently available local cache does not include the fetched amendment companion file for `119_hr_3838`. The bill detail advertises:

```text
https://api.congress.gov/v3/bill/119/hr/3838/amendments?format=json
```

but the packet builder found no amendment records to match against roll descriptions such as:

```text
Meeks of New York Part A Amendment No. 34
Mace of South Carolina Part A Amendment No. 14
Greene of Georgia Part A Amendment No. 24
```

Without amendment-specific purpose or description text, bill-level NDAA context is not enough to explain what a Yea or Nay meant on each amendment.

## Rows That Look Upgradeable

None yet.

Reason: no target row had a matched amendment record with purpose or description text.

The tests include a synthetic positive case proving that when a matching amendment record does include purpose text, the packet is classified as `likely_upgrade_candidate`. The current real target data simply does not have that companion data loaded yet.

## Rows That Remain Limited

All 17 target rows remain limited.

Reason: the source packet can identify the broader bill and available amendment source path, but not the amendment-specific practical policy effect.

## Recommended Next Step For Interpretation Promotion

Next implementation should fetch or load the Congress.gov amendments companion payload for `119:hr:3838`, then regenerate the source packets.

After that:

1. Match amendment records to House roll descriptions by amendment number and sponsor text.
2. If amendment purpose/description exists, mark the row as `likely_upgrade_candidate` for human/deterministic review.
3. Only after review should any `vote_interpretations` rows be updated.
4. Keep rows limited when amendment text is absent or too vague.

Do not promote based only on the bill-level NDAA summary.

## Risks And Limitations

- Congress.gov amendment records may not use the same "Part A Amendment No." labels as House floor descriptions.
- Some amendment purpose fields may still be too terse to support voter-facing practical meaning.
- Committee report and CBO links help understand the bill but do not explain each amendment.
- This pass does not fetch new source files; it only uses and exposes cached source availability.
- This pass does not resolve the separate chamber-filtering/data-integrity audit concern.
- This pass does not make National Security a strong issue read.

## Tests / Verification

Commands run:

```text
cd backend
.\.venv_win\Scripts\python.exe -m pytest tests\test_congress_adapter.py tests\test_source_packets.py tests\test_manual_interpretations.py
```

Initial result:

```text
13 passed, 4 errors
```

The errors were pytest temp-directory permission errors under `C:\Users\Dylan\AppData\Local\Temp\pytest-of-Dylan`, not code assertion failures.

Rerun with in-repo basetemp and sandbox escalation for pytest temp access:

```text
cd backend
.\.venv_win\Scripts\python.exe -m pytest --basetemp=.pytest_tmp_source_packets tests\test_congress_adapter.py tests\test_source_packets.py tests\test_manual_interpretations.py
```

Final result:

```text
17 passed in 0.13s
```

Frontend build was skipped because this milestone did not change frontend files or UI behavior.

## Files Changed

- `backend/app/etl/congress_adapter.py`
- `backend/app/etl/source_packets.py`
- `backend/tests/test_congress_adapter.py`
- `backend/tests/test_source_packets.py`
- `docs/review_packets/congressgov_source_packet_enrichment_phase_1.md`

Existing untracked review artifacts remain outside this milestone unless explicitly added later:

- `docs/review_packets/chamber_filtering_data_integrity_audit.md`
- `docs/review_packets/evidence_depth_coverage_expansion_plan.md`
- `review_bundle_frontend_data_grounding/`

