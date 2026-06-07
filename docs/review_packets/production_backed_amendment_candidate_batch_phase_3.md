# Production-Backed Amendment Candidate Batch - Phase 3

Date: 2026-06-07

Scope: read-only production discovery and review-packet generation for the next amendment enrichment candidate. This phase used production Supabase as the source of truth for discovery, then used existing local Congress.gov cache and Phase 2 source-packet tooling to evaluate candidates.

No production data was written. No import was run. No API, UI, counting, alignment, or production interpretation records were changed.

## Approval Gate

This packet is for human review only.

Do not import any candidate interpretation until the user explicitly approves a separate production import step.

## Production Discovery Summary

Read-only production discovery found:

| Metric | Count |
| --- | ---: |
| Amendment-like unique roll calls | 21 |
| Already interpreted amendment roll calls | 19 |
| Weak amendment roll calls | 2 |

No remaining production section met the Phase 2 "amendment-heavy" threshold of three or more weak amendment roll calls in the same issue domain and bill.

The two remaining weak amendment roll calls are:

| Roll | Domain | Bill | Current status | Source-packet result | Selection note |
| ---: | --- | --- | --- | --- | --- |
| 32 | Justice & Public Safety | `119:hr:27` HALT Fentanyl Act | `ambiguous` | `likely_upgrade_candidate` | Best target: matched Congress.gov amendment record includes amendment-specific description. |
| 180 | Economy & Taxes | `119:hr:3944` Military Construction and Veterans Affairs, Agriculture, and Legislative Branch Appropriations Act, 2026 | `ambiguous` | `still_limited` | Not selected: en bloc amendment did not match fetched amendment detail. |

## Selected Target Section

Selected target:

- Representative: Valerie P. Foushee
- Issue section: Justice & Public Safety
- Bill: `119:hr:27`, HALT Fentanyl Act
- Roll call: House Roll 32, February 6, 2025
- Vote action: On Agreeing to the Amendment
- Amendment: Trahan of Massachusetts Part B Amendment No. 2
- Current interpretation status: `ambiguous`

Why selected:

- It is one of only two remaining weak amendment roll calls in production.
- It has the strongest source coverage among remaining weak amendment rows.
- The Congress.gov amendment record matched the House roll-call description by printed amendment number.
- The matched amendment description states the practical effect of the amendment.
- It sits in a visible Valerie Foushee Justice & Public Safety section where one ambiguous row can be upgraded without changing any logic.

Expected value:

- Converts a currently ambiguous amendment row into a reviewed, source-grounded amendment interpretation if approved later.
- Clarifies that the vote was about delaying enactment of H.R. 27 until specified certifications about overdose-death reduction were made.
- Improves the Justice & Public Safety evidence read by reducing ambiguous amendment context.

## Current Production Baseline

Valerie P. Foushee / Justice & Public Safety:

| Metric | Current |
| --- | ---: |
| Recorded eligible rows | 13 |
| Interpreted rows | 6 |
| Ambiguous rows | 1 |
| Insufficient-evidence rows | 6 |
| Missing interpretation rows | 0 |
| Current interpreted support count | 2 |
| Current interpreted oppose count | 4 |
| Current readiness | Mixed but interpretable |

If Roll 32 is later approved and imported:

| Metric | Estimated after approved import |
| --- | ---: |
| Recorded eligible rows | 13 |
| Interpreted rows | 7 |
| Ambiguous rows | 0 |
| Insufficient-evidence rows | 6 |
| Interpreted support count | 3 |
| Interpreted oppose count | 4 |
| Estimated readiness | Mixed but interpretable |

Readiness impact: the label likely remains Mixed but interpretable because the section already has interpreted votes on both sides. The practical quality improves because the only ambiguous amendment row in this section would become traceable and interpretable.

## Source Coverage

Selected Roll 32 source packet:

| Source field | Coverage |
| --- | --- |
| House Clerk roll call | Available |
| Congress.gov bill detail | Available |
| CRS bill summary | Available |
| Bill actions | Available |
| Bill text versions | Available |
| Amendment records | Available |
| Matched amendment record | Available |
| Matched amendment description | Available |
| Committees | Available |
| CBO estimate | Not available |

Matched amendment:

- Congress.gov amendment id: `119:hamdt:5`
- Printed House amendment number: 2
- Match confidence: high
- Match reason: printed amendment number in the roll-call description matched the Congress.gov amendment description
- Amendment description: delay enactment of the bill until the Secretary of Health and Human Services and the Attorney General each certify that the bill will lead to a reduction in overdose deaths
- Latest action: failed by recorded vote, Roll 32

## Candidate Interpretation Table

