import assert from "node:assert/strict";
import test from "node:test";

import {
  formatSafePublicThemePhrase,
  getPublicThemeFallback,
  getPublicThemeForFacet,
  isSafePublicThemePhrase,
} from "./publicCopyThemes.mjs";

test("public theme helper prefers curated facet and domain-safe fallbacks", () => {
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
