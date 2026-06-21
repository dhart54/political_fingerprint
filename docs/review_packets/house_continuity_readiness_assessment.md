# House Continuity Readiness Assessment

Branch: `codex/house-continuity-readiness-assessment`  
Base: `main` at `61f009f` (`PR #42`; includes `PR #41` at `0edb9df`)  
Recommendation: `NOT READY`

## Artifacts

- Machine-readable analysis: `docs/analysis/house_continuity_readiness_analysis.json`
- Threshold table: `docs/analysis/house_continuity_thresholds.csv`
- Profile validation table: `docs/analysis/house_continuity_profile_examples.csv`
- Reusable read-only script: `scripts/house_continuity_readiness_analysis.py`

The script is permanent because this readiness question should be rerunnable after future evidence expansion. It runs in a read-only database transaction and writes local artifacts only.

## Executive Conclusion

Current 118th and 119th House evidence is strong enough to show a "record across Congresses" view, but not strong enough to launch continuity/change summaries.

There is broad member-level coverage: 367 of 441 current House officials have substantive interpreted evidence in both Congresses, and 365 clear a simple "3 rows per Congress in at least one common domain" threshold. That apparent readiness is misleading. The structured data does not yet prove materially comparable policy questions; most shared `issue_facet` values are broad-domain labels, not subtopic matches. The 118th evidence is also much heavier on amendments, while many 119th domains are mostly final-passage or other floor actions. That means apparent change can often be explained by agenda composition and vote-type mix.

Recommended first framing: `Record Across Congresses`, not `Continuity / Change`.

## Coverage Inventory

Public `/metadata/coverage` and `/coverage/metadata` both returned database-backed totals:

| Field | Public value |
|---|---:|
| roll_call_count | 2,259 |
| eligible_roll_call_count | 627 |
| source_url_share | 1.0 |
| window_start | 2024-03-13 |
| window_end | 2026-06-19 |

The roll-call and eligible counts reconcile with production. The public `window_start` is the fingerprint precompute window, while the raw scoped roll-call inventory begins earlier. This is a semantics difference, not a data mismatch.

House-only roll-call universe:

| Congress | House roll calls | Eligible | Interpreted | Limited | Procedural | Ineligible |
|---|---:|---:|---:|---:|---:|---:|
| 118 | 1,208 | 414 | 305 | 903 | 254 | 794 |
| 119 | 555 | 121 | 70 | 198 | 182 | 434 |

House member vote rows:

| Congress | Cast vote rows | Eligible participation | Substantive interpreted yea/nay | Interpreted not-voting | Interpreted present |
|---|---:|---:|---:|---:|---:|
| 118 | 515,823 | 176,973 | 126,221 | 4,475 | 35 |
| 119 | 239,897 | 52,310 | 29,651 | 625 | 25 |

House official coverage:

| Group | Profiles | 118th substantive | 119th substantive | Both | One Congress only | None |
|---|---:|---:|---:|---:|---:|---:|
| Current House | 441 | 367 | 441 | 367 | 74 | 0 |
| Former House | 77 | 76 | 6 | 5 | 72 | 0 |

Common-domain coverage:

| Metric | Count |
|---|---:|
| Officials with at least one common substantive domain | 372 |
| Officials with multiple common substantive domains | 368 |
| Current officials with both-Congress substantive evidence | 367 |

Important semantic resolution: identical public validation counts across officials are shared evidence-universe counts. In profile `scope_metadata`, `eligible_roll_call_count` means distinct eligible roll calls in the selected scope, not that official's vote-row count. Official-specific records require the `votes_cast` join and are reflected in position/evidence rows.

## Scope Semantics

Public scoped profile checks for Valerie Foushee confirmed:

| Scope | Congresses | Eligible roll-call count | Window |
|---|---|---:|---|
| `scope=118` | `[118]` | 433 | 2023-01-09 to 2024-12-21 |
| `scope=119` | `[119]` | 194 | 2025-01-03 to 2026-06-16 |
| `scope=all` | `[118, 119]` | 627 | 2023-01-09 to 2026-06-16 |

No cross-Congress leakage was found in scoped metadata. The label could still be clearer because universe-level counts appear inside profile responses.

## Domain Comparability

No domain is strongly comparable. Four are conditionally comparable only with explicit issue-by-issue review. Four are not currently comparable.

