# Record Across Congresses Frontend Contract

Branch: `codex/record-across-congresses-frontend-contract`  
Base: `main` at `f07fe8982d33edbd86de9002a97d8445b4272d4f`

## Summary

This review packet defines the product and UX contract for a future House-only `Record Across Congresses` panel. It uses the merged backend chain as its source basis:

- PR #45 versioned derived artifact;
- PR #46 internal family accessor;
- PR #47 House legislator join helper;
- PR #48 internal `Record Across Congresses` adapter.

This milestone does not implement runtime frontend code, backend routes, schema changes, public API exposure, or production writes.

## User-Facing Purpose

The future panel is for showing reviewed House vote evidence that exists in both the 118th and 119th Congresses for the same policy-question family. It should let users inspect records side by side at the family level, with direct visibility into caveats, roll-call IDs, and separated counts.

The panel must preserve comparability limits. It may show where reviewed evidence exists and how many cast substantive Yes/No, not-voting, present, and missing/no-record rows are present in each Congress. It must not draw behavioral, ideological, causal, motive, or direction-of-view conclusions.

## Placement Recommendation

Recommended placement: an advanced collapsed section below the current strongest issue evidence path on the profile page.

Options considered:

- Below current strongest issue evidence: good because users first get the primary issue read, then can inspect broader record context.
- Inside an advanced/collapsed section: good because this evidence is more caveated and should not compete with the first useful answer.
- Inside existing scope controls: not recommended because the panel is not a simple scope filter; it has its own family-comparability contract.
- Separate tab or card: possible later, but too prominent before copy and rendered validation prove the hierarchy works.

Recommendation: place a collapsed `Record Across Congresses` section after `ProfileQuickRead` and the strongest issue evidence area, before lower-priority comparison or candidate context. Open it only when data is available or when the empty state helps explain why the section is unavailable.

## Information Hierarchy

Future panel hierarchy:

1. Title: `Record Across Congresses`
2. One-sentence explanation.
3. Availability summary with total display-eligible families, closest family matches, and caveated family matches.
4. Family rows or cards, sorted with closest family matches first, then caveated family matches, then stable ordering from the adapter.
5. Per-family header: family name, issue domain, match label, and governing question.
6. Per-Congress counts: 118th and 119th side by side, with cast substantive Yes/No separated from not-voting, present, and missing/no-record.
7. Caveat directly below each family row.
8. Source/evidence drilldown prompt that opens the roll-call evidence used for the family.
9. Sparse or unavailable state when no family has evidence in both Congresses.

## Allowed Copy

These strings are approved for future prototype use. They avoid unsupported implications and are also stored in `docs/review_packets/record_across_congresses_frontend_copy_guardrails.json`.

| Use | Approved copy |
|---|---|
| Panel title | `Record Across Congresses` |
| One-sentence explanation | `Reviewed House vote evidence exists in both the 118th and 119th Congresses for these policy-question families.` |
| Direct-comparable family label | `Closest family match` |
| Conditional-comparable family label | `Caveated family match` |
| No eligible families state | `No reviewed family has enough House vote evidence in both Congresses for this panel yet.` |
| 118th-only state | `Reviewed family evidence is available in the 118th Congress, but not in the 119th Congress for this official.` |
| 119th-only state | `Reviewed family evidence is available in the 119th Congress, but not in the 118th Congress for this official.` |
| Not-voting caveat | `Not-voting rows are shown separately and are not counted as Yes or No votes.` |
| Missing/no-record caveat | `Missing/no-record means this official has no counted vote row for that roll call in the reviewed data.` |
| Related-but-not-comparable exclusion | `Related rows that do not meet the family standard are not shown in this panel.` |
| Why this does not make an inference | `This panel places reviewed roll-call evidence from two Congresses side by side. It does not describe what that means about the official's views, behavior, or reasons.` |
| Source/evidence drilldown prompt | `Open the roll-call evidence used for this family.` |

## Disallowed Copy

Frontend implementation must not use these phrases or close variants for this feature:

- `changed`
- `change`
- `trend`
- `shifted`
- `movement`
- `more supportive`
- `less supportive`
- `consistent`
- `flip`
- `ideological`
- `evolved`
- `moderated`
- `became`
- `continuity`
- `moved toward`
- `moved away from`

Unsafe examples and safe replacements:

