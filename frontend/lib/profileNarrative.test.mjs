import assert from "node:assert/strict";
import test from "node:test";

import {
  buildIssueCardPreview,
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
    interpreted_support_count: 3,
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

  assert.match(narrative.headline, /clearest reviewed issue read is National Security/);
  assert.match(narrative.body, /National Security/);
  assert.match(narrative.body, /This reviewed sample shows mostly opposed reads in National Security & Foreign Policy and Economy & Taxes/);
  assert.match(narrative.body, /Start with the issue cards below, then open representative votes/);
  assert.equal(narrative.patternRows[1].domain, "ECONOMY_TAXES");
  assert.match(narrative.evidenceLine, /32 reviewed Yes\/No meanings/);
  assert.equal(narrative.patternRows.length, 3);
  assert.doesNotMatch(
    `${narrative.headline} ${narrative.body}`,
    /liberal|conservative|extreme|always|corrupt|you should vote|full career|ideology|motive|consistent with the prior Congress|drift|shift|steady mix/i,
  );
});

test("record narrative and pattern themes do not use raw evidence snippets", () => {
  const narrative = buildRecordNarrative({
    legislator: {
      name_display: "Valerie P. Foushee",
      chamber: "house",
      party: "D",
    },
    positions: [
      {
        domain: "NATIONAL_SECURITY_FOREIGN",
        recorded_votes: 150,
        interpreted_support_count: 22,
        interpreted_oppose_count: 128,
        interpreted_other_count: 0,
        what_happened: "this was a direct vote on Protecting America's Strategic Petroleum Reserve from China Act",
        reason: "the vote is useful because it records a direct position",
      },
    ],
  });
  const publicCopy = [
    narrative.headline,
    narrative.body,
    narrative.evidenceLine,
    ...narrative.patternRows.map((row) => `${row.label} ${row.theme}`),
    ...narrative.patternRows.map((row) => `${row.preview.status} ${row.preview.countLine} ${row.preview.themeLine} ${row.preview.receiptLine}`),
  ].join(" ");

  assert.match(publicCopy, /National Security & Foreign Policy/);
  assert.match(publicCopy, /defense authorization, foreign military sales, and national-security amendments/);
  assert.doesNotMatch(
    publicCopy,
    /this was a direct vote|the vote is useful because|records a direct position|Protecting America's Strategic Petroleum Reserve/i,
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
    rows.map((row) => [row.domain, row.supportCount, row.opposeCount, row.label, row.preview.status]),
    [
      ["NATIONAL_SECURITY_FOREIGN", 2, 17, "Mostly opposed", "Mostly opposed in reviewed sample"],
      ["ECONOMY_TAXES", 0, 6, "Mostly opposed", "Mostly opposed in reviewed sample"],
      ["JUSTICE_PUBLIC_SAFETY", 3, 4, "Mixed", "Mixed but interpretable"],
    ],
  );
});