| Domain | Classification | 118 substantive rows | 119 substantive rows | Officials with both | Main reason |
|---|---|---:|---:|---:|---|
| Economy/Taxes | Conditionally comparable | 21,669 | 5,080 | 368 | Budget/tax overlap exists, but 118 is amendment-heavy and 119 includes budget resolution/concurrence mix. |
| Environment/Energy | Conditionally comparable | 9,930 | 4,166 | 365 | Some energy/minerals overlap, but 118 amendment mix differs from 119 final/resolution mix. |
| National Security/Foreign | Conditionally comparable | 51,242 | 11,144 | 367 | Largest evidence base, but questions range from Ukraine/Israel/Iran to war-powers and defense amendments. |
| Justice/Public Safety | Conditionally comparable | 19,337 | 4,629 | 367 | Law enforcement/DC crime/bail themes overlap, but subtopics differ. |
| Health/Social | Not currently comparable | 5,834 | 1,264 | 361 | 118 health workers/COVID/choice mix differs from 119 Medicaid/child-care/pregnancy measures. |
| Education/Workforce | Not currently comparable | 6,570 | 2,522 | 362 | 118 school-facility/choice/resolution mix differs from 119 school-systems/ghost-students/worker education bills. |
| Immigration/Border | Not currently comparable | 4,543 | 846 | 365 | 118 border/Biden policy/Hamas-terrorists questions differ from 119 DC compliance/Haiti TPS. |
| Infrastructure/Tech/Transport | Not currently comparable | 7,096 | 0 | 0 | No 119 substantive interpreted evidence in the analysis window. |

Shared issue domain alone is not sufficient. The structured topic field often mirrors the broad domain, so material comparability currently depends on manual review of questions, bill titles, vote types, and source-grounded summaries.

## Agenda-Difference Risks

Concrete examples:

- Valerie Foushee's public `scope=all` Economy/Taxes comparison reports a different pattern: 118th `mixed` on 51 reviewed Yes/No rows versus 119th `mostly_opposed` on 11. Underlying examples differ: 118 includes the Family and Small Business Taxpayer Protection Act and Lower Energy Costs Act amendments; 119 includes the budget resolution, Senate amendment concurrence, and American Entrepreneurs First Act.
- Health/Social is unsafe for change language: 118 examples include CHOICE/COVID/health-worker questions, while 119 examples include Medicaid, child-care violations, and pregnancy/family-support measures.
- Infrastructure/Tech/Transport cannot support cross-Congress comparison because the current analysis found 118 substantive rows and zero 119 substantive interpreted rows.
- Amendment/final-passage mix is materially different. Economy/Taxes has 17,534 amendment rows in the 118th versus 861 in the 119th; Health/Social has 2,910 118th amendment rows and no 119th amendment rows.
- Member tenure matters: 74 current House officials have only 119th substantive evidence, mostly newer members.
- Not-voting can distort sparse profiles: Aumua Amata Coleman Radewagen has a meaningful not-voting burden and only one common domain, so continuity/change language is unsafe.

These are agenda and evidence-composition risks, not behavioral conclusions.

## Threshold Simulation

| Contract | Eligible current officials | Share of current House | Primary exclusions | Risk |
|---|---:|---:|---|---|
| Any common domain, 1 row per Congress | 367 | 83.22% | 74 no common domain | High; broad domain overlap hides agenda differences. |
| 3 rows per Congress in one common domain | 365 | 82.77% | 74 no common domain; 2 below row threshold | High; still domain-only. |
| 3 rows per Congress in multiple domains | 361 | 81.86% | 78 no common domain; 2 below row threshold | High; still domain-only. |
| Add limited/procedural and not-voting controls | 0 | 0.00% | 365 burden controls | Shows current loaded evidence contains too much non-counting/limited context for a strict contract. |
| Add comparable topic and opportunity balance | 0 | 0.00% | 365 burden controls | Safer but currently yields no qualifying profiles. |
| Proposed limited-profile contract | 0 | 0.00% | 361 burden controls; 78 no common domain | Not viable for product launch now. |

Coverage-maximizing thresholds would produce many profiles, but they would also produce high false-change risk. The stricter contracts protect trust and currently produce no qualifying profiles.

## Profile Validation

