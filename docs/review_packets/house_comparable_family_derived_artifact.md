# House Comparable Family Derived Artifact

Branch: `codex/house-family-derived-artifact`  
Base: `main` at `0f0eac9811351d371ee0da50f9333b22cf8be53f`  
Artifact: `docs/derived/house_comparable_policy_question_families_v1.json`  
Artifact version: `house-comparable-policy-question-families-v1`

## Why This Exists

PR #44 proved that some existing interpreted House evidence can be grouped into reviewed comparable policy-question families, but it also showed that broad issue-domain overlap remains unsafe for continuity/change language.

This milestone promotes that reviewed audit into a durable, versioned derived artifact outside the production schema. The artifact is meant to be diffable, reviewable, and reusable by future internal/backend work without adding tables, migrations, public endpoints, frontend labels, or production writes.

## How It Differs From Production Schema

- It is a checked-in JSON artifact, not a database table.
- It is derived from the reviewed PR #44 audit artifacts and current read-only roll-call identity validation.
- It does not change `vote_classifications`, `vote_interpretations`, support/opposition counts, readiness, alignment, APIs, or frontend output.
- It can be regenerated after future evidence expansion by rerunning `scripts/house_comparable_family_artifact.py`.

## Safe Uses

- Internal review of comparable House policy-question families.
- Future read-only internal accessor work for `Record Across Congresses`.
- Limited-profile eligibility checks based on reviewed `directly_comparable` and `conditionally_comparable` common families.
- Audit reconciliation against PR #44 totals.

## Unsafe Uses

- It does not authorize `Continuity / Change` product framing.
- It does not authorize behavioral movement, ideological movement, causal, motive, endorsement, corruption, or vote-recommendation claims.
- It does not authorize frontend comparison copy or public labels saying an official changed position.
- It does not make `related_but_not_comparable` or `ungrouped` rows eligible for future comparison output.
- It does not permit grouping by broad issue domain alone.

## Artifact Contents

The artifact includes:

- version and schema metadata;
- source PR #44 references;
- methodology summary;
- family-model, product-framing, and readiness recommendations;
- 15 reviewed candidate families;
- comparability status for each family;
- governing question, inclusion/exclusion criteria, rationale, and caveats;
- roll-call IDs grouped by Congress with chamber, Congress, session, and roll number preserved;
- measures and amendment identity signals where available;
- representative examples;
- future limited `Record Across Congresses` eligibility flags;
- explicit non-authorization of continuity/change claims;
- full ungrouped roll-call inventory marked ineligible.

## Reconciliation

The derived artifact reconciles to PR #44:

| Metric | Value |
|---|---:|
| Target interpreted roll calls | 306 |
| Candidate families | 15 |
| Common families | 13 |
| Directly comparable common families | 4 |
| Conditionally comparable common families | 7 |
| Related but non-comparable clusters | 4 |
| Ungrouped roll calls | 225 |
| Substantive vote rows covered by candidate families | 33,825 |
| Substantive vote-row coverage | 26.59% |

## Families By Status

Directly comparable common families:

- `env_hunting_fishing_access`
- `jps_federal_officer_service_weapons`
- `jps_law_enforcement_safety_reporting`
- `nsf_annual_defense_authorization`

Conditionally comparable common families:

- `eco_government_funding_packages`
- `env_critical_minerals_supply`
- `env_home_appliance_energy_rules`
- `jps_law_enforcement_support_resolutions`
- `jps_violent_offenders_pretrial_detention`
- `nsf_ukraine_assistance_restrictions`
- `nsf_war_powers_removal_resolutions`

Related but not comparable clusters:

- `eco_budget_reconciliation_process`
- `eco_small_business_finance_regulation`
- `env_energy_permitting_fossil_infrastructure`
- `jps_fentanyl_scheduling_penalties`

Ungrouped:

- 225 target interpreted roll calls remain excluded from eligibility.

## Validation

Builder validation confirmed:

- every artifact roll-call ID exists in the current target evidence universe;
- Congress, chamber, session, and roll-call identity are preserved;
- no 119th row appears in a 118th slot or vice versa;
- all directly and conditionally comparable families contain rows in both Congresses;
- related and ungrouped rows are excluded from future limited comparison eligibility;
- procedural, limited, and not-voting evidence remain non-counting;
- PR #44 totals reconcile;
- the artifact does not imply broad continuity/change readiness.

Targeted tests:

```text
python -m pytest backend\tests\test_house_comparable_family_artifact.py backend\tests\test_house_comparable_policy_question_audit.py
```

Result: `11 passed`.

No frontend validation was required because no frontend runtime code changed.

## Regeneration

After future evidence expansion or reviewed family changes:

1. Rerun or update the comparable-family audit source artifact.
2. Rerun:

```text
python scripts\house_comparable_family_artifact.py
```

3. Run targeted artifact tests.
4. Review diffs in `docs/derived/house_comparable_policy_question_families_v1.json`.
5. Update this review packet or create a successor packet if the artifact version changes.

## Product Framing

`Record Across Congresses` remains the correct framing. The artifact records where future limited comparisons may be technically eligible, but the strict burden controls from PR #44 still exclude all current officials under a full caveated contract, and the artifact must not produce public continuity/change conclusions.

## Recommended Next Milestone

Recommendation: **Build a read-only backend/internal accessor for the derived artifact.**

This is the smallest useful next step because it lets future backend or product work consume the reviewed artifact without adding production schema, changing frontend language, or broadening family coverage before the access pattern is understood.
