import { isProceduralContextRow } from "./proceduralContext.mjs";

export const PUBLIC_COVERAGE_STATE = Object.freeze({
  reviewedConclusion: "reviewed_conclusion",
  developingRecord: "developing_record",
  limitedEvidence: "limited_evidence",
  noEditorialCoverage: "no_editorial_coverage",
  proceduralContextOnly: "procedural_context_only",
});

const PUBLIC_STRENGTH = Object.freeze({
  bounded_repeated_pattern: "A consistent pattern in the reviewed record",
  bounded_selective_pattern: "A selective pattern in the reviewed record",
  bounded_conditional_boundary: "A mixed record with a clear boundary",
  contested_candidate: "A developing pattern",
  insufficient_evidence: "Not enough reviewed evidence yet",
});

export function buildPublicEditorialPresentation(candidate, evidenceRows = []) {
  const inference = candidate?.source?.inference_candidate || {};
  const coverage = buildEditorialCoverage(candidate, evidenceRows);
  const internalLevel = String(inference.inference_level || "");
  const strengthLabel = PUBLIC_STRENGTH[internalLevel]
    || mapLegacyStrength(candidate?.synthesis?.evidenceBreadth, coverage.state);

  return {
    conclusion: coverage.state === PUBLIC_COVERAGE_STATE.reviewedConclusion
      ? candidate?.synthesis?.primary
      : null,
    strengthLabel,
    patterns: (candidate?.synthesis?.patterns || []).map(cleanPattern).filter(Boolean),
    exceptions: buildExceptions(candidate, inference),
    votingContext: candidate?.synthesis?.votingContext,
    votingContextBoundary: cleanInternalLanguage(candidate?.synthesis?.votingContextBoundary),
    coverage,
    limits: buildLimits(candidate, inference, coverage),
  };
}

export function buildEditorialCoverage(candidate, evidenceRows = []) {
  const source = candidate?.source || {};
  const inference = source.inference_candidate || {};
  const interpretations = source.interpretations || [];
  const expectedVotes = interpretations.length;
  const observedKeys = new Set(evidenceRows.map(rowKey));
  const observedVotes = interpretations.filter((entry) => observedKeys.has(entryKey(candidate, entry))).length;
  const yesNoVotes = interpretations.filter((entry) => isYesNoAction(entry.member_action)).length;
  const notVoting = interpretations.filter((entry) => entry.member_action === "Not Voting").length;
  const present = interpretations.filter((entry) => entry.member_action === "Present").length;
  const expectedEpisodes = finiteNumber(source.slice_counts?.policy_episodes)
    ?? finiteNumber(inference.independent_episode_count)
    ?? countEpisodes(candidate, interpretations);
  const observedEpisodes = countObservedEpisodes(candidate, interpretations, observedKeys);
  const missingVotes = Math.max(expectedVotes - observedVotes, 0);
  const inferenceLevel = String(inference.inference_level || "");
  const hasConclusion = Boolean(candidate?.synthesis?.primary)
    && inferenceLevel !== "insufficient_evidence"
    && inferenceLevel !== "contested_candidate";
  const state = hasConclusion
    ? PUBLIC_COVERAGE_STATE.reviewedConclusion
    : observedEpisodes >= 2
      ? PUBLIC_COVERAGE_STATE.developingRecord
      : PUBLIC_COVERAGE_STATE.limitedEvidence;

  return {
    state,
    label: coverageLabel(state),
    message: coverageMessage({
      state,
      expectedVotes,
      yesNoVotes,
      expectedEpisodes,
      missingVotes,
      notVoting,
      present,
    }),
    reviewedPeriod: candidate?.identity?.reviewedPeriod || inference.reviewed_period,
    expectedVotes,
    observedVotes,
    yesNoVotes,
    notVoting,
    present,
    missingVotes,
    expectedEpisodes,
    observedEpisodes,
    completeForSelectedSet: missingVotes === 0,
  };
}

export function buildBasicEvidencePresentation(rows = []) {
  const proceduralRows = rows.filter(isProceduralContextRow);
  const notVotingRows = rows.filter((row) => row.position === "not_voting");
  const substantiveRows = rows.filter((row) => (
    row.interpretation_status === "interpreted"
    && (row.position === "yea" || row.position === "nay")
    && !isProceduralContextRow(row)
  ));
  const limitedRows = rows.filter((row) => (
    !substantiveRows.includes(row)
    && !proceduralRows.includes(row)
    && !notVotingRows.includes(row)
  ));
  const state = rows.length > 0 && proceduralRows.length === rows.length
    ? PUBLIC_COVERAGE_STATE.proceduralContextOnly
    : PUBLIC_COVERAGE_STATE.noEditorialCoverage;

  return {
    state,
    label: state === PUBLIC_COVERAGE_STATE.proceduralContextOnly
      ? "Procedural context only"
      : "Vote evidence",
    message: state === PUBLIC_COVERAGE_STATE.proceduralContextOnly
      ? "The available records concern floor process. They remain visible as context, but they do not establish a direct position on the underlying issue."
      : substantiveRows.length
        ? `${plural(substantiveRows.length, "reviewed Yes/No vote")} ${substantiveRows.length === 1 ? "is" : "are"} available. These receipts show recorded actions; this basic view does not combine them into a broader issue conclusion.`
        : "Vote receipts may be available, but this issue does not yet have enough reviewed substantive evidence for a plain-language issue conclusion.",
    substantiveVotes: substantiveRows.length,
    proceduralRecords: proceduralRows.length,
    notVoting: notVotingRows.length,
    limitedRecords: limitedRows.length,
  };
}

