import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import {
  deriveIssueReadiness,
  groupIssueRowsByReadiness,
  sortIssueRowsByReadiness,
  summarizeReadinessGroups,
} from "./issueReadiness.mjs";

test("issue domains are grouped by readiness label", () => {
  const groups = groupIssueRowsByReadiness([
    positionRow({
      domain: "ECONOMY_TAXES",
      interpreted_oppose_count: 6,
      recorded_votes: 6,
    }),
    positionRow({
      domain: "JUSTICE_PUBLIC_SAFETY",
      interpreted_oppose_count: 3,
      interpreted_support_count: 2,
      recorded_votes: 5,
    }),
    positionRow({
      domain: "NATIONAL_SECURITY_FOREIGN",
      interpreted_oppose_count: 1,
      recorded_votes: 7,
    }),
    positionRow({
      domain: "HEALTH_SOCIAL",
      recorded_votes: 3,
    }),
  ]);
  const summary = summarizeReadinessGroups(groups);

  assert.deepEqual(summary, [
    {
      key: "strong_evidence",
      label: "Clearest vote evidence",
      readinessLabel: "Clear vote pattern",
      count: 1,
      domains: ["ECONOMY_TAXES"],
    },
    {
      key: "mixed_but_interpretable",
      label: "Evidence in more than one direction",
      readinessLabel: "Evidence in more than one direction",
      count: 1,
      domains: ["JUSTICE_PUBLIC_SAFETY"],
    },
    {
      key: "limited_evidence",
      label: "Limited vote evidence",
      readinessLabel: "Limited vote evidence",
      count: 1,
      domains: ["NATIONAL_SECURITY_FOREIGN"],
    },
    {
      key: "not_enough_to_summarize",
      label: "Receipts only",
      readinessLabel: "Receipts only",
      count: 1,
      domains: ["HEALTH_SOCIAL"],
    },
  ]);
});

test("strong evidence sorts above limited and not-ready evidence", () => {
  const sorted = sortIssueRowsByReadiness([
    positionRow({
      domain: "NATIONAL_SECURITY_FOREIGN",
      interpreted_oppose_count: 1,
      recorded_votes: 7,
    }),
    positionRow({
      domain: "HEALTH_SOCIAL",
      recorded_votes: 3,
    }),
    positionRow({
      domain: "ECONOMY_TAXES",
      interpreted_oppose_count: 6,
      recorded_votes: 6,
    }),
    positionRow({
      domain: "JUSTICE_PUBLIC_SAFETY",
      interpreted_oppose_count: 3,
      interpreted_support_count: 2,
      recorded_votes: 5,
    }),
  ]);

  assert.deepEqual(
    sorted.map((row) => row.domain),
    ["ECONOMY_TAXES", "JUSTICE_PUBLIC_SAFETY", "NATIONAL_SECURITY_FOREIGN", "HEALTH_SOCIAL"],
  );
});

test("dominant support or opposition is not grouped as mixed", () => {
  const nationalSecurity = deriveIssueReadiness(
    positionRow({
      domain: "NATIONAL_SECURITY_FOREIGN",
      interpreted_oppose_count: 128,
      interpreted_support_count: 22,
      recorded_votes: 150,
    }),
  );
  const closeSplit = deriveIssueReadiness(
    positionRow({
      domain: "JUSTICE_PUBLIC_SAFETY",
      interpreted_oppose_count: 4,
      interpreted_support_count: 3,
      recorded_votes: 7,
    }),
  );

  assert.equal(nationalSecurity.key, "strong_evidence");
  assert.match(nationalSecurity.reason, /one side predominates/);
  assert.equal(closeSplit.key, "mixed_but_interpretable");
});

test("limited and not-ready sections do not receive confident readiness labels", () => {
  const limited = deriveIssueReadiness(
    positionRow({
      interpreted_support_count: 2,
      recorded_votes: 5,
    }),
  );
  const notReady = deriveIssueReadiness(
    positionRow({
      recorded_votes: 5,
    }),
  );

  assert.equal(limited.key, "limited_evidence");
  assert.match(limited.reason, /should stay cautious/);
  assert.equal(notReady.key, "not_enough_to_summarize");
  assert.match(notReady.reason, /reviewed Yes\/No vote meaning is not loaded yet/);
});

test("representative issue picker uses neutral evidence navigation without readiness conclusions", () => {
  const componentSource = readFileSync(new URL("../components/PositionByIssue.js", import.meta.url), "utf8");

  assert.match(componentSource, /function BasicIssueList/);
  assert.match(componentSource, /Open another issue to inspect its available vote receipts/);
  assert.match(componentSource, /without combining them into a broader issue conclusion/);
  assert.doesNotMatch(componentSource, /IssueReadinessTile|Clearest vote evidence|vote pattern|buildTakeaway/);
  assert.doesNotMatch(
    componentSource,
    /is corrupt|you should vote|support this candidate|oppose this candidate|bought|extreme|radical|worst|best politician/i,
  );
});

function positionRow(overrides = {}) {
  return {
    domain: "ECONOMY_TAXES",
    interpreted_oppose_count: 0,
    interpreted_other_count: 0,
    interpreted_support_count: 0,
    interpreted_total: 0,
    nay_count: 0,
    nay_share: 0,
    other_count: 0,
    recorded_votes: 0,
    total_votes: 0,
    yea_count: 0,
    yea_share: 0,
    ...overrides,
  };
}
