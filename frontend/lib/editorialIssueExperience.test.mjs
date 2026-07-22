import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { editorialGoldIssueFixtureData, editorialGoldLegislator } from "./editorialGoldRenderFixture.mjs";
import {
  EDITORIAL_EXPERIENCE_MODE,
  isEditorialExperienceRow,
  isEditorialSliceEligible,
  selectEditorialIssueExperience,
} from "./editorialIssueExperience.mjs";
import { buildImportantContext, groupOfficialSources } from "./editorialIssuePresentation.mjs";
import { productionEditorialIssueSlices } from "./editorialIssueProductionSlices.mjs";
import { reviewEditorialIssueSlices } from "./editorialIssueReviewSlices.mjs";
import { justiceEditorialIssueFixtureData } from "./justiceEditorialRenderFixture.mjs";
import {
  syntheticEditorialCandidate,
  syntheticEditorialIssueFixtureData,
  syntheticEditorialLegislator,
} from "./editorialIssueTestFixtures.mjs";
import { valerieFousheeEconomyEditorialGold } from "./valerieFousheeEconomyEditorialGold.mjs";

const fousheeRows = editorialGoldIssueFixtureData.evidenceByDomain.ECONOMY_TAXES.evidence;
const fousheeCandidate = reviewEditorialIssueSlices[0];
const justiceCandidate = reviewEditorialIssueSlices.find((candidate) => candidate.identity.issueId === "JUSTICE_PUBLIC_SAFETY");
const justiceRows = justiceEditorialIssueFixtureData.evidenceByDomain.JUSTICE_PUBLIC_SAFETY.evidence;

test("Justice review candidate uses the generic contract with explicit episodes", () => {
  const experience = selectEditorialIssueExperience({ candidates: reviewEditorialIssueSlices, domain: "JUSTICE_PUBLIC_SAFETY", evidenceRows: justiceRows, legislator: editorialGoldLegislator, mode: "review" });
  assert.ok(experience);
  assert.equal(justiceCandidate.publication.editorialStatus, "human_approval_pending");
  assert.equal(justiceCandidate.publication.productionEligible, false);
  assert.deepEqual(experience.indicators.map((item) => item.label), ["7 substantive votes", "5 policy episodes", "0 Not Voting", "6 context-only records"]);
  assert.equal(experience.records.length, 13);
  assert.equal(experience.records.filter((item) => item.inclusionClass === "substantive").length, 7);
  assert.equal(experience.records.filter((item) => item.inclusionClass === "context_only").length, 6);
  assert.equal(new Set(experience.records.filter((item) => item.inclusionClass === "substantive").map((item) => item.episodeId)).size, 5);
  assert.equal(experience.records.find((item) => item.id === "roll-131").arguments.opponents, undefined);
  assert.match(experience.synthesis.primary, /selective, guardrail-oriented approach/i);
  assert.equal(experience.synthesis.evidenceBreadth, "Bounded selective pattern");
  assert.equal(experience.synthesis.patterns.filter((item) => item.startsWith("Across independent episodes:")).length, 2);
  assert.match(experience.synthesis.howToRead, /strengthen, narrow, contradict, or replace/i);
});

test("Justice public sources use reader-facing groups and retain stable URLs", () => {
  const publicSources = justiceCandidate.source.interpretations.flatMap((row) => row.two_minute.sources)
    .concat(justiceCandidate.source.controls.flatMap((row) => row.sources));
  const allowed = new Set(["Vote and legislative status", "Bill or resolution text", "Nonpartisan analysis", "Competing arguments", "Additional official evidence"]);
  assert.ok(publicSources.every((source) => allowed.has(source.group)));
  assert.ok(publicSources.every((source) => !source.group.includes("_")));
  const experience = selectEditorialIssueExperience({ candidates: reviewEditorialIssueSlices, domain: "JUSTICE_PUBLIC_SAFETY", evidenceRows: justiceRows, legislator: editorialGoldLegislator, mode: "review" });
  const adaptedUrls = new Set(experience.records.flatMap((record) => record.sources || []).map((source) => source.url));
  assert.deepEqual(adaptedUrls, new Set(publicSources.map((source) => source.url)));
});

test("Justice candidate is excluded from ordinary production selection", () => {
  assert.equal(selectEditorialIssueExperience({ candidates: reviewEditorialIssueSlices, domain: "JUSTICE_PUBLIC_SAFETY", evidenceRows: justiceRows, legislator: editorialGoldLegislator }), null);
});

