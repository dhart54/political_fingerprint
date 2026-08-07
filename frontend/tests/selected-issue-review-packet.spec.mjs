import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";

import { expect, test } from "@playwright/test";

import { installPassARoutes, positions } from "./pass-a-fixtures.mjs";
import {
  selectedIssueEvidenceForScope,
  selectedIssueReview,
} from "./selected-issue-fixtures.mjs";

const output = process.env.SELECTED_ISSUE_REVIEW_DIR;
const testedCommit = process.env.SELECTED_ISSUE_TESTED_COMMIT;
const selectedPath = "/?representative=leg_valerie_p_foushee&issue=JUSTICE_PUBLIC_SAFETY";
const manifest = [];

test.beforeEach(async ({ page }) => {
  await installPassARoutes(page, {
    justiceEvidenceOverride: selectedIssueEvidenceForScope,
    justicePresentationOverride: selectedIssueReview.presentation,
    positionsOverride: selectedIssuePositionsForScope,
  });
});

test("capture Selected Issue Experience V1.1 exact-commit packet", async ({ page }) => {
  test.setTimeout(180_000);
  test.skip(
    !output || !testedCommit,
    "Set SELECTED_ISSUE_REVIEW_DIR and SELECTED_ISSUE_TESTED_COMMIT.",
  );
  fs.mkdirSync(output, { recursive: true });
  await page.emulateMedia({ reducedMotion: "reduce" });

  await setViewport(page, 1440, 1000);
  await openSelectedIssue(page, "all");
  await page.locator("#issue-detail > header").scrollIntoViewIfNeeded();
  await capturePage(page, "01-header-selected-issue-opening-1440.png", {
    scope: "all",
    state: "header and selected-issue opening",
    description: "Bounded header and selected-issue opening at 1440px.",
  });

  await page.locator("#issue-summary").scrollIntoViewIfNeeded();
  await capturePage(page, "02-scope-strip-takeaway-1440.png", {
    scope: "all",
    state: "scope strip and takeaway",
    description: "Distinct action and summary scopes with the approved substantive takeaway.",
  });

  await captureLocator(page, page.getByTestId("reviewed-analysis"), "03-complete-pattern-list-1440.png", {
    scope: "all",
    state: "complete visible pattern list",
    description: "All five governed patterns with symbols, explanations, counts, and one action each.",
  });

  await openSelectedIssue(page, "119");
  await scrollSectionBelowHeader(page, "#vote-record");
  await capturePage(page, "04-default-vote-record-1440.png", {
    scope: "119",
    state: "default vote record",
    description: "Default compact vote record with independent Vote and Type filters.",
  });

  await page.getByRole("button", {
    name: /View 2 votes for Opposition to expanding fraud-enforcement capacity/,
  }).click();
  await capturePage(page, "05-selected-opposition-pattern-1440.png", {
    scope: "119",
    state: "selected Opposition pattern",
    description: "Compact governed Opposition state with only exact matching votes.",
  });

  await openSelectedIssue(page, "119");
  const normalNay = page.locator('[data-canonical-action-id="house:119:2:275"]');
  await normalNay.getByRole("button").click();
  await expect(page.locator(".pattern-strip")).toHaveCount(0);
  await captureLocator(page, normalNay, "06-normal-nay-no-pattern-strip-1440.png", {
    scope: "119",
    state: "normal Nay expanded without pattern state",
    expandedAction: "house:119:2:275",
    description: "A normal Nay opened from the unfiltered record without creating an Opposition strip.",
  });
  await normalNay.getByRole("button").click();

  const ndaaGroup = page.getByTestId("related-action-group").filter({
    hasText: "National Defense Authorization Act for Fiscal Year 2027",
  });
  await captureLocator(page, ndaaGroup, "07-ndaa-parent-all-children-1440.png", {
    scope: "119",
    state: "NDAA parent and all children visible",
    description: "Thin contextual parent with every independent child action visible.",
  });

  const roll275 = page.locator('[data-canonical-action-id="house:119:2:275"]');
  if (await roll275.getByRole("button").getAttribute("aria-expanded") !== "true") {
    await roll275.getByRole("button").click();
  }
  await captureLocator(page, roll275, "08-expanded-standard-vote-1440.png", {
    scope: "119",
    state: "standard vote expanded",
    expandedAction: "house:119:2:275",
    description: "Expanded standard vote with natural voter-facing fields and official sources.",
  });

  const roll278 = page.locator('[data-canonical-action-id="house:119:2:278"]');
  await roll278.getByRole("button").click();
  await captureLocator(page, roll278, "09-expanded-non-counting-control-1440.png", {
    scope: "119",
    state: "non-counting control expanded",
    expandedAction: "house:119:2:278",
    description: "Expanded non-counting control with its exceptional status and material limitation.",
  });

  await setViewport(page, 390, 844);
  await openSelectedIssue(page, "all");
  await capturePage(page, "10-selected-issue-390.png", {
    scope: "all",
    state: "mobile selected issue",
    description: "Complete selected issue at 390px without horizontal overflow.",
  }, { fullPage: true });

  await openSelectedIssue(page, "119");
  await scrollSectionBelowHeader(page, "#vote-record");
  await capturePage(page, "11-vote-record-390.png", {
    scope: "119",
    state: "mobile vote record",
    description: "Vote record at 390px with separate wrapping filters and visible child actions.",
  });

  const mobileRoll275 = page.locator('[data-canonical-action-id="house:119:2:275"]');
  await mobileRoll275.getByRole("button").click();
  await captureLocator(page, mobileRoll275, "12-expanded-vote-390.png", {
    scope: "119",
    state: "mobile expanded vote",
    expandedAction: "house:119:2:275",
    description: "Expanded voter receipt stacked at 390px with usable source links.",
  });

  expect(manifest).toHaveLength(12);
  fs.writeFileSync(
    path.join(output, "manifest.json"),
    `${JSON.stringify({
      schema_version: "selected_issue_experience_review_packet_v1_1",
      tested_commit: testedCommit,
      generated_at: new Date().toISOString(),
      captures: manifest,
    }, null, 2)}\n`,
    "utf8",
  );
});

