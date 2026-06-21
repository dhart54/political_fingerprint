# House Comparable Policy-Question Family Audit

Generated: `2026-06-21T13:10:45Z`

## Executive Conclusion

Family-model recommendation: `FAMILY MODEL READY WITH MANUAL REVIEW`.
Continuity/change readiness: `READY FOR LIMITED PROFILES`.

The audit found common, source-grounded families, but the model still depends on manual review and explicit caveats. `Record Across Congresses` should remain the product framing until a reviewed derived artifact is promoted in a later milestone.

## Coverage

- Target interpreted roll calls: 306
- Candidate families identified: 15
- Common families identified: 13
- Directly comparable common families: 4
- Conditionally comparable common families: 7
- Related but non-comparable clusters: 4
- Ungrouped roll calls: 225
- Substantive vote rows covered by candidate families: 33825 (26.59%)

## Comparable Families By Domain

### Government funding packages

- Domain: `ECONOMY_TAXES`
- Status: `conditionally_comparable`
- Governing question: Whether the House should pass broad appropriations or continuing-funding packages.
- Roll calls by Congress: {"118": 5, "119": 5}
- Vote types: amendment, appropriations
- Limitation: Appropriations bills vary by covered agencies and fiscal year; compare only with a funding-package caveat.

### Small-business finance and regulation

- Domain: `ECONOMY_TAXES`
- Status: `related_but_not_comparable`
- Governing question: Whether the House should change federal rules affecting small-business finance, loans, or agency regulatory costs.
- Roll calls by Congress: {"118": 4, "119": 2}
- Vote types: amendment, final_passage, rule
- Limitation: Use as a related cluster only unless a narrower recurring bill family is reviewed.

### Critical minerals supply

- Domain: `ENVIRONMENT_ENERGY`
- Status: `conditionally_comparable`
- Governing question: Whether the House should advance measures intended to expand, coordinate, or define domestic critical-minerals policy.
- Roll calls by Congress: {"118": 1, "119": 2}
- Vote types: final_passage
- Limitation: The bills use different policy tools, so comparison should be limited to the recurring critical-minerals governing question.

### Energy permitting and fossil-fuel infrastructure

- Domain: `ENVIRONMENT_ENERGY`
- Status: `related_but_not_comparable`
- Governing question: Whether the House should expand or protect permitting, review, or access for fossil-fuel and energy infrastructure.
- Roll calls by Congress: {"118": 11, "119": 1}
- Vote types: amendment, final_passage
- Limitation: This cluster is useful for audit triage, not continuity/change eligibility.

### Home-appliance energy rules

- Domain: `ENVIRONMENT_ENERGY`
- Status: `conditionally_comparable`
- Governing question: Whether the House should limit federal restrictions or efficiency rules affecting household energy appliances.
- Roll calls by Congress: {"118": 2, "119": 2}
- Vote types: amendment, final_passage
- Limitation: Some 118th evidence is amendment-based while 119th evidence is final-passage; use a vote-type caveat.

### Hunting and fishing access

- Domain: `ENVIRONMENT_ENERGY`
- Status: `directly_comparable`
- Governing question: Whether the House should pass the Protecting Access for Hunters and Anglers Act.
- Roll calls by Congress: {"118": 1, "119": 1}
- Vote types: final_passage
- Limitation: The Congress-specific bill text and legislative path still need source review before public comparison language.

### Federal officer service-weapon purchase

- Domain: `JUSTICE_PUBLIC_SAFETY`
- Status: `directly_comparable`
- Governing question: Whether federal law-enforcement officers, including retirees in some versions, should be able to buy retired service weapons.
- Roll calls by Congress: {"118": 5, "119": 1}
- Vote types: amendment, final_passage
- Limitation: Amendment rows within the family need vote-type caveats if used alongside final-passage rows.

### Law-enforcement safety reporting

- Domain: `JUSTICE_PUBLIC_SAFETY`
- Status: `directly_comparable`
- Governing question: Whether the Justice Department should report on targeted attacks or safety data involving law-enforcement officers.
- Roll calls by Congress: {"118": 1, "119": 1}
- Vote types: final_passage
- Limitation: The legislative text may differ by Congress; final public use should cite the exact bills.

### Law-enforcement support resolutions

- Domain: `JUSTICE_PUBLIC_SAFETY`
- Status: `conditionally_comparable`
- Governing question: Whether the House should adopt resolutions expressing support for law-enforcement officers or agencies.
- Roll calls by Congress: {"118": 3, "119": 1}
- Vote types: amendment, other
- Limitation: Resolution votes are materially different from statutory final passage and should not be mixed with bill enactment votes.

