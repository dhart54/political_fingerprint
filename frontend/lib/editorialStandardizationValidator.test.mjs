import assert from "node:assert/strict";
import test from "node:test";

import { adaptEditorialIssueSlice, EDITORIAL_EXPERIENCE_MODE } from "./editorialIssueExperience.mjs";
import {
  editorialReferenceFixtures,
  syntheticLargeRecordCandidate,
  syntheticLargeRecordRows,
} from "./editorialStandardizationFixtures.mjs";
import {
  EDITORIAL_STANDARDIZATION_RULES,
  validateEditorialStandardization,
} from "./editorialStandardizationValidator.mjs";
import { classifyActionServiceStatus, MEMBER_ACTION_STATUS } from "./editorialSharedEvidence.mjs";
import { formatPublicDateRange, firstCompleteSentence, publicSentenceDefects } from "./editorialTextIntegrity.mjs";
import { blindEditorialPipelineValidationFixture } from "./blindEditorialPipelineReviewSlice.mjs";
import {
  editorialConclusionReferenceFixtures,
  evaluateConclusionReferences,
} from "./editorialConclusionReferenceFixtures.mjs";

const referenceCases = editorialReferenceFixtures.map((fixture) => ({
  fixture,
  candidate: structuredClone(fixture.candidate),
  experience: structuredClone(adaptEditorialIssueSlice(fixture.candidate, fixture.evidenceRows, EDITORIAL_EXPERIENCE_MODE.review)),
}));
const economy = referenceCases[0];
const fousheeJustice = referenceCases[1];
const massieJustice = referenceCases[2];

test("the three human-reviewed presentation fixtures pass every deterministic gate", () => {
  assert.equal(referenceCases.length, 3);
  for (const item of referenceCases) {
    const report = validateEditorialStandardization(item);
    assert.equal(report.state, "pass", JSON.stringify(report.findings, null, 2));
    assert.equal(report.publicationEligibilityMustFail, false);
    assert.equal(item.candidate.publication.editorialStatus, "human_approval_pending");
    assert.equal(item.candidate.publication.benchmarkStatus, "not_promoted");
    assert.equal(item.candidate.publication.productionEligible, false);
    assert.equal(item.candidate.standardizationFixture.designation, "human_reviewed_presentation_fixture");
  }
});

test("Massie result extraction preserves legislative abbreviations and complete authoritative outcomes", () => {
  const fentanyl = massieJustice.experience.episodes.find((episode) => episode.id === "halt-fentanyl-legislative-path");
  assert.equal(fentanyl.actions[0].actionAndResult, "Massie voted Nay. The amendment failed; the House then passed H.R. 27 without it.");
  assert.equal(fentanyl.actions[1].actionAndResult, "Massie voted Nay. H.R. 27 passed the House but did not itself become law.");
  assert.equal(firstCompleteSentence("H. Res. 5 passed. A later action followed."), "H. Res. 5 passed.");
  assert.equal(firstCompleteSentence("The House considered D.C. rules. It adjourned."), "The House considered D.C. rules.");
  assert.equal(firstCompleteSentence("S. 331 became Public Law 119-26. Implementation followed."), "S. 331 became Public Law 119-26.");
  assert.deepEqual(publicSentenceDefects("The House then passed H.R."), ["PUBLIC_SENTENCE_ABBREVIATION_FRAGMENT"]);
});

test("public date ranges are deterministic and humanized", () => {
  assert.equal(formatPublicDateRange("2025-05-15"), "May 15, 2025");
  assert.equal(formatPublicDateRange("2025-02-06", "2025-02-12"), "Feb. 6–12, 2025");
  assert.equal(formatPublicDateRange("2025-09-19", "2025-11-12"), "Sep. 19–Nov. 12, 2025");
  assert.equal(formatPublicDateRange("2025-12-20", "2026-01-05"), "Dec. 20, 2025–Jan. 5, 2026");
});

test("service classification fails closed without exact dates", () => {
  assert.equal(classifyActionServiceStatus({ actionDate: "2025-02-06", serviceStartDate: "2025-04-01", serviceDatePrecision: "year" }), MEMBER_ACTION_STATUS.missingEvidence);
  assert.equal(classifyActionServiceStatus({ actionDate: "2025-02-06", serviceStartDate: "2025-04-01", serviceDatePrecision: "day" }), MEMBER_ACTION_STATUS.notYetServing);
  assert.equal(classifyActionServiceStatus({ actionDate: "2025-06-12", serviceEndDate: "2025-05-01", serviceDatePrecision: "day" }), MEMBER_ACTION_STATUS.noLongerServing);
  assert.equal(classifyActionServiceStatus({ actionDate: "2025-06-12", hasEvidence: true, recordedStatus: "Present", serviceDatePrecision: "year" }), MEMBER_ACTION_STATUS.present);
});

