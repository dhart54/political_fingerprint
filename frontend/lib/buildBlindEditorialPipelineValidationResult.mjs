import { readFile, writeFile } from "node:fs/promises";

import {
  blindEditorialPipelineReviewProfile,
  blindEditorialPipelineValidationFixture,
} from "./blindEditorialPipelineReviewSlice.mjs";
import { blindEditorialPipelineValidationData } from "./blindEditorialPipelineValidationData.mjs";
import { adaptEditorialIssueSlice, EDITORIAL_EXPERIENCE_MODE } from "./editorialIssueExperience.mjs";
import {
  EDITORIAL_STANDARDIZATION_RULES,
  validateEditorialStandardization,
} from "./editorialStandardizationValidator.mjs";

const root = new URL("../../", import.meta.url);
const output = new URL(
  "docs/editorial/blind_editorial_pipeline_validation_v1/final_validation_result.json",
  root,
);
const firstCandidateUrl = new URL(
  "docs/editorial/blind_editorial_pipeline_validation_v1/first_generated_candidate.json",
  root,
);
const profile = blindEditorialPipelineReviewProfile;
const candidate = profile.candidate;
const evidenceRows = profile.fixtureData.evidenceByDomain.JUSTICE_PUBLIC_SAFETY.evidence;
const experience = adaptEditorialIssueSlice(
  candidate,
  evidenceRows,
  EDITORIAL_EXPERIENCE_MODE.review,
);
const report = validateEditorialStandardization({ candidate, experience });
const firstCandidate = JSON.parse(await readFile(firstCandidateUrl, "utf8"));
const value = {
  schemaVersion: "blind_editorial_pipeline_validation_result_v2",
  deterministicBuildIdentifier: blindEditorialPipelineValidationData.deterministicBuildIdentifier,
  startingCommit: blindEditorialPipelineValidationData.startingCommit,
  selectionLock: blindEditorialPipelineValidationData.selectionLock,
  selectedMember: blindEditorialPipelineValidationData.selectedMember,
  state: report.state,
  publicationEligibilityMustFail: report.publicationEligibilityMustFail,
  ruleCount: EDITORIAL_STANDARDIZATION_RULES.length,
  ruleResults: EDITORIAL_STANDARDIZATION_RULES.map((rule) => {
    const findings = report.findings.filter((finding) => finding.ruleId === rule.id);
    return {
      ruleId: rule.id,
      severity: rule.severity,
      result: findings.length ? "fail" : "pass",
      findings,
    };
  }),
  findings: report.findings,
  structuralExpectations: {
    substantiveActions: experience.publicPresentation.coverage.expectedVotes,
    independentEpisodes: experience.publicPresentation.coverage.expectedEpisodes,
    featuredEpisodes: experience.featuredEpisodes.length,
    completeRecordActions: experience.completeRecord
      .flatMap((family) => family.congresses)
      .flatMap((congress) => congress.episodes)
      .flatMap((episode) => episode.actions).length,
    proceduralContextActions: experience.proceduralRecords.length,
    analyticalSectionKeys: Object.keys(candidate.synthesis.analyticalSections),
  },
  preservedFirstGeneratedConclusion: firstCandidate.inference.primary_conclusion,
  firstAttemptAssessment: "structurally_valid_editorial_utility_failure_found_in_bounded_smoke_review",
  finalGeneratedConclusion: candidate.synthesis.primary,
  publication: candidate.publication,
  fixtureDesignation: blindEditorialPipelineValidationFixture.designation,
};
const serialized = `${JSON.stringify(value, null, 2)}\n`;

if (process.argv.includes("--check")) {
  const existing = await readFile(output, "utf8");
  if (existing !== serialized) throw new Error("final validation result differs");
} else {
  await writeFile(output, serialized, "utf8");
}
