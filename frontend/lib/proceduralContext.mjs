const PROCEDURAL_FACETS = new Set([
  "floor_rule_for_multiple_bills",
  "house_of_representatives",
  "House floor procedure",
]);

const PROCEDURAL_VOTE_TYPES = new Set([
  "concurrence",
  "motion",
  "procedural",
  "rule",
]);

export function isProceduralContextRow(row) {
  if (!row || row.interpretation_status === "interpreted") {
    return false;
  }

  const facet = String(row.issue_facet || "").trim();
  const voteType = String(row.vote_context?.vote_type || row.vote_type || "").trim().toLowerCase();
  const text = [
    row.issue_facet,
    row.description,
    row.question,
    row.bill_title,
    row.measure_title,
    row.uncertainty_note,
    row.vote_context?.question,
    row.vote_context?.description,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();

  const isHouseRuleFacet = PROCEDURAL_FACETS.has(facet);
  const isRuleVote = voteType === "rule" || /\b(ordering the previous question|agreeing to the resolution|providing for consideration|rule resolution)\b/.test(text);

  return (
    voteType === "procedural" ||
    isRuleVote ||
    (
      isHouseRuleFacet &&
      /\b(house rule|rule resolution|providing for consideration)\b/.test(text)
    ) ||
    (
      PROCEDURAL_VOTE_TYPES.has(voteType) &&
      /\b(house rule|rule resolution|providing for consideration)\b/.test(text)
    )
  );
}

export function buildProceduralContextSummary(row) {
  if (!isProceduralContextRow(row)) {
    return "";
  }

  const position = formatVotePosition(row?.position);
  const voteType = formatProceduralVoteType(row);
  const measure = formatProceduralMeasure(row);
  const relation = measure ? ` tied to ${measure}` : " tied to floor consideration";
  return `${position}. Procedural-context row. This was ${voteType}${relation}. It remains visible to explain floor process, but it is not counted as support or opposition and should not be read as final passage or as a direct position on the underlying bill.`;
}

function formatProceduralVoteType(row) {
  const question = String(row?.question || row?.description || "").toLowerCase();
  const voteType = String(row?.vote_context?.vote_type || row?.vote_type || "").toLowerCase();

  if (question.includes("ordering the previous question")) {
    return "a vote on ordering the previous question";
  }
  if (question.includes("agreeing to the resolution")) {
    return "a vote on agreeing to a rule resolution";
  }
  if (voteType === "rule") {
    return "a House rule vote";
  }
  if (voteType === "motion") {
    return "a procedural motion";
  }
  if (voteType === "concurrence") {
    return "a concurrence-related procedural vote";
  }
  return "a procedural or floor-rule vote";
}

function formatProceduralMeasure(row) {
  const bill = String(row?.bill_id || row?.source_bill_id || "").trim();
  const title = String(row?.bill_title || row?.measure_title || "").trim();

  if (title && bill) {
    return `${title} (${bill})`;
  }
  return title || bill || "";
}

function formatVotePosition(position) {
  if (position === "not_voting") {
    return "Not voting";
  }
  return String(position || "")
    .split("_")
    .map((segment) => (segment ? segment[0].toUpperCase() + segment.slice(1) : segment))
    .join(" ");
}
