import assert from "node:assert/strict";
import test from "node:test";
import fs from "node:fs";
import { createRequire } from "node:module";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import * as selectedIssue from "./selectedIssueExperience.mjs";
import { buildPublicReceipt } from "./publicReceipt.mjs";

const require = createRequire(import.meta.url);
const { transform } = require("next/dist/build/swc/index.js");
const review = JSON.parse(fs.readFileSync(new URL("../../docs/reviews/m15b_interpretive_trust/before_after_public_review.json", import.meta.url), "utf8"));
const treatment = JSON.parse(fs.readFileSync(new URL("../../docs/reviews/m15b_interpretive_trust/active_limitation_treatment_review.json", import.meta.url), "utf8"));

// Render the real production component, using the project's existing JSX compiler.
async function component(name, dependencies = {}) {
  const filename = new URL(`../components/${name}.js`, import.meta.url);
  const { code } = await transform(fs.readFileSync(filename, "utf8"), {
    filename: filename.pathname, jsc: { parser: { syntax: "ecmascript", jsx: true },
      target: "es2022", transform: { react: { runtime: "automatic" } } },
    module: { type: "commonjs" },
  });
  const compiledModule = { exports: {} };
  new Function("require", "module", "exports", code)(
    (id) => Object.hasOwn(dependencies, id) ? dependencies[id] : require(id), compiledModule, compiledModule.exports);
  return compiledModule.exports;
}
const icon = await component("SemanticIcon");
const analysis = await component("ReviewedAnalysisSection", {
  "./SemanticIcon": icon, "../lib/selectedIssueExperience.mjs": selectedIssue,
});

test("pending NS candidate removes only its unsupported trajectory from actual rendered analysis", () => {
  const { before, after_candidate: after } = review.national_security;
  const render = (presentation) => renderToStaticMarkup(React.createElement(analysis.default, { presentation, rows: [], onSeeActions() {} }));
  const oldHtml = render(before); const newHtml = render(after);
  assert.match(oldHtml, /A change over time/);
  assert.doesNotMatch(newHtml, /A change over time/);
  assert.match(oldHtml, /15 findings · 32 votes/);
  assert.match(newHtml, /14 findings · 30 votes/);
  assert.doesNotMatch(newHtml, /Opposed the FY2026 package and supported the FY2027 package/);
  assert.deepEqual(after.exact_action_receipts, before.exact_action_receipts);
  for (const field of ["repeated_patterns", "notable_choices", "syntheses", "limitations"]) {
    assert.deepEqual(after[field], before[field]);
  }
  assert.equal(review.accepted, false);
  assert.equal(review.production_selectable, false);
});

test("all active caveat output matches the bounded review, with no structural provenance leaks", () => {
  let changes = 0;
  for (const row of review.receipt_rendering) {
    const actual = buildPublicReceipt({ governed_receipt_projection: { caveats: row.source_caveats } }).limitations;
    assert.deepEqual(actual, row.new_public, `${row.domain} ${row.canonical_action_id}`);
    if (JSON.stringify(row.old_public) !== JSON.stringify(actual)) changes++;
    for (const text of actual) {
      assert.doesNotMatch(text, /(?:docs|backend|frontend|scripts)[\\/]|[a-f0-9]{40,}|implementation_id|acceptance_receipt/);
    }
  }
  assert.equal(changes, 35);
  assert.equal(treatment.entries.length, changes);
  for (const entry of treatment.entries) {
    assert.equal(entry.public_copy, entry.source_text);
    assert.equal(entry.proposed_treatment, "PUBLIC");
  }
});
