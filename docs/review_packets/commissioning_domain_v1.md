# Commissioning Domain V1 review packet

## Result

Environment & Energy was commissioned as the first complete new domain outside Economy and Justice/Public Safety. The frozen corpus has eight substantive 119th-Congress House actions, four episodes, four mechanism families, eight selected real-member overlays, and one exact pending persistence batch.

The batch was staged in production only after disposable PostgreSQL and repository gates passed. It remains unpublished: every new artifact is `human_approval_pending`, `not_promoted`, and `production_eligible: false`; the database publication registry and selector are both zero; the frontend production registry remains `Object.freeze([])`.

## Git and selection

- Starting commit and pinned `origin/main`: `08e675e2039d76f16b8c9576e4b5a8254bc44d72`.
- Final commit: the draft pull request head is authoritative. A commit cannot contain its own SHA; the exact head is recorded in GitHub and the delivery message.
- Branch: `codex/commissioning-domain-v1`.
- Selection formula: 30% authoritative-source completeness, 20% episode richness, 15% action diversity, 15% member-vector diversity, 10% bounded scope, and 10% inverse unresolved evidence.
- Selected: Environment & Energy, score 91.

| Rejected domain | Score | Reason |
| --- | ---: | --- |
| National Security & Foreign Policy | 72 | Actions concentrated in one NDAA amendment series; the remaining War Powers votes repeated one mechanism. |
| Education & Workforce | 70 | Only six clearly direct actions and no defensible multi-action episode. |
| Health & Social Policy | 61 | Only four direct substantive passage actions after procedural exclusions. |
| Immigration & Border | 48 | Below the six-action minimum after procedural exclusions. |
| Infrastructure, Technology & Transportation | 32 | Only two safe substantive actions. |

## Actions, evidence, and episodes

Accepted House rolls are 5, 6, 7, 55, 64, 76, 78, and 93. They cover:

1. three bounded stages of H.R. 6938;
2. two separate critical-resource supply proposals;
3. two separate home-energy standards/program proposals; and
4. one federal-lands lead-ammunition/tackle proposal.

Ten candidate actions were rejected with stable reasons: seven procedural motions/rules and three bounded-scope or insufficient-interpretation exclusions. The accepted corpus uses 15 official congressional sources: eight House Clerk roll records, one Congress.gov text record, one CRS appropriations status table, and five House committee reports. All eight actions have exact roll, measure, stage, text/report, result, and member-vote coverage.

The claim map contains 66 supported claims and six supported absences. The absences preserve the lack of safely bounded stage-specific supporter/opponent arguments for the three H.R. 6938 actions. Source conflicts: zero.

No new trait type was required. Six new source-grounded trait values were retained for human review: `package_stage_retention`, `combined_divisions`, `accelerates_domestic_mineral_projects`, `constrains_efficiency_rulemaking`, `repeals_home_energy_programs`, and `limits_land_manager_authority`. One candidate relationship type, `separate_proposals_in_one_policy_family`, remains a shared `human_exception_required` decision.

The corpus was frozen before member selection at semantic hash `da334c1ef783d7cb78ad7187f8fdab7d0df412747af099d3afebee72a6672eaf`.

## Deterministic member cohort

The selector used the most frequent complete vector, greedy maximum-minimum Hamming distance, a lowest-coverage edge, and a same-vector cross-party pair where available. Bioguide ID was the final tie-break; existing editorial references were deprioritized.

| Member | Vector over rolls 5/6/7/55/64/76/78/93 | Purpose |
| --- | --- | --- |
| Aguilar (`A000371`) | Y/Y/Y/N/N/N/N/N | Most frequent complete vector |
| Costa (`C001059`) | Y/Y/Y/Y/Y/N/N/N | Maximum-minimum diversity |
| Cuellar (`C001063`) | Y/Y/Y/Y/Y/Y/N/Y | Selective/divided render |
| Fitzpatrick (`F000466`) | Y/Y/Y/N/N/Y/N/N | Cross-party invariance pair |
| Hunt (`H001095`) | NV/NV/NV/NV/Y/NV/NV/Y | Coverage/Not Voting edge |
| Johnson (GA) (`J000288`) | N/N/N/N/N/N/N/N | Uniform-direction boundary |
| McClintock (`M001177`) | N/N/N/Y/Y/Y/Y/Y | Maximum-minimum diversity |
| Mrvan (`M001214`) | Y/Y/Y/N/N/Y/N/N | Cross-party invariance pair |

The input contained 432 House members, 369 complete Yes/No records, and 42 unique observed vectors.

## Generality and routing