test("pending editorial content is review-only and production requires all publication gates", () => {
  const review = selectEditorialIssueExperience({
    candidates: reviewEditorialIssueSlices,
    domain: "ECONOMY_TAXES",
    evidenceRows: fousheeRows,
    legislator: editorialGoldLegislator,
    mode: EDITORIAL_EXPERIENCE_MODE.review,
  });
  assert.ok(review);
  assert.equal(review.publication.isReview, true);
  assert.equal(selectEditorialIssueExperience({ candidates: reviewEditorialIssueSlices, domain: "ECONOMY_TAXES", evidenceRows: fousheeRows, legislator: editorialGoldLegislator }), null);

  for (const publication of [
    { editorialStatus: "human_approval_pending", benchmarkStatus: "gold_benchmark", productionEligible: true },
    { editorialStatus: "human_approved", benchmarkStatus: "not_promoted", productionEligible: true },
    { editorialStatus: "human_approved", benchmarkStatus: "gold_benchmark", productionEligible: false },
  ]) {
    assert.equal(isEditorialSliceEligible({ candidate: { publication } }), false);
  }
  assert.equal(isEditorialSliceEligible({ candidate: syntheticEditorialCandidate }), true);
  assert.equal(isEditorialSliceEligible({ candidate: fousheeCandidate }), false);
});

test("production eligibility fails closed when registry and source approval statuses disagree", () => {
  const eligible = cloneCandidate(syntheticEditorialCandidate);
  assert.equal(isEditorialSliceEligible({ candidate: eligible }), true);

  const pendingSource = cloneCandidate(eligible);
  pendingSource.source.human_approval_status = "human_approval_pending";
  assert.equal(isEditorialSliceEligible({ candidate: pendingSource }), false);

  const pendingRegistry = cloneCandidate(eligible);
  pendingRegistry.publication.editorialStatus = "human_approval_pending";
  assert.equal(isEditorialSliceEligible({ candidate: pendingRegistry }), false);

  const pendingRecord = cloneCandidate(eligible);
  pendingRecord.source.interpretations[1].human_approval_status = "human_approval_pending";
  assert.equal(isEditorialSliceEligible({ candidate: pendingRecord }), false);

  const missingSourceStatus = cloneCandidate(eligible);
  delete missingSourceStatus.source.human_approval_status;
  assert.equal(isEditorialSliceEligible({ candidate: missingSourceStatus }), false);
});

test("selector falls back for absent, mismatched, incomplete, and ineligible slices", () => {
  assert.equal(selectEditorialIssueExperience({ candidates: [], domain: "ECONOMY_TAXES", evidenceRows: fousheeRows, legislator: editorialGoldLegislator }), null);
  assert.equal(selectEditorialIssueExperience({ candidates: reviewEditorialIssueSlices, domain: "HEALTH_SOCIAL", evidenceRows: fousheeRows, legislator: editorialGoldLegislator, mode: "review" }), null);
  assert.equal(selectEditorialIssueExperience({ candidates: reviewEditorialIssueSlices, domain: "ECONOMY_TAXES", evidenceRows: fousheeRows, legislator: { ...editorialGoldLegislator, bioguide_id: "different" }, mode: "review" }), null);
  assert.equal(selectEditorialIssueExperience({ candidates: reviewEditorialIssueSlices, domain: "ECONOMY_TAXES", evidenceRows: fousheeRows.slice(1), legislator: editorialGoldLegislator, mode: "review" }), null);
});

test("generic adapter supports different identities, counts, mixed actions, omitted sections, and non-counting records", () => {
  const rows = syntheticEditorialIssueFixtureData.evidenceByDomain.ENVIRONMENT_ENERGY.evidence;
  const experience = selectEditorialIssueExperience({
    candidates: [syntheticEditorialCandidate],
    domain: "ENVIRONMENT_ENERGY",
    evidenceRows: rows,
    legislator: syntheticEditorialLegislator,
  });
  assert.ok(experience);
  assert.equal(experience.identity.memberDisplayName, "Jordan Example");
  assert.equal(experience.identity.issueDisplayName, "Synthetic Energy Choices");
  assert.deepEqual(experience.indicators.map((item) => item.label), ["2 substantive votes", "2 policy episodes", "1 Not Voting", "1 context-only record"]);
  assert.equal(experience.records.length, 4);
  assert.deepEqual(experience.records.map((record) => record.inclusionClass), ["substantive", "substantive", "not_voting", "context_only"]);
  assert.equal(experience.synthesis.votingContext, undefined);
  assert.equal(experience.synthesis.howToRead, undefined);
  assert.match(experience.synthesis.primary, /deliberately mixed/i);
  assert.equal(isEditorialExperienceRow(rows[0], experience), true);
  assert.equal(experience.records[0].measure, "Synthetic Grid Pilot Act");
  assert.equal(syntheticEditorialCandidate.source.interpretations[0].measure_id, syntheticEditorialCandidate.source.interpretations[1].measure_id);
  assert.deepEqual(experience.records.slice(0, 2).map((record) => record.episodeId), ["synthetic-grid-pilot", "synthetic-permit-deadline"]);
  assert.equal(experience.records[2].episodeId, null);
});

