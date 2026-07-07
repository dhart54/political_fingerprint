import { expect, test } from "@playwright/test";

const houseRep = {
  id: "leg_valerie_foushee",
  bioguide_id: "F000481",
  name_display: "Valerie P. Foushee",
  chamber: "house",
  state: "NC",
  district: "04",
  party: "D",
};

const senators = [
  {
    id: "leg_ted_budd",
    bioguide_id: "B001135",
    name_display: "Ted Budd",
    chamber: "senate",
    state: "NC",
    district: null,
    party: "R",
  },
];

test("single district ready auto-selects the House member", async ({ page }) => {
  await mockZipLookup(page, {
    payload: {
      zip: "27701",
      state: "NC",
      district: "04",
      data_source: "database",
      source_metadata: {
        source_type: "reviewed_zip_map",
        source_retrieved_at: "2026-07-01",
        source_version: "reviewed-v1",
      },
      district_mappings: [{ zip: "27701", state: "NC", district: "04" }],
      house_rep: houseRep,
      senators,
    },
  });

  await page.goto("/zip-lookup-state-fixture");

  await expect(page.getByText("One district found for this ZIP")).toBeVisible();
  await expect(page.getByText("Senators represent the whole state")).toBeVisible();
  await expect(page.getByTestId("zip-lookup-selected")).toContainText("Selected: Valerie P. Foushee; count: 1");
});

test("ambiguous ZIP shows ambiguity copy and does not auto-select", async ({ page }) => {
  await mockZipLookup(page, {
    payload: {
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
        { zip: "27701", state: "NC", district: "02" },
        { zip: "27701", state: "NC", district: "04" },
      ],
      house_rep: houseRep,
      senators,
    },
  });

  await page.goto("/zip-lookup-state-fixture");

  await expect(page.getByText("This ZIP may include more than one congressional district")).toBeVisible();
  await expect(page.getByText("Search by representative name.", { exact: true })).toBeVisible();
  await expect(page.getByTestId("zip-lookup-selected")).toContainText("Selected: none; count: 0");
});

test("fixture sample coverage is labeled and does not auto-select", async ({ page }) => {
  await mockZipLookup(page, {
    payload: {
      zip: "27701",
      state: "NC",
      district: "04",
      data_source: "fixtures",
      lookup_metadata: {
        fixture_sample_only: true,
        source_type: "fixture_sample",
      },
      district_mappings: [{ zip: "27701", state: "NC", district: "04" }],
      house_rep: houseRep,
      senators,
    },
  });

  await page.goto("/zip-lookup-state-fixture");

  await expect(page.getByText("This is sample coverage, not national coverage yet.").first()).toBeVisible();
  await expect(page.getByTestId("zip-lookup-selected")).toContainText("Selected: none; count: 0");
});

test("unsupported ZIP copy appears and does not auto-select", async ({ page }) => {
  await mockZipLookup(page, {
    status: 404,
    payload: { detail: "ZIP code not found" },
  });

  await page.goto("/zip-lookup-state-fixture");

  await expect(page.getByText("This ZIP is not in the loaded map yet")).toBeVisible();
  await expect(page.getByTestId("zip-lookup-selected")).toContainText("Selected: none; count: 0");
});

async function mockZipLookup(page, { payload, status = 200 }) {
  await page.route("**/lookup/zips", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        data_source: "fixtures",
        zips: [{ zip: "27701", state: "NC", district: "04" }],
      }),
    });
  });
  await page.route("**/lookup/zip/27701/races", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        zip: "27701",
        state: "NC",
        district: "04",
        data_source: "database",
        races: [],
      }),
    });
  });
  await page.route("**/lookup/zip/27701", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      status,
      body: JSON.stringify(payload),
    });
  });
}
