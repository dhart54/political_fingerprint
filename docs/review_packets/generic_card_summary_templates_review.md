# Generic Card Summary Templates Review

Generated: 2026-06-03

Scope: narrow frontend card-summary cleanup. This pass adds facet-based generic vote-card summary templates for visible non-gold interpreted facets. It does not add curated roll-number summaries, new interpretation records, backend/API changes, or broad rollout behavior.

## What Changed

`frontend/lib/voteCardSummary.mjs` now has concise, facet-based templates for:

- `law_enforcement_safety_reporting`
- `dc_police_pursuit_policy`
- `dc_policing_reform_repeal`
- `federal_law_enforcement_equipment`
- `federal_law_enforcement_retired_weapon_purchases`
- `school_foreign_funding_and_contract_restrictions`
- `school_foreign_influence_parent_notifications`
- `health_insurance_premiums`
- `health_insurance_premium_assistance`
- `medicaid_payment_rules_for_minor_health_procedures`
- `medicaid_payment_rules`
- `foreign_military_sales`
- `Defense authorization`
- `defense_authorization`

The templates are facet-based and source-bound. They do not branch on roll-call number.

## Before / After Examples

### Law-Enforcement Safety Reporting

Before:

```text
Yea. This was House passage of the Improving Law Enforcement Officer Safety and Wellness Through Data Act. The bill would require the Department of Justice to report on targeted attacks on law enforcement officers, crime-reporting feasibility, and officer mental health resources. The bill would create a DOJ reporting requirement rather than directly changing criminal penalties or law enforcement operations. Foushee voted Yea, matching most Democrats. The bill passed the House.
```

After:

```text
Yea. The House passed a bill requiring DOJ reports on targeted attacks against law-enforcement officers, reporting-system feasibility, and officer mental-health resources. Foushee voted to pass the bill, matching most Democrats. The bill passed the House.
```

### D.C. Police Pursuit Policy

Before:

```text
Nay. This was House passage of the District of Columbia Policing Protection Act. The bill would repeal D.C. restrictions on police vehicular pursuits and generally require pursuits when no other means of apprehension is available, subject to listed exceptions. The bill would change D.C. police-pursuit rules by removing the current restrictions described in the Congress.gov summary, adding a general pursuit requirement unless listed risk or effectiveness exceptions apply, and requiring a DOJ report on pursuit-alert technology. Foushee voted Nay, matching most Democrats. The bill passed the House.
```

After:

```text
Nay. The House passed a bill changing D.C. police pursuit rules by removing current restrictions and adding a general pursuit requirement with listed exceptions. Foushee voted against passing the bill, matching most Democrats. The bill passed the House.
```

### School Foreign-Funding Restrictions

Before:

```text
Nay. This was House passage of the bill. Would add foreign-funding or contract restrictions for schools. Foushee voted Nay, matching most Democrats. The bill passed the House.
```

After:

```text
Nay. The House passed a bill adding school restrictions tied to foreign funding, contracts, or influence. Foushee voted against passing the bill, matching most Democrats. The bill passed the House.
```

### Medicaid Payment Rules

Before:

```text
Yea. This was House passage of the bill. Would restrict federal Medicaid payment for specified procedures involving minors. Foushee voted Yea, matching most Democrats. The bill passed the House.
```

After:

```text
Yea. The House passed a bill restricting federal Medicaid payment for specified procedures involving minors. Foushee voted to pass the bill, matching most Democrats. The bill passed the House.
```

### Foreign Military Sales

Before:

```text
Nay. This was a vote on a foreign military sale resolution. The resolution concerned whether a specific foreign military sale could proceed. Foushee voted Nay, matching most Democrats. The measure passed.
```

After:

```text
Nay. The Senate voted on whether to allow a specific foreign military sale to proceed. Foushee voted against allowing that foreign military sale to proceed, matching most Democrats. The measure passed.
```

## Affected Facets / Domains

- Justice & Public Safety: `law_enforcement_safety_reporting`, `dc_police_pursuit_policy`, `dc_policing_reform_repeal`, federal law-enforcement retired weapon facets
- Education & Workforce: school foreign-funding and parent-notification facets
- Health & Social Services: health insurance premium and Medicaid payment facets
- National Security & Foreign Policy: foreign military sales and defense authorization

## Limited / Ambiguous Rows Preserved

This pass does not modify `buildLimitedContextSummary` and does not change interpretation status, counting, or overview support/opposition logic.

Example intentionally left limited:

```text
Nay. The available source text identifies an amendment but does not explain the full practical policy effect. This row remains visible but is not counted in the summarized vote pattern because the available source text does not explain the practical policy effect.
```

Procedural, ambiguous, or insufficient-evidence rows remain excluded from summarized support/opposition patterns.

## Tests / Build

```text
node --test frontend/lib/issueOverview.test.mjs
Result: pass, 8 tests passing.

npm run build
Result: pass. Next.js compiled successfully and generated 4 static pages.
```

## Files Changed

- `frontend/lib/voteCardSummary.mjs`
- `frontend/lib/issueOverview.test.mjs`
- `docs/review_packets/generic_card_summary_templates_review.md`

## Known Limitations

- This is not a broad rollout. It only adds templates for selected visible facets.
- It does not add new reviewed interpretation records or improve source grounding.
- It does not solve high-volume UI grouping for 20+ row issue sections.
- Some facets still use generic fallback summaries when they are not in this template set.

## Recommended Next Pass

The next small PR should audit high-volume sections where progressive disclosure is still too dense and decide whether grouped measure cards are needed before broader rollout.
