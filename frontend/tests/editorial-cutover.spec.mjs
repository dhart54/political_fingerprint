import { expect, test } from "@playwright/test";

const positions = {
  scope_metadata: {
    congresses: [119],
    requested_congresses: [119],
    scope_label: "Full record",
  },
  positions: [
    {
      domain: "ECONOMY_TAXES",
      recorded_votes: 5,
      interpreted_support_count: 1,
      interpreted_oppose_count: 1,
      interpreted_other_count: 3,
      yea_share: 0.5,
      nay_share: 0.5,
    },
  ],
};

const evidence = {
  domain: "ECONOMY_TAXES",
  evidence: [
    vote({ position: "yea", roll: 10 }),
    vote({ position: "nay", roll: 11 }),
    vote({ position: "present", roll: 12 }),
    vote({ position: "not_voting", roll: 13 }),
    vote({
      classification_reason: "limited_context",
      interpretation_status: "ambiguous",
      position: "yea",
      roll: 14,
      uncertainty_note: "The exact action has limited context.",
    }),
  ],
};

test.beforeEach(async ({ page }) => {
  await page.route("http://localhost:8000/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/positions")) {
      await route.fulfill({ json: positions });
      return;
    }
    if (path.includes("/positions/ECONOMY_TAXES/evidence")) {
      await route.fulfill({ json: evidence });
      return;
    }
    if (path.endsWith("/contact")) {
      await route.fulfill({ json: { contact_status: "not_loaded" } });
      return;
    }
    if (path.includes("/metadata/coverage") || path.includes("/coverage/metadata")) {
      await route.fulfill({
        json: {
          eligible_roll_call_count: 5,
          legislator_count: 1,
          source_url_share: 1,
        },
      });
      return;
    }
    await route.fulfill({ json: {} });
  });
});

test("representative page deliberately renders basic evidence and vote receipts", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Aaron Bean", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Show Votes" }).click();

  const summary = page.getByTestId("basic-evidence-summary");
  await expect(summary).toContainText("Vote evidence");
  await expect(summary).toContainText("does not combine them into a broader issue conclusion");
  await expect(summary).toContainText("Present");
  await expect(summary).toContainText("Not Voting");
  await expect(page.getByText("Representative votes", { exact: true })).toBeVisible();

  await page.getByRole("button", { name: "Show all reviewed votes" }).click();
  await expect(
    page.locator('a[href="https://clerk.house.gov/evs/2025/roll010.xml"]').first(),
  ).toHaveAttribute("href", "https://clerk.house.gov/evs/2025/roll010.xml");
  await expect(page.locator("body")).not.toContainText("Internal Server Error");
});

test("removed rich-editorial fixture route is deliberately unavailable", async ({ page }) => {
  const response = await page.goto("/golden-render-fixture");
  expect(response?.status()).toBe(404);
});

function vote({
  classification_reason = "policy_vote",
  interpretation_status = "interpreted",
  position,
  roll,
  uncertainty_note = "",
}) {
  const title = `Economic measure ${roll}`;
  return {
    chamber: "house",
    classification_reason,
    congress: 119,
    description: title,
    interpretation_status,
    issue_domain: "ECONOMY_TAXES",
    issue_facet: "economy_taxes",
    oppose_position: "nay",
    plain_english_summary: `${title} summary.`,
    policy_effect: `${title} effect.`,
    position,
    question: title,
    roll_call_id: `house:119:1:${roll}`,
    rollcall_number: roll,
    source_basis: [],
    source_url: `https://clerk.house.gov/evs/2025/roll${String(roll).padStart(3, "0")}.xml`,
    support_position: "yea",
    uncertainty_note,
    vote_context: {
      final_result: "passed",
      member_party: "R",
      member_party_majority_position: "yea",
      member_voted_with_party_majority: position === "yea",
      member_voted_with_winning_side: position === "yea",
      vote_type: "final_passage",
    },
    vote_date: "2025-01-10",
    vote_type: "final_passage",
    what_happened: `${title} action.`,
    why_it_mattered: `${title} stakes.`,
  };
}