async function openSelectedIssue(page, scope) {
  const suffix = scope === "all" ? "" : `&scope=${scope}`;
  await page.goto(`${selectedPath}${suffix}`);
  await expect(page.getByTestId("issue-detail")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Vote record" })).toBeVisible();
  await removeDevelopmentPortal(page);
}

async function setViewport(page, width, height) {
  await page.setViewportSize({ width, height });
}

async function scrollSectionBelowHeader(page, selector) {
  await page.locator(selector).evaluate((element) => {
    const headerHeight = document.querySelector("main > header")
      ?.getBoundingClientRect().height || 0;
    window.scrollTo({
      behavior: "instant",
      top: element.getBoundingClientRect().top + window.scrollY - headerHeight - 16,
    });
  });
}

async function capturePage(page, filename, metadata, options = {}) {
  const target = path.join(output, filename);
  await removeDevelopmentPortal(page);
  await page.screenshot({ path: target, ...options });
  recordCapture(page, target, filename, metadata);
}

async function captureLocator(page, locator, filename, metadata) {
  const target = path.join(output, filename);
  await removeDevelopmentPortal(page);
  await locator.scrollIntoViewIfNeeded();
  await locator.screenshot({ path: target });
  recordCapture(page, target, filename, metadata);
}

function recordCapture(page, target, filename, {
  scope,
  state,
  description,
  expandedAction = null,
}) {
  const viewport = page.viewportSize();
  manifest.push({
    filename,
    sha256: crypto.createHash("sha256").update(fs.readFileSync(target)).digest("hex"),
    viewport: `${viewport.width}x${viewport.height}`,
    url: page.url(),
    scope,
    interaction_state: state,
    expanded_action: expandedAction,
    tested_commit: testedCommit,
    capture_description: description,
  });
}

async function removeDevelopmentPortal(page) {
  const portal = page.locator("nextjs-portal");
  if (await portal.count()) {
    await portal.evaluate((element) => element.remove());
  }
}

function selectedIssuePositionsForScope(scope) {
  const count = scope === "119" ? 37 : scope === "118" ? 52 : 89;
  const interpreted = scope === "118" ? 0 : 35;
  return {
    ...positions,
    positions: positions.positions.map((row) => (
      row.domain === "JUSTICE_PUBLIC_SAFETY"
        ? {
            ...row,
            yea_count: Math.floor(count / 2),
            nay_count: Math.ceil(count / 2),
            total_votes: count,
            recorded_votes: count,
            interpreted_support_count: scope === "118" ? 0 : 5,
            interpreted_oppose_count: scope === "118" ? 0 : 30,
            interpreted_total: interpreted,
          }
        : row
    )),
  };
}
