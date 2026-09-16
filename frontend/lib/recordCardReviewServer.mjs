// Local, opt-in replay of verified public responses. No database or network client.
import fs from "node:fs";
import path from "node:path";
import { gunzipSync } from "node:zlib";
import { createHash } from "node:crypto";

export const REVIEW_PROFILES = [
  { id: "leg_valerie_p_foushee", bioguide_id: "F000477", name_display: "Valerie P. Foushee", chamber: "house", state: "NC", district: "04", party: "D" },
  { id: "leg_thomas_massie", bioguide_id: "M001184", name_display: "Thomas Massie", chamber: "house", state: "KY", district: "04", party: "R" },
];

export function recordCardReviewEnabled(env = process.env) {
  return env.ENABLE_RECORD_CARD_REVIEW === "1" && !env.VERCEL && env.VERCEL_ENV !== "production";
}

const root = path.resolve(process.cwd(), path.basename(process.cwd()) === "frontend" ? ".." : ".");
let cached;
export function loadRecordCardReview() {
  if (!recordCardReviewEnabled()) throw Error("Local review is disabled");
  if (cached) return cached;
  const candidate = JSON.parse(fs.readFileSync(path.join(root, "docs/review_packets/record_at_a_glance_v1/candidate.json"), "utf8"));
  const bytes = fs.readFileSync(path.join(root, candidate.source_snapshot));
  if (createHash("sha256").update(bytes).digest("hex") !== candidate.source_snapshot_sha256) throw Error("Review snapshot integrity mismatch");
  cached = { candidate, snapshot: JSON.parse(gunzipSync(bytes)) };
  return cached;
}

export function reviewResponse({ member, scope, resource, domain }) {
  if (!REVIEW_PROFILES.some((p) => p.id === member) || !["118", "119", "all"].includes(scope)) return null;
  if (resource === "profile") return { status: 200, body: REVIEW_PROFILES.find((p) => p.id === member) };
  if (!["positions", "editorial", "evidence"].includes(resource)) return null;
  if (resource === "evidence" && !/^[A-Z_]+$/.test(domain || "")) return null;
  return loadRecordCardReview().snapshot[`${member}:${scope}:${resource === "evidence" ? domain : resource}`] || null;
}