test("issue card previews align dominant and mixed labels with reviewed counts", () => {
  const nationalSecurity = buildIssueCardPreview({
    domain: "NATIONAL_SECURITY_FOREIGN",
    recorded_votes: 198,
    interpreted_support_count: 22,
    interpreted_oppose_count: 128,
  });
  const economy = buildIssueCardPreview({
    domain: "ECONOMY_TAXES",
    recorded_votes: 86,
    interpreted_support_count: 3,
    interpreted_oppose_count: 59,
  });
  const justice = buildIssueCardPreview({
    domain: "JUSTICE_PUBLIC_SAFETY",
    recorded_votes: 75,
    interpreted_support_count: 7,
    interpreted_oppose_count: 51,
  });
  const immigration = buildIssueCardPreview({
    domain: "IMMIGRATION_BORDER",
    recorded_votes: 20,
    interpreted_support_count: 5,
    interpreted_oppose_count: 8,
  });

  assert.equal(nationalSecurity.status, "Mostly opposed in reviewed sample");
  assert.equal(nationalSecurity.countLine, "128 opposed / 22 supported across 150 reviewed Yes/No votes.");
  assert.match(nationalSecurity.themeLine, /Opposition concentrated in defense authorization, foreign military sales, and national-security amendments\./);
  assert.equal(nationalSecurity.receiptLine, "Open for representative votes and the full reviewed list.");

  assert.equal(economy.status, "Mostly opposed in reviewed sample");
  assert.equal(economy.countLine, "59 opposed / 3 supported across 62 reviewed Yes/No votes.");
  assert.match(economy.themeLine, /budget framework and reconciliation/);

  assert.equal(justice.status, "Mostly opposed in reviewed sample");
  assert.equal(justice.countLine, "51 opposed / 7 supported across 58 reviewed Yes/No votes.");
  assert.match(justice.themeLine, /criminal-law and public-safety measures/);

  assert.equal(immigration.status, "Mixed but interpretable");
  assert.equal(immigration.countLine, "8 opposed / 5 supported across 13 reviewed Yes/No votes.");
  assert.match(immigration.themeLine, /Votes point in more than one direction/);
  assert.doesNotMatch(`${immigration.status} ${immigration.themeLine}`, /mostly opposed|mostly supported/i);
});

test("limited one-sided issue rows stay limited in profile and card previews", () => {
  const oneOpposed = {
    domain: "NATIONAL_SECURITY_FOREIGN",
    recorded_votes: 10,
    interpreted_support_count: 0,
    interpreted_oppose_count: 1,
  };
  const twoSupported = {
    domain: "ECONOMY_TAXES",
    recorded_votes: 10,
    interpreted_support_count: 2,
    interpreted_oppose_count: 0,
  };

  const opposedPreview = buildIssueCardPreview(oneOpposed);
  const supportedPreview = buildIssueCardPreview(twoSupported);
  const patternRows = buildIssuePatternRows([oneOpposed, twoSupported]);
  const narrative = buildRecordNarrative({
    legislator: {
      name_display: "Valerie P. Foushee",
      chamber: "house",
      party: "D",
    },
    positions: [oneOpposed, twoSupported],
  });
  const publicCopy = [
    opposedPreview.status,
    opposedPreview.countLine,
    opposedPreview.themeLine,
    supportedPreview.status,
    supportedPreview.countLine,
    supportedPreview.themeLine,
    narrative.headline,
    narrative.body,
    ...patternRows.map((row) => `${row.label} ${row.preview.status} ${row.preview.countLine} ${row.preview.themeLine}`),
  ].join(" ");

  assert.equal(opposedPreview.status, "Limited reviewed evidence");
  assert.equal(opposedPreview.countLine, "1 reviewed Yes/No vote is available out of 10 recorded votes.");
  assert.doesNotMatch(`${opposedPreview.status} ${opposedPreview.themeLine}`, /Mostly opposed/i);

  assert.equal(supportedPreview.status, "Limited reviewed evidence");
  assert.equal(supportedPreview.countLine, "2 reviewed Yes/No votes are available out of 10 recorded votes.");
  assert.doesNotMatch(`${supportedPreview.status} ${supportedPreview.themeLine}`, /Mostly supported/i);

  assert.deepEqual(
    patternRows.map((row) => [row.domain, row.label, row.preview.status]),
    [
      ["ECONOMY_TAXES", "Reviewed evidence", "Limited reviewed evidence"],
      ["NATIONAL_SECURITY_FOREIGN", "Reviewed evidence", "Limited reviewed evidence"],
    ],
  );
  assert.match(narrative.body, /Start with the issue cards below, then open representative votes/);
  assert.match(narrative.body, /should stay cautious|limited/i);
  assert.equal(patternRows.length, 2);
  assert.doesNotMatch(publicCopy, /mostly opposed reads|mostly supported reads|Mostly opposed in reviewed sample|Mostly supported in reviewed sample/i);
  assert.doesNotMatch(publicCopy, /mostly opposed in (?:the )?reviewed sample|mostly supported in (?:the )?reviewed sample|has the clearest pattern:\s*mostly/i);
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