test("source grouping is optional, stable, deduplicated, and hides internal identifiers", () => {
  const groups = groupOfficialSources([
    { stableId: "roll-1", source_id: "hidden-1", group: "Vote and legislative status", name: "Roll", locator: "first", url: "https://example.test/roll/1#member" },
    { stableId: "roll-1", group: "Vote and legislative status", name: "Same stable ID", locator: "duplicate", url: "https://example.test/other" },
    { stableId: "debate-1", group: "Competing arguments", name: "Debate", locator: "page 2", url: "https://example.test/debate/" },
    { stableId: "debate-2", group: "Competing arguments", name: "Same canonical URL", locator: "page 3", url: "https://example.test/debate#section" },
    { stableId: "missing-url", group: "Competing arguments", name: "Missing URL", locator: "none" },
    { stableId: "bad-url", group: "Competing arguments", name: "Bad URL", locator: "none", url: "not a url" },
    { stableId: "text-1", group: "Bill or resolution text", name: "Distinct text", locator: "section 1", url: "https://example.test/text" },
  ]);
  assert.deepEqual(groups.map((group) => group.name), ["Vote and legislative status", "Bill or resolution text", "Competing arguments"]);
  assert.equal(groups.reduce((total, group) => total + group.items.length, 0), 3);
  assert.deepEqual(groups.flatMap((group) => group.items.map((item) => item.url)), ["https://example.test/roll/1", "https://example.test/text", "https://example.test/debate"]);
  assert.doesNotMatch(JSON.stringify(groups), /source_id|stableId|hidden-1/);
  assert.deepEqual(groupOfficialSources([]), []);

  const experience = selectEditorialIssueExperience({
    candidates: [syntheticEditorialCandidate],
    domain: "ENVIRONMENT_ENERGY",
    evidenceRows: syntheticEditorialIssueFixtureData.evidenceByDomain.ENVIRONMENT_ENERGY.evidence,
    legislator: syntheticEditorialLegislator,
  });
  assert.doesNotMatch(JSON.stringify(experience), /claim_id|source_id|agent_confidence|review_question/i);
});

test("argument advocacy boundary handles both, one, neither, and explicit supplied boundaries", () => {
  const record = {
    inclusionClass: "substantive",
    additionalDetail: {},
    importantContext: [],
    arguments: {},
  };
  const withoutArguments = buildImportantContext(record);
  assert.ok(withoutArguments.some((item) => /does not reveal why/i.test(item)));
  assert.equal(withoutArguments.some((item) => /attributed advocacy/i.test(item)), false);

  const withArgument = buildImportantContext({ ...record, arguments: { supporters: { argument: "A supplied argument." } } });
  assert.ok(withArgument.includes("The argument shown is attributed advocacy, not evidence of the member's motive."));
  assert.equal(withArgument.some((item) => /supporter and opponent/i.test(item)), false);

  const opponentOnly = buildImportantContext({ ...record, arguments: { opponents: { argument: "A supplied argument." } } });
  assert.ok(opponentOnly.includes("The argument shown is attributed advocacy, not evidence of the member's motive."));

  const both = buildImportantContext({ ...record, arguments: { supporters: { argument: "Support." }, opponents: { argument: "Oppose." } } });
  assert.ok(both.includes("Supporter and opponent arguments are attributed advocacy, not evidence of the member's motive."));

  const explicit = "The reviewed materials did not provide a fair stage-specific opposing case.";
  const withExplicitBoundary = buildImportantContext({ ...record, arguments: { supporters: { argument: "Support." } }, institutionalAttribution: explicit });
  assert.ok(withExplicitBoundary.includes(explicit));
  assert.equal(withExplicitBoundary.some((item) => /argument shown is attributed advocacy/i.test(item)), false);

  const motiveSpecific = buildImportantContext({ ...record, arguments: { supporters: { argument: "Support." } }, institutionalAttribution: "This attributed argument does not explain why the member voted this way." });
  assert.equal(motiveSpecific.filter((item) => /why the member voted/i.test(item)).length, 1);
});