test("the synthetic large record remains bounded while every receipt stays accessible", () => {
  const experience = adaptEditorialIssueSlice(syntheticLargeRecordCandidate, syntheticLargeRecordRows, EDITORIAL_EXPERIENCE_MODE.review);
  const report = validateEditorialStandardization({ candidate: syntheticLargeRecordCandidate, experience });
  assert.equal(report.state, "pass", JSON.stringify(report.findings, null, 2));
  assert.equal(experience.featuredEpisodes.length, 5);
  assert.equal(experience.episodes.length, 12);
  assert.equal(experience.episodes.flatMap((episode) => episode.actions).length, 24);
  assert.equal(experience.ungroupedRecords.filter((record) => record.inclusionClass === "not_voting").length, 1);
  assert.equal(experience.proceduralRecords.length, 3);
  assert.equal(experience.completeRecord.some((family) => family.congresses.length === 2), true);
});

test("all twenty known-defect mutations are caught by stable rules", () => {
  const cases = [
    mutation("member leakage", "SHARED-001", massieJustice, ({ candidate }) => { candidate.source.shared_legislative_actions[0].ten_second.practical_choice += " Foushee supported it."; }),
    mutation("wrong overlay direction", "OVERLAY-001", massieJustice, ({ experience }) => { experience.episodes[0].actions[0].actionStatus = "yea"; }),
    mutation("truncated H.R.", "ACTION-013", massieJustice, ({ experience }) => { experience.episodes[0].actions[0].actionAndResult = "Massie voted Nay. The House then passed H.R."; }),
    mutation("zero complete Economy episodes", "COVERAGE-001", economy, ({ experience }) => { experience.publicPresentation.coverage.completeEpisodes = 0; }),
    mutation("one-off repeated pattern", "ANALYSIS-001", fousheeJustice, ({ candidate }) => { candidate.synthesis.analyticalSections.repeatedPatterns = [{ episodeId: "officer-safety-data-reporting", text: "Repeated reporting pattern." }]; }),
    mutation("Not Voting counted", "ANALYSIS-003", economy, ({ candidate }) => { candidate.validationHints = { nonYesNoCounted: true }; }),
    mutation("year-only service relabel", "SERVICE-001", economy, ({ options }) => { options.serviceChecks = [{ actionId: "roll-310", classifiedStatus: "not_yet_serving", serviceDatePrecision: "year", exactEligibilityEstablished: false }]; }),
    mutation("duplicate motive boundaries", "DETAIL-001", economy, ({ experience }) => { experience.episodes[0].actions[0].importantContext.push("The vote does not establish motive."); }),
    mutation("procedural conclusion support", "ANALYSIS-002", economy, ({ candidate }) => { candidate.validationHints = { proceduralConclusionRolls: [284] }; }),
    mutation("missing vote source", "ACTION-010", massieJustice, ({ experience }) => { experience.episodes[0].actions[0].sources = experience.episodes[0].actions[0].sources.filter((source) => !source.url.includes("clerk.house.gov")); }),
    mutation("invented opponent argument", "ACTION-012", massieJustice, ({ experience }) => { experience.episodes[0].actions[0].argumentSupport = { opponents: "unsupported" }; }),
    mutation("selected rich issue duplicated", "PUBLIC-002", massieJustice, ({ options, candidate }) => { options.genericIssueCards = [candidate.identity.issueId]; }),
    mutation("six featured episodes", "PUBLIC-003", massieJustice, ({ candidate }) => { candidate.episodePresentation.featuredEpisodeIds.push("unexpected-sixth-episode"); }),
    mutation("raw ISO date", "PUBLIC-004", economy, ({ options }) => { options.renderedText = "2025-09-19 – 2025-11-12"; }),
    mutation("shared evidence changed by member", "SHARED-002", massieJustice, ({ options, candidate }) => { const left = structuredClone(candidate.source.shared_legislative_actions); const right = structuredClone(left); right[0].thirty_second.mechanism = "Member-varying mechanism"; options.sharedEvidenceVariants = [left, right]; }),
    mutation("affected groups absent", "ACTION-007", economy, ({ experience }) => { experience.episodes[0].actions[0].impactAndOutcome.affected = undefined; }),
    mutation("cross-Congress episode merge", "EPISODE-005", economy, ({ candidate }) => { candidate.validationHints = { crossCongressRelationshipWithoutFamily: true }; }),
    mutation("D.C. entire-law overstatement", "PUBLIC-005", massieJustice, ({ experience }) => { experience.episodes.find((episode) => episode.id === "dc-policing-reform-repeal").sharedQuestion = "Whether to repeal the entirety of D.C.'s 2022 policing reform law."; }),
    mutation("unmatched punctuation", "ACTION-013", massieJustice, ({ experience }) => { experience.episodes[0].actions[0].actionAndResult = "Massie voted Nay (after debate."; }),
    mutation("internal workflow language", "PUBLIC-001", economy, ({ options }) => { options.renderedText = "Rerun this inference for the candidate conclusion."; }),
  ];
  assert.equal(cases.length, 20);
  for (const item of cases) {
    const report = validateEditorialStandardization({ candidate: item.candidate, experience: item.experience, ...item.options });
    assert.equal(report.state, "blocked", item.name);
    assert.equal(report.findings.some((finding) => finding.ruleId === item.expectedRule), true, `${item.name}: ${JSON.stringify(report.findings)}`);
  }
  assert.equal(EDITORIAL_STANDARDIZATION_RULES.every((rule) => /^[A-Z]+(?:-[A-Z]+)*-\d{3}$/.test(rule.id)), true);
});

