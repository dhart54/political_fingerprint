import assert from "node:assert/strict";
import test from "node:test";

import {
  buildConcretePreferencePrompt,
  buildComparisonLine,
  buildIssuePatternRows,
  buildRecordNarrative,
  getDirectionalAlignmentPreferences,
} from "./profileNarrative.mjs";

const valerieRows = [
  {
    domain: "ECONOMY_TAXES",
    recorded_votes: 8,
    interpreted_support_count: 0,
    interpreted_oppose_count: 6,
    interpreted_other_count: 1,
  },
  {
    domain: "NATIONAL_SECURITY_FOREIGN",
    recorded_votes: 22,
    interpreted_support_count: 2,
    interpreted_oppose_count: 17,
    interpreted_other_count: 0,
  },
  {
    domain: "JUSTICE_PUBLIC_SAFETY",
    recorded_votes: 13,
    interpreted_support_count: 2,
    interpreted_oppose_count: 4,
    interpreted_other_count: 0,
  },
  {
    domain: "INFRASTRUCTURE_TECH_TRANSPORT",
    recorded_votes: 1,
    interpreted_support_count: 0,
    interpreted_oppose_count: 0,
    interpreted_other_count: 0,
  },
];

test("record narrative names strongest and mixed reviewed patterns without ideology claims", () => {
  const narrative = buildRecordNarrative({
    legislator: {
      name_display: "Valerie P. Foushee",
      chamber: "house",
      party: "D",
    },
    positions: valerieRows,
  });

  assert.match(narrative.headline, /strongest reviewed evidence is in Economy/);
  assert.match(narrative.body, /Economy/);
  assert.match(narrative.body, /National Security/);
  assert.match(narrative.evidenceLine, /31 reviewed Yes\/No meanings/);
  assert.equal(narrative.patternRows.length, 3);
  assert.doesNotMatch(
    `${narrative.headline} ${narrative.body}`,
    /liberal|conservative|extreme|always|corrupt|you should vote|consistent with the prior Congress|drift|shift|steady mix/i,
  );
});

test("record narrative avoids cross-Congress movement claims when both Congresses have evidence", () => {
  const narrative = buildRecordNarrative({
    legislator: {
      name_display: "Casey Rivera",
      chamber: "house",
      party: "D",
    },
    scope: "all",
    positions: [
      {
        domain: "ECONOMY_TAXES",
        recorded_votes: 8,
        interpreted_support_count: 4,
        interpreted_oppose_count: 0,
        interpreted_other_count: 0,
        comparison: {
          status: "consistent",
          statement: "The recent voting pattern is consistent with the prior Congress.",
        },
      },
    ],
  });

  assert.match(narrative.body, /Reviewed votes are available in both Congresses/);
  assert.match(narrative.body, /Congress-specific counts shown separately below/);
  assert.doesNotMatch(narrative.body, /motive|ideology|score|consistent with the prior Congress|drift|shift|steady/i);
});

test("comparison line stays unavailable when one Congress lacks enough reviewed evidence", () => {
  assert.equal(
    buildComparisonLine([
      {
        domain: "ECONOMY_TAXES",
        comparison: {
          status: "insufficient_evidence",
          statement: "There is not enough reviewed evidence to compare the two Congresses confidently.",
        },
      },
    ]),
    "Congress-specific counts are shown separately below when reviewed votes are available.",
  );
});

test("issue pattern rows preserve support and opposition counts", () => {
  const rows = buildIssuePatternRows(valerieRows);

  assert.deepEqual(
    rows.map((row) => [row.domain, row.supportCount, row.opposeCount, row.label]),
    [
      ["ECONOMY_TAXES", 0, 6, "Mostly opposed"],
      ["NATIONAL_SECURITY_FOREIGN", 2, 17, "Mixed"],
      ["JUSTICE_PUBLIC_SAFETY", 2, 4, "Mixed"],
    ],
  );
});

test("concrete preference prompts require enough reviewed Yes/No evidence", () => {
  const economyPrompt = buildConcretePreferencePrompt(valerieRows[0]);
  const sparsePrompt = buildConcretePreferencePrompt(valerieRows[3]);

  assert.equal(economyPrompt.canAsk, true);
  assert.match(economyPrompt.prompt, /budget framework and reconciliation/);
  assert.equal(sparsePrompt.canAsk, false);
});

test("only concrete directional choices are sent to alignment", () => {
  assert.deepEqual(
    getDirectionalAlignmentPreferences({
      ECONOMY_TAXES: "support_more_action",
      NATIONAL_SECURITY_FOREIGN: "views_differ",
      JUSTICE_PUBLIC_SAFETY: "not_sure",
      HEALTH_SOCIAL: "oppose_more_action",
    }),
    {
      ECONOMY_TAXES: "support_more_action",
      HEALTH_SOCIAL: "oppose_more_action",
    },
  );
});