All 432 actual member records and all 42 unique observed vectors were evaluated. Routes were 1 `standard_generation_pass`, 193 `sampled_audit_candidate`, 238 `human_exception_required`, and 0 blocked. Archetypes were 219 bounded episode trajectories, 204 uniform-direction-without-common-throughline records, 8 limited/contested records, and 1 policy-mechanism divide.

All 256 binary Yes/No vectors were enumerated: 32 standard, 18 sampled audit, and 206 human exception. The 17 targeted mutations all produced their expected result: 11 blocked, 2 human exception, and 4 standard pass.

There were zero identity-invariance failures, zero party-invariance failures, zero direction-only winners, and zero member-, party-, title-, domain-, or exact-vector-specific prose branches.

## Preserved failures and corrections

- `COMM-V1-001`: the first H.R. 6938 candidate used an opaque repeated package title. Shared dossiers were corrected with the exact Division A, Divisions B-C, and final-passage stages; opaque-title and reorder mutations prove the generalized correction.
- `COMM-V1-002`: separate critical-resource and home-energy bills were initially treated as independent episodes. They were grouped as source-grounded policy families while preserving mechanism differences; incompatible-episode and unresolved-relationship mutations cover the correction.
- `COMM-V1-003`: the first disposable batch used relationship labels outside migration 0016. PostgreSQL rejected and rolled back the transaction. The graph was mapped to the established immutable vocabulary without a schema change; constraint and orphan probes cover the correction.

Unresolved shared exceptions are the six new trait values, the one candidate relationship type, related-bill episode judgments, and the intentionally absent stage-specific H.R. 6938 argument claims. They are routed once at the shared layer rather than copied per member.

## Persistence proof

- Batch key: `commissioning-domain-v1-environment-energy`.
- Artifacts: 74.
- Relationships: 68.
- Manifest SHA-256: `5821e12ca1e5666ed6ff39b1a9a2402a9f61e067d56dcd69a1870b5a64333c38`.
- Artifact semantic SHA-256: `ab9f580a6a55eafb7848bbb412788202558e78a05cc7b6771714e5a25b0e977d`.
- Relationship semantic SHA-256: `feb267bc4cf3e9dbc47b37c816bd59ddbc31e97fe7908244d6005055edc69cf7`.

Disposable PostgreSQL proved migration-0016 compatibility, exact 74/68 import/export equality, second-apply 0/0 idempotency, conflicting-content rejection, orphan rejection, pending-publication rejection, RLS and privilege boundaries, unchanged canonical fingerprints, exact 74/68 rollback with schema retention, clean reapply, and preservation of the original 71/95 batch.

Production staging inserted exactly 74 artifacts and 68 relationships in one transaction. The second exact apply inserted 0/0. Export matched both semantic hashes. Canonical table fingerprints were unchanged. The original batch remains 71/95. There are 12 total pending presentations (4 existing plus 8 new), 0 publication-registry rows, and 0 selector rows.

## Frontend and validation

The generic review-only registry renders all eight members; four bounded golden cases cover consistent/near-consistent, selective/divided, coverage edge, and human-exception presentations. Each exposes four episodes, eight receipts, official links, service/absence distinctions, and no horizontal overflow. No domain-specific React branch or public route was added.

Validation:

- deterministic builder and 8 commissioning backend tests passed;
- 91 focused backend editorial/persistence regressions passed (1 known Windows byte-pin case deselected);
- 743 tests passed and 9 skipped in the broad backend run; its eight failures were six production-vs-fixture environment expectations and two pre-existing CRLF exact-byte pins, all separately classified and rechecked;
- the fixture-isolated API subset passed 11/11;
- all 140 frontend unit tests passed;
- Playwright passed 13 active cases with 12 intentional skips;
- frontend lint passed with 8 pre-existing hook warnings;
- Next production build passed;
- documentation governance and `git diff --check` passed.

The two byte-pin failures are Windows line-ending normalization issues, not semantic drift. The source/manifest semantic checks, database round trips, and original production seed were independently verified.

## Human decisions required

1. Review and accept or reject the six new trait values and `separate_proposals_in_one_policy_family`.
2. Perform per-field factual/editorial review of the shared dossiers, claim map, supported absences, and episode assignments.
3. Review the eight member propositions and public presentations by route.
4. Decide separately whether any approved artifact becomes a benchmark.
5. Decide separately whether any approved artifact becomes production-eligible and receives a publication-registry entry.

## Limitations and recommendation

The corpus is a bounded eight-action commissioning sample, not a complete account of any member's environmental record. Three actions are stages of one cross-domain appropriations package; related-bill episode judgments remain pending human review; six argument states are intentionally absent; and observed 2026 votes do not establish motive, ideology, or future behavior.

