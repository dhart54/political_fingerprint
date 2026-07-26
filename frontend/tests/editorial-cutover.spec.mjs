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
      yea_count: 2,
      nay_count: 2,
      other_count: 1,
      total_votes: 5,
      recorded_votes: 4,
      interpreted_support_count: 1,
      interpreted_oppose_count: 1,
      interpreted_other_count: 3,
      yea_share: 0.5,
      nay_share: 0.5,
    },
    {
      domain: "EDUCATION_WORKFORCE",
      yea_count: 0,
      nay_count: 0,
      other_count: 1,
      total_votes: 1,
      recorded_votes: 0,
      interpreted_support_count: 0,
      interpreted_oppose_count: 0,
      interpreted_other_count: 1,
    },
    {
      domain: "ENVIRONMENT_ENERGY",
      yea_count: 0,
      nay_count: 0,
      other_count: 1,
      total_votes: 1,
      recorded_votes: 0,
      interpreted_support_count: 0,
      interpreted_oppose_count: 0,
      interpreted_other_count: 1,
    },
    {
      domain: "HEALTH_SOCIAL",
      yea_count: 0,
      nay_count: 0,
      other_count: 0,
      total_votes: 0,
      recorded_votes: 0,
      interpreted_support_count: 0,
      interpreted_oppose_count: 0,
      interpreted_other_count: 0,
    },
  ],
};

const evidenceByDomain = {
  ECONOMY_TAXES: {
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
  },
  EDUCATION_WORKFORCE: {
    domain: "EDUCATION_WORKFORCE",
    evidence: [vote({ domain: "EDUCATION_WORKFORCE", position: "not_voting", roll: 20 })],
  },
  ENVIRONMENT_ENERGY: {
    domain: "ENVIRONMENT_ENERGY",
    evidence: [vote({ domain: "ENVIRONMENT_ENERGY", position: "present", roll: 30 })],
  },
};

test.beforeEach(async ({ page }) => {
  await page.route("http://localhost:8000/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/positions")) {
      await route.fulfill({ json: positions });
      return;
    }
    const evidenceMatch = path.match(/\/positions\/([^/]+)\/evidence$/);
    if (evidenceMatch && evidenceByDomain[evidenceMatch[1]]) {
      await route.fulfill({ json: evidenceByDomain[evidenceMatch[1]] });
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
  await expect(page.getByText("Record Coverage", { exact: true })).toBeVisible();
  await expect(page.getByText("legislator", { exact: true })).toBeVisible();
  await expect(page.getByText("eligible roll calls", { exact: true })).toBeVisible();
  await expect(page.locator("body")).not.toContainText(
    /clearest(?: reviewed)? patterns?|strongest issue evidence|strongest issue card|best read/i,
  );
  await expect(page.getByText("Best-covered issue", { exact: true })).toBeVisible();
  const economyCard = page.getByRole("button", { name: "Inspect Economy & Taxes votes" });
  await expect(economyCard).toHaveCount(1);
  const compositionLegend = economyCard.getByRole("list", { name: "Recorded action composition legend" });
  await expect(compositionLegend).toContainText("Yea 2");
  await expect(compositionLegend).toContainText("Nay 2");
  await expect(compositionLegend).toContainText("Non-directional / context 1");
  await expect(compositionLegend).not.toContainText("Present");
  await expect(page.getByText(/Budgets, taxation, government funding/).first()).toBeVisible();
  await expect(page.getByRole("button", { name: /Inspect Health & Social Services votes/i })).toHaveCount(0);
  const profileIssueCards = page.locator('section').filter({ hasText: "Record Coverage" }).getByRole("button", { name: /Inspect .* votes/i });
  await expect(profileIssueCards.nth(0)).toHaveAttribute("aria-label", "Inspect Economy & Taxes votes");
  await expect(page.getByRole("region", { name: "Explore all issue evidence" })).toHaveCount(0);
  await economyCard.focus();
  await page.keyboard.press("Enter");

  const summary = page.getByTestId("basic-evidence-summary");
  await expect(summary).toContainText("Vote evidence");
  await expect(summary).toContainText("does not combine them into a broader issue conclusion");
  await expect(summary).toContainText("Present");
  await expect(summary).toContainText("Not Voting");
  await expect(page.getByText("Reviewed substantive Yes/No", { exact: true })).toBeVisible();

  await page.getByRole("button", { name: "Show all vote receipts" }).click();
  await expect(
    page.locator('a[href="https://clerk.house.gov/evs/2025/roll010.xml"]').first(),
  ).toHaveAttribute("href", "https://clerk.house.gov/evs/2025/roll010.xml");
  await expect(page.locator("body")).not.toContainText("Internal Server Error");
});

test("non-directional-only issue records remain selectable with receipts and no directional conclusion", async ({ page }) => {
  await page.goto("/");

  await page.getByRole("button", { name: "Inspect Education & Workforce votes" }).first().click();
  const educationSummary = page.getByTestId("basic-evidence-summary");
  await expect(educationSummary).toContainText("Not Voting");
  await expect(educationSummary).not.toContainText(/support|opposition/i);
  await expect(
    page.locator('a[href="https://clerk.house.gov/evs/2025/roll020.xml"]').first(),
  ).toHaveAttribute("href", "https://clerk.house.gov/evs/2025/roll020.xml");

  await page.getByRole("button", { name: "Inspect Environment & Energy votes" }).first().click();
  const environmentSummary = page.getByTestId("basic-evidence-summary");
  await expect(environmentSummary).toContainText("Present");
  await expect(environmentSummary).not.toContainText(/support|opposition/i);
  await expect(
    page.locator('a[href="https://clerk.house.gov/evs/2025/roll030.xml"]').first(),
  ).toHaveAttribute("href", "https://clerk.house.gov/evs/2025/roll030.xml");
});

test("removed rich-editorial fixture route is deliberately unavailable", async ({ page }) => {
  const response = await page.goto("/golden-render-fixture");
  expect(response?.status()).toBe(404);
});

function vote({
  classification_reason = "policy_vote",
  domain = "ECONOMY_TAXES",
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
    issue_domain: domain,
    issue_facet: domain.toLowerCase(),
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
