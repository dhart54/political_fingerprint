import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";

import { buildFindingIndex, buildSelectedIssueModel } from "./selectedIssueExperience.mjs";
import { buildPublicReceipt } from "./publicReceipt.mjs";

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

function receipt(actionId) {
  return buildPublicReceipt(rows.find((row) => row.canonical_action_id === actionId));
}

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

test("M14G renders exact governed EO and U.S. Code labels", () => {
  const expected = [
    [
      "house:119:1:332",
      "https://www.govinfo.gov/content/pkg/FR-2025-04-03/html/2025-05836.htm",
      "Executive order",
    ],
    [
      "house:119:2:184",
      "https://www.govinfo.gov/content/pkg/FR-2025-01-30/html/2025-02090.htm",
      "Executive order",
    ],
    [
      "house:119:1:79",
      "https://www.govinfo.gov/content/pkg/USCODE-2024-title20/html/USCODE-2024-title20-chap28-subchapIV-partG-sec1094.htm",
      "U.S. Code",
    ],
  ];
  for (const [actionId, url, label] of expected) {
    const source = receipt(actionId).actionSources.find((item) => item.url === url);
    assert.deepEqual(source, { label, url });
    assert.notEqual(source.label, "Bill or amendment text");
  }
});

test("action sources without an allowed public label retain URL-derived labels", () => {
  const legacyUrl = "https://www.govinfo.gov/content/pkg/FR-2025-04-03/html/2025-05836.htm";
  const withoutPublicLabel = buildPublicReceipt({
    source_basis: [{ label: "Executive order", url: legacyUrl }],
  });
  assert.deepEqual(withoutPublicLabel.actionSources, [{
    label: "Bill or amendment text",
    url: legacyUrl,
  }]);
  const arbitraryLabel = buildPublicReceipt({
    source_basis: [{ public_label: "Untrusted label", url: legacyUrl }],
  });
  assert.equal(arbitraryLabel.actionSources[0].label, "Bill or amendment text");
});