Recommendation: the pipeline is operationally ready for a controlled multi-domain batch expansion after the shared ontology/relationship decisions and editorial route calibration above are reviewed. It is not ready for broad House publication, automatic benchmark promotion, or public database selection.

## Correction V1 addendum

Human inspection after the original staging found `COMM-V1-004`. Roll 5 had
entered Environment & Energy from package context even though the exact
Division A retention action concerned Commerce, Justice, Science, and related
agencies. The same inspection found that unresolved shared traits and episode
relationships were being amplified into member-level human exceptions.

The original result above remains the historical first run. Its accepted action,
freeze, 432-member/256-vector evaluations, 74/68 manifest, hashes, production
state, and original validator behavior were not overwritten. The first run did
not catch this defect automatically.

### Corrected corpus

- Accepted rolls: 6, 7, 55, 64, 76, 78, and 93.
- Rejected roll 5 reason:
  `exact_action_not_materially_environment_energy`.
- Corpus: 7 substantive actions, 6 episodes, 14 official sources, 59 supported
  claims, and 4 supported absences.
- Corrected freeze:
  `885384e2d3dfec9c3acd6b9e8700b752817d4e983758953f6d6d96a2f59709aa`.
- Roll 6 remains bounded to the combined Divisions B-C retention action.
- Roll 7 remains a cross-domain final-passage action whose Environment & Energy
  meaning is limited to Divisions B-C and whose stage stays within the same
  appropriations episode.
- Rolls 55 and 64 are independent episodes under the Critical Mineral Supply
  policy family. Rolls 76 and 78 are independent episodes under the Home Energy
  Policy family. Roll 93 is standalone.
- Episode identity is fixed by the legislative action and mechanism. Nay/Yea,
  Yea/Nay, Nay/Nay, and Yea/Yea remain separate recorded actions and never
  change the hierarchy.

The generic eligibility contract evaluates exact action content independently
from a parent package, other divisions, earlier/later stages, titles, and
measure-wide subjects. Context cannot rescue a domain-ineligible exact action.

### Corrected cohort and routing

The rerun evaluated all 432 members, including 372 complete Yes/No records and
35 unique observed vectors. The deterministic seven-member cohort is A000372,
J000288, C001059, M001231, F000466, H001095, and M001214.

Actual member routes are:

- 173 `standard_generation_pass`;
- 199 `sampled_audit_candidate`;
- 60 `human_exception_required`;
- 0 `blocked`.

All 128 binary vectors were evaluated: 112 standard and 16 sampled audit. No
binary vector required a member exception. The corrected mutation suite
preserves all 17 original cases and adds ten eligibility/routing/hierarchy
cases, for 27/27 passing. Identity, party, direction-only, and member/domain/title/roll/
exact-vector branch failures remain zero.

There are seven de-duplicated shared decisions: six trait values and the roll 7
cross-domain action boundary. They remain shared
`human_exception_required` decisions and prevent approval/publication, but do
not change a member route. Incomplete member evidence still routes to human
exception. The former related-proposal question is resolved by the directed
six-episode/two-family hierarchy.

### Corrected persistence and disposable proof

- Batch:
  `commissioning-domain-v1-environment-energy-corrected-six-episode`.
- Artifacts/relationships: 69/60.
- Manifest:
  `3e1ecd448f086fae52bd69a74303899940f0e417978a82df34970317052752fc`.
- Artifact semantic hash:
  `c2e2f63577f9b7b4224b09c073add4fdccf443dd121d986fda76eb6ec00919ad`.
- Relationship semantic hash:
  `7e4826fc8002799a7b1702363cd6fa1859d95cd5379f3b85cdc63111ae7f1238`.

Disposable PostgreSQL mirrored the 71/95 seed plus original 74/68 batch,
rolled back only the original batch, confirmed the seed remained exact, applied
the corrected 69/60 batch, proved semantic export equality and 0/0 idempotency,
rejected conflicts, orphans, and pending publication, preserved RLS/privileges,
rolled back the corrected batch exactly, and reapplied it with matching hashes.
Two seed-builder byte-pin tests retain their pre-existing Windows CRLF mismatch;
the checked reviewed-seed importer and corrected exact-hash path passed.

The review-only frontend now renders the corrected seven-action fixtures through
the existing generic adapter. It contains no roll 5 receipt. The production
registry remains empty.

The exact prepared production operations are in
`commissioning_domain_v1_production_correction.md`. Neither the original
production rollback nor the corrected production apply was executed.

Additional human decisions are required for rolls 6 and 7, the six traits,
corrected member presentations, explicit production
rollback/reapplication authorization, benchmark promotion, and publication.