| Profile | Role in validation | 118 basis | 119 basis | Common domains | Claim allowed | Safest framing |
|---|---|---:|---:|---|---|---|
| Valerie P. Foushee | Required | 302 | 67 | 7 | No | Record across Congresses; issue details only. |
| Aaron Bean | Required | 304 | 70 | 7 | No | Record across Congresses; issue details only. |
| Austin Scott | Strong evidence both | 305 | 70 | 7 | No | Strong record volume, but not continuity/change. |
| Ben Cline | Apparent continuity | 305 | 70 | 7 | No | Similar-looking patterns still need comparable-question proof. |
| Thomas R. Suozzi | Apparent change | 126 | 70 | 7 | No | Apparent change may reflect agenda and tenure/evidence mix. |
| Charles J. "Chuck" Fleischmann | Agenda-difference unsafe | 305 | 70 | 7 | No | Good volume, but broad-domain/subtopic mismatch remains. |
| Allred | 118th-only | 305 | 0 | 0 | No | Prior record only. |
| Abraham J. Hamadeh | 119th-only | 0 | 68 | 0 | No | Recent record only. |
| James Gallagher | Sparse profile | 0 | 1 | 0 | No | Insufficient evidence. |
| Aumua Amata Coleman Radewagen | Not-voting burden | 112 | 12 | 1 | No | Single-domain record with absence caveat. |

## Product Framing Assessment

| Option | Assessment |
|---|---|
| `Continuity / Change` | Not defensible now. It implies stable comparable opportunities and risks overstating behavioral movement from agenda differences. |
| `Record Across Congresses` | Best current framing. It accurately says evidence exists across Congresses without claiming movement. |
| `Compare Prior and Recent Congress` | Usable only as an issue-by-issue evidence browser with strong "not enough to claim change" language. |
| No cross-Congress summary yet | Safest if the product cannot avoid change implications in the UI. |

## Proposed Eligibility Contract

Do not launch continuity/change until all of the following are true for a profile and domain:

- At least 3 substantive interpreted Yes/No rows in each Congress for the same issue domain.
- At least 2 common domains for any profile-level cross-Congress summary.
- A reviewed material policy-question match, not just shared broad domain.
- Comparable vote-type mix or explicit labeling that the vote types differ.
- Support and opposition opportunities present in both Congresses.
- Not-voting share below 20% of interpreted eligible rows.
- Limited/procedural/non-counting share below 50% in the relevant comparison set.
- Service overlap confirms the official had real opportunity in both Congresses.
- Procedural and limited rows remain non-counting; not-voting remains excluded from support/opposition.

Expected current coverage under this contract: 0 current House officials, 0.00%.

## Validation

- Read-only production DB analysis completed; transaction reported `transaction_read_only = on`.
- No production tables or derived outputs changed.
- Public `/metadata/coverage` and `/coverage/metadata` reconciled to `roll_call_count = 2259` and `eligible_roll_call_count = 627`.
- `scope=118`, `scope=119`, and `scope=all` semantics validated on the public positions endpoint.
- No scope leakage found in metadata.
- Not-voting remained excluded from substantive Yes/No evidence rows.
- Procedural and limited evidence remained non-counting.
- Targeted test for analysis tooling: `python -m pytest tests\test_house_continuity_readiness_analysis.py` passed (`3 passed`).
- Previously blocked tmp-path persistence test: sandbox rerun reproduced `PermissionError: [WinError 5]`; escalated rerun passed (`1 passed`). This confirms the prior failure is local sandbox filesystem-specific.

Frontend validation was not required because no frontend runtime code changed.

## Unresolved Risks

- Structured topic fields are not granular enough to prove material policy-question comparability.
- Existing public comparison wording can say "different" or "consistent" from broad-domain patterns; that may be stronger than this readiness review supports for a future continuity/change feature.
- Strict burden controls currently exclude all profiles because loaded evidence includes large limited/procedural/non-counting surface area.
- Current 119th evidence is shallower than 118th evidence in several domains.
- Manual examples are source-grounded but not a substitute for a durable measure-family model.

## Smallest Next Milestone

Create a read-only comparable-question audit layer for House evidence:

- Add or derive a reviewed `policy_question_family` / comparable-measure-family artifact for existing interpreted rows.
- Start with the four conditionally comparable domains: Economy/Taxes, Environment/Energy, National Security/Foreign, and Justice/Public Safety.
- Re-run threshold simulation using comparable families rather than broad domains.
- Do not implement frontend continuity/change language until that audit yields a nonzero, trustworthy qualifying set.

Final decision: `NOT READY`.
