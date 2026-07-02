# Curated Theme Coverage Expansion Review Packet

## Intent

PR #65 established the safety contract: top-level interpretation copy may use curated themes, safe fallbacks, counts, and bounded context, but not raw evidence or audit fields. This pass improves quality inside that boundary by expanding explicit curated theme coverage where the facet itself safely supports the theme.

## Audit Summary

The audit covered active frontend public-copy helpers/tests, `PositionByIssue` interpretation surfaces, the PR #65 plan/review packet, Valerie review packets, and the comparable reviewed House evidence dataset.

| Facet id / label | Domain | Current public theme | Curated now | Generic fallback now | Recommended theme | Confidence | Decision |
|---|---|---:|---:|---:|---|---|---|
| `environment_energy` | Environment & Energy | `environment energy` | no | no | `environment and energy measures` | high | add |
| `economy_taxes` | Economy & Taxes | `economy taxes` | no | no | `fiscal and tax measures` | high | add |
| `justice_public_safety` | Justice & Public Safety | `justice public safety` | no | no | `public-safety and legal-policy measures` | high | add |
| `national_security_foreign` | National Security & Foreign Policy | `national security foreign` | no | no | `national-security and foreign-policy measures` | high | add |
| `Motion to commit` / `motion_to_commit` | National Security & Foreign Policy | `other reviewed national-security measures` | yes | yes | `motions to commit` | high | replace generic explicit mapping |
| `House amendment vote` | Multiple | `House amendment vote` | no | no | force domain fallback / no substance mapping | skip | no substance without raw vote text |
| `administrative_law_and_regulatory_procedures` | Justice & Public Safety | `administrative law and regulatory procedures` | no | no | leave unchanged | medium | safe phrase, but current use is ambiguous amendment context |
| `budget_reconciliation_and_debt_limit` | Economy & Taxes | `budget framework and reconciliation` | yes | no | keep existing | high | no change |
| `small_business_loan_eligibility` | Economy & Taxes | `small-business loan eligibility` | yes | no | keep existing | high | no change |
| `military_construction_and_va_appropriations` | Economy & Taxes | `military and veterans appropriations` | yes | no | keep existing | high | no change |
| `temporary_government_funding` | Economy & Taxes | `temporary government funding` | yes | no | keep existing | high | no change |
| `government_funding_and_shutdown` | Economy & Taxes | `shutdown-ending government funding` | yes | no | keep existing | high | no change |
| `small_business_regulation` | Economy & Taxes | `small-business regulatory-cost limits` | yes | no | keep existing | high | no change |
| `appropriations_amendment` | Economy & Taxes | `appropriations amendments` | yes | no | keep existing | medium | no change |
| `conference_instruction` | Economy & Taxes | `conference instructions` | yes | no | keep existing | medium | no change |
| `fentanyl_scheduling_and_penalties` | Justice & Public Safety | `fentanyl scheduling and penalty thresholds` | yes | no | keep existing | high | no change |
| `federal_law_enforcement_equipment` | Justice & Public Safety | `federal law-enforcement retired weapon purchasing` | yes | no | keep existing | high | no change |
| `law_enforcement_safety_reporting` | Justice & Public Safety | `law-enforcement safety and wellness reporting` | yes | no | keep existing | high | no change |
| `dc_police_pursuit_policy` | Justice & Public Safety | `D.C. police pursuit policy` | yes | no | keep existing | high | no change |
| `dc_policing_reform_repeal` | Justice & Public Safety | `D.C. policing reform repeal` | yes | no | keep existing | high | no change |
| `Defense authorization` / `defense_authorization` | National Security & Foreign Policy | `defense authorization legislation` | yes | no | keep existing | high | no change |
| `Defense authorization amendment` | National Security & Foreign Policy | `defense authorization amendments` | yes | no | keep existing | high | no change |
| `foreign_military_sales` | National Security & Foreign Policy | `foreign military sales` | yes | no | keep existing | high | no change |
| `Veterans cemetery administration` | National Security & Foreign Policy | `veterans cemetery administration` | yes | no | keep existing | high | no change |
| `House floor procedure` | National Security & Foreign Policy | `procedural House floor action` | yes | no | keep existing | high | no change |
| `house_of_representatives` | Procedural rows | `procedural House rule or motion` | yes | no | keep existing | high | no change |
| `floor_rule_for_multiple_bills` | Education & Workforce | `procedural floor rules for multiple bills` | yes | no | keep existing | high | no change |
| `floor_rule_for_energy_and_budget_measures` | Environment & Energy | `procedural floor rules for energy and budget measures` | yes | no | keep existing | high | no change |
| `floor_procedure_on_hydrogen_vehicle_rule` | Environment & Energy | `procedural floor action on hydrogen vehicle rules` | yes | no | keep existing | high | no change |
| `federal_employee_collective_bargaining` | Education & Workforce | `federal employee collective-bargaining rules` | yes | no | keep existing | high | no change |
| `school_foreign_funding_and_contract_restrictions` | Education & Workforce | `school foreign-funding and contract restrictions` | yes | no | keep existing | high | no change |
| `school_foreign_influence_parent_notifications` | Education & Workforce | `school foreign-influence parent notifications` | yes | no | keep existing | high | no change |
| `natural_gas_pipeline_and_lng_review_coordination` | Environment & Energy | `natural gas pipeline and LNG review coordination` | yes | no | keep existing | high | no change |
| `health_insurance_premiums` / `health_insurance_premium_assistance` | Health & Social Policy | `health insurance premium assistance` | yes | no | keep existing | high | no change |
| `medicaid_payment_rules_for_minor_health_procedures` / `medicaid_payment_rules` | Health & Social Policy | `Medicaid payment rules for specified minor health procedures` | yes | no | keep existing | high | no change |
| `china_related_security_restrictions` | National Security & Foreign Policy | `China-related security restrictions` | yes | no | keep existing | high | no change |
| `iran_related_security_measures` | National Security & Foreign Policy | `Iran-related security measures` | yes | no | keep existing | high | no change |
| `war_powers_votes` | National Security & Foreign Policy | `war-powers votes` | yes | no | keep existing | high | no change |