### Violent offenders and pretrial detention

- Domain: `JUSTICE_PUBLIC_SAFETY`
- Status: `conditionally_comparable`
- Governing question: Whether the House should pass measures aimed at keeping violent offenders in custody or reporting cashless-bail practices.
- Roll calls by Congress: {"118": 1, "119": 2}
- Vote types: final_passage
- Limitation: Do not combine bail-reporting and violent-offender detention rows without an explicit scope caveat.

### Annual defense authorization

- Domain: `NATIONAL_SECURITY_FOREIGN`
- Status: `directly_comparable`
- Governing question: Whether the House should pass the annual defense authorization package setting defense and related national-security policy.
- Roll calls by Congress: {"118": 2, "119": 1}
- Vote types: final_passage
- Limitation: The authorization bills differ by fiscal year and contents; comparison is about the recurring authorization action, not identical provisions.

### Ukraine assistance or funding restrictions

- Domain: `NATIONAL_SECURITY_FOREIGN`
- Status: `conditionally_comparable`
- Governing question: Whether the House should restrict, prohibit, or remove U.S. funding or assistance for Ukraine-related activities.
- Roll calls by Congress: {"118": 12, "119": 1}
- Vote types: amendment
- Limitation: Different parent bills and funding streams make this a conditional family, not a claim about an identical program.

### War-powers removal resolutions

- Domain: `NATIONAL_SECURITY_FOREIGN`
- Status: `conditionally_comparable`
- Governing question: Whether the House should direct removal of U.S. armed forces from named hostilities or deployments not separately authorized by Congress.
- Roll calls by Congress: {"118": 2, "119": 6}
- Vote types: other
- Limitation: Treat as comparable only with an explicit theater/scope caveat.

## Field Reliability Inventory

- bill and resolution identity: completeness 100%; usefulness `supporting`. Too narrow across Congresses and cannot substitute for amendment meaning.
- amendment identity: completeness 99%; usefulness `supporting`. Too incomplete for durable family assignment without manual/source-packet review.
- parent measure: completeness 100%; usefulness `supporting`. Parent-measure context cannot replace the narrower amendment question.
- amendment-to-amendment and en-bloc relationships: completeness 0%; usefulness `limited`. Sparse and source-dependent; not reliable as a primary grouping field.
- vote question: completeness 100%; usefulness `supporting`. Often generic (`On Passage`, `On Agreeing to the Amendment`) and not enough for policy-family meaning.
- source-grounded summary: completeness 100%; usefulness `supporting`. Quality varies; generic direct-vote summaries remain too broad.
- interpretation summary: completeness 100%; usefulness `supporting`. Not uniformly present across older/generic rows.
- issue facet: completeness 11%; usefulness `limited`. Many 118th rows use generic `House amendment vote`; broad facets are not comparable questions.
- sponsor or amendment sponsor: completeness 0%; usefulness `limited`. Cannot be used reliably without source-packet enrichment.
- vote type: completeness 100%; usefulness `supporting`. Same vote type does not guarantee same governing question.
- policy purpose: completeness 100%; usefulness `supporting`. Coverage and specificity vary by interpretation vintage.
- official source title and description: completeness 100%; usefulness `supporting`. Titles can be broad, amended, or generic; descriptions may repeat question text.
- existing measure-family or relationship fields: completeness 0%; usefulness `limited`. Supports keeping this milestone as a review artifact rather than a production model.

## Threshold Simulations

- `direct_one_common_family_one_cast_vote`: 360 current officials (81.63%); exclusions {"below_family_or_vote_threshold": 81}.
- `direct_one_common_family_three_cast_votes`: 0 current officials (0.00%); exclusions {"below_family_or_vote_threshold": 441}.
- `direct_two_common_families`: 358 current officials (81.18%); exclusions {"below_family_or_vote_threshold": 83}.
- `direct_support_and_opposition_opportunity`: 0 current officials (0.00%); exclusions {"below_family_or_vote_threshold": 441}.
- `direct_not_voting_below_20`: 356 current officials (80.73%); exclusions {"below_family_or_vote_threshold": 79, "not_voting_burden": 6}.
- `direct_limited_procedural_below_50`: 0 current officials (0.00%); exclusions {"limited_procedural_burden": 441}.
- `direct_and_conditional_one_family`: 367 current officials (83.22%); exclusions {"below_family_or_vote_threshold": 74}.
- `direct_and_conditional_three_cast_votes`: 354 current officials (80.27%); exclusions {"below_family_or_vote_threshold": 87}.
- `direct_and_conditional_two_families`: 362 current officials (82.09%); exclusions {"below_family_or_vote_threshold": 79}.
- `direct_and_conditional_full_caveated_contract`: 0 current officials (0.00%); exclusions {"limited_procedural_burden": 435, "not_voting_burden": 6}.

