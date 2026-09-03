import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";

import { buildFindingIndex, buildSelectedIssueModel } from "./selectedIssueExperience.mjs";

const candidate = JSON.parse(fs.readFileSync(path.resolve("../docs/editorial/site_integration_candidates/f000477_education_workforce_m14g_v1/site_integration_candidate.json"), "utf8"));
const presentation = candidate.subject.presentation;
const rows = candidate.subject.receipt_projections;

test("M14G resolves to three findings and six supporting actions", () => {
  const model = buildSelectedIssueModel({ presentation, rows, scope: "119" });
  assert.equal(model.interpretation.findingCount, 3);
  assert.equal(model.interpretation.supportingVoteCount, 6);
  assert.equal(model.evidence.count, 17);
});
test("M14G exposes two directionless patterns and one Mixed notable choice", () => {
  const patterns = buildFindingIndex(presentation, rows, "repeated_patterns");
  const notable = buildFindingIndex(presentation, rows, "notable_choices");
  assert.equal(patterns.length, 2);
  assert.equal(notable.length, 1);
  assert.deepEqual(patterns.map((item) => item.showDirection), [false, false]);
  assert.equal(notable[0].showDirection, true);
  assert.equal(notable[0].statusLabel, "Mixed");
  assert.equal(buildFindingIndex(presentation, rows, "syntheses").length, 0);
  assert.equal(buildFindingIndex(presentation, rows, "policy_trajectories").length, 0);
});
