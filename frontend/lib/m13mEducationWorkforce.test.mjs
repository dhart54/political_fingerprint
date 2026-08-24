import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";

import { buildFindingIndex } from "./selectedIssueExperience.mjs";

const candidate = JSON.parse(fs.readFileSync(path.resolve("../docs/editorial/full_record_reviews/site_integration_candidates/f000477_education_workforce_119_v1/site_integration_candidate.json"), "utf8"));
const presentation = candidate.subject.presentation;

test("M13M exposes one pattern and one notable, with Mixed only on H.R. 1048", () => {
  const patterns = buildFindingIndex(presentation, [], "repeated_patterns");
  const notable = buildFindingIndex(presentation, [], "notable_choices");
  assert.equal(buildFindingIndex(presentation, [], "syntheses").length, 0);
  assert.equal(patterns.length, 1);
  assert.equal(notable.length, 1);
  assert.equal(patterns[0].showDirection, false);
  assert.equal(patterns[0].statusLabel, null);
  assert.equal(notable[0].showDirection, true);
  assert.equal(notable[0].statusLabel, "Mixed");
  assert.deepEqual([patterns[0].actionCount, notable[0].actionCount], [2, 2]);
});

test("M13M finding lineage is exactly four actions and excludes H.R. 1005", () => {
  const findings = [
    ...buildFindingIndex(presentation, [], "repeated_patterns"),
    ...buildFindingIndex(presentation, [], "notable_choices"),
  ];
  const actionIds = new Set(findings.flatMap((row) => row.actionIds));
  assert.equal(actionIds.size, 4);
  assert.equal(actionIds.has("house:119:1:312"), false);
});
