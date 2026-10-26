import assert from "node:assert/strict";
import test from "node:test";
import { readableOfficialVoteUrl } from "./officialVoteLinks.mjs";
import { buildPublicReceipt } from "./publicReceipt.mjs";

const verified = [
  ["https://clerk.house.gov/evs/2025/roll313.xml", "https://clerk.house.gov/Votes/2025313"],
  ["https://clerk.house.gov/evs/2025/roll032.xml", "https://clerk.house.gov/Votes/202532"],
  ["https://clerk.house.gov/evs/2024/roll001.xml", "https://clerk.house.gov/Votes/20241"],
  ["https://clerk.house.gov/evs/2026/roll019.xml", "https://clerk.house.gov/Votes/202619"],
];

test("verified official routes offer readable pages and retain exact raw provenance", () => {
  for (const [raw, readable] of verified) {
    assert.equal(readableOfficialVoteUrl(raw), readable);
    for (const source of [raw, { url: raw, source_id: "unchanged", source_sha256: "a".repeat(64) }, { source_url: raw }]) {
      const row = { governed_receipt_projection: { vote_sources: [source, source], member_action: "Not Voting" } };
      const before = structuredClone(row);
      assert.deepEqual(buildPublicReceipt(row).voteSources, [{ label: "Official vote", url: raw, readableUrl: readable }]);
      assert.equal(buildPublicReceipt(row).representativeVote, "Not Voting");
      assert.deepEqual(row, before);
    }
    assert.equal(buildPublicReceipt({ source_url: raw }).voteSources[0].readableUrl, readable);
    assert.deepEqual(buildPublicReceipt({ source_basis: [raw] }).actionSources, [{ label: "Bill or amendment text", url: raw }]);
  }
});

test("existing readable sources and unsupported formats remain exact without guessed URLs", () => {
  for (const raw of [
    ...verified.map(([, readable]) => readable),
    "https://clerk.house.gov/Votes/2025313?RollCallNum=313",
    "https://clerk.house.gov/evs/2025/roll313",
    "https://clerk.house.gov/evs/2025/roll313.xml?download=1",
    "https://clerk.house.gov/evs/2025/roll313.xml#vote",
    "https://clerk.house.gov/evs/2025/roll000.xml",
    "https://clerk.house.gov/evs/0000/roll313.xml",
    "https://clerk.house.gov/evs/1789/roll313.xml",
    `https://clerk.house.gov/evs/${new Date().getUTCFullYear() + 1}/roll313.xml`,
    "https://clerk.house.gov/evs/2025/roll32.xml",
    "https://clerk.house.gov.example.org/evs/2025/roll313.xml",
    "https://clerk.house.gov@other.example/evs/2025/roll313.xml",
    "https://user@clerk.house.gov/evs/2025/roll313.xml",
    "https://clerk.house.gov:444/evs/2025/roll313.xml",
    "https://www.senate.gov/legislative/LIS/roll_call_votes/vote1192/vote_119_1_00081.xml",
    "https://www.senate.gov/legislative/LIS/roll_call_votes/vote1181/vote_119_1_00081.xml",
    "https://www.senate.gov/legislative/LIS/roll_call_votes/vote1191/vote_119_1_00000.xml",
    "https://www.senate.gov/legislative/LIS/roll_call_votes/vote0001/vote_000_1_00081.xml",
    "https://www.senate.gov/legislative/LIS/roll_call_votes/vote1191/vote_119_1_00081.xml",
    "https://www.congress.gov/bill/119th-congress/house-bill/1069",
  ]) {
    assert.equal(readableOfficialVoteUrl(raw), null, raw);
    assert.deepEqual(buildPublicReceipt({ source_url: raw }).voteSources, [{ label: "Official vote", url: raw }]);
  }
  for (const raw of [null, "not a URL", "javascript:alert(1)"]) assert.equal(readableOfficialVoteUrl(raw), null);
});
