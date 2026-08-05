import fs from "node:fs";
import path from "node:path";

export const selectedIssueReview = JSON.parse(fs.readFileSync(
  path.resolve("fixtures/foushee_justice_m6_review.json"),
  "utf8",
));

const controls = new Map([
  ["house:119:2:155", "context_only_control_exclusion"],
  ["house:119:2:278", "exact_action_eligibility"],
]);
const ndaaRolls = new Set([259, 265, 273, 275, 278]);
const amendmentTitles = new Map([
  [259, "Add a defense energy infrastructure certification regime"],
  [265, "Create a personal-firearm permission process at Defense facilities"],
  [273, "Add the Military Chaplains Modernization Act"],
  [275, "Bar federal funding for automated speed-enforcement cameras"],
  [278, "Final passage after amendments"],
]);
const standaloneTitles = new Map([
  [218, "Fraud Prevention and Accountability Act"],
  [221, "To amend the FISA Amendments Act of 2008 to extend the authorities of title VII of the Foreign Intelligence Surveillance Act of 1978, and for other purposes"],
  [227, "Financial Exploitation Prevention Act"],
  [234, "Weatherizing Infrastructure in the North and Terrorism Emergency Readiness Act"],
  [240, "Protecting Privacy in Purchases Act"],
]);

export const selectedIssueEvidence119 = selectedIssueReview.ledger.map((record) => {
  const isControl = controls.has(record.canonical_action_id);
  return {
    canonical_action_id: record.canonical_action_id,
    chamber: "house",
    congress: 119,
    rollcall_number: record.roll_call,
    vote_date: record.date,
    vote_type: record.legislative_stage,
    description: `House roll ${record.roll_call}`,
    position: record.member_action,
    interpretation_status: record.non_proposition_state || "interpreted",
    plain_english_summary:
      record.governed_action_meaning
      || "No safe public analytical meaning is available for this action.",
    question:
      record.governed_action_meaning
      || "The exact final-package policy question remains unresolved.",
    uncertainty_note: record.limitations.join(" "),
    source_url: record.official_vote_source?.[0]?.url,
    source_basis: (record.official_action_meaning_sources || []).map((source) => ({
      label: source.source_id,
      url: source.url,
    })),
    bill_title: record.session === 2 && ndaaRolls.has(record.roll_call)
      ? "National Defense Authorization Act for Fiscal Year 2027"
      : record.session === 2
        ? standaloneTitles.get(record.roll_call)
        : undefined,
    amendment_purpose: record.session === 2
      ? amendmentTitles.get(record.roll_call)
      : undefined,
    governed_receipt_projection: isControl ? undefined : {
      canonical_action_id: record.canonical_action_id,
      exact_action_meaning: record.governed_action_meaning,
      policy_question: record.governed_action_meaning,
      member_action: record.member_action,
      episode_id: record.episode_id,
      episode_relationship: record.episode_id
        ? "This action is one independently expandable part of the related policy episode."
        : "",
      caveats: record.limitations,
      vote_sources: record.official_vote_source,
      action_meaning_sources: record.official_action_meaning_sources,
    },
    vote_context: record.session === 2 && record.roll_call === 275
      ? { final_result: "passed" }
      : undefined,
    governed_receipt_control: isControl
      ? {
          status: "noncounting_control",
          boundary_type: controls.get(record.canonical_action_id),
          detail: record.limitations.join(" "),
        }
      : undefined,
  };
});

export const selectedIssueEvidence118 = Array.from({ length: 52 }, (_, index) => {
  const roll = 700 + index;
  const month = 1 + Math.floor(index / 26);
  const day = 1 + (index % 26);
  return {
    canonical_action_id: `house:118:2:${roll}`,
    chamber: "house",
    congress: 118,
    rollcall_number: roll,
    vote_date: `2024-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`,
    vote_type: "passage",
    description: `Recorded Justice action ${roll}`,
    position: index % 2 ? "nay" : "yea",
    interpretation_status: "unreviewed",
    plain_english_summary: `Recorded action ${roll} exact vote evidence.`,
    question: `Whether to adopt recorded action ${roll}.`,
    source_url: `https://clerk.house.gov/Votes/2024${roll}`,
    source_basis: [{
      label: "Official bill",
      url: `https://www.congress.gov/bill/118th-congress/house-bill/${roll}`,
    }],
  };
});

export function selectedIssueEvidenceForScope(scope) {
  if (scope === "119") {
    return selectedIssueEvidence119;
  }
  if (scope === "118") {
    return selectedIssueEvidence118;
  }
  return [...selectedIssueEvidence119, ...selectedIssueEvidence118];
}
