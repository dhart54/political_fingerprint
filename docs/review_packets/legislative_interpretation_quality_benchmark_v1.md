# Legislative Interpretation Quality Benchmark V1 Review Packet

## Summary

The benchmark contains **48 unique official roll calls**: 32 House substantive cases, 8 Senate substantive cases, and 8 explicit ambiguity/procedure controls. All gold interpretations and issue syntheses remain machine-draft candidates pending human source verification.

## Why Current Interpretations Feel Generic

The failure is usually not a false topic label. It is the absence of the policy baseline, concrete government lever, affected entity, magnitude/timing, attributed dispute, and lifecycle. Older rows often restate an official title; newer reviewed rows contain useful mechanism and status detail. The public-copy safety boundary then deliberately removes raw row fields from top-level synthesis, so even strong stored detail can collapse to a short curated facet or generic domain theme.

## Existing Pipeline Map

1. Official House/Senate and Congress.gov records enter chamber adapters and source caches.
2. Deterministic classifiers decide domain, vote eligibility, and procedural/limited-context treatment.
3. `vote_interpretations` stores status, support/opposition positions, reviewed plain-language fields, source basis, uncertainty, and review metadata.
4. Manual export/import packets support supervised review; LLM text does not decide eligibility or vote meaning.
5. Backend issue reads aggregate only eligible interpreted Yes/No rows; procedural and not-voting rows remain excluded.
6. Frontend evidence cards may show reviewed row fields, while top-level issue copy uses curated safe themes and generic fallbacks.
7. Golden-render fixtures exercise the current public surface deterministically.

## Benchmark Composition

- Cohorts: `{"control": 8, "house_substantive": 32, "senate_substantive": 8}`
- Chambers (controls included): `{"house": 36, "senate": 12}`
- Vote types: `{"amendment": 20, "appropriations": 1, "final_passage": 18, "motion": 4, "other": 3, "rule_or_procedural_control": 2}`
- Domains: `{"ECONOMY_TAXES": 4, "EDUCATION_WORKFORCE": 6, "ENVIRONMENT_ENERGY": 1, "HEALTH_SOCIAL": 14, "IMMIGRATION_BORDER": 1, "INFRASTRUCTURE_TECH_TRANSPORT": 4, "JUSTICE_PUBLIC_SAFETY": 6, "NATIONAL_SECURITY_FOREIGN": 12}`

## Source Hierarchy

The benchmark prefers official chamber and Congress.gov records, then CRS, CBO, committee reports, measure text, the Congressional Record, executive-agency material, attributed official advocacy, and other directly relevant government reports. Search snippets are never evidence, and advocacy is never presented as neutral fact.

## Dossier Contract

The reusable hierarchy is measure dossier → amendment dossier → roll-call interpretation → member-specific vote context → issue-synthesis evidence unit. Unknown facts remain `insufficient_official_evidence`; genuinely inapplicable fields use `not_applicable`. Structural claim maps are mandatory, and human source verification remains a separate status.

## Quality Rubric And Fatal Defects

Twelve dimensions score 0–4 (48 maximum). Fatal overrides cover reversed Yea/Nay mechanics, procedural/final confusion, false enactment, invented effects or affected groups, motive, neutralized advocacy, under-evidenced patterns, title restatements used as explanation, and unmapped material claims.

## Current-Quality Scorecard

| Surface | Mean / 48 | Tier distribution | Fatal cases | Strong+ |
|---|---:|---|---:|---:|
| Stored interpretation | 39.6 | `{"strong": 34, "useful": 14}` | 0 | 70.8% |
| Public evidence card | 33.8 | `{"strong": 34, "unacceptable": 14}` | 0 | 70.8% |
| Candidate gold | 40 | `{"generic_but_accurate": 8, "strong": 39, "useful": 1}` | 0 | 81.2% |

Thresholds are benchmark hypotheses, not production acceptance rules. Fatal defects override the numeric score. Candidate scores are diagnostic and do not confer editorial approval.

## Genericity Taxonomy

- `official_title_restatement`: 0; examples: none in V1 sample.
- `procedural_paraphrase_without_policy_effect`: 6; examples: house-2025-343, house-2025-308, senate-119-1-266.
- `generic_funding_provisions_language`: 0; examples: none in V1 sample.
- `generic_supported_or_opposed_measure_language`: 0; examples: none in V1 sample.
- `missing_policy_baseline`: 48; examples: house-2025-310, house-2025-285, house-2025-281.
- `missing_implementation_mechanism`: 8; examples: house-2025-343, house-2025-344, house-2025-308.
- `missing_affected_group`: 48; examples: house-2025-310, house-2025-285, house-2025-281.
- `missing_magnitude_or_timeline`: 37; examples: house-2025-310, house-2025-182, house-2025-156.
- `missing_credible_alternative`: 48; examples: house-2025-310, house-2025-285, house-2025-281.
- `missing_outcome`: 29; examples: house-2025-320, house-2025-262, house-2025-260.
- `generic_caveat_overwhelms_explanation`: 1; examples: house-2025-344.
- `issue_domain_substituted_for_substantive_theme`: 0; examples: none in V1 sample.
- `long_evidence_list_without_synthesis`: 0; examples: none in V1 sample.
- `repetitive_count_language`: 0; examples: none in V1 sample.
- `safe_but_content_free_fallback`: 0; examples: none in V1 sample.
- `unsupported_specificity`: 0; examples: none in V1 sample.
- `overbroad_pattern_claim`: 0; examples: none in V1 sample.

