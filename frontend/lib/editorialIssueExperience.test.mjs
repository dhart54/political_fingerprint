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
import { groupOfficialSources } from "./editorialIssuePresentation.mjs";
import { editorialIssueSlices } from "./editorialIssueSlices.mjs";
import {
  syntheticEditorialCandidate,
  syntheticEditorialIssueFixtureData,
  syntheticEditorialLegislator,
} from "./editorialIssueTestFixtures.mjs";
import { valerieFousheeEconomyEditorialGold } from "./valerieFousheeEconomyEditorialGold.mjs";

const fousheeRows = editorialGoldIssueFixtureData.evidenceByDomain.ECONOMY_TAXES.evidence;
const fousheeCandidate = editorialIssueSlices[0];

test("pending editorial content is review-only and production requires all publication gates", () => {
  const review = selectEditorialIssueExperience({
    domain: "ECONOMY_TAXES",
    evidenceRows: fousheeRows,
    legislator: editorialGoldLegislator,
    mode: EDITORIAL_EXPERIENCE_MODE.review,
  });
  assert.ok(review);
  assert.equal(review.publication.isReview, true);
  assert.equal(selectEditorialIssueExperience({ domain: "ECONOMY_TAXES", evidenceRows: fousheeRows, legislator: editorialGoldLegislator }), null);

  for (const publication of [
    { editorialStatus: "human_approval_pending", benchmarkStatus: "gold_benchmark", productionEligible: true },
    { editorialStatus: "human_approved", benchmarkStatus: "not_promoted", productionEligible: true },
    { editorialStatus: "human_approved", benchmarkStatus: "gold_benchmark", productionEligible: false },
  ]) {
    assert.equal(isEditorialSliceEligible({ candidate: { publication } }), false);
  }
  assert.equal(isEditorialSliceEligible({ candidate: syntheticEditorialCandidate }), true);
});

test("selector falls back for absent, mismatched, incomplete, and ineligible slices", () => {
  assert.equal(selectEditorialIssueExperience({ candidates: [], domain: "ECONOMY_TAXES", evidenceRows: fousheeRows, legislator: editorialGoldLegislator }), null);
  assert.equal(selectEditorialIssueExperience({ domain: "HEALTH_SOCIAL", evidenceRows: fousheeRows, legislator: editorialGoldLegislator, mode: "review" }), null);
  assert.equal(selectEditorialIssueExperience({ domain: "ECONOMY_TAXES", evidenceRows: fousheeRows, legislator: { ...editorialGoldLegislator, bioguide_id: "different" }, mode: "review" }), null);
  assert.equal(selectEditorialIssueExperience({ domain: "ECONOMY_TAXES", evidenceRows: fousheeRows.slice(1), legislator: editorialGoldLegislator, mode: "review" }), null);
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
});

test("source grouping is optional, stable, deduplicated, and hides internal identifiers", () => {
  const groups = groupOfficialSources([
    { stableId: "roll-1", group: "Vote and legislative status", name: "Roll", locator: "first", url: "https://example.test/roll/1" },
    { stableId: "roll-1", group: "Vote and legislative status", name: "Duplicate", locator: "duplicate", url: "https://example.test/other" },
    { group: "Competing arguments", name: "Debate", locator: "page 2", url: "https://example.test/debate/" },
    { group: "Competing arguments", name: "Debate duplicate", locator: "page 3", url: "https://example.test/debate" },
  ]);
  assert.deepEqual(groups.map((group) => group.name), ["Vote and legislative status", "Competing arguments"]);
  assert.equal(groups.reduce((total, group) => total + group.items.length, 0), 2);
  assert.deepEqual(groupOfficialSources([]), []);

  const experience = selectEditorialIssueExperience({
    candidates: [syntheticEditorialCandidate],
    domain: "ENVIRONMENT_ENERGY",
    evidenceRows: syntheticEditorialIssueFixtureData.evidenceByDomain.ENVIRONMENT_ENERGY.evidence,
    legislator: syntheticEditorialLegislator,
  });
  assert.doesNotMatch(JSON.stringify(experience), /claim_id|source_id|agent_confidence|review_question/i);
});

test("Foushee Economy regression preserves counts, ordering, non-counting classes, copy, and pending statuses", () => {
  const experience = selectEditorialIssueExperience({ domain: "ECONOMY_TAXES", evidenceRows: fousheeRows, legislator: editorialGoldLegislator, mode: "review" });
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
  assert.match(positionSource, /selectEditorialIssueExperience/);
  assert.match(positionSource, /<EditorialIssueExperience experience=/);
  assert.match(fixtureSource, /<PositionByIssue/);
  assert.doesNotMatch(fixtureSource, /<EditorialIssueExperience/);
  assert.doesNotMatch(rendererSource, /F000477|Foushee|Economy & Taxes|roll-310|six substantive|four policy/i);
});

test("public bundle still excludes internal review fields and claim IDs", () => {
  const serialized = JSON.stringify(valerieFousheeEconomyEditorialGold);
  for (const forbidden of ["claim_id", "current_stored_copy", "agent_confidence", "human_approved", "gold_benchmark", "review_question"]) {
    assert.equal(serialized.includes(forbidden), false, forbidden);
  }
  assert.equal(valerieFousheeEconomyEditorialGold.human_approval_status, "human_approval_pending");
});
