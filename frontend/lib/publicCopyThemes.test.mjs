import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import {
  formatSafePublicThemePhrase,
  getPublicThemeFallback,
  getPublicThemeForFacet,
  isSafePublicThemePhrase,
} from "./publicCopyThemes.mjs";

test("public theme helper prefers curated facet and domain-safe fallbacks", () => {
  assert.equal(getPublicThemeForFacet("economy_taxes", { domain: "ECONOMY_TAXES" }), "fiscal and tax measures");
  assert.equal(getPublicThemeForFacet("environment_energy", { domain: "ENVIRONMENT_ENERGY" }), "environment and energy measures");
  assert.equal(getPublicThemeForFacet("justice_public_safety", { domain: "JUSTICE_PUBLIC_SAFETY" }), "public-safety and legal-policy measures");
  assert.equal(
    getPublicThemeForFacet("national_security_foreign", { domain: "NATIONAL_SECURITY_FOREIGN" }),
    "national-security and foreign-policy measures",
  );
  assert.equal(getPublicThemeForFacet("Motion to commit", { domain: "NATIONAL_SECURITY_FOREIGN" }), "motions to commit");
  assert.equal(
    getPublicThemeForFacet("Defense authorization amendment", { domain: "NATIONAL_SECURITY_FOREIGN" }),
    "defense authorization amendments",
  );
  assert.equal(
    getPublicThemeForFacet("china_related_security_restrictions", { domain: "NATIONAL_SECURITY_FOREIGN" }),
    "China-related security restrictions",
  );
  assert.equal(
    getPublicThemeForFacet("strategic_petroleum_reserve_china_restrictions", { domain: "NATIONAL_SECURITY_FOREIGN" }),
    "China-related security restrictions",
  );
  assert.equal(
    getPublicThemeForFacet("iran_sanctions_related_measure", { domain: "NATIONAL_SECURITY_FOREIGN" }),
    "Iran-related security measures",
  );
  assert.equal(
    getPublicThemeForFacet("foreign_policy_war_powers_resolution", { domain: "NATIONAL_SECURITY_FOREIGN" }),
    "war-powers votes",
  );
  assert.equal(
    getPublicThemeForFacet("unknown_long_raw_facet_that_should_fall_back_because_it_has_far_too_many_words_for_public_copy", {
      domain: "NATIONAL_SECURITY_FOREIGN",
    }),
    "other reviewed national-security measures",
  );
  assert.equal(getPublicThemeFallback("ECONOMY_TAXES"), "other reviewed fiscal measures");
  assert.equal(getPublicThemeFallback("JUSTICE_PUBLIC_SAFETY"), "other reviewed public-safety measures");
});

test("broad domain facets no longer surface awkward short-label fallbacks", () => {
  const beforeAfterCases = [
    ["environment_energy", "ENVIRONMENT_ENERGY", "environment energy"],
    ["economy_taxes", "ECONOMY_TAXES", "economy taxes"],
    ["justice_public_safety", "JUSTICE_PUBLIC_SAFETY", "justice public safety"],
    ["national_security_foreign", "NATIONAL_SECURITY_FOREIGN", "national security foreign"],
  ];

  for (const [facet, domain, previousShortLabel] of beforeAfterCases) {
    const theme = getPublicThemeForFacet(facet, { domain });
    assert.notEqual(theme, previousShortLabel);
    assert.notEqual(theme, getPublicThemeFallback(domain));
    assert.equal(isSafePublicThemePhrase(theme, { curated: true }), true);
  }

  assert.equal(getPublicThemeForFacet("House amendment vote", { domain: "NATIONAL_SECURITY_FOREIGN" }), "House amendment vote");
});

test("public theme helper rejects audit and raw evidence phrases", () => {
  for (const unsafe of [
    "this was a direct vote on Protecting America's Strategic Petroleum Reserve from China Act",
    "this vote is useful because it records a direct position",
    "the vote is useful because it records a direct position",
    "records a direct position on the issue",
    "the House voted on whether to agree to Biggs of Arizona Part A Amendment No. 149",
    "the Senate voted on whether to allow a sale",
    "whether to agree to the amendment",
    "whether that amendment would be adopted",
    "Part A Amendment No. 149",
    "the amendment redirects funding",
    "the amendment decreases funding",
    "official roll call description",
    "classification reason copied from audit text",
    "source basis text",
  ]) {
    assert.equal(isSafePublicThemePhrase(unsafe), false, unsafe);
    assert.equal(formatSafePublicThemePhrase(unsafe), "", unsafe);
  }
});

test("public theme helper allows short public noun phrases", () => {
  for (const safe of [
    "defense authorization amendments",
    "foreign military sales",
    "China-related security restrictions",
    "Iran-related security measures",
    "war-powers votes",
    "veterans cemetery administration",
    "budget framework and reconciliation",
    "small-business loan eligibility",
    "temporary government funding",
    "D.C. policing reform repeal",
  ]) {
    assert.equal(isSafePublicThemePhrase(safe), true, safe);
    assert.equal(formatSafePublicThemePhrase(safe), safe);
  }
});

test("curated public themes do not contain unsafe markers", () => {
  const source = readFileSync(new URL("./publicCopyThemes.mjs", import.meta.url), "utf8");
  const mapBlock = source.match(/const PUBLIC_THEME_BY_FACET = \{([\s\S]*?)\};/)?.[1] || "";
  const curatedThemes = Array.from(mapBlock.matchAll(/:\s*"([^"]+)"/g)).map((match) => match[1]);

  assert.ok(curatedThemes.length > 0, "expected curated theme mappings");

  for (const theme of curatedThemes) {
    assert.equal(isSafePublicThemePhrase(theme, { curated: true }), true, theme);
  }
});
