import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";

import { buildFindingIndex, buildSelectedIssueModel } from "./selectedIssueExperience.mjs";

process.env.NEXT_PUBLIC_API_BASE_URL = "http://preview.test";
process.env.NEXT_PUBLIC_EDITORIAL_PRESENTATION_PREVIEW = "m14g-education-workforce";
const {
  fetchEditorialPresentations,
  fetchLegislatorProfile,
  fetchPositionEvidence,
  fetchPositions,
} = await import("./api.js");

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

test("M14G frontend opt-in routes all four reads through the detached API", async () => {
  const requests = [];
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url) => {
    requests.push(String(url));
    return { ok: true, json: async () => ({}) };
  };
  try {
    await fetchLegislatorProfile({ legislatorId: "leg_valerie_p_foushee" });
    await fetchEditorialPresentations({ legislatorId: "leg_valerie_p_foushee", scope: "119" });
    await fetchPositions({ legislatorId: "leg_valerie_p_foushee", scope: "119" });
    await fetchPositionEvidence({
      legislatorId: "leg_valerie_p_foushee",
      domain: "EDUCATION_WORKFORCE",
      scope: "119",
    });
  } finally {
    globalThis.fetch = originalFetch;
  }
  assert.equal(requests.length, 4);
  assert.ok(requests.every((url) => url.startsWith("http://preview.test/preview/m14g/legislators/")));
  assert.ok(requests.every((url) => url.includes("candidate=m14g-education-workforce")));
});
