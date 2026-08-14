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
  assert.equal(ukraine.statusLabel, "Bounded finding");
  assert.equal(ukraine.actionCount, 4);
  assert.equal(ukraine.episodeCount, 4);
});

test("H.R. 8800 is absent from all analytical findings", () => {
  for (const field of ["syntheses", "repeated_patterns", "policy_trajectories", "notable_choices"]) {
    for (const item of buildFindingIndex(presentation, [], field)) {
      assert.equal(item.actionIds.includes("house:119:2:278"), false);
    }
  }
});
