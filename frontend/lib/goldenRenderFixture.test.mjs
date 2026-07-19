import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { buildIssueOverview, formatRenderedIssueOverview } from "./issueOverview.mjs";
import { buildIssueCardPreview, buildRecordNarrative } from "./profileNarrative.mjs";
import {
  GOLDEN_RENDER_UNSAFE_PHRASES,
  goldenEvidenceByDomain,
  goldenFixtureData,
  goldenLegislator,
  limitedEvidenceFixtureData,
  limitedEvidenceLegislator,
} from "./goldenRenderFixture.mjs";

test("golden render fixture route is server-gated and unlinked from normal UI", () => {
  const routeSource = readFileSync(new URL("../app/golden-render-fixture/page.js", import.meta.url), "utf8");
  const homeSource = readFileSync(new URL("../app/page.js", import.meta.url), "utf8");

  assert.match(routeSource, /ENABLE_GOLDEN_RENDER_FIXTURE/);
  assert.match(routeSource, /VERCEL_ENV === "preview"/);
  assert.match(routeSource, /notFound\(\)/);
  assert.doesNotMatch(homeSource, /golden-render-fixture|ENABLE_GOLDEN_RENDER_FIXTURE/);
});

test("golden fixture top-level profile and issue copy excludes unsafe raw phrases", () => {
  const narrative = buildRecordNarrative({
    legislator: goldenLegislator,
    positions: goldenFixtureData.positions.positions,
  });
  const cardCopy = goldenFixtureData.positions.positions
    .map((row) => {
      const preview = buildIssueCardPreview(row);
      return `${preview.status} ${preview.countLine} ${preview.themeLine} ${preview.receiptLine}`;
    })
    .join(" ");
  const issueCopy = Object.entries(goldenEvidenceByDomain)
    .map(([domain, payload]) => formatRenderedIssueOverview(buildIssueOverview(payload.evidence, {
      domain,
      representativeName: goldenLegislator.name_display,
    })))
    .join(" ");
  const publicCopy = `${narrative.headline} ${narrative.body} ${narrative.evidenceLine} ${cardCopy} ${issueCopy}`;

  assert.match(publicCopy, /National Security & Foreign Policy/);
  assert.match(publicCopy, /Economy & Taxes/);
  assert.match(publicCopy, /Justice & Public Safety/);
  assert.match(publicCopy, /Immigration & Border Policy/);
  assert.match(publicCopy, /mixed rather than mostly support or mostly opposition/i);

  for (const phrase of GOLDEN_RENDER_UNSAFE_PHRASES) {
    assert.doesNotMatch(publicCopy, new RegExp(escapeRegExp(phrase), "i"), phrase);
  }
});

test("golden limited one-sided fixture stays limited in profile and cards", () => {
  const narrative = buildRecordNarrative({
    legislator: limitedEvidenceLegislator,
    positions: limitedEvidenceFixtureData.positions.positions,
  });
  const publicCopy = [
    narrative.headline,
    narrative.body,
    ...limitedEvidenceFixtureData.positions.positions.map((row) => {
      const preview = buildIssueCardPreview(row);
      return `${preview.status} ${preview.countLine} ${preview.themeLine}`;
    }),
  ].join(" ");

  assert.match(publicCopy, /Limited reviewed evidence/);
  assert.match(publicCopy, /should stay cautious|limited/i);
  assert.doesNotMatch(publicCopy, /mostly opposed reads|mostly supported reads|has the clearest pattern:\s*mostly/i);
  assert.doesNotMatch(publicCopy, /mostly opposed in (?:the )?reviewed sample|mostly supported in (?:the )?reviewed sample/i);
});

function escapeRegExp(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