| Unsafe sentence | Safe replacement |
|---|---|
| `Her record changed between Congresses.` | `Reviewed family evidence is available in both Congresses.` |
| `He became more supportive on this issue.` | `The panel shows cast substantive Yes/No counts separately for each Congress.` |
| `This trend shows movement on funding bills.` | `This family includes reviewed funding-package roll calls in both Congresses.` |
| `The official stayed consistent.` | `The same policy-question family has reviewed evidence in both Congresses.` |
| `This vote pattern moved away from the prior record.` | `Open the roll-call evidence used for this family.` |
| `The member flipped on Ukraine restrictions.` | `This caveated family has reviewed roll calls in both Congresses; read the family caveat before interpreting the rows.` |

## Response-Field Mapping

| Adapter field | Safe to display? | Display label | Transformation | Caveats required | Internal only? |
|---|---|---|---|---|---|
| `product_framing` | Yes | Panel title | Use exact value. | Must remain `Record Across Congresses`. | No |
| `artifact_version` | Limited | Data version | Show in details or debug footer only. | Explain as reviewed internal artifact version. | Prefer internal/admin detail |
| `availability_explanation` | Yes | About this panel | May use as source for explanatory copy. | Keep factual availability/count framing. | No |
| `non_authorization_metadata` | No | None | Do not show raw booleans. Use approved explanatory copy. | Must guide implementation QA. | Yes |
| `summary.record_across_congresses_available` | Yes | Evidence available | Render as availability state only. | Never pair with inference language. | No |
| `summary.display_eligible_family_count` | Yes | Families with evidence in both Congresses | Format as count. | Count means display availability only. | No |
| `summary.directly_comparable_display_eligible_family_count` | Yes | Closest family matches | Format as count. | Label must explain reviewed family match. | No |
| `summary.conditionally_comparable_display_eligible_family_count` | Yes | Caveated family matches | Format as count. | Show caveat affordance. | No |
| `families` | Yes | Family evidence | Render eligible families as rows/cards. | Excluded related/ungrouped rows must stay absent. | No |
| `family_id` | Limited | Family ID | Use for keys/debug/drilldown; not primary copy. | None. | Prefer internal |
| `family_name` | Yes | Family | Humanize if needed. | Keep near governing question. | No |
| `issue_domain` | Yes | Issue area | Format through existing issue-domain labels. | Do not use as broad-domain matching proof. | No |
| `comparability_status` | Yes | Family match type | Map `directly_comparable` to `Closest family match`; map `conditionally_comparable` to `Caveated family match`. | Conditional rows must show caveat. | No |
| `governing_question` | Yes | Reviewed question | Display as family question. | Preserve exact meaning; do not replace amendment meaning with parent measure meaning. | No |
| `comparability_caveat` | Yes | Caveat | Show inline under family header. | Required for every family row. | No |
| `roll_call_ids_considered_by_congress` | Yes | Roll calls used | Use as drilldown metadata. | Must match evidence drilldown path. | No |
| `family_evidence_counts_by_congress` | Yes | Counts by Congress | Render 118th and 119th side by side. | Counts remain separated. | No |
| `cast_substantive_yes_count` | Yes | Cast substantive Yes | Display as count. | Only interpreted substantive Yes rows. | No |
| `cast_substantive_no_count` | Yes | Cast substantive No | Display as count. | Only interpreted substantive No rows. | No |
| `not_voting_count` | Yes | Not voting | Display separately. | Never add to Yes/No. | No |
| `present_count` | Yes | Present | Display separately. | Never add to Yes/No. | No |
| `missing_no_record_count` | Yes | Missing/no-record | Display separately. | Explain no counted vote row exists in reviewed data. | No |
| `unavailable_reason` | Yes | Why unavailable | Map to approved sparse-state copy. | Must not imply judgment about the official. | No |

## Profile Examples

Production-shaped read-only adapter summaries were generated for the required profiles. For every profile, disallowed adapter term checks returned an empty list.

