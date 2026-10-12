import assert from "node:assert/strict";
import test from "node:test";
import { filterLoadedReceipts } from "./localRecordFilter.mjs";
import { buildLedgerItems } from "./selectedIssueExperience.mjs";

const row = (roll, title, extra = {}) => ({ rollcall_number: roll, chamber: "house", bill_title: title, ...extra });

for (const [printed, queries] of [
  ["H.R. 1", ["hr1", "  h. r.  1  ", "H R 1"]],
  ["S. 12", ["s12", "S. 12"]],
  ["H.J.Res. 8", ["hjres8", "h. j. res. 8"]],
  ["S.J.Res. 9", ["sjres9", "s j res 9"]],
  ["H.Con.Res. 10", ["hconres10", "h. con. res. 10"]],
  ["S.Con.Res. 11", ["sconres11", "s con res 11"]],
  ["H.Res. 2", ["hres2", "h. res. 2"]],
  ["S.Res. 3", ["sres3", "s res 3"]],
]) test(`printed identifier ${printed} tolerates case, punctuation and spacing without prefix collisions`, () => {
  const exact = row(99, printed), longer = row(98, `${printed}0`);
  for (const query of queries) assert.deepEqual(filterLoadedReceipts([exact, longer], query), [exact]);
});

test("roll identifiers match exact printed numbers, independently of bill numbers", () => {
  const exact = row(32, "H.R. 7"), other = row(320, "H.R. 32");
  for (const query of ["roll32", "Roll 32", "roll #032", "HOUSE roll call 32"]) assert.deepEqual(filterLoadedReceipts([exact, other], query), [exact]);
  assert.deepEqual(filterLoadedReceipts([exact, other], "hr32"), [other]);
});

test("identifier pairs cannot accidentally join a bill prefix with another field's roll number", () => {
  assert.deepEqual(filterLoadedReceipts([row(1, "H.R. 10")], "H.R. 1"), []);
});

test("title words use literal case-insensitive matching and combine with identifiers", () => {
  const a = row(2, "H.R. 1", { action_label: "Water and clean energy amendments" });
  const b = row(3, "H.R. 1", { action_label: "Budget changes" });
  assert.deepEqual(filterLoadedReceipts([a, b], " h.r.1   CLEAN   water "), [a]);
  assert.deepEqual(filterLoadedReceipts([a, b], "amend"), [a]);
});

test("only rendered title, parent measure, chamber and roll fields are indexed", () => {
  const a = row(4, "Printed title", {
    description: "Hidden description needle", question: "Hidden question needle",
    plain_english_summary: "Hidden interpretation needle", bill_id: "hidden-id",
    source_url: "https://example.com/hidden-source", vote_date: "2099-01-01", position: "nay",
  });
  for (const query of ["needle", "hidden-id", "hidden-source", "2099", "nay"]) assert.deepEqual(filterLoadedReceipts([a], query), []);
});

test("blank/punctuation-only queries preserve original array and row identity", () => {
  const rows = [row(1, "First"), row(2, "Second")];
  for (const query of ["", "  \t ", ". , :"]) assert.equal(filterLoadedReceipts(rows, query), rows);
});

test("matches retain the supplied order and do not mutate records or infer direction", () => {
  const a = Object.freeze(row(5, "Shared title", { position: "present" }));
  const b = Object.freeze(row(2, "Shared title", { position: "not_voting" }));
  const rows = Object.freeze([a, b]);
  assert.deepEqual(filterLoadedReceipts(rows, "shared"), [a, b]);
  assert.equal(filterLoadedReceipts(rows, "shared")[0], a);
  assert.deepEqual(filterLoadedReceipts(rows, "opposition"), []);
});

test("ordinary numeric terms match printed whole numbers, not longer numbers", () => {
  const a = row(1, "FY 2026"), b = row(10, "FY 20260");
  assert.deepEqual(filterLoadedReceipts([a, b], "2026"), [a]);
});

test("a filtered existing group retains its identity without inventing groups for single receipts", () => {
  const a = row(1, "H.R. 27", { canonical_action_id: "house:119:1:1", bill_id: "hr27-119", position: "yea" });
  const b = row(2, "H.R. 27", { canonical_action_id: "house:119:1:2", bill_id: "hr27-119", position: "nay" });
  const [group] = buildLedgerItems([b, a]);
  const [retained] = buildLedgerItems(filterLoadedReceipts([b, a], "roll1"), { retainedGroupIds: [group.id] });
  assert.equal(retained.type, "group");
  assert.equal(retained.id, group.id);
  assert.deepEqual(retained.rows, [a]);
  assert.deepEqual(retained.composition.positions, [{ label: "Yea", count: 1 }]);
  assert.equal(buildLedgerItems([a])[0].type, "action");
});
