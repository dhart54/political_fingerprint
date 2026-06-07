# NDAA Amendment Interpretation Promotion - Phase 1C

Date: 2026-06-05

Branch: `codex/evidence-depth-coverage-expansion-plan`

Scope: only the 17 House amendment roll calls on `119:hr:3838`, rolls 244-260, matched to Congress.gov amendment records in Phase 1B. No UI changes, no API shape changes, no automated LLM interpretation, no global support/opposition counting changes, no alignment logic changes, and no broad National Security rollout.

## Current Interpretation Path

Manual and deterministic vote interpretations are stored in the `vote_interpretations` table.

The source-controlled manual review pattern is:

- draft/export packets under `docs/interpretation_batches/`
- store reviewed JSON records in `docs/interpretation_batches/*_interpretations.json`
- validate and import them through `backend/app/etl/manual_interpretations.py`

These 17 rows already had manual interpretation records in:

- `docs/interpretation_batches/batch_002_valerie_national_security_interpretations.json`
- `docs/interpretation_batches/batch_003_valerie_national_security_remaining_interpretations.json`

Before this pass, all 17 were `insufficient_evidence` with null support/opposition fields because amendment-specific purpose text was missing.

No schema changes were needed.

## What Changed

Added a review-candidate helper:

- `backend/app/etl/ndaa_amendment_interpretations.py`

The helper builds manual interpretation candidates from:

- Phase 1B matched Congress.gov amendment source packets
- House Clerk roll-call XML for rolls 244-260
- Foushee's recorded House vote from the House Clerk XML

The helper promotes a row only when all of the following are clear:

1. the amendment purpose or description
2. the roll-call action
3. yea/nay meaning
4. Foushee's recorded vote
5. what not to infer

## Promotion Rule Used

For each target roll, House Clerk showed:

```text
vote-question: On Agreeing to the Amendment
```

For this vote type:

- `Yea` supports agreeing to/adopting the amendment.
- `Nay` opposes agreeing to/adopting the amendment.

This pass does not treat amendment votes as final passage of H.R. 3838.

## Promoted vs Kept Limited

| Result | Count |
| --- | ---: |
| Promoted to `interpreted` in manual interpretation batch files | 17 |
| Kept limited | 0 |
| Ambiguous | 0 |
| Insufficient evidence | 0 |

All 17 had:

- clear House Clerk action text
- clear Congress.gov amendment purpose/description
- clear Foushee recorded vote
- clear yea/nay meaning for an amendment-adoption vote

## All 17 Rows

| Roll | Foushee vote | Result | Matched amendment | Source-grounded amendment meaning | Status |
| --- | --- | --- | --- | --- | --- |
| 244 | Yea | Agreed to | `119:hamdt:99` | Would repeal the 2002 and 1991 Authorization for Use of Military Force (AUMFs). | promoted |
| 245 | Nay | Agreed to | `119:hamdt:85` | Would prohibit gender transition procedures, including surgery or medication, through the Exceptional Family Medical Program. | promoted |
| 246 | Nay | Agreed to | `119:hamdt:86` | Would prohibit DOD from covering or furnishing gender-related medical treatment under TRICARE. | promoted |
| 247 | Nay | Agreed to | `119:hamdt:87` | Would prohibit a male cadet or midshipman from participating in an athletic program or activity designated exclusively for females. | promoted |
| 248 | Nay | Agreed to | `119:hamdt:88` | Would prohibit DOD gender-identity survey/form fields beyond male/female sex or gender responses and require rejection of other responses to required questions. | promoted |
| 249 | Nay | Agreed to | `119:hamdt:89` | Would prohibit individuals from using single-sex spaces on military installations that do not correspond to biological sex. | promoted |
| 250 | Nay | Failed | `119:hamdt:78` | Would require DOD certification that certain offshore wind projects would not interfere with radar capabilities. | promoted |
| 251 | Nay | Agreed to | `119:hamdt:79` | Would eliminate DOD preferences and requirements for motor vehicles using electric or hybrid propulsion systems. | promoted |
| 252 | Nay | Agreed to | `119:hamdt:81` | Would increase penalties for entering a military installation or violating national defense area security regulations. | promoted |
| 253 | Nay | Agreed to | `119:hamdt:90` | Would restrict base commanders' ability to fly unauthorized flags at their discretion. | promoted |
| 254 | Nay | Failed | `119:hamdt:91` | Would ban DOD research, development, procurement, and promotion of cell-cultured meat. | promoted |
| 255 | Nay | Failed | `119:hamdt:93` | Would prohibit assistance to Ukraine. | promoted |
| 256 | Nay | Failed | `119:hamdt:94` | Would strike funding for the Overseas Humanitarian, Disaster, and Civic Aid program. | promoted |
| 257 | Nay | Failed | `119:hamdt:95` | Would strike foreign aid funding for the Taiwan Security Cooperation Initiative. | promoted |
| 258 | Nay | Agreed to | `119:hamdt:96` | Would prohibit DOD recruitment contracts with certain fact-checking and information-grading entities. | promoted |
| 259 | Nay | Failed | `119:hamdt:97` | Would limit critical-habitat designations on military and certain National Guard lands and exempt military personnel from ESA prohibitions during national-defense operations. | promoted |
| 260 | Yea | Agreed to | `119:hamdt:100` | Would require a DOD report to congressional armed-services committees on the Janet Yamanaka Mello fraud scheme involving 4-H Military Partnership Grant program funds. | promoted |

