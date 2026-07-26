import { expect, test } from "@playwright/test";

const actions = [32, 33, 130, 131, 166, 275, 299];

const positions = {
  scope_metadata: {
    congresses: [118, 119],
    requested_congresses: [118, 119],
    scope_label: "Full record",
  },
  positions: [
    {
      domain: "JUSTICE_PUBLIC_SAFETY",
      yea_count: 3,
      nay_count: 4,
      other_count: 0,
      total_votes: 7,
      recorded_votes: 7,
      interpreted_support_count: 3,
      interpreted_oppose_count: 4,
      interpreted_other_count: 0,
      interpreted_total: 7,
    },
  ],
};

const presentation = {
  schema_version: "editorial_public_presentations_api_v1",
  legislator_id: "leg_aaron_bean",
  member_bioguide_id: "F000477",
  scope: "all",
  presentations: [
    {
      issue_id: "JUSTICE_PUBLIC_SAFETY",
      requested_scope: "all",
      reviewed_scope: "119",
      tier: "reviewed_conclusion",
      tier_badge: "Reviewed conclusion",
      teaser: "The reviewed 119th-Congress sample shows a divide between safeguards and reviewed police authority measures.",
      coverage_text: "This conclusion covers 7 reviewed substantive actions across 5 independent policy episodes in the 119th Congress.",
      scope_boundary: "This conclusion remains bounded to the reviewed 119th-Congress record.",
      conclusion: {
        headline: "A divide by policy mechanism in the reviewed sample",
        body: "In this reviewed 119th-Congress sample, Foushee supported safeguards, research, reporting, or implementation constraints while opposing reviewed measures involving police tools, operational authority, or rollback of policing restrictions.",
      },
      repeated_patterns: [
        {
          proposition_id: "prop:support",
          heading: "Safeguards, research, reporting, and implementation constraints",
          body: "Across independent episodes, the reviewed wording describes support for these mechanisms.",
          action_ids: ["house:119:1:32", "house:119:1:131", "house:119:1:166"],
        },
        {
          proposition_id: "prop:oppose",
          heading: "Police tools, operational authority, and safeguard rollbacks",
          body: "Across independent episodes, the reviewed wording describes opposition to these mechanisms.",
          action_ids: ["house:119:1:130", "house:119:1:275", "house:119:1:299"],
        },
      ],
      policy_trajectories: [
        {
          proposition_id: "prop:fentanyl",
          heading: "The fentanyl episode is mixed",
          body: "The related amendment and passage stages remain one mixed episode.",
          action_ids: ["house:119:1:32", "house:119:1:33", "house:119:1:166"],
        },
      ],
      limitations: [
        {
          heading: "Limits of this read",
          body: "The record does not establish motive, ideology, character, future behavior, or a broad Justice philosophy.",
        },
      ],
    },
  ],
};

test.beforeEach(async ({ page }) => {
  await page.route("http://localhost:8000/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/editorial-presentations")) {
      await route.fulfill({ json: presentation });
      return;
    }
    if (path.endsWith("/positions")) {
      await route.fulfill({ json: positions });
      return;
    }
    if (path.endsWith("/positions/JUSTICE_PUBLIC_SAFETY/evidence")) {
      await route.fulfill({
        json: {
          domain: "JUSTICE_PUBLIC_SAFETY",
          evidence: actions.map(vote),
        },
      });
      return;
    }
    if (path.endsWith("/fingerprint")) {
      await route.fulfill({ json: { fingerprint: [] } });
      return;
    }
    if (path.endsWith("/contact")) {
      await route.fulfill({ json: { contact_status: "not_loaded" } });
      return;
    }
    if (path.includes("/metadata/coverage") || path.includes("/coverage/metadata")) {
      await route.fulfill({
        json: {
          eligible_roll_call_count: 7,
          legislator_count: 1,
          source_url_share: 1,
        },
      });
      return;
    }
    await route.fulfill({ json: {} });
  });
});

test("IR-native conclusion is display-only and supporting controls resolve to receipts", async ({ page }) => {
  await page.goto("/");
  const card = page.getByRole("button", { name: "Inspect Justice & Public Safety votes" });
  await expect(card).toContainText("Reviewed conclusion");
  await expect(card).toContainText("reviewed 119th-Congress sample");
  await card.click();

  const panel = page.getByTestId("editorial-presentation");
  await expect(panel).toHaveAttribute("data-presentation-tier", "reviewed_conclusion");
  await expect(panel).toContainText("A divide by policy mechanism");
  await expect(panel).toContainText("The fentanyl episode is mixed");
  await expect(panel).toContainText("bounded to the reviewed 119th-Congress record");

  await panel.getByRole("button", { name: "See supporting votes" }).first().click();
  const receipt = page.locator('[data-canonical-action-id="house:119:1:32"]').last();
  await expect(receipt).toBeVisible();
  await expect(receipt).toHaveAttribute("id", "vote-receipt-house-119-1-32");
  await expect(receipt).toHaveClass(/ring-2/);
});

test("IR-native presentation remains keyboard-accessible and responsive at 390px", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  const card = page.getByRole("button", { name: "Inspect Justice & Public Safety votes" });
  await card.focus();
  await page.keyboard.press("Enter");
  const panel = page.getByTestId("editorial-presentation");
  await expect(panel).toBeVisible();
  const supporting = panel.getByRole("button", { name: "See supporting votes" }).first();
  await supporting.focus();
  await expect(supporting).toBeFocused();
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(1);
});

test("/golden-render-fixture remains unavailable", async ({ page }) => {
  const response = await page.goto("/golden-render-fixture");
  expect(response?.status()).toBe(404);
});

function vote(roll) {
  const position = [32, 131, 166].includes(roll) ? "yea" : "nay";
  return {
    chamber: "house",
    classification_reason: "policy_vote",
    congress: 119,
    description: `Justice measure ${roll}`,
    interpretation_status: "interpreted",
    issue_domain: "JUSTICE_PUBLIC_SAFETY",
    issue_facet: "justice_public_safety",
    oppose_position: "nay",
    plain_english_summary: `Justice measure ${roll} summary.`,
    policy_effect: `Justice measure ${roll} effect.`,
    position,
    question: `Justice measure ${roll}`,
    roll_call_id: `house:119:1:${roll}`,
    rollcall_number: roll,
    source_basis: [],
    source_url: `https://clerk.house.gov/Votes/2025${roll}`,
    support_position: "yea",
    uncertainty_note: "",
    vote_context: {
      final_result: "passed",
      member_party: "D",
      member_party_majority_position: position,
      member_voted_with_party_majority: true,
      member_voted_with_winning_side: position === "yea",
      vote_type: roll === 32 ? "amendment" : "final_passage",
    },
    vote_date: "2025-01-10",
    vote_type: roll === 32 ? "amendment" : "final_passage",
    what_happened: `Justice measure ${roll} action.`,
    why_it_mattered: `Justice measure ${roll} stakes.`,
  };
}
