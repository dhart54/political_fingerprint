import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

import { adaptEditorialIssueSlice, EDITORIAL_EXPERIENCE_MODE } from "../frontend/lib/editorialIssueExperience.mjs";
import { blindEditorialPipelineValidationFixture } from "../frontend/lib/blindEditorialPipelineReviewSlice.mjs";
import {
  editorialConclusionReferenceFixtures,
  evaluateConclusionReferences,
} from "../frontend/lib/editorialConclusionReferenceFixtures.mjs";
import {
  editorialReferenceFixtures,
  syntheticLargeRecordCandidate,
  syntheticLargeRecordRows,
} from "../frontend/lib/editorialStandardizationFixtures.mjs";
import {
  EDITORIAL_STANDARDIZATION_RULES,
  summarizeValidationReports,
  validateEditorialStandardization,
} from "../frontend/lib/editorialStandardizationValidator.mjs";

const ROOT = resolve(import.meta.dirname, "..");
const JSON_PATH = resolve(ROOT, "docs/review_packets/editorial_standardization_validation_v1.json");
const MARKDOWN_PATH = resolve(ROOT, "docs/review_packets/editorial_standardization_validation_v1.md");
const check = process.argv.includes("--check");

const fixtures = [
  ...editorialReferenceFixtures,
  blindEditorialPipelineValidationFixture,
  {
    id: "synthetic-large-record-v1",
    designation: "standardization_regression_fixture",
    candidate: syntheticLargeRecordCandidate,
    evidenceRows: syntheticLargeRecordRows,
  },
];

const reports = fixtures.map((fixture) => {
  const experience = adaptEditorialIssueSlice(fixture.candidate, fixture.evidenceRows, EDITORIAL_EXPERIENCE_MODE.review);
  const report = validateEditorialStandardization({ candidate: fixture.candidate, experience });
  return {
    fixtureId: fixture.id,
    designation: fixture.designation,
    state: report.state,
    publicationEligibilityMustFail: report.publicationEligibilityMustFail,
    memberId: report.memberId,
    issue: report.issue,
    findings: report.findings,
    structuralExpectations: structuralExpectations(experience),
  };
});

const payload = {
  schemaVersion: "editorial_standardization_validation_v1",
  deterministic: true,
  humanApprovalConferred: false,
  politicalTruthOrFactualPerfectionProven: false,
  publicationBoundary: {
    editorialStatus: "human_approval_pending",
    benchmarkStatus: "not_promoted",
    productionEligible: false,
    productionRegistryExpectedEntries: 0,
  },
  summary: summarizeValidationReports(reports),
  ruleCatalog: EDITORIAL_STANDARDIZATION_RULES,
  reports,
  semanticReferenceResults: evaluateConclusionReferences(),
  semanticReferenceContracts: editorialConclusionReferenceFixtures.map((fixture) => ({
    fixtureId: fixture.fixtureId,
    designation: fixture.designation,
    requiredArchetype: fixture.requiredArchetype,
    requiredSemanticPropositions: fixture.requiredSemanticPropositions,
    requiredPolicyTraits: fixture.requiredPolicyTraits,
    permittedBoundaries: fixture.permittedBoundaries,
    forbiddenPropositions: fixture.forbiddenPropositions,
    supportingEpisodeIds: fixture.supportingEpisodeIds,
    analyticalSectionClassifications: fixture.analyticalSectionClassifications,
    maximumInventoryBehavior: fixture.maximumInventoryBehavior,
    expectedReaderLabelConcept: fixture.expectedReaderLabelConcept,
  })),
  mutationCoverage: {
    requiredMalformedCases: 32,
    testFile: "frontend/lib/editorialStandardizationValidator.test.mjs",
    interpretation: "The test suite deliberately mutates valid fixtures and asserts the expected stable rule ID. This report does not substitute for running the tests.",
  },
};

const json = `${JSON.stringify(payload, null, 2)}\n`;
const markdown = renderMarkdown(payload);

if (check) {
  const drift = readFileSync(JSON_PATH, "utf8") !== json || readFileSync(MARKDOWN_PATH, "utf8") !== markdown;
  if (drift) {
    console.error("Editorial standardization validation artifacts have drifted. Regenerate them before committing.");
    process.exitCode = 1;
  } else {
    console.log("Editorial standardization validation artifacts are deterministic and current.");
  }
} else {
  writeFileSync(JSON_PATH, json, "utf8");
  writeFileSync(MARKDOWN_PATH, markdown, "utf8");
  console.log(`Wrote ${JSON_PATH}`);
  console.log(`Wrote ${MARKDOWN_PATH}`);
}

function structuralExpectations(experience) {
  return {
    substantiveActions: experience.episodes.flatMap((episode) => episode.actions).filter((action) => action.inclusionClass === "substantive").length,
    independentEpisodes: experience.episodes.length,
    featuredEpisodes: experience.featuredEpisodes.length,
    notVotingActions: [...experience.episodes.flatMap((episode) => episode.actions), ...experience.ungroupedRecords].filter((action) => action.inclusionClass === "not_voting").length,
    proceduralContextActions: experience.proceduralRecords.length,
    completeRecordPolicyFamilies: experience.completeRecord.length,
    completeRecordCongresses: [...new Set(experience.completeRecord.flatMap((family) => family.congresses.map((group) => group.congress)))].sort(),
  };
}

function renderMarkdown(value) {
  const lines = [
    "# Editorial standardization validation v1",
    "",
    "This deterministic report checks contract conformance. It does not confer human approval, prove political truth, or guarantee factual perfection.",
    "",
    "## Summary",
    "",
    `- State: \`${value.summary.state}\``,
    `- Fixtures: ${value.summary.sliceCount}`,
    `- Rules: ${value.summary.ruleCount} (${value.summary.ruleCountBySeverity.block} blocking, ${value.summary.ruleCountBySeverity.warning} warning)`,
    `- Findings: ${value.summary.findingCountBySeverity.block} blocking, ${value.summary.findingCountBySeverity.warning} warning`,
    "- Real content remains `human_approval_pending`, `not_promoted`, and `productionEligible: false`.",
    "- Expected production-registry entries: 0.",
    "",
    "## Fixture results",
    "",
    "| Fixture | Designation | State | Actions | Episodes | Featured | Not Voting | Procedural |",
    "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ...value.reports.map((report) => `| ${report.fixtureId} | ${report.designation} | ${report.state} | ${report.structuralExpectations.substantiveActions} | ${report.structuralExpectations.independentEpisodes} | ${report.structuralExpectations.featuredEpisodes} | ${report.structuralExpectations.notVotingActions} | ${report.structuralExpectations.proceduralContextActions} |`),
    "",
    "## Mutation coverage",
    "",
    `The mutation suite contains ${value.mutationCoverage.requiredMalformedCases} deliberate known-defect cases and requires each one to produce its expected stable rule ID. Run the suite; this generated report is not a substitute for test execution.`,
    "",
    "## Semantic conclusion references",
    "",
    "| Fixture | Designation | Archetype | Result |",
    "| --- | --- | --- | --- |",
    ...value.semanticReferenceResults.map((result) => {
      const contract = value.semanticReferenceContracts.find((item) => item.fixtureId === result.fixtureId);
      return `| ${result.fixtureId} | ${result.designation} | ${contract.requiredArchetype} | ${result.state} |`;
    }),
    "",
    "## Publication boundary",
    "",
    "Reference-fixture designations are presentation and standardization contracts only. They are separate from editorial approval, benchmark promotion, production eligibility, registry inclusion, merge, and deployment.",
  ];
  return `${lines.join("\n")}\n`;
}