## Candidate Fields

Each promoted record includes:

- `interpretation_status: interpreted`
- `support_position: yea`
- `oppose_position: nay`
- `confidence: high`
- `issue_facet: Defense authorization amendment`
- `plain_english_summary`
- `yea_meaning`
- `nay_meaning`
- `policy_effect`
- `what_happened`
- `why_it_mattered`
- `member_vote_context`
- `what_not_to_infer`
- `source_basis`

## Before / After Example

### Roll 244 Before

```json
{
  "roll_call_id": 224,
  "interpretation_status": "insufficient_evidence",
  "plain_english_summary": null,
  "support_position": null,
  "oppose_position": null,
  "uncertainty_note": "The packet identifies the amendment sponsor and amendment number but does not include enough official amendment text to explain what the amendment would change."
}
```

### Roll 244 After

```json
{
  "roll_call_id": 224,
  "interpretation_status": "interpreted",
  "support_position": "yea",
  "oppose_position": "nay",
  "plain_english_summary": "This vote was on whether to agree to an amendment to H.R. 3838, the FY2026 defense authorization bill, that would repeal the 2002 and 1991 Authorization for Use of Military Force (AUMFs).",
  "yea_meaning": "A Yea vote supported agreeing to the amendment.",
  "nay_meaning": "A Nay vote opposed agreeing to the amendment.",
  "member_vote_context": "Foushee voted Yea, meaning she supported agreeing to this amendment.",
  "what_not_to_infer": "Do not infer motive, ideology, character, a voting recommendation, or a broad position on national security from this amendment vote. This was an amendment vote, not final passage of H.R. 3838.",
  "source_basis": [
    "House Clerk roll-call question, amendment author, result, and Foushee recorded vote for Roll 244",
    "Congress.gov amendment record 119:hamdt:99 purpose/description for H.R. 3838"
  ]
}
```

## Before / After Card Summary Examples

The frontend card text was not changed in this pass. If these reviewed records are imported and the existing frontend consumes them, these rows can move from limited-context cards to interpreted amendment cards.

Example Roll 244 after interpretation:

```text
Yea. This vote was on whether to agree to an amendment to H.R. 3838, the FY2026 defense authorization bill, that would repeal the 2002 and 1991 Authorization for Use of Military Force (AUMFs). Foushee voted Yea, meaning she supported agreeing to this amendment. This was an amendment vote, not final passage of H.R. 3838.
```

Example Roll 255 after interpretation:

```text
Nay. This vote was on whether to agree to an amendment to H.R. 3838, the FY2026 defense authorization bill, that would prohibit assistance to Ukraine. Foushee voted Nay, meaning she opposed agreeing to this amendment. The amendment failed.
```

## What The National Security Overview Could Now Say

If these records are imported and current readiness rules consume them, Valerie Foushee / National Security & Foreign Policy would have many more interpreted amendment rows. A cautious overview could say the reviewed sample includes amendment votes on:

- repeal of the 2002 and 1991 AUMFs
- military health care and military-installation sex/gender policy amendments
- offshore wind radar certification
- DOD vehicle-propulsion preferences
- military-installation security penalties
- base flag authority
- Ukraine assistance
- overseas humanitarian aid
- Taiwan security funding
- DOD recruitment-contract restrictions
- military/National Guard land and Endangered Species Act issues
- a DOD reporting requirement tied to a military grant fraud case

It still should not say Foushee is broadly for or against national security. These are amendment votes on a single House NDAA package.

## Rows Kept Limited And Why

None of the 17 matched H.R. 3838 amendment rows were kept limited in this pass.

The nearby floor-rule/procedural rows remain limited/ambiguous and were not changed.

## Risks And Limits

- The records are promoted in source-controlled manual interpretation batch JSON only. They were not imported into the database in this pass.
- The fetched `119_hr_3838` amendment companion cache is under `backend/data_sources/`, which is git-ignored.
- These are amendment votes, not final passage of the underlying NDAA.
- Some failed amendments use source language such as "sought to"; public copy must preserve that the amendment failed.
- This does not make a broad claim about Foushee's national-security ideology or overall record.
- This does not change support/opposition counting logic. Existing code will count these rows only if the reviewed records are imported through the existing `vote_interpretations` path.

## Tests

Manual validation:

```text
batch_002_valerie_national_security_interpretations.json valid_count=12 errors=[]
batch_003_valerie_national_security_remaining_interpretations.json valid_count=10 errors=[]
```

Targeted backend tests:

```text
cd backend
.\.venv_win\Scripts\python.exe -m pytest --basetemp=.pytest_tmp_phase1c tests\test_congress_adapter.py tests\test_source_packets.py tests\test_manual_interpretations.py tests\test_ndaa_amendment_interpretations.py
```

Result:

```text
collected 25 items
tests\test_congress_adapter.py .......
tests\test_source_packets.py .......
tests\test_manual_interpretations.py ......
tests\test_ndaa_amendment_interpretations.py .....
25 passed in 0.13s
```

Frontend tests/build skipped unless frontend behavior or frontend fixtures changed.

## Recommended Next Step

Product-review the 17 promoted amendment interpretations before importing them into a live database. If approved, import through:

```text
python -m app.etl.manual_interpretations import --input ..\docs\interpretation_batches\<batch> --reviewed-by <reviewer>
```

Then run the existing API/frontend evidence tests to confirm the National Security section remains cautious and does not overclaim from these amendment votes.
