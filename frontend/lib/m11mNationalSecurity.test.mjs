import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";

import { buildFindingIndex } from "./selectedIssueExperience.mjs";

const candidate = JSON.parse(fs.readFileSync(path.resolve(
  "../docs/editorial/full_record_reviews/site_integration_candidates/f000477_national_security_foreign_119_v1/site_integration_candidate.json",
), "utf8"));
const presentation = candidate.subject.presentation;

test("M11M presentation exposes the exact governed surface accounting", () => {
  assert.equal(buildFindingIndex(presentation, [], "syntheses").length, 2);
  assert.equal(buildFindingIndex(presentation, [], "repeated_patterns").length, 8);
  assert.equal(buildFindingIndex(presentation, [], "policy_trajectories").length, 1);
  assert.equal(buildFindingIndex(presentation, [], "notable_choices").length, 6);
});

test("Ukraine remains semantically bound without a public Mixed marker", () => {
  const ukraine = buildFindingIndex(presentation, [], "repeated_patterns")
    .find((row) => row.wording_item_id === "wording:pattern:ukraine-assistance");
  assert.equal(ukraine.primary_sentence,
    "Opposed three proposals to restrict Ukraine aid and supported one measure authorizing support for Ukraine.");
  assert.equal(ukraine.evidence_count_label, "4 votes · 4 assistance choices");
  assert.equal(ukraine.showDirection, false);
  assert.equal(ukraine.statusLabel, null);
  assert.equal(ukraine.actionCount, 4);
  assert.equal(ukraine.episodeCount, 4);
});

test("War Powers exposes nine public votes while retaining AUMF lineage", () => {
  const warPowers = buildFindingIndex(presentation, [], "syntheses")
    .find((row) => row.wording_item_id === "wording:synthesis:war-powers");
  const aumf = buildFindingIndex(presentation, [], "notable_choices")
    .find((row) => row.wording_item_id === "wording:notable:aumf-repeal");
  assert.equal(warPowers.evidence_count_label,
    "9 votes · 9 country-specific resolutions");
  assert.equal(warPowers.actionCount, 9);
  assert.equal(warPowers.semantic_lineage_action_ids.length, 10);
  assert.equal(warPowers.actionIds.includes("house:119:1:244"), false);
  assert.equal(warPowers.semantic_lineage_action_ids.includes("house:119:1:244"), true);
  assert.deepEqual(aumf.actionIds, ["house:119:1:244"]);
});

test("no-direction findings have no substitute public status", () => {
  const findings = [
    ...buildFindingIndex(presentation, [], "syntheses"),
    ...buildFindingIndex(presentation, [], "repeated_patterns"),
  ];
  for (const id of [
    "wording:synthesis:security-assistance",
    "wording:pattern:ukraine-assistance",
  ]) {
    const finding = findings.find((row) => row.wording_item_id === id);
    assert.equal(finding.showDirection, false);
    assert.equal(finding.statusLabel, null);
  }
  const trajectory = buildFindingIndex(presentation, [], "policy_trajectories")[0];
  assert.equal(trajectory.showDirection, true);
  assert.equal(trajectory.statusLabel, "Mixed");
});

test("H.R. 8800 is absent from all analytical findings", () => {
  for (const field of ["syntheses", "repeated_patterns", "policy_trajectories", "notable_choices"]) {
    for (const item of buildFindingIndex(presentation, [], field)) {
      assert.equal(item.actionIds.includes("house:119:2:278"), false);
    }
  }
});