export function issueAvailabilityLabel({ hasEditorialSlice, row }) {
  if (hasEditorialSlice) return "Reviewed analysis";
  const reviewed = Number(row?.interpreted_support_count || 0) + Number(row?.interpreted_oppose_count || 0);
  if (reviewed > 0) return "Vote evidence";
  return "Limited record";
}

function buildExceptions(candidate, inference) {
  const supplied = candidate?.synthesis?.exceptions || [];
  const inferred = (inference.contrary_or_limiting_evidence || [])
    .map((item) => item?.text)
    .filter((text) => text && !/complete .+ record|private motive|party alignment/i.test(text));
  return [...supplied, ...inferred].map(cleanInternalLanguage).filter(Boolean).slice(0, 4);
}

function buildLimits(candidate, inference, coverage) {
  const supplied = inference.inference_level
    ? ""
    : cleanInternalLanguage(candidate?.synthesis?.howToRead);
  const bounded = cleanInternalLanguage(inference.why_conclusion_does_not_go_further);
  const future = coverage.state === PUBLIC_COVERAGE_STATE.reviewedConclusion
    ? "This conclusion reflects the votes reviewed so far and may be refined as additional policy episodes are added."
    : "Additional reviewed policy episodes may make the record clearer.";
  return [...new Set([supplied, bounded, future].filter(Boolean))];
}

function cleanPattern(value) {
  return cleanInternalLanguage(String(value || "")
    .replace(/^Within one episode:\s*/i, "")
    .replace(/^Across independent episodes:\s*/i, ""));
}

function cleanInternalLanguage(value) {
  if (!value) return "";
  return String(value)
    .replace(/rerun this inference from (?:the )?expanded annotations;?/gi, "review the conclusion again as the evidence expands;")
    .replace(/did not select the candidate conclusion/gi, "did not determine the conclusion")
    .replace(/selecting the candidate conclusion/gi, "determining the conclusion")
    .replace(/selected the candidate conclusion/gi, "determined the conclusion")
    .replace(/select the candidate conclusion/gi, "determine the conclusion")
    .replace(/candidate conclusion/gi, "conclusion")
    .replace(/\bcandidate\b/gi, "conclusion")
    .trim();
}

function mapLegacyStrength(value, state) {
  const normalized = String(value || "").toLowerCase();
  if (/selective/.test(normalized)) return PUBLIC_STRENGTH.bounded_selective_pattern;
  if (/mixed|conditional|contested/.test(normalized)) return "A mixed or conditional pattern";
  if (/repeated|strong/.test(normalized)) return PUBLIC_STRENGTH.bounded_repeated_pattern;
  if (/limited|insufficient|not enough/.test(normalized)) return PUBLIC_STRENGTH.insufficient_evidence;
  return state === PUBLIC_COVERAGE_STATE.reviewedConclusion
    ? "A pattern in the reviewed record"
    : "A developing record";
}

function coverageLabel(state) {
  return {
    [PUBLIC_COVERAGE_STATE.reviewedConclusion]: "Reviewed conclusion available",
    [PUBLIC_COVERAGE_STATE.developingRecord]: "Developing record",
    [PUBLIC_COVERAGE_STATE.limitedEvidence]: "Limited evidence",
  }[state];
}

function coverageMessage({ state, expectedVotes, yesNoVotes, expectedEpisodes, missingVotes, notVoting, present }) {
  const parts = [
    `${plural(yesNoVotes, "substantive Yes/No vote")} across ${plural(expectedEpisodes, "independent policy episode")} ${yesNoVotes === 1 ? "was" : "were"} reviewed.`,
  ];
  if (notVoting) parts.push(`${plural(notVoting, "action")} ${notVoting === 1 ? "was" : "were"} Not Voting.`);
  if (present) parts.push(`${plural(present, "action")} ${present === 1 ? "was" : "were"} Present.`);
  if (missingVotes) parts.push(`${plural(missingVotes, "expected vote record")} ${missingVotes === 1 ? "is" : "are"} not available.`);
  else if (expectedVotes) parts.push("Every expected action in this selected set is accounted for.");
  if (state === PUBLIC_COVERAGE_STATE.developingRecord) parts.push("The reviewed evidence is meaningful, but the repeated pattern is still developing.");
  if (state === PUBLIC_COVERAGE_STATE.limitedEvidence) parts.push("Too few independent episodes are complete for a reliable cross-episode conclusion.");
  return parts.join(" ");
}

function countEpisodes(candidate, entries) {
  return new Set(entries.map((entry) => episodeId(candidate, entry)).filter(Boolean)).size;
}

function countObservedEpisodes(candidate, entries, observedKeys) {
  return new Set(entries
    .filter((entry) => observedKeys.has(entryKey(candidate, entry)) && isYesNoAction(entry.member_action))
    .map((entry) => episodeId(candidate, entry))
    .filter(Boolean)).size;
}

function episodeId(candidate, entry) {
  return entry.episode_id ?? candidate?.episodeByRoll?.[entry.roll] ?? null;
}

function entryKey(candidate, entry) {
  return `${candidate?.identity?.congress}:${entry.roll}`;
}

function rowKey(row) {
  return `${row?.congress}:${row?.rollcall_number}`;
}

function isYesNoAction(action) {
  return action === "Yea" || action === "Nay" || action === "Yes" || action === "No";
}

function finiteNumber(value) {
  return Number.isFinite(value) ? value : null;
}

function plural(value, singular) {
  return `${value} ${singular}${value === 1 ? "" : "s"}`;
}
