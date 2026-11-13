# Canonical measure lookup diagnosis

Base: verified remote main `d81eec08e3a4d195ac1676c8ceddbe0c91401d81`. Isolated owner checkout `.w/ls`, branch `codex/voter-canonical-measure-lookup`. Scope is diagnosis and durable audit evidence only; runtime, API, database, publication, configuration and editorial artifacts are unchanged.

## Result and authorization boundary

The miss is **absent structured measure identity in the currently loaded API response**, not faulty normalization. It cannot be corrected within the authorized frontend-only display/index envelope without deriving identity from prose or URLs. No such derivation was implemented. There is no observed source conflict; underlying database identity availability has not been inspected and is not claimed absent.

The parent permits routine frontend correction only for an omission where authoritative loaded identifier data already exists, or a normalization defect. Neither condition is met for this row. The remaining decision is whether to authorize a bounded API read-contract change to expose an existing, verified exact-action/measure binding, followed by frontend display/indexing. No production evidence import, data mutation or new interpretation is needed or proposed by this packet. ZIP verification and missing-contact recommendations remain separate candidates.

## Exact response and official identity

GET `https://political-fingerprint.onrender.com/legislators/leg_valerie_p_foushee/positions/NATIONAL_SECURITY_FOREIGN/evidence?scope=119` returns93 rows. The captured, unmodified response is `live-evidence.json.gz`; decoded SHA256 `ad443f45a73cb52e2810355cf2ae79f9ea0fa8019757000c3837858de7d96065`.

Target path is `$.evidence[?(@.canonical_action_id == 'house:119:2:282')]`:

| Existing field/path | Value |
| --- | --- |
| Response `legislator_id`, `domain`, `scope` | `leg_valerie_p_foushee`, `NATIONAL_SECURITY_FOREIGN`, `119` |
| Row `canonical_action_id`, `congress`, `session`, `rollcall_number` | `house:119:2:282`,119,2,282 |
| Row `position`, projection `member_action` | `yea`, `Yea` |
| Row `source_url`, projection `vote_sources[0].url` | `https://clerk.house.gov/evs/2026/roll282.xml` |
| Row `bill_title` | Descriptive Iran War Powers title; no printed measure number |
| Projection `exact_action_meaning` and `policy_question`; row `question`/`plain_english_summary` | Explicitly mention H.Con.Res.89 as part of approved action prose |
| Projection `action_meaning_sources[0].url`; row `source_basis[0].url` | `https://api.congress.gov/v3/bill/119/hconres/89/actions` |
| Projection `action_meaning_sources[1].url`; row `source_basis[1].url` | `https://www.congress.gov/119/bills/hconres89/BILLS-119hconres89eh.xml` |
| Exact structured measure fields and existing alias fields, including nested `raw_evidence` and `vote_context` | Absent; see reproducer's exhaustive existing-alias check |

The live official XML, captured independently by GET and preserved as `roll282.xml.gz`, has decoded SHA256 `3bc8e86e67a5e60b7e164f19b94e72d3f778e859342a029d59387e575feddba0`. At `/rollcall-vote/vote-metadata`: `congress=119`, `session=2nd`, `rollcall-num=282`, `legis-num=H CON RES89` (spaces in source: `H CON RES 89`), action date23-Jul-2026, On Agreeing to the Resolution, Passed. The source's recorded-vote for `legislator/@name-id=F000477` is Foushee/Yea. This independently confirms the exact source/action/member binding; it does not put a structured measure field into the app response. CongressAPI and bill-text links were not used to bypass keys or access restrictions.

## Code and displayed matcher trace

- `frontend/lib/api.js:91`, `fetchPositionEvidence`: loads the scoped evidence response without adding measure identity.
- `backend/app/api/positions.py:302`: active site integration selects reviewed receipt projections, unions database rows by canonical action identity, then applies the governed presentation overlay.
- `backend/app/editorial_presentations/publication_replacement_runtime_v2r.py:198`: the installed V2R wrapper routes the evidence overlay to `reviewed_record.overlay_reviewed_actions`; it does not invent missing measure identifiers. The retained raw row and public projection both lack the structured identifier in this capture.
- `backend/app/api/precomputed.py:361`, `get_governed_position_evidence_rows`: obtains DB rows then calls `_serialize_evidence_row`.
- `backend/app/api/precomputed.py:1975`, `_get_db_governed_position_evidence_rows`: joins `bills` through `rc.bill_id` but selects `b.title`/`b.summary`; it does not select exact bill identity/type/number. This read establishes the code path, not the contents or completeness of the production DB.
- `backend/app/api/precomputed.py:2484`, `_serialize_evidence_row`: outputs title/summary and roll identity; does not serialize structured exact measure identity. Amendment parent fields belong to the amendment-reference contract and are not a substitute for this resolution's exact identity.
- `frontend/lib/selectedIssueExperience.mjs:168`, `getActionPresentation`: target title is the descriptive `bill_title`, parentMeasure empty, actionType Resolution adoption. No measure identifier is returned.
- `frontend/components/ActionReceipt.js:53`: collapsed receipt prints that title and `House · Roll282 · Resolution adoption`; expanded approved prose names H.Con.Res.89.
- `frontend/lib/localRecordFilter.mjs:34`: matcher indexes action title, parentMeasure and chamber/roll only. Neither the approved prose nor source URLs is indexed.
- `frontend/lib/evidenceGrouping.mjs:136` and `selectedIssueExperience.mjs:259` already recognize various explicit bill-ID aliases for grouping, but none is supplied for this target. No grouping contract was changed.

`H.Con.Res. 89`, `hconres89` and `h con res 89` all normalize to `hconres 89`. A controlled diagnostic row with that identifier actually printed in the title matches all three; the unmodified live row matches none. `roll 282` reaches `house:119:2:282`. This separates missing matcher input from normalization failure.

## Reproduction and validation

From repo root:

```powershell
node docs/audits/voter-comprehension-20261013/reproduce-measure-lookup.mjs
node docs/audits/voter-comprehension-20261013/reproduce-measure-lookup.mjs --regression
```

First command is an offline integrity/diagnosis check: validates every manifest file/hash, response/member/scope, exact official roll/member binding, missing identifier fields, successful normalization, actual printed inputs and both query results. It exits0 at the base. Second asserts the desired lookup outcome and exits1 because the expected target is absent from the measure matches; the explicit failing regression is retained, not weakened or added as a failing release gate. It uses the captured actual93-row response without inventing fields or mutating records.

The existing focused localRecordFilter and selectedIssueExperience unit suites pass29/29 at unchanged runtime. The initial sandbox test-worker launch failed with spawnEPERM; an attempted no-isolation option was unsupported by installed Node22.16. The standard command then passed outside that process sandbox. These tooling errors are not product failures. No browser/build loop was rerun for this diagnosis-only change.

The original live desktop/narrow reproduction and audit limits are in [audit.md](audit.md), `audit-steps.json.gz`, the screenshots and `manifest.json`. The audit used existing Windows headless Chromium with actual public responses; expert heuristic assessment only, no human60-second timing/comprehension result. No browser reconnection, permission/configuration changes or access bypass. No contact submission or external transmission of vote context. Captured evidence is historical evidence for this timestamp and does not authorize editorial acceptance/publication.

This draft packet is for independent diagnosis review. No frontend runtime was changed, so no duplicate frontend build/browser release loop or production deployment is warranted. Exact-head reproduction and targeted existing unit contracts are recorded in the review checkpoint; hosted runtime gates apply to a later authorized implementation. No merge is authorized for this increment.
