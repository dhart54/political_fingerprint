import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

import { blindEditorialPipelineReviewProfile } from "../frontend/lib/blindEditorialPipelineReviewSlice.mjs";
import { blindEditorialPipelineValidationData } from "../frontend/lib/blindEditorialPipelineValidationData.mjs";
import { adaptEditorialIssueSlice, EDITORIAL_EXPERIENCE_MODE } from "../frontend/lib/editorialIssueExperience.mjs";
import {
  EDITORIAL_STANDARDIZATION_RULES,
  validateEditorialStandardization,
} from "../frontend/lib/editorialStandardizationValidator.mjs";

const ROOT = resolve(import.meta.dirname, "..");
const FIRST_PATH = resolve(ROOT, "docs/editorial/blind_editorial_pipeline_validation_v1/first_validation_result.json");
const FINAL_PATH = resolve(ROOT, "docs/editorial/blind_editorial_pipeline_validation_v1/final_validation_result.json");
const check = process.argv.includes("--check");

const profile = blindEditorialPipelineReviewProfile;
const evidenceRows = profile.fixtureData.evidenceByDomain.JUSTICE_PUBLIC_SAFETY.evidence;
const experience = adaptEditorialIssueSlice(
  profile.candidate,
  evidenceRows,
  EDITORIAL_EXPERIENCE_MODE.review,
);
const report = validateEditorialStandardization({
  candidate: profile.candidate,
  experience,
  sharedEvidenceVariants: [
    profile.candidate.source.shared_legislative_actions,
    profile.candidate.source.shared_legislative_actions,
  ],
});
const payload = {
  schemaVersion: "blind_editorial_pipeline_validation_result_v1",
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
      result: findings.length ? "finding" : "pass",
      findings,
    };
  }),
  findings: report.findings,
  structuralExpectations: {
    substantiveActions: experience.episodes
      .flatMap((episode) => episode.actions)
      .filter((action) => action.inclusionClass === "substantive").length,
    independentEpisodes: experience.episodes.length,
    featuredEpisodes: experience.featuredEpisodes.length,
    completeRecordActions: experience.completeRecord
      .flatMap((family) => family.congresses)
      .flatMap((congress) => congress.episodes)
      .flatMap((episode) => episode.actions).length,
    proceduralContextActions: experience.proceduralRecords.length,
    analyticalSectionKeys: Object.keys(experience.publicPresentation?.analyticalSections || {}),
  },
  firstGeneratedConclusion: profile.candidate.synthesis.primary,
  publication: profile.candidate.publication,
};
const serialized = `${JSON.stringify(payload, null, 2)}\n`;

if (check) {
  const mismatches = [];
  if (!existsSync(FIRST_PATH)) {
    mismatches.push("first validation result is missing");
  } else {
    const first = JSON.parse(readFileSync(FIRST_PATH, "utf8"));
    if (
      first.selectionLock !== payload.selectionLock
      || first.selectedMember?.member_id !== payload.selectedMember?.member_id
    ) {
      mismatches.push("first validation result no longer matches the locked selection");
    }
  }
  if (!existsSync(FINAL_PATH) || readFileSync(FINAL_PATH, "utf8") !== serialized) {
    mismatches.push("final validation result has drifted");
  }
  if (mismatches.length) {
    console.error(mismatches.join("; "));
    process.exitCode = 1;
  } else {
    console.log(`Blind first-result preservation and final ${payload.ruleCount}-rule validation are current.`);
  }
} else {
  if (!existsSync(FIRST_PATH)) {
    writeFileSync(FIRST_PATH, serialized, "utf8");
    console.log(`Preserved first validation result at ${FIRST_PATH}`);
  }
  writeFileSync(FINAL_PATH, serialized, "utf8");
  console.log(`Wrote final validation result at ${FINAL_PATH}`);
  console.log(`State: ${payload.state}; findings: ${payload.findings.length}; rules: ${payload.ruleCount}`);
}
