// Explicit transport contract. The server owns acceptance and canonical seals;
// this branch never borrows a legacy tier or invents an overall issue teaser.
const ACTION = "house:119:2:180";
const EPISODE = "episode:s2393:119";
const PROP = "prop:75edca987585935c";
const canonical = (v) => Array.isArray(v) ? `[${v.map(canonical).join(",")}]`
  : v !== null && typeof v === "object" ? `{${Object.keys(v).sort().map((k) => `${JSON.stringify(k)}:${canonical(v[k])}`).join(",")}}` : JSON.stringify(v);
const equal = (a, b) => canonical(a) === canonical(b);
const keys = (v, expected) => v !== null && typeof v === "object" && !Array.isArray(v)
  && equal(Object.keys(v).sort(), [...expected].sort());
const digest = (v) => typeof v === "string" && /^[0-9a-f]{64}$/.test(v);
const sources = [
  { source_id: "clerk:119:2:180", url: "https://clerk.house.gov/evs/2026/roll180.xml", governed_bytes_sha256: "eb88c63efbc5d13d03dcf1107601a087a1049e141679d10d89718e30331fd83f" },
  { source_id: "govinfo:s2393es", url: "https://www.govinfo.gov/content/pkg/BILLS-119s2393es/html/BILLS-119s2393es.htm", governed_bytes_sha256: "144cf0e5cc200e45790954355bcd42e45a247eee3ef64faba0d5e01beccec203" },
];

export function isBoundedChoiceProjection(p, envelope) {
  if (!keys(p, ["issue_id", "requested_scope", "tier", "presentation_branch", "bounded_choice", "conclusion", "teaser", "repeated_patterns", "policy_trajectories", "notable_choices", "policy_episodes", "review_state", "evidence_metadata"])) return false;
  const member = envelope?.member_bioguide_id;
  const supporting = member === "F000477";
  const slug = supporting ? "leg_valerie_p_foushee" : "leg_thomas_massie";
  if (!["F000477", "M001184"].includes(member) || envelope.legislator_id !== slug
      || !["119", "all"].includes(envelope.scope) || p.requested_scope !== envelope.scope
      || p.issue_id !== "HEALTH_SOCIAL" || p.tier !== "bounded_choice_review"
      || p.presentation_branch !== "bounded_choice_review" || p.conclusion !== null || p.teaser !== null
      || ![p.repeated_patterns, p.policy_trajectories, p.notable_choices, p.policy_episodes].every((a) => equal(a, []))) return false;
  if (!equal(p.review_state, { review_scope: "bounded_partial_record", review_completion_state: "in_progress",
    public_claim_class: "vote_record_only", congress_scope: [119], total_recorded_actions: 1, complete_episode_count: 1,
    full_issue_synthesis_eligible: false, benchmark_sample_available: false, conclusion_teaser: null })
    || !equal(p.evidence_metadata, { display_action_ids: supporting ? [ACTION] : [] })) return false;
  const b = p.bounded_choice;
  if (!keys(b, ["schema_version", "presentation_branch", "artifact_id", "member_id", "issue_id", "congress", "review_scope",
    "semantic_subject_sha256", "display_role", "official_member_action", "records", "boundaries", "proposition_ids", "action_ids",
    "episode_ids", "sources", "receipt", "authorizing", "publication_basis", "presentation_subject_sha256"])) return false;
  if (b.schema_version !== "bounded_choice_presentation_v1" || b.presentation_branch !== p.presentation_branch
      || b.artifact_id !== `bounded-choice:${member.toLowerCase()}:health:s2393:119:v1:presentation`
      || b.member_id !== member || b.issue_id !== p.issue_id || b.congress !== 119 || b.review_scope !== "bounded_partial_record"
      || !digest(b.semantic_subject_sha256) || !digest(b.presentation_subject_sha256)
      || b.display_role !== (supporting ? "supporting_notable_choice" : "non_directional_accounting")
      || b.official_member_action !== (supporting ? "Yea" : "Not Voting") || b.authorizing !== false
      || b.publication_basis !== p.presentation_branch || !equal(b.action_ids, [ACTION]) || !equal(b.episode_ids, [EPISODE])
      || !equal(b.proposition_ids, supporting ? [PROP] : []) || !equal(b.sources, sources)
      || !equal(b.receipt, { action_id: ACTION, bill: "S.2393", date: "2026-05-20", question: "On Motion to Suspend the Rules and Pass", chamber: "House", roll_number: 180 })) return false;
  const scopeId = `scope:s2393-review:${member.toLowerCase()}`;
  const boundaries = [{ action_ids: [ACTION], boundary_id: scopeId, boundary_type: "reviewed_congress_scope", episode_ids: [EPISODE], presentation_target: "scope_note" }];
  if (!supporting) boundaries.push({ action_ids: [ACTION], boundary_id: "coverage:c9ecb27beef8637e", boundary_type: "not_voting", detail: "Resolved Not Voting actions are non-directional.", presentation_target: "coverage_note" });
  if (!equal(b.boundaries, boundaries)) return false;
  const fields = supporting ? ["finding", "finding_title", "qualifications", "scope_label"] : ["accounting", "qualifications", "scope_label"];
  if (!keys(b.records, fields)) return false;
  return fields.every((field) => {
    const record = b.records[field];
    const suffix = field === "scope_label" ? "scope" : field;
    const finding = field === "finding" || field === "finding_title";
    const accounting = field === "accounting";
    return keys(record, ["mapping", "statement_id", "text"]) && typeof record.text === "string" && record.text.trim().length > 0
      && record.statement_id === `statement:s2393-review:${member}:${suffix}`
      && equal(record.mapping, { action_ids: [ACTION], boundary_ids: finding ? [] : [accounting ? "coverage:c9ecb27beef8637e" : scopeId],
        episode_ids: accounting ? [] : [EPISODE], mapping_id: `mapping:s2393-review:${member}:${suffix}`,
        presentation_target: finding ? "other_notable_choices" : accounting ? "coverage_note" : "scope_note",
        proposition_ids: finding ? [PROP] : [], receipt_refs: ["docs/review_packets/health_one_action_owner_decision_receipt_draft.md"],
        source_refs: ["clerk:119:2:180", "govinfo:s2393es"] });
  });
}
