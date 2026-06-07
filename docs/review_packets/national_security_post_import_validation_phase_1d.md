# National Security Post-Import Validation - Phase 1D

## Production Target

This phase intentionally targeted the configured production/main Supabase database because a separate Supabase dev branch/project is not currently available and the site is not live.

- DATABASE_URL source: `backend/.env`
- Supabase host: `aws-1-us-east-1.pooler.supabase.com`
- Supabase project ref: `wfh...fao` redacted
- Database: `postgres`
- Import path: `backend/app/etl/manual_interpretations.py`
- Import behavior: idempotent `ON CONFLICT (roll_call_id) DO UPDATE`
- Schema changes: none
- Approved write phrase received: `Approved: run the production import`

## Import Scope

Only the 17 approved NDAA amendment interpretations were imported.

- Domain: `NATIONAL_SECURITY_FOREIGN`
- Facet: `Defense authorization amendment`
- roll_call_id values: `224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 240`
- House roll numbers: `244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255, 256, 257, 258, 259, 260`
- Rows inserted: `0`
- Rows updated: `17`
- Existing rows overwritten: all 17 existed as `insufficient_evidence`

Important model note: `vote_interpretations` are roll-call-level records, not legislator-specific records. This import can affect other representative evidence views that include these same roll calls.

## Rollback Artifact

Rollback file created before import:

`docs/review_packets/production_import_rollback_phase_1d.sql`

The rollback file is limited to the 17 target roll_call_id values. Because all 17 rows existed before import, it contains restore `INSERT ... ON CONFLICT DO UPDATE` statements and no delete statements. Rollback was not run.

## Before / After Counts

Valerie Foushee / National Security & Foreign Policy:

| Metric | Before | After |
| --- | ---: | ---: |
| Total evidence rows | 22 | 22 |
| Interpreted Yes/No rows | 2 | 19 |
| Limited / ambiguous / insufficient rows | 20 | 3 |
| Not-voting rows | 0 | 0 |
| Support count | 0 | 2 |
| Oppose count | 2 | 17 |
| Interpreted NDAA rolls 244-260 | 0 | 17 |
| Readiness label | Limited evidence | Mixed but interpretable |

The issue overview remains cautious: it says the reviewed votes are mixed, identifies limited rows, and warns against broad issue-area conclusions.

## Rendered National Security Overview After Import

What these votes were about

In this National Security & Foreign Policy sample, the reviewed votes where Foushee cast a Yes or No covered several policy questions: whether to adopt amendments to defense authorization legislation; whether to pass defense and national-security authorization legislation; and whether to pass legislation affecting veterans cemetery administration. Three additional rows remain visible below but are not counted because the available source text does not clearly explain the practical policy effect.

What Foushee did

Of the 19 reviewed Yes/No votes that could be interpreted, 2 supported the measures shown and 17 opposed them. Most of those votes matched most Democrats. Most opposed measures that passed the House.

What pattern that creates

Foushee's reviewed votes where she cast a Yes or No in this sample were mixed. Her record here is best read as a mixed record on this specific set of Republican-led House measures, not as a simple statement that she is broadly for or against this issue area.

How a voter might read that

If you generally favored these House Republican measures, this section may look misaligned with your views. If you generally wanted Democrats to oppose those measures or objected to their terms, this section may look aligned. The vote record alone does not show her motive.

What not to infer

Do not infer motive, ideology, character, corruption, or a voting recommendation from this section. The rows show recorded votes and reviewed bill meaning for this sample, not her full record in this issue area. Not-voting and limited-context rows remain visible below, but they are not forced into the pattern.

## First 10 Default-Visible Card Summaries

1. Roll 242: Nay. The source packet concerns a previous-question vote on a resolution for considering other bills rather than direct passage of the underlying policy bills, so yea/nay meaning is procedural and not treated as direct policy alignment. This row remains visible but is not counted in the summarized vote pattern because the available source text does not explain the practical policy effect.

2. Roll 243: Nay. The source packet concerns a resolution for considering other bills rather than direct passage of the underlying policy bills, so yea/nay meaning is procedural and not treated as direct policy alignment. This row remains visible but is not counted in the summarized vote pattern because the available source text does not explain the practical policy effect.

