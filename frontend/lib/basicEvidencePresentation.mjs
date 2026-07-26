import { isProceduralContextRow } from "./proceduralContext.mjs";

export const BASIC_EVIDENCE_STATE = Object.freeze({
  voteEvidence: "vote_evidence",
  proceduralContextOnly: "procedural_context_only",
});

export function buildBasicEvidencePresentation(rows = []) {
  const proceduralRows = rows.filter(isProceduralContextRow);
  const notVotingRows = rows.filter((row) => normalize(row.position) === "not_voting");
  const presentRows = rows.filter((row) => normalize(row.position) === "present");
  const substantiveRows = rows.filter((row) => (
    normalize(row.interpretation_status) === "interpreted"
    && ["yea", "nay"].includes(normalize(row.position))
    && !isProceduralContextRow(row)
  ));
  const limitedRows = rows.filter((row) => (
    !substantiveRows.includes(row)
    && !proceduralRows.includes(row)
    && !notVotingRows.includes(row)
    && !presentRows.includes(row)
  ));
  const state = rows.length > 0 && proceduralRows.length === rows.length
    ? BASIC_EVIDENCE_STATE.proceduralContextOnly
    : BASIC_EVIDENCE_STATE.voteEvidence;

  return {
    state,
    label: state === BASIC_EVIDENCE_STATE.proceduralContextOnly
      ? "Procedural context only"
      : "Vote evidence",
    message: state === BASIC_EVIDENCE_STATE.proceduralContextOnly
      ? "The available records concern floor process. They remain visible as context, but they do not establish a direct position on the underlying issue."
      : substantiveRows.length
        ? `${plural(substantiveRows.length, "reviewed substantive Yes/No action")} ${substantiveRows.length === 1 ? "is" : "are"} available. These vote receipts show recorded actions; this basic view does not combine them into a broader issue conclusion.`
        : "Vote receipts may be available, but this issue does not yet have enough reviewed substantive evidence for a plain-language issue conclusion.",
    substantiveVotes: substantiveRows.length,
    proceduralRecords: proceduralRows.length,
    notVoting: notVotingRows.length,
    present: presentRows.length,
    limitedRecords: limitedRows.length,
  };
}

export function issueAvailabilityLabel(row) {
  if (!hasAvailableIssueEvidence(row)) {
    return "No evidence";
  }
  return Number(row?.recorded_votes || 0) > 0
    ? "Vote evidence"
    : "Non-directional evidence";
}

export function hasAvailableIssueEvidence(row) {
  const total = Number(row?.total_votes);
  if (Number.isFinite(total)) {
    return total > 0;
  }
  return Number(row?.yea_count || 0)
    + Number(row?.nay_count || 0)
    + Number(row?.other_count || 0) > 0;
}

function normalize(value) {
  return String(value || "").trim().toLowerCase().replaceAll(" ", "_");
}

function plural(value, singular) {
  return `${value} ${value === 1 ? singular : `${singular}s`}`;
}
