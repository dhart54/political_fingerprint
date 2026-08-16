import fs from "node:fs";
import path from "node:path";

const candidate = JSON.parse(fs.readFileSync(path.resolve("../docs/editorial/full_record_reviews/site_integration_candidates/f000477_environment_energy_119_v1/site_integration_candidate.json"), "utf8"));

export const environmentPresentation = candidate.subject.presentation;
export const environmentEvidence119 = candidate.subject.preview_data.evidence_119;

export function environmentEvidenceForScope(scope) {
  return scope === "118" ? [] : environmentEvidence119;
}

export function environmentPositionsForScope(scope) {
  if (scope === "118") {
    return { scope_metadata: { congresses: [118], requested_congresses: [118], scope_label: "118th Congress" }, positions: [] };
  }
  const yea = environmentEvidence119.filter((row) => row.position === "yea").length;
  const nay = environmentEvidence119.filter((row) => row.position === "nay").length;
  return { scope_metadata: { congresses: [119], requested_congresses: [119], scope_label: scope === "all" ? "All available Congresses" : "119th Congress" }, positions: [{ domain: "ENVIRONMENT_ENERGY", yea_count: yea, nay_count: nay, other_count: environmentEvidence119.length - yea - nay, total_votes: 63, recorded_votes: 63, interpreted_support_count: environmentEvidence119.filter((row) => row.governed_receipt_projection.exact_choice_position_effect === "supports_exact_choice").length, interpreted_oppose_count: environmentEvidence119.filter((row) => row.governed_receipt_projection.exact_choice_position_effect === "opposes_exact_choice").length, interpreted_other_count: 0, interpreted_total: 63 }] };
}
