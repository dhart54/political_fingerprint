# Justice Inference Framework Validation V1

## Result

The small cohort supports the reusable-research model. One shared set of five researched policy episodes produced six distinct candidate patterns across seven members, including one exact-vector equivalence case. No measure dossier, roll-stage interpretation, source mapping, or existing Foushee factual claim was changed.

## Conclusions produced

- Foushee and Adams: the same selective enforcement boundary, supported by equivalent episode structure while preserving identity and party context.
- Aderholt: repeated support for the reviewed permanent enforcement and police authority/tool mechanisms, with reporting as neutral context.
- Massie: a mixed but interpretable divide between the single fentanyl episode and three independent police-tool/authority episodes.
- Bishop: support for several reviewed national mechanisms with a repeated boundary at the two D.C. policing changes.
- García: opposition across five concrete mechanism families, bounded so it does not infer a common motive or ideology.
- Moskowitz: broad support across reviewed mechanisms, materially weakened by opposition to repealing most reviewed D.C. policing safeguards.

## Framework findings

The generic member-overlay contract was added as a domain-neutral layer. It validates actions, coverage, shared references, candidate effects, and publication gates; rejects duplicated dossier fields; excludes Not Voting from Yes/No coverage; blocks cross-episode inference below three complete episodes; and never passes party metadata into inference. The existing generic episode aggregator required no semantic correction, and existing Foushee output files remain unchanged.

The Justice-specific candidate library lives in the review artifact builder, not generic runtime. Its decision function receives only the seven episode-stage actions. Member names and party are unavailable to candidate selection. Generated frontend data contains only member-varying fields and joins the same PR #95 source object through the existing selector, adapter, `EditorialIssueExperience`, source presentation, and eligibility gates.

## Template-leakage and edge-case results

- Different real vectors produce different trajectories and candidates.
- The dominant contrasting vector does not receive the Foushee/Adams candidate.
- Equivalent vectors receive equivalent candidate IDs, effects, assessment, and theme structure.
- Changing the load-bearing safeguard-repeal episode replaces the broad-support-with-exception candidate in the counterfactual test.
- Rolls 32, 33, and 166 count as one episode for every member.
- Synthetic Not Voting actions remain excluded and insufficient coverage returns `insufficient_coverage`.
- Holding actions constant while changing party metadata leaves decision-relevant inference identical.
- Contrary evidence can weaken a candidate; added synthetic contrary episodes can contest or defeat one.
- Decision-function source contains no selected member names; generic runtime contains no selected IDs, roll-specific branches, party branches, or Justice conclusion text.

## Publication and dependency safety

All overlays, candidates, generated data, matrices, and review slices remain `human_approval_pending`, `not_promoted`, and `productionEligible: false`. None of the six added members appears in `editorialIssueProductionSlices.mjs`. Default production selection continues to fail closed and use only the production registry.

## Remaining risks

- The cohort is intentionally small and overrepresents complete records; synthetic cases, not real selected members, carry missing-vote coverage.
- Candidate wording still requires human editorial approval.
- Five episodes cannot validate every Justice mechanism or support a national-validity claim.
- A larger review-only batch should test more naturally incomplete records and additional vote vectors before nationwide scaling.

## Recommendation

Proceed next to a larger review-only multi-member batch rather than public-product polish. The architecture and anti-template behavior are promising, but broader record diversity and real missing-coverage cases should be validated before publication work.
