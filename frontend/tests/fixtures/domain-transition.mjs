// SYNTHETIC TEST ONLY. Never import this fixture from application/runtime code.
// No approval, publication registry, real candidate, or production write is modeled.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { gunzipSync } from "node:zlib";
import { contentHash } from "../../lib/recordCard.mjs";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../..");
const manifest = JSON.parse(fs.readFileSync(path.join(root, "frontend/lib/recordCardContent.json"), "utf8"));
const historical = JSON.parse(fs.readFileSync(path.join(root, "docs/review_packets/record_at_a_glance_v1/candidate.json"), "utf8"));
const snapshot = JSON.parse(gunzipSync(fs.readFileSync(path.join(root, historical.source_snapshot))));

export const SYNTHETIC_DOMAIN = "ECONOMY_TAXES";
export const SYNTHETIC_ROOT = "test-only:offline-domain-transition:not-publication-authority";
export const TRANSITION_SCOPES = ["119", "all"];
export const transitionIdentity = {
  legislatorId: manifest.legislator_id,
  memberBioguideId: manifest.member_bioguide_id,
};

export async function makeDomainTransitionFixture() {
  const four = structuredClone(manifest);
  const five = structuredClone(manifest);
  five.synthetic_test_only = true;
  const fifthSource = { issue_id: SYNTHETIC_DOMAIN, presentation_sha256: {}, evidence_coverage: {} };
  const payloads = { four: {}, five: {} };
  for (const scope of TRANSITION_SCOPES) {
    const current = snapshot[`${manifest.legislator_id}:${scope}:editorial`].body;
    payloads.four[scope] = structuredClone(current);
    const next = structuredClone(current);
    const fifth = next.presentations.find((p) => p.issue_id === SYNTHETIC_DOMAIN);
    if (fifth.tier !== "receipts_only" || fifth.review_state) throw Error("Synthetic fifth-domain slot is no longer unreviewed");
    Object.assign(fifth, {
      tier: "reviewed_conclusion",
      tier_badge: "TEST ONLY synthetic domain",
      teaser: "TEST ONLY synthetic fifth-domain summary; no accepted candidate content.",
      public_status_label: "TEST ONLY synthetic fixture",
      reviewed_scope: "119",
      scope_boundary: `TEST ONLY synthetic 119th-Congress boundary requested in ${scope} scope.`,
      review_state: { congress_scope: [119], synthetic_test_only: true },
      provenance: { artifact_id: SYNTHETIC_ROOT, artifact_version: 1, synthetic_test_only: true },
    });
    payloads.five[scope] = next;
    fifthSource.presentation_sha256[scope] = await contentHash(fifth);
    fifthSource.evidence_coverage[scope] = {
      cutoff: null,
      cutoff_label: null,
      status: "unspecified_in_bound_review_scope",
      source_field: "scope_boundary",
      source_text: fifth.scope_boundary,
      source_sha256: await contentHash(fifth.scope_boundary),
    };
  }
  five.sources.push(fifthSource);
  return {
    synthetic_test_only: true,
    manifests: { four, five },
    payloads,
    staged: { root: SYNTHETIC_ROOT, activated: false, publication_eligible: false },
  };
}