3. Roll 244: Yea. The House voted on whether to agree to Meeks of New York Part A Amendment No. 34. The amendment would repeal the 2002 and 1991 Authorization for Use of Military Force (AUMFs). The amendment was agreed to. The vote decided whether that amendment would be adopted into the House's FY2026 defense authorization bill. It was not final passage of the full NDAA. Foushee voted Yea, matching most Democrats. The measure passed.

4. Roll 245: Nay. The House voted on whether to agree to Norman of South Carolina Part A Amendment No. 13. The amendment would prohibit the provision of gender transition procedures, including surgery or medication, through the Exceptional Family Medical Program. The amendment was agreed to. The vote decided whether that amendment would be adopted into the House's FY2026 defense authorization bill. It was not final passage of the full NDAA. Foushee voted Nay, matching most Democrats. The measure passed.

5. Roll 246: Nay. The House voted on whether to agree to Mace of South Carolina Part A Amendment No. 14. The amendment would prohibit the Department of Defense from covering or furnishing gender-related medical treatment under TRICARE. The amendment was agreed to. The vote decided whether that amendment would be adopted into the House's FY2026 defense authorization bill. It was not final passage of the full NDAA. Foushee voted Nay, matching most Democrats. The measure passed.

6. Roll 247: Nay. The House voted on whether to agree to Mace of South Carolina Part A Amendment No. 15. The amendment would prohibit the Superintendent of a Service Academy from allowing a cadet or midshipman who is male from participating in an athletic program or activity that is designated exclusively for females. The amendment was agreed to. The vote decided whether that amendment would be adopted into the House's FY2026 defense authorization bill. It was not final passage of the full NDAA. Foushee voted Nay, matching most Democrats. The measure passed.

7. Roll 248: Nay. The House voted on whether to agree to Mace of South Carolina Part A Amendment No. 16. The amendment would prohibit the Secretary of Defense from soliciting information through a form or survey regarding the gender identity of an individual, providing an option to indicate the sex or gender of an individual is something other than male or female, and would require the Secretary reject a response other than male or female to a required question on a form or survey regarding sex or gender. The amendment was agreed to. The vote decided whether that amendment would be adopted into the House's FY2026 defense authorization bill. It was not final passage of the full NDAA. Foushee voted Nay, matching most Democrats. The measure passed.

8. Roll 249: Nay. The House voted on whether to agree to Mace of South Carolina Part A Amendment No. 17. The amendment would prohibit individuals from accessing or using single-sex spaces on military installations which do not correspond to the biological sex of the individual. The amendment was agreed to. The vote decided whether that amendment would be adopted into the House's FY2026 defense authorization bill. It was not final passage of the full NDAA. Foushee voted Nay, matching most Democrats. The measure passed.

9. Roll 250: Nay. The House voted on whether to agree to Smith of New Jersey Part A Amendment No. 7. The amendment would require the Secretary of Defense to certify that offshore wind projects in the North Atlantic and Mid-Atlantic Planning Areas will not interfere with radar capabilities. The amendment failed. The vote decided whether that amendment would be adopted into the House's FY2026 defense authorization bill. It was not final passage of the full NDAA. Foushee voted Nay, matching most Democrats. The measure failed.

10. Roll 251: Nay. The House voted on whether to agree to Patronis of Florida Part A Amendment No. 9. The amendment would eliminate the preference for motor vehicles using electric or hybrid propulsion systems and related requirements of the Department of Defense. The amendment was agreed to. The vote decided whether that amendment would be adopted into the House's FY2026 defense authorization bill. It was not final passage of the full NDAA. Foushee voted Nay, matching most Democrats. The measure passed.

## Grouped Evidence Preview After Import

- Floor/procedure group: Rolls 242 and 243 remain limited-context rows for a House floor rule / previous-question sequence. They are not counted in the summarized pattern.
- NDAA group: Rolls 244-260 and 262 relate to H.R. 3838 / FY2026 defense authorization. The group contains 17 amendment rows plus the final House passage row. Amendment rows should not be treated as final passage of the full NDAA.
- Veterans cemetery group: Rolls 319 and 320 relate to the National Defense Authorization Act for Fiscal Year 2026 title in the current grouping metadata; Roll 319 remains procedural/ambiguous and Roll 320 is interpreted final passage of a veterans cemetery administration bill.

