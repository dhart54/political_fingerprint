import assert from "node:assert/strict";
import test from "node:test";
import { measureReferenceLabel } from "./measureReference.mjs";
import { getActionPresentation, buildLedgerItems } from "./selectedIssueExperience.mjs";
import { filterLoadedReceipts } from "./localRecordFilter.mjs";

const row = { congress: 119, chamber: "house", rollcall_number: 282,
  measure_reference: { congress: 119, type: "hconres", number: 89 } };

test("all eight sourced measure types format independently of voting chamber", () => {
  for (const [type, prefix] of Object.entries({ hr: "H.R.", s: "S.", hres: "H.Res.", sres: "S.Res.", hjres: "H.J.Res.", sjres: "S.J.Res.", hconres: "H.Con.Res.", sconres: "S.Con.Res." })) {
    for (const chamber of ["house", "senate"]) {
      assert.equal(measureReferenceLabel({ ...row, chamber, measure_reference: { ...row.measure_reference, type } }), `${prefix} 89 (Congress 119)`);
    }
  }
});

test("missing, invalid, extra, boolean and mismatched Congress fields never manufacture a label", () => {
  for (const reference of [null, [], {}, "hconres89", { ...row.measure_reference, type: "amendment" },
    { ...row.measure_reference, type: "toString" }, { ...row.measure_reference, type: { toString: false } }, { ...row.measure_reference, number: true },
    { ...row.measure_reference, number: 0 }, { ...row.measure_reference, number: 1.5 },
    { ...row.measure_reference, number: "89" }, { ...row.measure_reference, congress: 118 },
    { ...row.measure_reference, label: "Invented" }]) {
    const invalid = { ...row, measure_reference: reference, source_url: "https://api.congress.gov/v3/bill/119/hconres/89/actions" };
    assert.equal(measureReferenceLabel(invalid), "");
    assert.deepEqual(filterLoadedReceipts([invalid], "hconres89"), []);
  }
});

test("associated measure never replaces an exact amendment label or changes groups", () => {
  const amendment = { ...row, action_label: "Exact amendment on reporting deadlines", vote_type: "amendment" };
  const withoutMeasure = { ...amendment, measure_reference: null };
  const original = getActionPresentation(withoutMeasure);
  const groupShape = (rows) => buildLedgerItems(rows).map(item => ({ id: item.id, type: item.type, label: item.label, composition: item.composition }));
  const groups = groupShape([withoutMeasure]);
  assert.equal(measureReferenceLabel(amendment), "H.Con.Res. 89 (Congress 119)");
  assert.deepEqual(getActionPresentation(amendment), original);
  assert.equal(original.title, "Exact amendment on reporting deadlines");
  assert.equal(original.actionType, "Amendment");
  assert.deepEqual(groupShape([amendment]), groups);
  assert.ok(!("bill_id" in amendment));
});