test("semantic references validate propositions rather than byte-identical paragraphs", () => {
  const results = evaluateConclusionReferences();
  assert.equal(editorialConclusionReferenceFixtures.length, 4);
  assert.equal(results.every((result) => result.state === "pass"), true, JSON.stringify(results, null, 2));
  assert.equal(editorialConclusionReferenceFixtures.at(-1).designation, "editorial_utility_calibration_pending");
  assert.equal(editorialConclusionReferenceFixtures.at(-1).fixtureId, "garcia-justice-calibration-v1");
});

test("a duplicated bounded-sample phrase is blocked as deterministic duplicate detail", () => {
  const candidate = structuredClone(fousheeJustice.candidate);
  const experience = structuredClone(fousheeJustice.experience);
  candidate.synthesis.primary = "In this reviewed sample, the record shows a repeated pattern in this sample.";
  const report = validateEditorialStandardization({ candidate, experience });
  assert.equal(report.state, "blocked");
  assert.equal(report.findings.some((finding) => finding.ruleId === "DETAIL-001"), true);
});

test("direction-only and circular synthesis mutations are blocked generically", () => {
  const mutations = [
    ({ candidate }) => {
      candidate.source.inference_candidate.candidate_basis = {
        basis_type: "substantive_repeated_pattern",
        substantive_theme_ids: ["cross-mechanism-opposition"],
      };
    },
    ({ candidate }) => {
      candidate.synthesis.primary = "The member opposed different proposals across several policy mechanisms.";
    },
    ({ candidate }) => {
      candidate.synthesis.analyticalSections.repeatedPatterns = [{
        text: "Nay on reviewed actions across multiple mechanisms.",
      }];
    },
    ({ candidate, experience }) => {
      for (const action of experience.episodes.flatMap((episode) => episode.actions)) {
        if (action.inclusionClass === "substantive") action.actionStatus = "nay";
      }
      candidate.synthesis.primary = "The record establishes a coherent public-safety philosophy.";
    },
  ];
  for (const mutate of mutations) {
    const value = {
      candidate: structuredClone(fousheeJustice.candidate),
      experience: structuredClone(fousheeJustice.experience),
    };
    mutate(value);
    const report = validateEditorialStandardization(value);
    assert.equal(report.state, "blocked", JSON.stringify(report.findings));
    assert.equal(report.findings.some((finding) => finding.ruleId === "SYNTHESIS-001"), true);
  }
});

test("detail validation catches semantic qualifier repetition and redundant vote-motive disclaimers", () => {
  for (const context of [
    "The substitute included exceptions; it was not an unconditional pursuit mandate.",
    "A Nay does not reveal which objection drove the vote.",
  ]) {
    const candidate = structuredClone(massieJustice.candidate);
    const experience = structuredClone(massieJustice.experience);
    const action = experience.episodes.find((episode) => episode.id === "dc-police-pursuit-rules").actions[0];
    action.importantContext.push(context);
    const report = validateEditorialStandardization({ candidate, experience });
    assert.equal(report.state, "blocked");
    assert.equal(report.findings.some((finding) => finding.ruleId === "DETAIL-001"), true);
  }
});

