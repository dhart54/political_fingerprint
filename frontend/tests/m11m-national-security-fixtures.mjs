import fs from "node:fs";
import path from "node:path";

const root = path.resolve("..");
const candidate = JSON.parse(fs.readFileSync(path.join(
  root,
  "docs/editorial/full_record_reviews/site_integration_candidates/f000477_national_security_foreign_119_v1/site_integration_candidate.json",
), "utf8"));
const episodes = JSON.parse(fs.readFileSync(path.join(
  root,
  "docs/editorial/full_record_reviews/policy_episode_implementations/f000477_national_security_foreign_119_v1/episode_decision_implementation_bundle.json",
), "utf8"));

export const nationalSecurityPresentation = candidate.subject.presentation;

export const nationalSecurityEvidence119 = episodes.subject.implementation_records
  .flatMap((episode) => episode.actions.map((action) => ({
    canonical_action_id: action.action_id,
    chamber: "house",
    congress: 119,
    rollcall_number: Number(action.action_id.split(":").at(-1)),
    vote_date: action.official_action_date,
    vote_type: action.action_role,
    description: `House roll ${action.action_id.split(":").at(-1)}`,
    issue_domain: "NATIONAL_SECURITY_FOREIGN",
    position: action.accepted_exact_choice_position_effect === "supports_exact_choice"
      ? "yea"
      : "nay",
    interpretation_status: "interpreted",
    plain_english_summary: action.accepted_exact_action_meaning,
    question: action.accepted_exact_action_meaning,
    uncertainty_note: action.accepted_limitations.join(" "),
    source_url: `https://clerk.house.gov/Votes/2026${action.action_id.split(":").at(-1)}`,
    source_basis: action.source_references.map((source) => ({
      label: source.startsWith("clerk:") ? "Official House vote" : "Official measure source",
      url: source.startsWith("clerk:")
        ? `https://clerk.house.gov/Votes/2026${action.action_id.split(":").at(-1)}`
        : "https://www.congress.gov/",
    })),
    governed_receipt_projection: {
      canonical_action_id: action.action_id,
      exact_action_meaning: action.accepted_exact_action_meaning,
      policy_question: action.accepted_exact_action_meaning,
      member_action: action.accepted_exact_choice_position_effect === "supports_exact_choice"
        ? "Yea"
        : "Nay",
      episode_id: episode.episode_id,
      episode_relationship: "This action is independently expandable in the reviewed record.",
      caveats: action.accepted_limitations,
      vote_sources: [{ label: "Official House vote", url: "https://clerk.house.gov/" }],
      action_meaning_sources: [{ label: "Official measure source", url: "https://www.congress.gov/" }],
    },
  })))
  .concat([{
    canonical_action_id: "house:119:2:278",
    chamber: "house",
    congress: 119,
    rollcall_number: 278,
    vote_date: "2026-07-22",
    vote_type: "passage",
    description: "H.R. 8800 final passage after amendments",
    issue_domain: "NATIONAL_SECURITY_FOREIGN",
    position: "nay",
    interpretation_status: "insufficient_evidence",
    plain_english_summary: "No safe public analytical meaning is available for this action.",
    question: "The complete final House-passed package is not established by the reviewed source set.",
    uncertainty_note: "This action remains outside interpretation and every analytical finding.",
    source_url: "https://clerk.house.gov/Votes/2026278",
    source_basis: [{ label: "Official House vote", url: "https://clerk.house.gov/Votes/2026278" }],
    governed_receipt_control: {
      status: "noncounting_control",
      boundary_type: "source_blocked_uninterpreted",
      detail: "No safe public analytical meaning is available for this action.",
    },
  }]);

export function nationalSecurityEvidenceForScope(scope) {
  return scope === "118" ? [] : nationalSecurityEvidence119;
}

export function nationalSecurityPositionsForScope(scope) {
  if (scope === "118") {
    return {
      scope_metadata: { congresses: [118], requested_congresses: [118], scope_label: "118th Congress" },
      positions: [],
    };
  }
  const yea = nationalSecurityEvidence119.filter((row) => row.position === "yea").length;
  const nay = nationalSecurityEvidence119.filter((row) => row.position === "nay").length;
  return {
    scope_metadata: {
      congresses: [119],
      requested_congresses: [119],
      scope_label: scope === "all" ? "All available Congresses" : "119th Congress",
    },
    positions: [{
      domain: "NATIONAL_SECURITY_FOREIGN",
      yea_count: yea,
      nay_count: nay,
      other_count: 1,
      total_votes: 82,
      recorded_votes: 82,
      interpreted_support_count: yea,
      interpreted_oppose_count: nay,
      interpreted_other_count: 0,
      interpreted_total: 81,
    }],
  };
}
