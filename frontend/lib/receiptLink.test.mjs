import assert from "node:assert/strict";
import test from "node:test";
import { buildReceiptLink } from "./receiptLink.mjs";
const context = { legislatorId: "leg_example", issue: "ECONOMY_TAXES", scope: "119", routePath: "/" };
const row = { canonical_action_id: "house:119:1:400" };
test("receipt link binds member, issue, scope and exact action", () => {
  assert.equal(buildReceiptLink(context, row), "/?representative=leg_example&issue=ECONOMY_TAXES&scope=119#action-receipt-house-119-1-400");
});
test("receipt link discards finding and unrelated query state, keeping review path", () => {
  const link = buildReceiptLink({ ...context, scope: "all", routePath: "/review/record-card?finding=x&source=hash&view=receipts&extra=x#finding-detail" }, row);
  assert.equal(link, "/review/record-card?representative=leg_example&issue=ECONOMY_TAXES#action-receipt-house-119-1-400");
});
test("raw unreviewed receipt identity stays distinct and exact", () => {
  assert.equal(buildReceiptLink(context, { interpretation_review_state: "not_yet_in_reviewed_interpretation", roll_call_id: "database-id" }).split("#")[1], "action-receipt-raw-database-id");
});
test("incomplete receipt identity or route does not produce a misleading link", () => {
  for (const incomplete of [{}, { interpretation_review_state: "not_yet_in_reviewed_interpretation" }, { canonical_action_id: "unsafe#id" }]) assert.equal(buildReceiptLink(context, incomplete), "");
  assert.equal(buildReceiptLink(null, row), "");
  assert.equal(buildReceiptLink({ ...context, issue: null }, row), "");
});
