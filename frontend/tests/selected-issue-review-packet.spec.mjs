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

test("capture Selected Issue Experience V1 after-state packet", async ({ page }) => {
  test.setTimeout(180_000);
  test.skip(
    !output || !testedCommit,
    "Set SELECTED_ISSUE_REVIEW_DIR and SELECTED_ISSUE_TESTED_COMMIT.",
  );
  fs.mkdirSync(output, { recursive: true });
  await page.emulateMedia({ reducedMotion: "reduce" });

  await setViewport(page, 1440, 1000);
  await openSelectedIssue(page, "all");
  await capturePage(page, "01-full-selected-issue-desktop.png", {
    scope: "all",
    state: "default full page",
    description: "Full selected-issue desktop experience.",
  }, { fullPage: true });

  await page.locator("#issue-detail > header").scrollIntoViewIfNeeded();
  await capturePage(page, "02-selected-issue-opening-summary.png", {
    scope: "all",
    state: "opening and reviewed summary",
    description: "Selected issue identity, distinct scopes, and reviewed-summary opening.",
  });

  const patternIndex = page.getByText("Pattern index", { exact: true })
    .locator("..")
    .locator("..");
  await captureLocator(page, patternIndex, "03-compact-pattern-index.png", {
    scope: "all",
    state: "pattern index default",
    description: "Compact proportional index for all five governed patterns.",
  });

  await page.getByRole("button", {
    name: /Show 3 exact actions for The HALT Fentanyl path is one mixed episode/,
  }).click();
  await captureLocator(page, page.locator("#vote-record"), "04-pattern-filtered-ledger.png", {
    scope: "all",
    state: "HALT Fentanyl pattern filter",
    expandedAction: "house:119:1:166",
    description: "Pattern-filtered ledger showing three actions as one mixed episode.",
  });

  await openSelectedIssue(page, "119");
  await captureLocator(page, page.locator("#vote-record"), "05-default-compact-ledger.png", {
    scope: "119",
    state: "default compact ledger",
    description: "Compact chronological ledger with the first action batch visible.",
  });

  const ndaaGroup = page.getByTestId("related-action-group").filter({
    hasText: "National Defense Authorization Act for Fiscal Year 2027",
  });
  await captureLocator(page, ndaaGroup, "06-ndaa-related-action-group.png", {
    scope: "119",
    state: "NDAA group expanded",
    description: "Five independent NDAA actions with vote and control composition.",
  });

  const roll275 = page.locator('[data-canonical-action-id="house:119:2:275"]');
  await roll275.getByRole("button").click();
  await captureLocator(page, roll275, "07-expanded-substantive-receipt.png", {
    scope: "119",
    state: "substantive receipt expanded",
    expandedAction: "house:119:2:275",
    description: "Expanded substantive voter receipt with official links.",
  });

  const roll278 = page.locator('[data-canonical-action-id="house:119:2:278"]');
  await roll278.getByRole("button").click();
  await captureLocator(page, roll278, "08-expanded-non-counting-control.png", {
    scope: "119",
    state: "non-counting control expanded",
    expandedAction: "house:119:2:278",
    description: "Expanded governed non-counting control with material limitation.",
  });

  const limitations = page.getByText("Limitations and unresolved actions · 3")
    .locator("..");
  await captureLocator(page, limitations, "09-limitations-collapsed.png", {
    scope: "119",
    state: "limitations collapsed",
    description: "Collapsed limitations state with visible item count.",
  });
  await page.getByText("Limitations and unresolved actions · 3").click();
  await captureLocator(page, limitations, "10-limitations-expanded.png", {
    scope: "119",
    state: "limitations expanded",
    description: "All three governed issue limitations expanded.",
  });

  await openSelectedIssue(page, "all");
  await captureLocator(page, page.locator("#issue-detail > header"), "11-scope-all-distinction.png", {
    scope: "all",
    state: "scope distinction",
    description: "All-Congress 89-action evidence distinguished from 119th-Congress interpretation.",
  });

  await openSelectedIssue(page, "119");
  await captureLocator(page, page.locator("#issue-detail > header"), "12-scope-119.png", {
    scope: "119",
    state: "119th Congress scope",
    description: "119th-Congress 37-action governed state.",
  });

  await openSelectedIssue(page, "118");
  await capturePage(page, "13-scope-118-receipts-only.png", {
    scope: "118",
    state: "receipts only",
    description: "118th-Congress 52-action receipts-only state without synthesis.",
  });

  await setViewport(page, 390, 844);
  await openSelectedIssue(page, "all");
  await capturePage(page, "14-mobile-selected-issue-390.png", {
    scope: "all",
    state: "mobile selected issue",
    description: "Selected issue at 390px without horizontal overflow.",
  }, { fullPage: true });

  await setViewport(page, 320, 844);
  await openSelectedIssue(page, "119");
  await captureLocator(page, page.locator("#vote-record"), "15-mobile-ledger-320.png", {
    scope: "119",
    state: "narrow mobile ledger",
    description: "Compact grouped ledger at 320px.",
  });

  await setViewport(page, 1440, 1000);
  await openSelectedIssue(page, "119");
  const focusControl = page.getByRole("button", {
    name: /Show 2 exact actions for Support for terrorism-preparedness mandates/,
  });
  await focusControl.focus();
  await expect(focusControl).toBeFocused();
  await focusControl.scrollIntoViewIfNeeded();
  await capturePage(page, "16-keyboard-focus-pattern-control.png", {
    scope: "119",
    state: "keyboard focus",
    description: "Visible keyboard focus on a meaningful pattern-to-ledger control.",
  });

  expect(manifest).toHaveLength(16);
  fs.writeFileSync(
    path.join(output, "manifest.json"),
    `${JSON.stringify({
      schema_version: "selected_issue_experience_review_packet_v1",
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
  await expect(page.getByRole("heading", { name: "Chronological action ledger" })).toBeVisible();
  await removeDevelopmentPortal(page);
}

async function setViewport(page, width, height) {
  await page.setViewportSize({ width, height });
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
