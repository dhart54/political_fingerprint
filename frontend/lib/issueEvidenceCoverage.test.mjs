import assert from "node:assert/strict";
import test from "node:test";

import {
  DOMAIN_DESCRIPTIONS,
  DOMAIN_ORDER,
  getDomainDescription,
  getEvidenceCoverageLabel,
  getRecordedActionComposition,
  orderIssueRowsByEvidenceUsefulness,
  pluralizeCountNoun,
} from "./issueEvidenceCoverage.mjs";

test("orders issue rows by neutral evidence usefulness with stable domain ties", () => {
  const ordered = orderIssueRowsByEvidenceUsefulness([
    row({ domain: "JUSTICE_PUBLIC_SAFETY", total_votes: 4, interpreted_support_count: 1 }),
    row({ domain: "ENVIRONMENT_ENERGY", total_votes: 5 }),
    row({ domain: "EDUCATION_WORKFORCE", total_votes: 4, interpreted_oppose_count: 2 }),
    row({ domain: "ECONOMY_TAXES", total_votes: 4, interpreted_support_count: 2 }),
  ]);

  assert.deepEqual(
    ordered.map(({ domain }) => domain),
    [
      "ENVIRONMENT_ENERGY",
      "ECONOMY_TAXES",
      "EDUCATION_WORKFORCE",
      "JUSTICE_PUBLIC_SAFETY",
    ],
  );
});

test("reversing every Yea and Nay leaves usefulness ordering unchanged", () => {
  const rows = [
    row({ domain: "ECONOMY_TAXES", yea_count: 7, nay_count: 1, total_votes: 9 }),
    row({ domain: "HEALTH_SOCIAL", yea_count: 2, nay_count: 5, total_votes: 8 }),
    row({ domain: "JUSTICE_PUBLIC_SAFETY", yea_count: 1, nay_count: 1, total_votes: 3 }),
  ];
  const reversed = rows.map((item) => ({
    ...item,
    yea_count: item.nay_count,
    nay_count: item.yea_count,
  }));

  assert.deepEqual(
    orderIssueRowsByEvidenceUsefulness(rows).map(({ domain }) => domain),
    orderIssueRowsByEvidenceUsefulness(reversed).map(({ domain }) => domain),
  );
});

test("every supported domain has one shared member-neutral description", () => {
  assert.deepEqual(Object.keys(DOMAIN_DESCRIPTIONS), DOMAIN_ORDER);
  for (const domain of DOMAIN_ORDER) {
    const description = getDomainDescription(domain);
    assert.ok(description.length > 30);
    assert.doesNotMatch(
      description,
      /member|legislator|representative|senator|supports|opposes|yea|nay|party/i,
    );
  }
  assert.equal(
    getDomainDescription("ECONOMY_TAXES"),
    getDomainDescription("ECONOMY_TAXES"),
  );
});

test("coverage labels are bounded by evidence availability", () => {
  assert.equal(getEvidenceCoverageLabel(row({ total_votes: 0 })), "No evidence");
  assert.equal(
    getEvidenceCoverageLabel(row({ other_count: 1, total_votes: 1 })),
    "Non-directional evidence",
  );
  assert.equal(
    getEvidenceCoverageLabel(row({ yea_count: 2, total_votes: 2 })),
    "Receipts only",
  );
  assert.equal(
    getEvidenceCoverageLabel(row({ total_votes: 2, interpreted_support_count: 1 })),
    "Limited record",
  );
  assert.equal(
    getEvidenceCoverageLabel(row({ total_votes: 5, interpreted_oppose_count: 3 })),
    "Developing record",
  );
  assert.equal(
    getEvidenceCoverageLabel(row({ total_votes: 10, interpreted_support_count: 6, interpreted_oppose_count: 2 })),
    "Broad reviewed record",
  );
});

test("action composition reports recorded states without policy direction labels", () => {
  const composition = getRecordedActionComposition(
    row({ yea_count: 4, nay_count: 3, other_count: 3, total_votes: 99 }),
  );

  assert.deepEqual(
    composition.map(({ label, count }) => ({ label, count })),
    [
      { label: "Yea", count: 4 },
      { label: "Nay", count: 3 },
      { label: "Non-directional / context", count: 3 },
    ],
  );
  assert.equal(Math.round(composition.reduce((sum, item) => sum + item.percent, 0)), 100);
  assert.deepEqual(composition.map(({ percent }) => percent), [40, 30, 30]);
  assert.doesNotMatch(JSON.stringify(composition), /support|oppose|aligned|favorable/i);
});

test("count nouns use correct singular and plural forms", () => {
  assert.equal(pluralizeCountNoun(1, "legislator"), "legislator");
  assert.equal(pluralizeCountNoun(2, "legislator"), "legislators");
  assert.equal(pluralizeCountNoun(1, "recorded action"), "recorded action");
  assert.equal(pluralizeCountNoun(0, "recorded action"), "recorded actions");
  assert.equal(pluralizeCountNoun(1, "issue area", "issue areas"), "issue area");
});

function row(overrides = {}) {
  return {
    domain: "ECONOMY_TAXES",
    interpreted_oppose_count: 0,
    interpreted_other_count: 0,
    interpreted_support_count: 0,
    nay_count: 0,
    other_count: 0,
    total_votes: 0,
    yea_count: 0,
    ...overrides,
  };
}
