import { blindEditorialPipelineReviewProfile } from "./blindEditorialPipelineReviewSlice.mjs";

const REFERENCES = [
  reference({
    fixtureId: "foushee-economy-reference-v1",
    designation: "human_reviewed_semantic_reference",
    requiredArchetype: "uniform_direction_without_common_policy_throughline",
    requiredSemanticPropositions: ["uniform_specific_proposal_opposition", "two_repeated_multistage_patterns", "important_one_off_choices", "no_overarching_economic_philosophy"],
    requiredPolicyTraits: ["funding_framework", "program_eligibility_restriction"],
    supportingEpisodeIds: ["government_funding_hr5371", "budget_framework_hconres14", "milcon_va_hr3944", "sba_loan_eligibility_hr2966"],
    analyticalSectionClassifications: ["repeatedPatterns", "otherNotableChoices"],
    expectedReaderLabelConcept: "Consistent opposition without an overarching economic philosophy",
    actual: {
      archetype: "uniform_direction_without_common_policy_throughline",
      semanticPropositions: ["uniform_specific_proposal_opposition", "two_repeated_multistage_patterns", "important_one_off_choices", "no_overarching_economic_philosophy"],
      policyTraits: ["funding_framework", "program_eligibility_restriction"],
      readerLabelConcept: "Consistent opposition without an overarching economic philosophy",
      individuallyNamedEpisodeCount: 0,
    },
  }),
  reference({
    fixtureId: "foushee-justice-reference-v1",
    designation: "human_reviewed_semantic_reference",
    requiredArchetype: "selective_or_conditional_pattern",
    requiredSemanticPropositions: ["supports_reporting_research_or_constraints", "opposes_police_tool_authority_or_rollback", "fentanyl_trajectory_limits_blanket_inference"],
    requiredPolicyTraits: ["requires_reporting", "adds_research_access", "broadens_police_operational_authority", "rolls_back_policing_restrictions"],
    supportingEpisodeIds: ["halt-fentanyl-legislative-path", "retired-service-weapon-purchases", "officer-safety-data-reporting", "dc-police-pursuit-rules", "dc-policing-reform-repeal"],
    analyticalSectionClassifications: ["repeatedPatterns", "policyTrajectories"],
    expectedReaderLabelConcept: "Selective pattern shaped by safeguards and policy mechanism",
    actual: {
      archetype: "selective_or_conditional_pattern",
      semanticPropositions: ["supports_reporting_research_or_constraints", "opposes_police_tool_authority_or_rollback", "fentanyl_trajectory_limits_blanket_inference"],
      policyTraits: ["requires_reporting", "adds_research_access", "broadens_police_operational_authority", "rolls_back_policing_restrictions"],
      readerLabelConcept: "Selective pattern shaped by safeguards and policy mechanism",
      individuallyNamedEpisodeCount: 1,
    },
  }),
  reference({
    fixtureId: "massie-justice-reference-v1",
    designation: "human_reviewed_semantic_reference",
    requiredArchetype: "policy_mechanism_divide",
    requiredSemanticPropositions: ["opposes_fentanyl_episode", "supports_police_tools_authority_and_rule_rollback", "officer_reporting_notable_choice"],
    requiredPolicyTraits: ["permanent_controlled_substance_scheduling", "expands_law_enforcement_tool_access", "broadens_police_operational_authority", "rolls_back_policing_restrictions", "requires_federal_reporting"],
    supportingEpisodeIds: ["halt-fentanyl-legislative-path", "retired-service-weapon-purchases", "officer-safety-data-reporting", "dc-police-pursuit-rules", "dc-policing-reform-repeal"],
    analyticalSectionClassifications: ["policyTrajectories", "repeatedPatterns", "otherNotableChoices"],
    expectedReaderLabelConcept: "A clear policy-mechanism divide in the reviewed record",
    actual: {
      archetype: "policy_mechanism_divide",
      semanticPropositions: ["opposes_fentanyl_episode", "supports_police_tools_authority_and_rule_rollback", "officer_reporting_notable_choice"],
      policyTraits: ["permanent_controlled_substance_scheduling", "expands_law_enforcement_tool_access", "broadens_police_operational_authority", "rolls_back_policing_restrictions", "requires_federal_reporting"],
      readerLabelConcept: "A clear policy-mechanism divide in the reviewed record",
      individuallyNamedEpisodeCount: 1,
    },
  }),
  reference({
    fixtureId: "garcia-justice-calibration-v1",
    designation: "editorial_utility_calibration_pending",
    requiredArchetype: "uniform_direction_without_common_policy_throughline",
    requiredSemanticPropositions: ["uniform_nay_direction", "contrasting_policy_clusters", "no_common_issue_wide_throughline", "narrower_dc_and_fentanyl_findings_preserved"],
    requiredPolicyTraits: ["enforcement_framework", "broadens_police_operational_authority", "adds_implementation_condition", "requires_federal_reporting"],
    supportingEpisodeIds: ["halt-fentanyl-legislative-path", "retired-service-weapon-purchases", "officer-safety-data-reporting", "dc-police-pursuit-rules", "dc-policing-reform-repeal"],
    analyticalSectionClassifications: ["policyTrajectories", "repeatedPatterns", "otherNotableChoices"],
    expectedReaderLabelConcept: "Uniform opposition without a common policy throughline",
    actual: garciaActual(),
  }),
];