Grouping makes the section easier to scan by separating the dense NDAA amendment cluster from procedural rows and the later veterans-cemetery rows.

## Confidence Labels

- The 17 imported NDAA amendment rows show `high` confidence.
- Existing interpreted final-passage rows also remain interpreted.
- The 3 remaining limited/procedural rows do not receive confidence labels and are not counted in the summarized support/opposition pattern.

## Label Cleanup After Import

The defense authorization amendment facet now uses status-aware measure-group labels:

- Mostly interpreted/source-grounded amendment groups render as `defense authorization amendments`.
- Mostly limited, ambiguous, or insufficient amendment groups render as `limited-context defense authorization amendments`.
- Meaningfully mixed amendment groups render as `mixed-context defense authorization amendments`.

Before cleanup, the post-import National Security measure group still rendered as `limited-context defense authorization amendments` even though all 17 NDAA amendment rows were interpreted. After cleanup, the group renders as `defense authorization amendments`, and the overview says the reviewed votes included whether to adopt amendments to defense authorization legislation.

This is a frontend label/status cleanup only. No additional data import occurred, no row interpretation statuses changed, and support/opposition counting stayed unchanged.

The label cleanup does not create a broad claim that Foushee is for or against national security. The section remains `Mixed but interpretable` and continues to describe only this reviewed sample.

## Voter Value After Import

The voter can now understand that most of the previously weak National Security evidence was a cluster of amendment votes around the FY2026 defense authorization bill. The app can explain what each amendment would have done, whether Foushee supported or opposed agreeing to it, whether that matched most Democrats, and whether the amendment passed or failed.

The voter still should not infer a broad position for or against national security, motive, ideology, character, corruption, or a voting recommendation. These rows are mostly one NDAA amendment cluster, not a full National Security & Foreign Policy record.

This reduces scroll/value mismatch because the 17 dense rows now carry source-grounded meaning instead of appearing mostly as limited evidence. The section should move from `Limited evidence` to `Mixed but interpretable`, while still being framed as a specific reviewed sample.

## Guardrail Check

- No broad "for/against national security" claim was introduced.
- No motive, ideology, character, corruption, or voting recommendation claim was introduced.
- NDAA amendment votes are described as amendment votes, not final passage of the full NDAA.
- Not-voting rows counted: none.
- No automatic promotion beyond the approved 17 rows.
- No UI/API/counting/alignment code changed.
- Rollback file existed before import.
- Production write was limited to the approved 17 roll_call_id values.
- No additional data import occurred during the label cleanup.

## Tests

- `cd backend; .\.venv_win\Scripts\python.exe -m pytest --basetemp=$env:TEMP\pf_pytest_phase1d_backend_escalated tests\test_manual_interpretations.py tests\test_source_packets.py tests\test_ndaa_amendment_interpretations.py tests\test_congress_adapter.py`
  - Result: `25 passed in 0.17s`
- `node --test frontend/lib/issueOverview.test.mjs frontend/lib/evidenceGrouping.test.mjs frontend/lib/issueReadiness.test.mjs frontend/lib/voteCardSummary.test.mjs`
  - Result after label cleanup: `20 passed`
- `cd frontend; npm run build`
  - Result after label cleanup: passed

The frontend validation used existing frontend rendering helpers against the post-import production-backed evidence response.

## Product Conclusion

Congress.gov amendment enrichment materially improved National Security voter value for this slice. It is worth generalizing for amendment-heavy clusters where the roll-call action and amendment-specific purpose can be matched confidently.

Recommended next step: do a small UI compression / amendment-cluster polish pass before broadening enrichment further, because the improved card content is source-grounded but dense.

## Known Risks

- Production Supabase was used as the working database because no separate Supabase dev/staging target is available.
- The imported records are roll-call-level and can affect other officials who voted on the same 17 roll calls.
- The first 10 card summaries are accurate but dense. A UI compression pass should make amendment clusters easier to review.
