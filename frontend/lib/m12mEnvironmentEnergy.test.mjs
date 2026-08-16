import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";

import { buildFindingIndex } from "./selectedIssueExperience.mjs";

const candidate = JSON.parse(fs.readFileSync(path.resolve("../docs/editorial/full_record_reviews/site_integration_candidates/f000477_environment_energy_119_v1/site_integration_candidate.json"), "utf8"));
const presentation = candidate.subject.presentation;

test("M12M exposes one synthesis and three patterns without invented direction", () => {
  const findings = [...buildFindingIndex(presentation, [], "syntheses"), ...buildFindingIndex(presentation, [], "repeated_patterns")];
  assert.equal(findings.length, 4);
  for (const finding of findings) {
    assert.equal(finding.showDirection, false);
    assert.equal(finding.statusLabel, null);
  }
  assert.deepEqual(findings.map((row) => row.actionCount), [13, 2, 4, 7]);
});

test("M12M excludes non-directional and no-proposition actions", () => {
  const findings = [...buildFindingIndex(presentation, [], "syntheses"), ...buildFindingIndex(presentation, [], "repeated_patterns")];
  for (const actionId of ["house:119:2:136"]) {
    assert.equal(findings.some((row) => row.actionIds.includes(actionId)), false);
  }
});
