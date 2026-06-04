# Facet Label Cleanup Review

Generated: 2026-06-03

Scope: narrow frontend scale-readiness cleanup. This pass adds voter-facing issue-facet labels/descriptions for high-volume raw or procedural facets identified in `docs/review_packets/interpretation_scale_readiness_audit.md`.

No backend/API behavior changed. No new interpretation records were added. No curated roll-number summaries were added.

## Summary

The issue-overview object already groups evidence rows by `issue_facet`. Before this pass, many high-volume facets outside the Valerie / Economy and Valerie / Justice slices fell through to raw labels such as `floor_rule_for_multiple_bills`, `house_of_representatives`, or `Defense authorization amendment`.

This pass adds reviewed labels and plain descriptions for the highest-impact unmapped facets so overview objects and measure groups can use voter-facing wording while preserving evidence limits for procedural or insufficient rows.

## Affected Domains

- Education & Workforce
- Environment & Energy
- Health & Social Services
- Infrastructure, Tech & Transportation
- Justice & Public Safety
- National Security & Foreign Policy

## Before / After Label Examples

| Before | After |
|---|---|
| `Defense authorization` | defense authorization bill |
| `Defense authorization amendment` | limited-context defense authorization amendments |
| `House floor procedure` | procedural House floor action |
| `Motion to commit` | motion to commit |
| `floor_rule_for_multiple_bills` | procedural floor rule for multiple bills |
| `house_of_representatives` | procedural House rule or motion |
| `floor_rule_for_energy_and_budget_measures` | procedural floor rule for energy and budget measures |
| `federal_employee_collective_bargaining` | federal employee collective bargaining |
| `school_foreign_funding_and_contract_restrictions` | school foreign-funding and contract restrictions |
| `school_foreign_influence_parent_notifications` | school foreign-influence parent notifications |
| `natural_gas_pipeline_and_lng_review_coordination` | natural gas pipeline and LNG review coordination |
| `health_insurance_premiums` | health insurance premium assistance |
| `medicaid_payment_rules_for_minor_health_procedures` | Medicaid payment rules for specified minor health procedures |

## Rendered Example Checks

### National Security & Foreign Policy

Measure labels now render as:

```text
defense authorization bill
motion to commit
```

Limited/procedural labels now render as:

```text
limited-context defense authorization amendments
procedural House floor action
```

Overview copy uses neutral policy-question language and does not expose `Defense authorization amendment` or `House floor procedure` as raw public labels.

### Education & Workforce

Measure labels now render as:

```text
federal employee collective bargaining
school foreign-funding and contract restrictions
school foreign-influence parent notifications
```

Limited/procedural label:

```text
procedural floor rule for multiple bills
```

### Health & Social Services

Measure labels now render as:

```text
health insurance premium assistance
Medicaid payment rules for specified minor health procedures
```

Limited/procedural label:

```text
procedural House rule or motion
```

## Procedural / Limited-Context Treatment

Procedural and floor-rule facets are labeled as procedural or limited-context. This pass does not make those rows more interpretable than the source packet supports.

Examples:

- `Defense authorization amendment` -> `limited-context defense authorization amendments`
- `House floor procedure` -> `procedural House floor action`
- `floor_rule_for_multiple_bills` -> `procedural floor rule for multiple bills`
- `floor_rule_for_energy_and_budget_measures` -> `procedural floor rule for energy and budget measures`
- `house_of_representatives` -> `procedural House rule or motion`

These labels are meant to make evidence limits clearer, not to count weak rows as support or opposition.

## Facets Intentionally Left Raw or Limited

Some facets remain outside this pass because they either need more domain review or were lower-volume in the audit:

- `abortion`
- `administrative_law_and_regulatory_procedures`
- `congressional_oversight`
- any future facet not present in the current audit

Rows with insufficient source context remain limited even when their facet now has a voter-facing label.

## Tests / Build

```text
node --test frontend/lib/issueOverview.test.mjs
Result: pass, 7 tests passing.

npm run build
Result: pass. Next.js compiled successfully and generated 4 static pages.
```

## Files Changed

- `frontend/lib/issueOverview.mjs`
- `frontend/lib/issueOverview.test.mjs`
- `docs/review_packets/facet_label_cleanup_review.md`

## Recommended Next Cleanup Pass

Next pass should focus on generic card-summary templates for top non-gold facets that are already interpreted but still read repetitively, especially:

- Justice/Public Safety: `law_enforcement_safety_reporting`, `dc_police_pursuit_policy`, `dc_policing_reform_repeal`
- National Security/Foreign Policy: `defense authorization bill`, `motion to commit`, `foreign military sales`
- Education/Workforce: school foreign-funding and parent-notification facets
- Health/Social: health insurance premium assistance and Medicaid payment rules

That should remain separate from this label-only pass.