## Field, Source, And Comprehension Completeness

- Dossier field completeness: 40.0%.
- Claim/source-map structural completeness: 100.0%.
- Four-question answerability: 70.8%.
- `insufficient_official_evidence` is counted as incomplete, not silently converted into a claim.

## Public-Rendering Information Loss

Raw reviewed evidence fields are correctly blocked from uncontrolled top-level use. Evidence cards retain some reviewed meaning, but issue synthesis uses curated themes. The lost information is typically the baseline, mechanism, affected entities, amounts/timing, arguments, later status, and exact yea/nay translation. The future contract should allow human-approved claim objects—not arbitrary raw text—to flow to top-level copy.

## Issue-Synthesis Findings

Eight representative/domain slices are included. Current synthesis distribution: `{"generic_but_accurate": 8}`. Candidate distribution: `{"generic_but_accurate": 1, "strong": 7}`. The deterministic minimum is 3 substantive interpreted votes; 6 procedural/control appearances are explicitly excluded. Each candidate claim maps to included votes and remains subject to human review. Sparse slices must say evidence is limited rather than assert a pattern.

## Measure Reuse Findings

The 48 roll calls reduce to an estimated 19 reusable research units under a conservative grouping. 20 amendments still require amendment dossiers; 8 controls can reference a parent dossier without inheriting its substantive meaning. Estimated research/review reduction: 60.4%.

Recommended hierarchy: measure dossier → amendment dossier → roll-call interpretation → member-specific vote context → issue-synthesis evidence unit.

## Human Review Requirements

Machine generation may draft paraphrases, propose claim links, identify missing fields, and calculate rubric diagnostics. Human reviewers must verify policy mechanism, affected entities, yea/nay mechanics, advocacy attribution, outcome/later status, and every issue-pattern conclusion before `gold_benchmark` status. Automated scoring does not replace editorial judgment.

## Comprehension Protocol

Each case asks what Congress was deciding, what would change, who/what was affected, and what the member's vote meant. A candidate cannot be strong unless questions 1, 2, and 4 are answerable. Later user testing should randomize current versus candidate copy, prohibit source lookup during the first pass, code critical misconceptions, and then test whether receipts correct misunderstandings.

## Recommended Next Implementation Milestone

**Valerie Foushee Economy & Taxes Interpretation Quality V2**: add the dossier and claim-map objects for one existing golden slice; source-verify the vote mechanics; expose only human-approved public claims; update vote cards and one issue synthesis; then run rendered comprehension checks before scaling coverage.

## Production Safety

No production connection, database write, schema/migration, interpretation import, API change, frontend change, runtime change, alignment/readiness change, or paid model call occurred.

## Stop Conditions And Limitations

- Machine-draft candidates are not approved gold.
- Missing official evidence remains explicit.
- Source-map completeness here is structural; editorial source verification remains required.
- Publication must stop if unrelated artifacts would be staged.

## Detailed Breakdowns

### Vote type

| Group | Cases | Stored mean | Public mean | Candidate mean |
|---|---:|---:|---:|---:|
| amendment | 20 | 41.2 | 40.3 | 41.8 |
| appropriations | 1 | 41 | 41 | 42 |
| final_passage | 18 | 37.1 | 22.4 | 41.8 |
| motion | 4 | 41 | 41 | 31 |
| other | 3 | 41 | 41 | 34.7 |
| rule_or_procedural_control | 2 | 41 | 41 | 31 |

### Issue domain

| Group | Cases | Stored mean | Public mean | Candidate mean |
|---|---:|---:|---:|---:|
| ECONOMY_TAXES | 4 | 42 | 41.5 | 43.5 |
| EDUCATION_WORKFORCE | 6 | 37.5 | 28 | 37.8 |
| ENVIRONMENT_ENERGY | 1 | 34 | 15 | 41 |
| HEALTH_SOCIAL | 14 | 40.1 | 35.6 | 40.5 |
| IMMIGRATION_BORDER | 1 | 34 | 15 | 41 |
| INFRASTRUCTURE_TECH_TRANSPORT | 4 | 41 | 41 | 31 |
| JUSTICE_PUBLIC_SAFETY | 6 | 36.8 | 19.3 | 40.8 |
| NATIONAL_SECURITY_FOREIGN | 12 | 41.2 | 39.8 | 41.8 |

### Chamber

| Group | Cases | Stored mean | Public mean | Candidate mean |
|---|---:|---:|---:|---:|
| house | 36 | 39.2 | 31.3 | 40.6 |
| senate | 12 | 41 | 41 | 38.3 |

### Review mode

| Group | Cases | Stored mean | Public mean | Candidate mean |
|---|---:|---:|---:|---:|
| deterministic_control | 8 | 41 | 41 | 31 |
| reviewed | 40 | 39.4 | 32.3 | 41.8 |

## Tests

Validation commands and final results are recorded in the active plan and PR body after execution.

## Files Changed

This milestone adds only benchmark scripts, focused tests, generated benchmark/rubric artifacts, design contracts, the active plan, and review packets.
