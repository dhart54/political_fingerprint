# Congress.gov Amendment Companion Enrichment - Phase 1B

Date: 2026-06-05

Branch: `codex/evidence-depth-coverage-expansion-plan`

Scope: bounded Congress.gov amendment companion enrichment for `119:hr:3838` defense authorization amendment rows. No UI changes, no API shape changes, no interpretation promotion, no support/opposition counting changes, and no alignment changes.

## What Already Existed

- `backend/app/etl/fetch_sources.py` already supported Congress.gov bill enrichment, including:
  - `fetch_congress_bill_amendments`
  - `build_congress_bill_amendments_url`
  - the `congress-bill --include-enrichment` path
- `backend/app/etl/congress_adapter.py` already merged companion payloads from:
  - `bill_summaries`
  - `bill_subjects`
  - `bill_actions`
  - `bill_texts`
  - `bill_amendments`
  - `bill_committees`
- Phase 1 added `backend/app/etl/source_packets.py`, which builds deterministic review packets and classifies them as review-only source-readiness results.

## Pre-Change Amendment Cache State

Before Phase 1B, local cache contained:

- `backend/data_sources/congress/bills/119_hr_3838.json`
- `backend/data_sources/congress/bill_summaries/119_hr_3838.json`
- `backend/data_sources/congress/bill_subjects/119_hr_3838.json`

It did not contain:

- `backend/data_sources/congress/bill_amendments/119_hr_3838.json`

The bill-detail cache did advertise an amendments subresource:

```text
https://api.congress.gov/v3/bill/119/hr/3838/amendments?format=json
```

## Amendment Records Loaded

Fetched with existing Congress.gov support:

```text
cd backend
.\.venv_win\Scripts\python.exe -c "... fetch_congress_bill_amendments(congress=119, bill_type='hr', bill_number=3838, ...)"
```

Result:

```text
status=downloaded
destination=C:\Users\Dylan\Documents\Data Science\political_fingerprint\backend\data_sources\congress\bill_amendments\119_hr_3838.json
bytes_written=23591
```

Loaded amendment companion payload:

- Total amendment records: 26
- `HAMDT` records: 25
- `SAMDT` records: 1

Congress.gov amendment fields available in this payload include:

- `congress`
- `description`
- `latestAction`
- `number`
- `purpose` on many records
- `type`
- `updateDate`
- `url`

## Implementation Changes

### Adapter

`backend/app/etl/congress_adapter.py`

- Preserves bill-detail source-subresource metadata before companion payloads overwrite fields such as `bill["amendments"]`.
- Keeps deterministic companion merge behavior unchanged.
- This lets source packets show both fetched amendment records and the original Congress.gov amendments subresource URL.

### Source Packets

`backend/app/etl/source_packets.py`

- Adds amendment-specific packet fields:
  - `latest_action`
  - `type`
  - `match_confidence`
  - `match_reason`
- Improves printed House amendment matching:
  - Roll text: `Meeks of New York Part A Amendment No. 34`
  - Congress.gov text: `An amendment numbered 34 printed in Part A of House Report 119-255...`
- Treats a unique printed-number match as high confidence.
- Keeps uncertain matches limited.
- Adds individual Congress.gov amendment URLs to `source_context.congressgov_source_urls`.

## Match Logic

Matching uses existing row/source fields only:

1. Parse the roll-call description for a printed House amendment number and sponsor text.
2. Normalize Congress.gov amendment descriptions that say `amendment numbered X`.
3. Match by unique printed House amendment number first.
4. Fall back to Congress.gov amendment record number only when necessary.
5. Fall back to sponsor text only when no number is available.
6. If no confident match exists, keep the row limited.

No row is promoted to `interpreted` by this logic.

## Target Rows

Target: 17 National Security & Foreign Policy / Defense authorization amendment rows tied to H.R. 3838.

All 17 were previously `insufficient_evidence` because packets identified the amendment sponsor/number but lacked amendment-specific practical context.