test("roll 131 keeps its explicit one-sided argument boundary without generic duplication", () => {
  const experience = selectEditorialIssueExperience({ candidates: reviewEditorialIssueSlices, domain: "JUSTICE_PUBLIC_SAFETY", evidenceRows: justiceRows, legislator: editorialGoldLegislator, mode: "review" });
  const record = experience.records.find((item) => item.id === "roll-131");
  const context = buildImportantContext(record);
  assert.ok(record.arguments.supporters);
  assert.equal(record.arguments.opponents, undefined);
  assert.equal(context.filter((item) => /No adequate stage-specific opposing argument/i.test(item)).length, 1);
  assert.equal(context.some((item) => /fair stage-specific opposing case/i.test(item)), false);
  assert.equal(context.some((item) => /Supporter and opponent arguments/i.test(item)), false);
  assert.equal(context.filter((item) => /does not reveal why|member's motive/i.test(item)).length, 1);
});

test("Foushee Economy regression preserves counts, ordering, non-counting classes, copy, and pending statuses", () => {
  const experience = selectEditorialIssueExperience({ candidates: reviewEditorialIssueSlices, domain: "ECONOMY_TAXES", evidenceRows: fousheeRows, legislator: editorialGoldLegislator, mode: "review" });
  assert.deepEqual(experience.records.map((record) => record.id), ["roll-310", "roll-285", "roll-281", "roll-182", "roll-156", "roll-100", "roll-50", "context-263", "context-180"]);
  assert.equal(experience.records.filter((record) => record.inclusionClass === "substantive").length, 6);
  assert.equal(experience.records.filter((record) => record.inclusionClass === "not_voting").length, 1);
  assert.equal(experience.records.filter((record) => record.inclusionClass === "context_only").length, 2);
  assert.match(experience.synthesis.primary, /six substantive votes represent four policy episodes/i);
  assert.ok(valerieFousheeEconomyEditorialGold.interpretations.every((entry) => entry.human_approval_status === "human_approval_pending"));
  assert.ok(valerieFousheeEconomyEditorialGold.controls.every((entry) => entry.human_approval_status === "human_approval_pending"));
  assert.equal(fousheeCandidate.publication.productionEligible, false);
});

test("fixture and real issue route share the selector, adapter, and renderer", () => {
  const positionSource = readFileSync(new URL("../components/PositionByIssue.js", import.meta.url), "utf8");
  const fixtureSource = readFileSync(new URL("../components/GoldenRenderFixture.js", import.meta.url), "utf8");
  const rendererSource = readFileSync(new URL("../components/EditorialIssueExperience.js", import.meta.url), "utf8");
  const selectorSource = readFileSync(new URL("./editorialIssueExperience.mjs", import.meta.url), "utf8");
  const productionRegistrySource = readFileSync(new URL("./editorialIssueProductionSlices.mjs", import.meta.url), "utf8");
  const reviewRegistrySource = readFileSync(new URL("./editorialIssueReviewSlices.mjs", import.meta.url), "utf8");
  assert.match(positionSource, /selectEditorialIssueExperience/);
  assert.match(positionSource, /<EditorialIssueExperience experience=/);
  assert.doesNotMatch(positionSource, /editorialIssueReviewSlices|valerieFousheeEconomyEditorialGold/);
  assert.match(selectorSource, /editorialIssueProductionSlices/);
  assert.doesNotMatch(selectorSource, /editorialIssueReviewSlices|valerieFousheeEconomyEditorialGold/);
  assert.doesNotMatch(productionRegistrySource, /F000477|Foushee|valerieFousheeEconomyEditorialGold|human_approval_pending/);
  assert.match(reviewRegistrySource, /valerieFousheeEconomyEditorialGold/);
  assert.equal(productionEditorialIssueSlices.length, 0);
  assert.match(fixtureSource, /<PositionByIssue/);
  assert.match(fixtureSource, /reviewEditorialIssueSlices/);
  assert.doesNotMatch(fixtureSource, /<EditorialIssueExperience/);
  assert.doesNotMatch(rendererSource, /F000477|Foushee|Economy & Taxes|roll-310|six substantive|four policy/i);
});

function cloneCandidate(candidate) {
  return JSON.parse(JSON.stringify(candidate));
}

test("public bundle still excludes internal review fields and claim IDs", () => {
  const serialized = JSON.stringify(valerieFousheeEconomyEditorialGold);
  for (const forbidden of ["claim_id", "current_stored_copy", "agent_confidence", "human_approved", "gold_benchmark", "review_question"]) {
    assert.equal(serialized.includes(forbidden), false, forbidden);
  }
  assert.equal(valerieFousheeEconomyEditorialGold.human_approval_status, "human_approval_pending");
});