| Profile | Future UI state | Direct | Conditional | Example family display | Caveats and count notes | Claim boundary |
|---|---|---:|---:|---|---|---|
| Valerie P. Foushee | 11 families with evidence in both Congresses | 4 | 7 | `eco_government_funding_packages`; caveated family match | 118th Yes 1, No 4; 119th Yes 0, No 5; funding-package caveat visible | No inference claim |
| Aaron Bean | 11 families with evidence in both Congresses | 4 | 7 | `eco_government_funding_packages`; caveated family match | 118th Yes 4, No 1; 119th Yes 5, No 0; funding-package caveat visible | No inference claim |
| Adam Smith | 11 families with evidence in both Congresses | 4 | 7 | `eco_government_funding_packages`; caveated family match | 118th Yes 1, No 4; 119th Yes 2, No 3; funding-package caveat visible | No inference claim |
| Abraham J. Hamadeh | Empty state: 119th evidence only for example family | 0 | 0 | `eco_government_funding_packages`; unavailable | 118th missing/no-record 5; 119th Yes 5; no display family count | No inference claim |
| Allred | Empty state: 118th evidence only for example family | 0 | 0 | `eco_government_funding_packages`; unavailable | 118th Yes 1, No 4; 119th missing/no-record 5 | No inference claim |
| Aumua Amata Coleman Radewagen | 1 caveated family with evidence in both Congresses | 0 | 1 | `nsf_ukraine_assistance_restrictions`; caveated family match | 118th No 9, not-voting 3; 119th No 1; conditional caveat visible | No inference claim |
| James Gallagher | Empty state: no family has evidence in both Congresses | 0 | 0 | `eco_government_funding_packages`; unavailable | 118th missing/no-record 5; 119th missing/no-record 5 | No inference claim |
| No display-eligible profile | Use James Gallagher as representative no-family state | 0 | 0 | Show no-family state, not family cards by default | Missing/no-record explanation available in details | No inference claim |

Sparse-state behavior:

- If only 118th has counted substantive evidence, use the 118th-only state.
- If only 119th has counted substantive evidence, use the 119th-only state.
- If neither Congress has counted substantive evidence, use the no eligible families state plus missing/no-record caveat in details.
- Not-voting and present rows may explain why raw roll-call participation does not equal counted substantive Yes/No evidence.

Related and ungrouped rows:

- Do not render them as eligible family cards.
- Do not show them in the availability summary.
- If users ask why a row is absent, use the related-row exclusion copy from the allowed set.

## Component Contract Proposal

No component is implemented in this milestone. Future boundaries:

| Component | Conceptual props | Safety responsibilities |
|---|---|---|
| `RecordAcrossCongressesPanel` | `response`, `onOpenEvidence` | Owns title, explanation, availability state, and no-inference note. Refuses to render if product framing differs. |
| `RecordAcrossCongressesSummary` | `summary` | Shows total, closest family match count, and caveated family match count as availability only. |
| `ComparableFamilyCard` | `family`, `onOpenEvidence` | Shows family name, issue domain, governing question, match label, caveat, and drilldown prompt. |
| `CongressEvidenceCounts` | `countsByCongress` | Renders 118th/119th counts side by side; keeps Yes/No/not-voting/present/missing separated. |
| `ComparabilityCaveat` | `caveat`, `status` | Keeps caveats visible, especially for caveated family matches. |
| `NoCrossCongressEvidenceState` | `summary`, `families` | Uses approved sparse-state copy and never interprets absence as a statement about the official. |
| `RecordAcrossEvidenceDrilldownLink` | `familyId`, `rollCallIdsByCongress` | Opens existing evidence path by roll-call IDs; does not create new evidence meaning. |

## Validation

Validation performed:

- Confirmed no runtime frontend files were changed.
- Confirmed no backend route was added.
- Confirmed no schema, migration, or production write was added.
- Confirmed no public API exposure is part of this spec.
- Confirmed proposed approved copy uses `Record Across Congresses`.
- Confirmed approved copy in `record_across_congresses_frontend_copy_guardrails.json` does not include the disallowed vocabulary.
- Confirmed profile examples keep not-voting and missing/no-record separate from Yes/No.
- Confirmed related and ungrouped rows remain excluded by design.
- Confirmed direct and conditional caveats are visible in the proposed hierarchy and profile examples.

No rendered frontend validation is required because this milestone intentionally changes no runtime frontend code.

## Design Decision

Decision: `READY FOR INTERNAL ENDPOINT`

Smallest next milestone: define a guarded private/internal endpoint contract that returns the PR #48 adapter response to trusted callers only. Do that before any frontend prototype so transport, exposure, and response naming can be reviewed without user-facing UI pressure.

After that, a separate frontend prototype milestone can implement the collapsed panel and run rendered desktop/mobile validation against production-shaped examples.

## Permanent Files

- `docs/review_packets/record_across_congresses_frontend_contract.md`: durable UX/content contract for future implementation.
- `docs/review_packets/record_across_congresses_frontend_copy_guardrails.json`: machine-checkable approved copy and disallowed vocabulary for this feature.

Both remain useful after this milestone because future endpoint and frontend work can use them as the source of accepted copy, field mapping, and component safety responsibilities.