## Representative Profiles

- required_valerie_foushee: Valerie P. Foushee - future comparison eligible: true; result: Future comparison eligibility exists only for directly comparable reviewed families; no continuity/change claim is made. Families: Government funding packages (conditionally_comparable), Small-business finance and regulation (related_but_not_comparable), Critical minerals supply (conditionally_comparable), Energy permitting and fossil-fuel infrastructure (related_but_not_comparable).
- required_aaron_bean: Aaron Bean - future comparison eligible: true; result: Future comparison eligibility exists only for directly comparable reviewed families; no continuity/change claim is made. Families: Government funding packages (conditionally_comparable), Small-business finance and regulation (related_but_not_comparable), Critical minerals supply (conditionally_comparable), Energy permitting and fossil-fuel infrastructure (related_but_not_comparable).
- strong_common_family_evidence: Adam Smith - future comparison eligible: true; result: Future comparison eligibility exists only for directly comparable reviewed families; no continuity/change claim is made. Families: Government funding packages (conditionally_comparable), Small-business finance and regulation (related_but_not_comparable), Critical minerals supply (conditionally_comparable), Energy permitting and fossil-fuel infrastructure (related_but_not_comparable).
- apparent_continuity_eligible_future_comparison: Adriano Espaillat - future comparison eligible: true; result: Future comparison eligibility exists only for directly comparable reviewed families; no continuity/change claim is made. Families: Government funding packages (conditionally_comparable), Small-business finance and regulation (related_but_not_comparable), Critical minerals supply (conditionally_comparable), Energy permitting and fossil-fuel infrastructure (related_but_not_comparable).
- apparent_change_eligible_future_comparison: Angie Craig - future comparison eligible: true; result: Future comparison eligibility exists only for directly comparable reviewed families; no continuity/change claim is made. Families: Government funding packages (conditionally_comparable), Small-business finance and regulation (related_but_not_comparable), Critical minerals supply (conditionally_comparable), Energy permitting and fossil-fuel infrastructure (related_but_not_comparable).
- invalidated_by_vote_type_mismatch: Adrian Smith - future comparison eligible: true; result: Targeted family example is invalidated for uncaveated comparison because amendment/final-passage mechanisms differ. Families: Government funding packages (conditionally_comparable), Small-business finance and regulation (related_but_not_comparable), Energy permitting and fossil-fuel infrastructure (related_but_not_comparable), Home-appliance energy rules (conditionally_comparable).
- invalidated_by_different_policy_subtopics: Al Green - future comparison eligible: true; result: Targeted family example is invalidated because related rows ask different policy subtopic questions. Families: Government funding packages (conditionally_comparable), Small-business finance and regulation (related_but_not_comparable), Critical minerals supply (conditionally_comparable), Energy permitting and fossil-fuel infrastructure (related_but_not_comparable).
- sparse_profile: Abraham J. Hamadeh - future comparison eligible: false; result: Targeted example is not eligible because common-family evidence is sparse or absent. Families: none.
- meaningful_not_voting_burden: Aumua Amata Coleman Radewagen - future comparison eligible: false; result: Targeted example is not eligible under not-voting burden controls. Families: Ukraine assistance or funding restrictions (conditionally_comparable).

## Validation

- Read-only transaction: `on`.
- Production writes performed: no.
- Production data or derived outputs changed: no.
- Prior readiness totals reconciled: `True`.
- Cross-Congress leakage check: family eligibility requires roll calls in both 118th and 119th Congresses with session-aware roll-call identity preserved.
- Not-voting remains excluded from support/opposition counts.
- Procedural and limited evidence remain non-counting.

## Remaining Risks

- Many 118th amendment rows still rely on generic `House amendment vote` facets; source-grounded summaries carry most of the family signal.
- Conditional families mix different fiscal years, theaters, parent bills, or vote mechanisms and require visible caveats.
- The audit does not prove every target row can be safely grouped; ungrouped and related clusters should remain outside eligibility.
- Family assignment is useful as a derived review artifact, but not yet justified as a permanent production schema model.

## Production Persistence Recommendation

Recommendation: add a versioned derived artifact outside the production schema in a later milestone. Do not add a permanent production model yet.

## Smallest Next Milestone

Review a versioned derived family artifact for the common directly comparable families before any frontend continuity/change language.