| Roll | Printed amendment | Matched Congress.gov amendment | Match confidence | Review classification | Amendment-specific source text |
| --- | --- | --- | --- | --- | --- |
| 244 | Part A Amendment No. 34 | `119:hamdt:99` | high | `likely_upgrade_candidate` | Amendment repeals the 2002 and 1991 Authorization for Use of Military Force (AUMFs). |
| 245 | Part A Amendment No. 13 | `119:hamdt:85` | high | `likely_upgrade_candidate` | Amendment prohibits the provision of gender transition procedures, including surgery or medication, through the Exceptional Family Medical Program. |
| 246 | Part A Amendment No. 14 | `119:hamdt:86` | high | `likely_upgrade_candidate` | Amendment prohibits the Department of Defense from covering or furnishing gender-related medical treatment under TRICARE. |
| 247 | Part A Amendment No. 15 | `119:hamdt:87` | high | `likely_upgrade_candidate` | Amendment prohibits the Superintendent of a Service Academy from allowing a cadet or midshipman who is male from participating in an athletic program or activity that is designated exclusively for females. |
| 248 | Part A Amendment No. 16 | `119:hamdt:88` | high | `likely_upgrade_candidate` | Amendment prohibits the Secretary of Defense from soliciting information through a form or survey regarding gender identity and related sex/gender response fields. |
| 249 | Part A Amendment No. 17 | `119:hamdt:89` | high | `likely_upgrade_candidate` | Amendment prohibits individuals from accessing or using single-sex spaces on military installations which do not correspond to the biological sex of the individual. |
| 250 | Part A Amendment No. 7 | `119:hamdt:78` | high | `likely_upgrade_candidate` | Amendment sought to require the Secretary of Defense to certify that offshore wind projects in the North Atlantic and Mid-Atlantic Planning Areas will not interfere with radar capabilities. |
| 251 | Part A Amendment No. 9 | `119:hamdt:79` | high | `likely_upgrade_candidate` | Amendment eliminates the preference for motor vehicles using electric or hybrid propulsion systems and related Department of Defense requirements. |
| 252 | Part A Amendment No. 11 | `119:hamdt:81` | high | `likely_upgrade_candidate` | Amendment increases penalties for entering a military installation or violating national defense area security regulations. |
| 253 | Part A Amendment No. 18 | `119:hamdt:90` | high | `likely_upgrade_candidate` | Amendment restricts base commanders' ability to fly unauthorized flags at their discretion. |
| 254 | Part A Amendment No. 20 | `119:hamdt:91` | high | `likely_upgrade_candidate` | Amendment would ban DOD research, development, procurement, and promotion of cell-cultured meat. |
| 255 | Part A Amendment No. 22 | `119:hamdt:93` | high | `likely_upgrade_candidate` | Amendment would prohibit assistance to Ukraine. |
| 256 | Part A Amendment No. 23 | `119:hamdt:94` | high | `likely_upgrade_candidate` | Amendment sought to strike funding for the Overseas Humanitarian, Disaster, and Civic Aid program. |
| 257 | Part A Amendment No. 24 | `119:hamdt:95` | high | `likely_upgrade_candidate` | Amendment sought to strike foreign aid funding for the Taiwan Security Cooperation Initiative. |
| 258 | Part A Amendment No. 25 | `119:hamdt:96` | high | `likely_upgrade_candidate` | Amendment modifies FY2024 NDAA section 1555 to prohibit DOD recruitment contracts with certain fact-checking and information-grading entities. |
| 259 | Part A Amendment No. 29 | `119:hamdt:97` | high | `likely_upgrade_candidate` | Amendment sought to limit critical-habitat designations on military and certain National Guard lands and exempt military personnel from ESA prohibitions during national-defense operations. |
| 260 | Part A Amendment No. 253 | `119:hamdt:100` | high | `likely_upgrade_candidate` | Amendment requires a Department of Defense report to congressional armed-services committees on the Janet Yamanaka Mello fraud scheme involving 4-H Military Partnership Grant program funds. |

## Classification Results

Before Phase 1B:

| Classification | Count |
| --- | ---: |
| `likely_upgrade_candidate` | 0 |
| `still_limited` | 17 |
| `no_useful_context_found` | 0 |
| `source_missing_or_unavailable` | 0 |

After Phase 1B:

| Classification | Count |
| --- | ---: |
| `likely_upgrade_candidate` | 17 |
| `still_limited` | 0 |
| `no_useful_context_found` | 0 |
| `source_missing_or_unavailable` | 0 |

Important: this is review classification only. The underlying `interpretation_status` remains unchanged.

## Before / After Example

Roll 244 before:

```json
{
  "roll_call_id": 224,
  "rollcall_number": 244,
  "vote_description": "Meeks of New York Part A Amendment No. 34",
  "interpretation_status": "insufficient_evidence",
  "review_classification": "still_limited",
  "reason": "The packet identified the amendment but did not include amendment-specific purpose or description text."
}
```

Roll 244 after:

```json
{
  "roll_call_id": 224,
  "rollcall_number": 244,
  "vote_description": "Meeks of New York Part A Amendment No. 34",
  "amendment": {
    "amendment_id": "119:hamdt:99",
    "amendment_number": "34",
    "amendment_label": "Part A Amendment No. 34",
    "sponsor_text": "Meeks of New York",
    "purpose": "Amendment repeals the 2002 and 1991 Authorization for Use of Military Force (AUMFs).",
    "description": "An amendment numbered 34 printed in Part A of House Report 119-255 to insert the text of H.R. 1488, repealing the 2002 and 1991, Authorization for Use of Military Force (AUMFs).",
    "latest_action": {
      "action_date": "2025-09-10",
      "action_time": "16:35:30",
      "text": "On agreeing to the Meeks amendment (A023) Agreed to by recorded vote: 261 - 167 (Roll no. 244)."
    },
    "type": "HAMDT",
    "source_url": "https://api.congress.gov/v3/amendment/119/hamdt/99?format=json",
    "match_confidence": "high",
    "match_reason": "Matched the printed House amendment number from the roll-call description to the Congress.gov amendment description.",
    "matched_from_roll_description": true
  },
  "review_classification": "likely_upgrade_candidate",
  "review_notes": [
    "A Congress.gov amendment record appears to match the roll-call amendment hint and includes purpose or description text.",
    "This is a review candidate only; interpretation_status is not changed by this source packet."
  ]
}
```

## Source Availability After Phase 1B

Across the 17 target rows:

| Source availability field | Rows with field |
| --- | ---: |
| bill cache hit | 17 |
| bill summary | 17 |
| actions | 17 |
| amendment records | 17 |
| amendment subresource reference | 17 |
| matched amendment | 17 |
| matched amendment purpose or description | 17 |
| committee reports | 17 |
| CBO cost estimates | 17 |
| Congress.gov source URLs | 17 |
| text versions | 0 |
| committees | 0 |

## Does This Materially Improve Voter-Understandable Meaning?

Yes, for review potential.

The source packets now contain amendment-specific purpose/description text for all 17 target rows. That is the missing source layer needed to review what each amendment was about. This still does not automatically establish support/opposition meaning, because yea/nay meaning must be reviewed against the roll-call action and source context before promotion.

## Rows Remaining Limited

None of the 17 target rows remain `still_limited` at the source-packet review classification layer.

However, all 17 remain limited in the actual product interpretation data until a separate review/promotion step explicitly updates deterministic interpretation records.

## Recommended Next Step

Create a separate review/promotion pass for these 17 rows:

1. For each row, use the matched amendment purpose/description, latest action, House roll-call question, and House result.
2. Draft deterministic plain-language interpretation fields.
3. Keep any amendment limited if the purpose is too broad, ambiguous, or procedural.
4. Run tests proving no support/opposition counting or alignment logic changes except through explicit reviewed interpretation records.
5. Do not promote rows automatically from the enrichment classifier alone.

## Risks and Limitations

- Congress.gov amendment records use HAMDT numbers that differ from printed House amendment numbers; this pass matches by printed-number text inside the amendment description.
- Some amendment descriptions use "sought to" because the amendment failed; promotion should preserve the actual vote outcome and not turn failed amendments into enacted policy.
- Some purposes are politically sensitive; public copy must stay neutral and source-bound.
- Text-version and committee companion payloads for H.R. 3838 remain unloaded in this bounded pass.
- The one `SAMDT` record in the companion payload is not part of the 17 House roll-call target rows.

## Tests

Command:

```text
cd backend
.\.venv_win\Scripts\python.exe -m pytest --basetemp=.pytest_tmp_phase1b tests\test_congress_adapter.py tests\test_source_packets.py tests\test_manual_interpretations.py
```

Result:

```text
collected 20 items
tests\test_congress_adapter.py .......
tests\test_source_packets.py .......
tests\test_manual_interpretations.py ......
20 passed in 0.14s
```

Frontend build skipped because no frontend or UI files changed.

## Cleanup Note

`backend/.pytest_tmp_source_packets` still exists from the prior run and produces a Windows permission warning during `git status`. Phase 1B also used `backend/.pytest_tmp_phase1b` for pytest. No destructive cleanup was performed.

## Files Changed

- `backend/app/etl/congress_adapter.py`
- `backend/app/etl/source_packets.py`
- `backend/data_sources/congress/bill_amendments/119_hr_3838.json`
- `backend/tests/test_congress_adapter.py`
- `backend/tests/test_source_packets.py`
- `docs/review_packets/congressgov_amendment_companion_enrichment_phase_1b.md`

