import { isProceduralContextRow } from "./proceduralContext.mjs";

export const BASIC_EVIDENCE_STATE = Object.freeze({
  voteEvidence: "vote_evidence",
  proceduralContextOnly: "procedural_context_only",
});

export function buildBasicEvidencePresentation(rows = []) {
  const proceduralRows = rows.filter(isProceduralContextRow);
  const notVotingRows = rows.filter((row) => normalize(row.position) === "not_voting");
  const presentRows = rows.filter((row) => normalize(row.position) === "present");
  const missingEvidenceRows = rows.filter(isMissingEvidenceRow);
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
    && !missingEvidenceRows.includes(row)
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
        ? `${plural(substantiveRows.length, "reviewed Yes/No vote")} ${substantiveRows.length === 1 ? "is" : "are"} available. These receipts show recorded actions; this basic view does not combine them into a broader issue conclusion.`
        : "Vote receipts may be available, but this issue does not yet have enough reviewed substantive evidence for a plain-language issue conclusion.",
    substantiveVotes: substantiveRows.length,
    proceduralRecords: proceduralRows.length,
    notVoting: notVotingRows.length,
    present: presentRows.length,
    missingEvidence: missingEvidenceRows.length,
    limitedRecords: limitedRows.length,
  };
}

export function issueAvailabilityLabel(row) {
  const reviewed = Number(row?.interpreted_support_count || 0)
    + Number(row?.interpreted_oppose_count || 0);
  return reviewed > 0 ? "Vote evidence" : "Limited record";
}

function isMissingEvidenceRow(row) {
  const values = [
    row?.position,
    row?.action_status,
    row?.evidence_status,
    row?.interpretation_status,
    row?.service_status,
  ].map(normalize);
  return values.includes("missing_evidence") || values.includes("missing");
}

function normalize(value) {
  return String(value || "").trim().toLowerCase().replaceAll(" ", "_");
}

function plural(value, singular) {
  return `${value} ${value === 1 ? singular : `${singular}s`}`;
}