| Roll | Candidate tier | Current status | Recommended status | Member vote used for context | Support position | Oppose position | Candidate summary | Source basis | What not to infer |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 32 | Strong | `ambiguous` | `interpreted` after review approval | Foushee voted Yea | `yea` | `nay` | This vote was on whether to agree to the Trahan amendment to H.R. 27, the HALT Fentanyl Act. The amendment would have delayed enactment until the Secretary of Health and Human Services and the Attorney General each certified that the bill would lead to a reduction in overdose deaths. Foushee voted Yea, meaning she supported agreeing to this amendment. | House Clerk Roll 32 question, result, and Foushee recorded vote; Congress.gov amendment record `119:hamdt:5`; Congress.gov H.R. 27 bill summary and actions. | Do not infer motive, ideology, character, a voting recommendation, or a broad position on fentanyl policy from this amendment vote. This was an amendment vote, not final passage of H.R. 27. |

Draft fields for later reviewed JSON, if approved:

```json
{
  "roll_call_id": 30,
  "classification_version": "v1",
  "interpretation_version": "interpretation_v1",
  "interpretation_status": "interpreted",
  "plain_english_summary": "This vote was on whether to agree to the Trahan amendment to H.R. 27, the HALT Fentanyl Act. The amendment would have delayed enactment until the Secretary of Health and Human Services and the Attorney General each certified that the bill would lead to a reduction in overdose deaths.",
  "yea_meaning": "A Yea vote supported agreeing to the amendment.",
  "nay_meaning": "A Nay vote opposed agreeing to the amendment.",
  "policy_effect": "If adopted, the amendment would have delayed enactment of H.R. 27 until the Secretary of Health and Human Services and the Attorney General each certified that the bill would lead to a reduction in overdose deaths.",
  "issue_facet": "fentanyl_scheduling_and_overdose_certification",
  "support_position": "yea",
  "oppose_position": "nay",
  "confidence": "high",
  "source_basis": [
    "House Clerk Roll 32 question, result, and Foushee recorded vote",
    "Congress.gov amendment record 119:hamdt:5 description for H.R. 27",
    "Congress.gov H.R. 27 bill summary and actions"
  ],
  "source_url": "https://clerk.house.gov/evs/2025/roll032.xml",
  "uncertainty_note": null,
  "interpretation_reason": "Manual review candidate used the House Clerk amendment vote action and matched Congress.gov amendment description for a source-grounded amendment interpretation.",
  "what_happened": "The House voted on whether to agree to the Trahan amendment to H.R. 27. The amendment would have delayed enactment until the Secretary of Health and Human Services and the Attorney General each certified that the bill would lead to a reduction in overdose deaths. The amendment failed.",
  "why_it_mattered": "The vote decided whether that amendment would be adopted into H.R. 27 before final passage. It was not final passage of the HALT Fentanyl Act.",
  "member_vote_context": "Foushee voted Yea, meaning she supported agreeing to this amendment.",
  "what_not_to_infer": "Do not infer motive, ideology, character, a voting recommendation, or a broad position on fentanyl policy from this amendment vote. This was an amendment vote, not final passage of H.R. 27."
}
```

## Rows Still Insufficient Or Limited

### Remaining Weak Amendment Row

Roll 180 / `119:hr:3944` remains limited.

Reason:

- Production row says Carter of Texas Amendment En Bloc No. 2.
- Local Congress.gov cache has bill-level summary, actions, text versions, committees, committee reports, and 138 amendment records.
- Phase 2 source-packet matching did not identify a matching amendment record from the en bloc roll-call description.
- Without amendment-specific matched text, the row should remain ambiguous.

### Valerie Justice & Public Safety Rows Still Insufficient

Six Valerie / Justice & Public Safety rows remain insufficient evidence after this candidate because they are rule or procedural-context rows, not amendment rows selected for this phase:

- H. Res. 489, Roll 160
- H. Res. 489, Roll 161
- H. Res. 707, Roll 267
- H. Res. 707, Roll 268
- H. Res. 879, Roll 290
- H. Res. 879, Roll 291

Those rows require separate procedural-rule interpretation review. They are outside this amendment companion milestone.

## Risks

- This phase found no remaining multi-roll weak amendment-heavy production section; the selected target is the best available single-roll amendment candidate.
- The candidate should still receive human review before import because it affects a visible issue section.
- H.R. 27 final passage is already interpreted separately; the amendment candidate must not be collapsed into final-passage meaning.
- The amendment failed, so public copy must say what adoption would have done rather than imply the delay became law.
- The candidate uses cached official-source context only; no broad new source collection was performed.

## Import Boundary

No import was run.

Before any production import:

1. Human reviewer approves the candidate text.
2. Candidate is moved into a reviewed interpretation JSON file.
3. Import is explicitly requested by the user.
4. Post-import validation confirms only Roll 32 changed.

