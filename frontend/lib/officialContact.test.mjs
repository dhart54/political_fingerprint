import assert from "node:assert/strict";
import test from "node:test";
import { buildContactDetails } from "./officialContact.mjs";

const id = "leg_valerie_p_foushee";
const supplied = {
  legislator_id: id, contact_status: "loaded", data_source: "database",
  phone: "(202) 225-1784", official_website_url: "https://foushee.house.gov/",
  contact_form_url: "https://foushee.house.gov/contact",
  source_url: "https://foushee.house.gov/", source_type: "official_house_website",
  source_retrieved_at: "2026-05-19",
};

test("contact fields retain supplied identity, provenance, date and safe paths", () => {
  const result = buildContactDetails(supplied, id);
  assert.equal(result.origin, "database");
  assert.equal(result.websiteUrl, supplied.official_website_url);
  assert.equal(result.formUrl, supplied.contact_form_url);
  assert.equal(result.sourceUrl, supplied.source_url);
  assert.equal(result.retrievedAt, "2026-05-19");
  assert.deepEqual(result.phone, { text: supplied.phone, href: "tel:2022251784" });
  assert.equal(result.withheld, false);
});

test("mismatched, absent and malformed contact identities fail closed", () => {
  for (const payload of [null, [], {}, { ...supplied, legislator_id: "other" }, { ...supplied, contact_status: "unknown" }]) {
    assert.throws(() => buildContactDetails(payload, id));
  }
});

test("not-loaded metadata cannot manufacture contact paths from stray fields", () => {
  const result = buildContactDetails({ ...supplied, contact_status: "not_loaded", data_source: "none" }, id);
  assert.equal(result.status, "missing");
  assert.equal(result.phone, null); assert.equal(result.websiteUrl, null); assert.equal(result.formUrl, null);
});

test("curated fallback and unknown origins remain distinct from stored metadata", () => {
  assert.equal(buildContactDetails({ ...supplied, data_source: "curated_fallback" }, id).origin, "curated_fallback");
  assert.equal(buildContactDetails({ ...supplied, data_source: "unexpected" }, id).origin, "not_supplied");
});

for (const url of [
  "javascript:alert(1)", "data:text/html,hello", "http://foushee.house.gov/contact",
  "https://foushee.house.gov.evil.example/contact", "https://example.com/",
  "https://user:password@foushee.house.gov/", "https://foushee.house.gov:8443/",
  "https://foushee.house.gov/contact?issue=JUSTICE_PUBLIC_SAFETY", "https://foushee.house.gov/contact#vote",
  "//foushee.house.gov/contact", "https://foushee.house.gov/\ncontact",
]) test(`unsafe or context-bearing contact URL is withheld: ${url}`, () => {
  const result = buildContactDetails({ ...supplied, contact_form_url: url }, id);
  assert.equal(result.formUrl, null); assert.equal(result.withheld, true);
  assert.equal(result.websiteUrl, supplied.official_website_url);
});

test("Senate paths and explicitly supplied international phone syntax are supported", () => {
  const result = buildContactDetails({ ...supplied, official_website_url: "https://www.budd.senate.gov/", phone: "+1 (202) 224-3154" }, id);
  assert.equal(result.websiteUrl, "https://www.budd.senate.gov/");
  assert.equal(result.phone.href, "tel:+12022243154");
});

test("phone parameters, extensions, malformed numbers and invalid dates are not invented or repaired", () => {
  for (const phone of ["tel:2022251784", "2022251784;ext=12", "2022251784?issue=vote", "202", "2022251784 ext 12"]) {
    assert.equal(buildContactDetails({ ...supplied, phone }, id).phone, null);
  }
  for (const source_retrieved_at of [null, "today", "2026-02-30", "2026-05-19junk", "2026-05-19T99:00:00Z"]) {
    assert.equal(buildContactDetails({ ...supplied, source_retrieved_at }, id).retrievedAt, null);
  }
});

test("unknown source types cannot become a prototype object or an invented source claim", () => {
  for (const source_type of ["__proto__", "constructor", "unknown"]) assert.equal(buildContactDetails({ ...supplied, source_type }, id).sourceType, null);
});

test("a rejected or mismatched source URL cannot claim the declared official source family", () => {
  for (const source_url of ["https://foushee.house.gov.evil.example/", "https://www.budd.senate.gov/", null]) {
    assert.equal(buildContactDetails({ ...supplied, source_url }, id).sourceType, null);
  }
});

test("partial metadata preserves its supplied safe field without invented provenance", () => {
  const result = buildContactDetails({ legislator_id: id, contact_status: "loaded", phone: supplied.phone }, id);
  assert.equal(result.origin, "not_supplied"); assert.equal(result.retrievedAt, null);
  assert.equal(result.sourceUrl, null); assert.equal(result.websiteUrl, null); assert.equal(result.formUrl, null);
  assert.equal(result.phone.href, "tel:2022251784");
});
