import fs from "node:fs";
import path from "node:path";

const candidate = JSON.parse(fs.readFileSync(path.resolve("../docs/editorial/full_record_reviews/site_integration_candidates/f000477_education_workforce_119_v1/site_integration_candidate.json"), "utf8"));

export const educationPresentation = candidate.subject.presentation;
export const educationEvidence119 = candidate.subject.preview_data.evidence_119;

export function educationEvidenceForScope(scope) {
  return scope === "118" ? [] : educationEvidence119;
}

export function educationPositionsForScope(scope) {
  if (scope === "118") {
    return { scope_metadata: { congresses: [118], requested_congresses: [118], scope_label: "118th Congress" }, positions: [] };
  }
  const yea = educationEvidence119.filter((row) => row.position === "yea").length;
  const nay = educationEvidence119.filter((row) => row.position === "nay").length;
  const interpretedSupport = educationEvidence119.filter((row) => row.governed_receipt_projection.exact_choice_position_effect === "supports_exact_choice").length;
  const interpretedOppose = educationEvidence119.filter((row) => row.governed_receipt_projection.exact_choice_position_effect === "opposes_exact_choice").length;
  return { scope_metadata: { congresses: [119], requested_congresses: [119], scope_label: scope === "all" ? "All available Congresses" : "119th Congress" }, positions: [{ domain: "EDUCATION_WORKFORCE", yea_count: yea, nay_count: nay, other_count: educationEvidence119.length - yea - nay, total_votes: 17, recorded_votes: yea + nay, interpreted_support_count: interpretedSupport, interpreted_oppose_count: interpretedOppose, interpreted_other_count: educationEvidence119.length - interpretedSupport - interpretedOppose, interpreted_total: 17 }] };
}