## Mappings Added

- `economy_taxes`: `fiscal and tax measures`
- `environment_energy`: `environment and energy measures`
- `justice_public_safety`: `public-safety and legal-policy measures`
- `national_security_foreign`: `national-security and foreign-policy measures`
- `Motion to commit` / `motion_to_commit`: `motions to commit`

## Mappings Skipped

- `House amendment vote`: skipped because the facet is only a vote type. Mapping it to a policy theme would require reading raw vote descriptions, which is outside this milestone and would weaken the boundary. It now forces the normal domain fallback instead of surfacing as a top-level short-label theme.
- `administrative_law_and_regulatory_procedures`: left unchanged because the safe short label is acceptable and the current reviewed use is ambiguous amendment context.

## Before / After Examples

- Before: `national security foreign`; after: `national-security and foreign-policy measures`.
- Before: `environment energy`; after: `environment and energy measures`.
- Before: `other reviewed national-security measures` for `Motion to commit`; after: `motions to commit`.

## Safety Preservation

This pass does not change the PR #65 safety contract. Raw fields such as `what_happened`, `why_it_mattered`, `plain_english_summary`, `description`, `question`, `uncertainty_note`, `interpretation_reason`, `classification_reason`, and `source_basis` remain ineligible for top-level public themes.

## Tests Added Or Updated

- Public theme helper tests for the new high-confidence mappings.
- Regression coverage that broad domain facets no longer surface awkward short-label fallbacks.
- Regression coverage that `House amendment vote` remains unmapped and resolves to the domain fallback rather than being converted into a substance claim or public short-label theme.
- Source-level check that every curated theme in `PUBLIC_THEME_BY_FACET` passes `isSafePublicThemePhrase`.
- Issue-overview regression showing broad facet copy and `motions to commit` appear without raw evidence leakage.

## Validation Results

- `node --test lib\*.test.mjs`: passed, 70/70.
- `npm run lint`: passed with 8 existing React hook dependency warnings and 0 errors.
- `npm run build`: passed with the same 8 existing React hook dependency warnings.
- `rg -n "INTERNAL_API_TOKEN|X-Internal-API-Token|/internal/record-across-congresses" .next\static`: no matches.

## Rendered Validation

- Local built app shell rendered at `http://127.0.0.1:3000`.
- Desktop default viewport: no horizontal overflow.
- Mobile `390x844`: no horizontal overflow.
- Limitation: Valerie Foushee National Security could not be rendered locally because ZIP `27701` is not in the loaded local ZIP map. Source-level tests cover the curated theme and unsafe-string boundaries.
- Note: the generic Evidence helper line still says `classification reason`; that is receipt-affordance copy, not top-level issue interpretation copy.
