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
      assert.doesNotMatch(text, /This candidate does not establish|synthesis conclusion/);
      assert.doesNotMatch(text, /(?:docs|backend|frontend|scripts)[\\/]|[a-f0-9]{40,}|implementation_id|acceptance_receipt/);
    }
  }
  assert.equal(changes, 0);
  assert.equal(treatment.entries.length, 35);
  for (const entry of treatment.entries) {
    assert.equal(entry.proposed_treatment, "MIXED_REQUIRES_PUBLIC_COPY");
    assert.equal(entry.semantic_public_acceptance, "pending");
  }
});


test("detached Justice proposal renders authored copy without activating it", () => {
  assert.equal(treatment.authored_public_copy_changes.length, 1);
  const mapping = treatment.authored_public_copy_changes[0];
  assert.equal(mapping.occurrences.length, 35);
  assert.equal(new Set(mapping.occurrences.map(x => `${x.domain}:${x.canonical_action_id}`)).size, 35);
  assert.equal(mapping.semantic_public_acceptance, "pending");
  assert.equal(mapping.proposed_public_copy, "This action alone does not establish motive, ideology, or a broader position on this issue.");
  assert.deepEqual(buildPublicReceipt({ governed_receipt_projection: { caveats: [mapping.source_text] } }).limitations, []);
  assert.deepEqual(buildPublicReceipt({ governed_receipt_projection: {
    caveats: [mapping.source_text], limitation_treatments: [{source_text: mapping.source_text,
      treatment: "public", public_copy: mapping.proposed_public_copy}],
  } }).limitations, [mapping.proposed_public_copy]);
  assert.equal(treatment.accepted, false);
  assert.equal(treatment.active_runtime_unchanged, true);
});

test("all NS derived accounting agrees with surviving findings", () => {
  const after = review.national_security.after_candidate;
  const findings = [...after.repeated_patterns, ...after.notable_choices, ...after.policy_trajectories];
  const actions = [...new Set(findings.flatMap(f => f.action_ids))].sort();
  assert.equal(after.policy_trajectories.length, 0);
  assert.equal(findings.length, 14);
  assert.equal(actions.length, 30);
  const label = `${findings.length} findings · ${actions.length} votes`;
  assert.equal(after.coverage_text, label);
  assert.equal(after.overview.evidence_count_label, label);
  assert.deepEqual(after.evidence_metadata.display_action_ids, actions);
  const episodes = [...new Set(findings.flatMap(f => f.episode_ids))].sort();
  for (const key of ["episode_ids", "semantic_lineage_episode_ids", "public_supporting_episode_ids"]) {
    assert.deepEqual(after.overview[key], episodes);
  }
  assert.doesNotMatch(JSON.stringify(after.overview), /trajectory-milcon-va|annual appropriations/);
  for (const id of ["house:119:1:182", "house:119:2:175"]) {
    assert.equal(actions.includes(id), false);
    const receipt = review.national_security.ledger_preservation.retained_receipts.find(r => r.canonical_action_id === id);
    assert.ok(receipt.governed_receipt_projection.exact_action_meaning);
    assert.ok(review.national_security.ledger_preservation.retained_episode_ids.includes(receipt.governed_receipt_projection.episode_id));
  }
  for (const key of ["action_ids", "semantic_lineage_action_ids", "public_supporting_action_ids"]) {
    assert.deepEqual(after.overview[key], actions);
  }
});
