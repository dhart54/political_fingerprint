import assert from "node:assert/strict";
import test from "node:test";

import { formatDisplayMeasureTitle } from "./measureDisplay.mjs";

test("measure display names shorten recurring long titles without losing identity", () => {
  assert.equal(
    formatDisplayMeasureTitle("Concurrent resolution on the budget for fiscal year 2025."),
    "FY2025 Congressional Budget Resolution",
  );
  assert.equal(
    formatDisplayMeasureTitle("Military Construction and Veterans Affairs Appropriations Act, 2026"),
    "Military Construction and VA Appropriations Act, 2026",
  );
  assert.equal(
    formatDisplayMeasureTitle("S. Amdt. No. 1234 to National Defense Authorization Act for Fiscal Year 2026"),
    "Amendment 1234: National Defense Authorization Act, 2026",
  );
});

test("unknown long titles are truncated while full official titles remain available elsewhere", () => {
  const title = "A bill to establish a long technical program name with many source-specific clauses and cross references, and for other purposes.";
  const display = formatDisplayMeasureTitle(title, { maxLength: 50 });

  assert.ok(display.length <= 53);
  assert.match(display, /\.\.\.$/);
});
