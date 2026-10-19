import assert from "node:assert/strict";
import test from "node:test";
import fs from "node:fs";
import { createRequire } from "node:module";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { buildSelectedIssueModel } from "./selectedIssueExperience.mjs";

const require = createRequire(import.meta.url);
const { transform } = require("next/dist/build/swc/index.js");
const filename = new URL("../components/BoundedChoiceReview.js", import.meta.url);
const { code } = await transform(fs.readFileSync(filename, "utf8"), {
  filename: filename.pathname, jsc: { parser: { syntax: "ecmascript", jsx: true }, target: "es2022", transform: { react: { runtime: "automatic" } } }, module: { type: "commonjs" },
});
const compiled = { exports: {} };
new Function("require", "module", "exports", code)(require, compiled, compiled.exports);
const Component = compiled.exports.default;
for (const member of ["F000477", "M001184"]) {
  const presentation = JSON.parse(fs.readFileSync(new URL(`../../docs/editorial/review_packages/health_bounded_choice_v1/${member.toLowerCase()}-presentation.json`, import.meta.url), "utf8"));
  test(`${member} renders actual mapped choice without adding an overall conclusion`, () => {
    const html = renderToStaticMarkup(React.createElement(Component, { presentation }));
    assert.match(html, /Details and qualifications/);
    assert.match(html, /Inspect this vote and its sources/);
    assert.match(html, member === "F000477" ? /data-testid="supporting-choice"/ : /data-testid="not-voting-accounting"/);
    assert.doesNotMatch(html, /Overall Health|primary_conclusion|gold_benchmark/);
    const model = buildSelectedIssueModel({ presentation: { presentation_branch: "bounded_choice_review", bounded_choice: presentation, tier: "bounded_choice_review", review_state: { congress_scope: [119], review_scope: "bounded_partial_record", total_recorded_actions: 1, complete_episode_count: 1 } }, scope: "119" });
    assert.equal(model.interpretation.findingCount, member === "F000477" ? 1 : 0);
  });
}