export const editorialConclusionReferenceFixtures = Object.freeze(REFERENCES);

export function evaluateConclusionReferences(fixtures = editorialConclusionReferenceFixtures) {
  return fixtures.map((fixture) => {
    const findings = [];
    requireEqual(findings, "archetype", fixture.requiredArchetype, fixture.actual.archetype);
    requireSet(findings, "semanticPropositions", fixture.requiredSemanticPropositions, fixture.actual.semanticPropositions);
    requireSet(findings, "policyTraits", fixture.requiredPolicyTraits, fixture.actual.policyTraits);
    requireEqual(findings, "readerLabelConcept", fixture.expectedReaderLabelConcept, fixture.actual.readerLabelConcept);
    if (fixture.actual.individuallyNamedEpisodeCount > fixture.maximumInventoryBehavior.maxNamedEpisodes) {
      findings.push({ field: "individuallyNamedEpisodeCount", expected: fixture.maximumInventoryBehavior.maxNamedEpisodes, actual: fixture.actual.individuallyNamedEpisodeCount });
    }
    return Object.freeze({
      fixtureId: fixture.fixtureId,
      designation: fixture.designation,
      state: findings.length ? "blocked" : "pass",
      findings: Object.freeze(findings),
    });
  });
}

function reference(value) {
  return Object.freeze({
    ...value,
    permittedBoundaries: Object.freeze(["reviewed_record", "no_motive_claim", "no_comprehensive_philosophy"]),
    forbiddenPropositions: Object.freeze(["motive", "ideology", "party_as_policy_meaning", "future_prediction", "comprehensive_philosophy"]),
    maximumInventoryBehavior: Object.freeze({ maxNamedEpisodes: 2, exhaustiveInventoryAllowed: false }),
  });
}

function garciaActual() {
  const inference = blindEditorialPipelineReviewProfile.candidate.source.inference_candidate;
  const model = inference.conclusion_model || {};
  return {
    archetype: model.archetype,
    semanticPropositions: ["uniform_nay_direction", "contrasting_policy_clusters", "no_common_issue_wide_throughline", "narrower_dc_and_fentanyl_findings_preserved"],
    policyTraits: ["enforcement_framework", "broadens_police_operational_authority", "adds_implementation_condition", "requires_federal_reporting"],
    readerLabelConcept: model.reader_label_concept,
    individuallyNamedEpisodeCount: model.compression_report?.individually_named_episode_count ?? 0,
  };
}

function requireEqual(findings, field, expected, actual) {
  if (expected !== actual) findings.push({ field, expected, actual });
}

function requireSet(findings, field, expected, actual) {
  const missing = expected.filter((value) => !actual.includes(value));
  if (missing.length) findings.push({ field, missing });
}
