import { expect, test } from "@playwright/test";

const actions = [32, 33, 130, 131, 166, 275, 299];
const foushee = {
  id: "leg_valerie_p_foushee",
  bioguide_id: "F000477",
  name_display: "Valerie P. Foushee",
  chamber: "house",
  state: "NC",
  district: "04",
  party: "D",
};

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
  legislator_id: "leg_valerie_p_foushee",
  member_bioguide_id: "F000477",
  scope: "all",
  presentations: [
    {
      issue_id: "JUSTICE_PUBLIC_SAFETY",
      requested_scope: "all",
      reviewed_scope: "119",
      tier: "reviewed_conclusion",
      tier_badge: "Reviewed conclusion",
      teaser: "The reviewed 119th-Congress sample shows support for reporting and for evidence, research, or implementation conditions in two independent episodes, alongside opposition to three specific proposals concerning retired-service firearm access, broader D.C. police pursuit authority, or repeal of most reviewed D.C. policing restrictions.",
      coverage_text: "This conclusion covers 7 reviewed substantive actions across 5 independent policy episodes in the 119th Congress.",
      scope_boundary: "This conclusion remains bounded to the reviewed 119th-Congress record.",
      conclusion: {
        headline: "A divide by policy mechanism in the reviewed sample",
        body: "In this reviewed 119th-Congress sample, Foushee supported reporting and evidence, research, or implementation conditions in two independent episodes, while opposing three specific proposals concerning retired-service firearm access, broader D.C. police pursuit authority, and repeal of most reviewed D.C. policing restrictions.",
      },
      repeated_patterns: [
        {
          proposition_id: "prop:support",
          heading: "Certification, fentanyl research provisions, and officer-safety reporting",
          body: "Across independent episodes, the reviewed wording describes support for these mechanisms.",
          action_ids: ["house:119:1:32", "house:119:1:131", "house:119:1:166"],
        },
        {
          proposition_id: "prop:oppose",
          heading: "Retired-service firearm access, D.C. pursuit authority, and policing-rule rollbacks",
          body: "Across independent episodes, Foushee opposed creating a reviewed federal program for eligible current and retired officers to buy qualifying retired agency firearms, broader D.C. police pursuit authority, and repeal of most reviewed D.C. policing restrictions.",
          action_ids: ["house:119:1:130", "house:119:1:275", "house:119:1:299"],
        },
      ],
      policy_trajectories: [
        {
          proposition_id: "prop:fentanyl",
          heading: "The fentanyl episode is mixed",
          body: "Within one fentanyl legislative episode, Foushee supported a certification amendment, opposed the earlier House bill, and supported a later related framework that permanently scheduled fentanyl-related substances and included research provisions. These related stages count as one episode for breadth and do not establish a change in position, motive, or philosophy.",
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

const nonDirectionalPresentation = {
  ...presentation,
  presentations: [
    {
      ...presentation.presentations[0],
      tier: "non_directional_or_limited_evidence",
      tier_badge: "Limited reviewed evidence",
      teaser: "The supplied record contains non-directional or limited evidence.",
      conclusion: null,
      repeated_patterns: [],
      policy_trajectories: [],
      limitations: [],
    },
  ],
};

test.beforeEach(async ({ page }, testInfo) => {
  const presentationPayload = testInfo.title.includes("non-directional tier")
    ? nonDirectionalPresentation
    : presentation;
  const handleApi = async (route) => {
    const path = new URL(route.request().url()).pathname.replace(/\/+$/, "");
    if (path.endsWith("/editorial-presentations")) {
      await route.fulfill({ json: presentationPayload });
      return;
    }
    if (path.endsWith("/lookup/zip/27701")) {
      await route.fulfill({
        json: {
          zip: "27701",
          state: "NC",
          district: "04",
          data_source: "database",
          source_metadata: {
            source_type: "reviewed_zip_map",
            source_retrieved_at: "2026-07-01",
            source_version: "reviewed-v1",
          },
          district_mappings: [
            { zip: "27701", state: "NC", district: "04" },
          ],
          house_rep: foushee,
          senators: [],
        },
      });
      return;
    }
    if (path.endsWith("/lookup/zip/27701/races")) {
      await route.fulfill({ json: { races: [] } });
      return;
    }
    if (path.endsWith("/lookup/zips")) {
      await route.fulfill({
        json: { data_source: "database", zips: ["27701"] },
      });
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
  };
  for (const pattern of [
    "**/lookup/**",
    "**/legislators/**",
    "**/metadata/**",
    "**/coverage/**",
  ]) {
    await page.route(pattern, handleApi);
  }
});

test("IR-native conclusion is display-only and supporting controls resolve to receipts", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Valerie P. Foushee", exact: true }),
  ).toBeVisible();
  const card = page.getByRole("button", { name: "Inspect Justice & Public Safety votes" });
  await expect(card).toContainText("Reviewed conclusion");
  await expect(card).toContainText("reviewed 119th-Congress sample");
  await card.click();

  const panel = page.getByTestId("editorial-presentation");
  await expect(panel).toHaveAttribute("data-presentation-tier", "reviewed_conclusion");
  await expect(panel).toContainText("A divide by policy mechanism");
  await expect(panel).toContainText("The fentanyl episode is mixed");
  await expect(panel).toContainText("bounded to the reviewed 119th-Congress record");

  const supporting = panel.getByRole("button", {
    name: "See supporting votes for Certification, fentanyl research provisions, and officer-safety reporting",
  });
  await supporting.click();
  const receipt = page.locator('[data-canonical-action-id="house:119:1:32"]').last();
  await expect(receipt).toBeVisible();
  await expect(receipt).toHaveAttribute("id", "vote-receipt-house-119-1-32");
  await expect(receipt).toHaveClass(/ring-2/);
  await expect(receipt).toBeFocused();
});

test("IR-native presentation remains keyboard-accessible and responsive at 390px", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.addInitScript(() => {
    window.__presentationScrollBehaviors = [];
    const original = Element.prototype.scrollIntoView;
    Element.prototype.scrollIntoView = function scrollIntoView(options) {
      window.__presentationScrollBehaviors.push(options?.behavior || null);
      return original.call(this, options);
    };
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Valerie P. Foushee", exact: true }),
  ).toBeVisible();
  const card = page.getByRole("button", { name: "Inspect Justice & Public Safety votes" });
  await card.focus();
  await page.keyboard.press("Enter");
  const panel = page.getByTestId("editorial-presentation");
  await expect(panel).toBeVisible();
  const supportingButtons = panel.getByRole("button", {
    name: /See supporting votes for/,
  });
  const labels = await supportingButtons.evaluateAll((buttons) =>
    buttons.map((button) => button.getAttribute("aria-label")),
  );
  expect(new Set(labels).size).toBe(labels.length);
  const supporting = supportingButtons.first();
  await supporting.focus();
  await expect(supporting).toBeFocused();
  await page.keyboard.press("Enter");
  const receipt = page.locator("#vote-receipt-house-119-1-32");
  await expect(receipt).toBeFocused();
  await expect(receipt).toHaveClass(/ring-2/);
  const scrollBehaviors = await page.evaluate(
    () => window.__presentationScrollBehaviors,
  );
  expect(scrollBehaviors).toContain("auto");
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(1);
});

test("supplied non-directional tier renders no analytical synthesis", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Valerie P. Foushee", exact: true }),
  ).toBeVisible();
  const card = page.getByRole("button", {
    name: "Inspect Justice & Public Safety votes",
  });
  await expect(card).toContainText("Limited reviewed evidence");
  await card.click();
  const panel = page.getByTestId("editorial-presentation");
  await expect(panel).toHaveAttribute(
    "data-presentation-tier",
    "non_directional_or_limited_evidence",
  );
  await expect(panel).toContainText(
    "The supplied record contains non-directional or limited evidence.",
  );
  await expect(panel).not.toContainText("A divide by policy mechanism");
  await expect(panel).not.toContainText("Repeated patterns");
  await expect(panel).not.toContainText(
    "Certification, fentanyl research provisions, and officer-safety reporting",
  );
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