test("conclusion utility mutations are caught by stable proposition-aware rules", () => {
  const blind = {
    candidate: structuredClone(blindEditorialPipelineValidationFixture.candidate),
    experience: structuredClone(adaptEditorialIssueSlice(
      blindEditorialPipelineValidationFixture.candidate,
      blindEditorialPipelineValidationFixture.evidenceRows,
      EDITORIAL_EXPERIENCE_MODE.review,
    )),
  };
  const cases = [
    mutation("exhaustive inventory", "CONCLUSION-UTILITY-001", massieJustice, ({ candidate }) => {
      candidate.synthesis.conclusionModel.supporting_policy_clusters = [];
      candidate.synthesis.conclusionModel.evidence_episode_ids = candidate.memberEpisodeTrajectories.map((item) => item.episode_id);
      candidate.synthesis.compressionReport.policy_cluster_count = 0;
    }),
    mutation("uniform Nay coherent philosophy", "CONCLUSION-UTILITY-007", blind, ({ candidate }) => {
      candidate.synthesis.primary = "The uniform Nay record establishes a coherent public-safety philosophy.";
    }),
    mutation("uniform Yea coherent philosophy", "CONCLUSION-UTILITY-007", blind, ({ candidate, experience }) => {
      for (const action of experience.episodes.flatMap((episode) => episode.actions)) action.actionStatus = "yea";
      candidate.synthesis.primary = "The uniform Yea record establishes a coherent public-safety philosophy.";
    }),
    mutation("missing policy dimension", "CONCLUSION-UTILITY-003", massieJustice, ({ candidate }) => {
      candidate.synthesis.conclusionModel.thesis_proposition.policy_dimension_present = false;
    }),
    mutation("direction-only repeated thesis", "CONCLUSION-UTILITY-002", massieJustice, ({ candidate }) => {
      candidate.synthesis.conclusionModel.archetype = "substantive_repeated_pattern";
      candidate.synthesis.conclusionModel.thesis_proposition.policy_dimension_present = false;
    }),
    mutation("missing heterogeneous uniform contrast", "CONCLUSION-UTILITY-004", blind, ({ candidate }) => {
      candidate.synthesis.conclusionModel.contrast_proposition = null;
    }),
    mutation("duplicates all analytical bullets", "CONCLUSION-UTILITY-005", massieJustice, ({ candidate }) => {
      candidate.synthesis.compressionReport.duplicated_analytical_propositions = ["trajectory", "repeated_pattern", "notable_choice"];
    }),
    mutation("circular conclusion", "CONCLUSION-UTILITY-006", massieJustice, ({ candidate }) => {
      candidate.synthesis.primary = "This is consistent opposition because the member opposed the reviewed proposals.";
    }),
    mutation("excessive qualification", "CONCLUSION-UTILITY-008", massieJustice, ({ candidate }) => {
      candidate.synthesis.primary = "The record is limited, but however it cannot establish motive, although it does not establish a philosophy.";
    }),
    mutation("unnecessary named episodes", "CONCLUSION-UTILITY-009", massieJustice, ({ candidate }) => {
      candidate.synthesis.compressionReport.individually_named_episode_count = 5;
    }),
    mutation("label and archetype mismatch", "CONCLUSION-UTILITY-010", massieJustice, ({ candidate }) => {
      candidate.synthesis.readerFacingLabel = "Uniform opposition without a common policy throughline";
    }),
    mutation("duplicate receipt context", "DETAIL-001", massieJustice, ({ experience }) => {
      const action = experience.episodes.find((episode) => episode.id === "dc-police-pursuit-rules").actions[0];
      action.importantContext.push("A Nay does not reveal which objection drove the vote.");
      action.importantContext.push("The substitute included exceptions; it was not an unconditional pursuit mandate.");
    }),
  ];
  assert.equal(cases.length, 12);
  for (const item of cases) {
    const report = validateEditorialStandardization({ candidate: item.candidate, experience: item.experience, ...item.options });
    assert.equal(report.findings.some((finding) => finding.ruleId === item.expectedRule), true, `${item.name}: ${JSON.stringify(report.findings)}`);
    if (item.expectedRule !== "CONCLUSION-UTILITY-008") assert.equal(report.state, "blocked", item.name);
  }
});

function mutation(name, expectedRule, source, mutate) {
  const value = { name, expectedRule, candidate: structuredClone(source.candidate), experience: structuredClone(source.experience), options: {} };
  mutate(value);
  return value;
}
