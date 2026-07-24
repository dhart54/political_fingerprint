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
  const strengthLabel = candidate?.synthesis?.readerFacingLabel || PUBLIC_STRENGTH[internalLevel]
    || mapLegacyStrength(candidate?.synthesis?.evidenceBreadth, coverage.state);

  return {
    conclusion: coverage.state === PUBLIC_COVERAGE_STATE.reviewedConclusion
      ? candidate?.synthesis?.primary
      : null,
    strengthLabel,
    analyticalSections: buildAnalyticalSections(candidate),
    patterns: (candidate?.synthesis?.patterns || []).map(cleanPattern).filter(Boolean),
    exceptions: buildExceptions(candidate, inference),
    votingContext: candidate?.synthesis?.votingContext,
    votingContextBoundary: cleanInternalLanguage(candidate?.synthesis?.votingContextBoundary),
    coverage,
    coverageLine: compactCoverageLine(coverage),
    proceduralContextLine: sourceProceduralLine(candidate?.source?.slice_counts?.context_controls),
  };
}

export function buildEditorialCoverage(candidate, evidenceRows = []) {
  const source = candidate?.source || {};
  const inference = source.inference_candidate || {};
  const interpretations = source.interpretations || [];
  const observedKeys = new Set(evidenceRows.map(rowKey));
  const structuredCoverage = hasStructuredCoverage(inference.coverage) ? inference.coverage : null;
  const legacyExpectedVotes = interpretations.length;
  const legacyObservedVotes = interpretations.filter((entry) => observedKeys.has(entryKey(candidate, entry))).length;
  const legacyExpectedEpisodes = finiteNumber(source.slice_counts?.policy_episodes)
    ?? finiteNumber(inference.independent_episode_count)
    ?? countEpisodes(candidate, interpretations);
  const legacyObservedEpisodes = countObservedEpisodes(candidate, interpretations, observedKeys);
  const expectedVotes = structuredCoverage
    ? coverageNumber(structuredCoverage, "substantive_rolls_expected")
    : legacyExpectedVotes;
  const observedVotes = structuredCoverage
    ? coverageNumber(structuredCoverage, "substantive_rolls_observed")
    : legacyObservedVotes;
  const yesNoVotes = structuredCoverage
    ? coverageNumber(structuredCoverage, "substantive_yes_no_actions")
    : interpretations.filter((entry) => isYesNoAction(entry.member_action)).length;
  const notVoting = structuredCoverage
    ? coverageNumber(structuredCoverage, "not_voting_actions")
    : interpretations.filter((entry) => entry.member_action === "Not Voting").length;
  const present = structuredCoverage
    ? coverageNumber(structuredCoverage, "present_actions")
    : interpretations.filter((entry) => entry.member_action === "Present").length;
  const missingVotes = structuredCoverage
    ? coverageNumber(structuredCoverage, "missing_actions")
    : Math.max(expectedVotes - observedVotes, 0);
  const expectedEpisodes = structuredCoverage
    ? coverageNumber(structuredCoverage, "independent_episodes_expected")
    : legacyExpectedEpisodes;
  const completeEpisodes = structuredCoverage
    ? coverageNumber(structuredCoverage, "independent_episodes_complete")
    : legacyObservedEpisodes;
  const partialEpisodes = structuredCoverage
    ? coverageNumber(structuredCoverage, "independent_episodes_partial")
    : 0;
  const missingEpisodes = structuredCoverage
    ? coverageNumber(structuredCoverage, "independent_episodes_missing")
    : Math.max(expectedEpisodes - legacyObservedEpisodes, 0);
  const observedEpisodes = completeEpisodes + partialEpisodes;
  const inferenceLevel = String(inference.inference_level || "");
  const hasConclusion = Boolean(candidate?.synthesis?.primary)
    && inferenceLevel !== "insufficient_evidence"
    && inferenceLevel !== "contested_candidate";
  const state = hasConclusion
    ? PUBLIC_COVERAGE_STATE.reviewedConclusion
    : inferenceLevel === "insufficient_evidence"
      ? PUBLIC_COVERAGE_STATE.limitedEvidence
      : inferenceLevel === "contested_candidate"
        ? PUBLIC_COVERAGE_STATE.developingRecord
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
      completeEpisodes,
      partialEpisodes,
      missingEpisodes,
      missingVotes,
      notVoting,
      present,
      usesAuthoritativeCoverage: Boolean(structuredCoverage),
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
    completeEpisodes,
    partialEpisodes,
    missingEpisodes,
    completeForSelectedSet: missingVotes === 0 && partialEpisodes === 0 && missingEpisodes === 0,
    usesAuthoritativeCoverage: Boolean(structuredCoverage),
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
  const explicitlyPublic = (candidate?.synthesis?.exceptions || [])
    .map((item, index) => exceptionEntry(item, { index, isPublic: true }));
  const inferred = (inference.contrary_or_limiting_evidence || [])
    .map((item, index) => exceptionEntry(item, { index }));
  const annotationEntries = (inference.episode_annotations || []).flatMap((annotation, annotationIndex) => [
    ...(annotation.contrary_or_limiting_evidence || []).map((text, index) => exceptionEntry(text, {
      episodeId: annotation.episode_id,
      index: annotationIndex * 100 + index,
      direction: annotation.conclusion_effect?.direction,
    })),
    ...(annotation.package_vote_limitations || []).map((text, index) => exceptionEntry(text, {
      episodeId: annotation.episode_id,
      index: annotationIndex * 100 + 50 + index,
      direction: annotation.conclusion_effect?.direction,
      isPackageLimit: true,
    })),
  ]);
  const weakeningEpisodes = new Set((inference.weakening_independent_episodes || [])
    .map((episode) => episode?.episode_id)
    .filter(Boolean));
  for (const entry of [...inferred, ...annotationEntries]) {
    if (weakeningEpisodes.has(entry.episodeId) || /weaken|conflict|contrar/i.test(entry.direction)) {
      entry.isWeakening = true;
    }
  }

  const entries = deduplicateExceptions([...explicitlyPublic, ...inferred, ...annotationEntries])
    .filter((entry) => entry.text
      && !/complete .+ record|private motive|party alignment/i.test(entry.text)
      && !containsInternalMethodology(entry.text));
  const selected = [];
  addRankedExceptions(selected, entries.filter((entry) => entry.isPublic), { preferDiversity: false });
  addRankedExceptions(selected, entries.filter((entry) => entry.isWeakening && !entry.isPublic), { preferDiversity: true, fillRemaining: false });
  addRankedExceptions(selected, entries.filter((entry) => entry.episodeId && !entry.isPublic && !entry.isWeakening), { preferDiversity: true, fillRemaining: false });
  addRankedExceptions(selected, entries.filter((entry) => entry.episodeId && !entry.isPublic), { preferDiversity: false });
  addRankedExceptions(selected, entries.filter((entry) => !entry.episodeId && !entry.isPublic), { preferDiversity: false });
  return selected.slice(0, 4).map((entry) => entry.text);
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

export function compactCoverageLine(coverage) {
  const parts = [];
  if (coverage.completeForSelectedSet) {
    parts.push(plural(coverage.yesNoVotes, "substantive vote"));
    parts.push(plural(coverage.completeEpisodes, "policy episode"));
  } else {
    const inServiceExpected = Math.max(coverage.expectedVotes, 0);
    const reviewed = Math.max(inServiceExpected - coverage.missingVotes, 0);
    parts.push(`${reviewed} of ${inServiceExpected} expected in-service actions reviewed`);
    if (coverage.completeEpisodes) parts.push(plural(coverage.completeEpisodes, "complete episode"));
    if (coverage.partialEpisodes) parts.push(plural(coverage.partialEpisodes, "partial episode"));
    if (coverage.missingEpisodes) parts.push(plural(coverage.missingEpisodes, "missing episode"));
  }
  if (coverage.notVoting) parts.push(plural(coverage.notVoting, "Not Voting action"));
  if (coverage.present) parts.push(plural(coverage.present, "Present action"));
  if (coverage.reviewedPeriod) parts.push(cleanPeriodLabel(coverage.reviewedPeriod));
  return parts.join(" · ");
}

function buildAnalyticalSections(candidate) {
  const supplied = candidate?.synthesis?.analyticalSections || {};
  const definitions = [
    ["repeatedPatterns", "Repeated patterns"],
    ["policyTrajectories", "Policy trajectories"],
    ["otherNotableChoices", "Other notable choices"],
    ["meaningfulExceptions", "Meaningful exceptions"],
  ];
  return definitions.map(([key, title]) => ({
    key,
    title,
    items: asArray(supplied[key]).map((item) => typeof item === "string" ? { text: item } : item).filter((item) => item?.text),
  })).filter((section) => section.items.length).map((section) => ({
    ...section,
    title: section.items.length === 1 ? singularAnalyticalHeading(section.key) : section.title,
  }));
}

function singularAnalyticalHeading(key) {
  return {
    repeatedPatterns: "Repeated pattern",
    policyTrajectories: "Policy trajectory",
    otherNotableChoices: "Other notable choice",
    meaningfulExceptions: "Meaningful exception",
  }[key];
}

function sourceProceduralLine(value) {
  if (!Number.isFinite(value) || value <= 0) return null;
  return `${plural(value, "procedural action")} available as context`;
}

function cleanPeriodLabel(value) {
  const text = String(value || "").trim();
  const congress = text.match(/\b(\d{3})(?:st|nd|rd|th)? Congress\b/i)?.[0];
  return congress || text.replace(/^(\d{3})(?:st|nd|rd|th)?\s*-\s*\1(?:st|nd|rd|th)?\s*-\s*/i, "");
}

function coverageMessage({
  state,
  expectedVotes,
  yesNoVotes,
  expectedEpisodes,
  completeEpisodes,
  partialEpisodes,
  missingEpisodes,
  missingVotes,
  notVoting,
  present,
  usesAuthoritativeCoverage,
}) {
  const parts = [
    `${plural(yesNoVotes, "substantive Yes/No vote")} ${yesNoVotes === 1 ? "was" : "were"} reviewed across ${plural(completeEpisodes, "complete independent policy episode")}.`,
  ];
  if (usesAuthoritativeCoverage) parts.push(`The selected set contains ${plural(expectedEpisodes, "expected independent policy episode")}.`);
  if (partialEpisodes) parts.push(`${plural(partialEpisodes, "independent policy episode")} ${partialEpisodes === 1 ? "is" : "are"} partially covered.`);
  if (missingEpisodes) parts.push(`${plural(missingEpisodes, "independent policy episode")} ${missingEpisodes === 1 ? "is" : "are"} missing.`);
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

function hasStructuredCoverage(value) {
  return Boolean(value && typeof value === "object" && !Array.isArray(value));
}

function coverageNumber(coverage, key) {
  return Math.max(finiteNumber(coverage?.[key]) ?? 0, 0);
}

function asArray(value) {
  if (Array.isArray(value)) return value;
  return value ? [value] : [];
}

function exceptionEntry(item, options = {}) {
  const rawText = typeof item === "string" ? item : item?.text;
  const text = cleanInternalLanguage(rawText);
  return {
    text,
    episodeId: options.episodeId ?? item?.episode_id ?? item?.episodeId ?? null,
    direction: options.direction ?? item?.direction ?? "",
    index: options.index ?? 0,
    isPublic: Boolean(options.isPublic),
    isWeakening: false,
    isPackageLimit: Boolean(options.isPackageLimit),
  };
}

function deduplicateExceptions(entries) {
  const unique = [];
  for (const entry of entries) {
    if (!entry.text || unique.some((existing) => semanticallyEquivalent(existing.text, entry.text))) continue;
    unique.push(entry);
  }
  return unique;
}

function semanticallyEquivalent(left, right) {
  const leftKey = semanticKey(left);
  const rightKey = semanticKey(right);
  if (leftKey === rightKey) return true;
  const leftTokens = new Set(leftKey.split(" ").filter(Boolean));
  const rightTokens = new Set(rightKey.split(" ").filter(Boolean));
  const union = new Set([...leftTokens, ...rightTokens]);
  const overlap = [...leftTokens].filter((token) => rightTokens.has(token)).length;
  return union.size > 0 && overlap / union.size >= 0.86;
}

function semanticKey(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .replace(/\b(the|a|an|this|that|it|was|were|is|are)\b/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function containsInternalMethodology(value) {
  return /\b(inference|annotations?|immutable|recomput(?:e|ation)|schema|support balance)\b|bounded[_ -](?:conditional|selective|repeated)|\b(?:candidate_id|inference_level)\b/i.test(value);
}

function addRankedExceptions(selected, candidates, { preferDiversity, fillRemaining = true }) {
  if (selected.length >= 4 || !candidates.length) return;
  const remaining = candidates
    .filter((candidate) => !selected.some((entry) => semanticallyEquivalent(entry.text, candidate.text)))
    .sort((left, right) => exceptionRelevance(right) - exceptionRelevance(left) || left.index - right.index);
  if (preferDiversity) {
    const usedEpisodes = new Set(selected.map((entry) => entry.episodeId).filter(Boolean));
    for (const candidate of remaining) {
      if (selected.length >= 4) return;
      if (candidate.episodeId && !usedEpisodes.has(candidate.episodeId)) {
        selected.push(candidate);
        usedEpisodes.add(candidate.episodeId);
      }
    }
  }
  if (!fillRemaining) return;
  for (const candidate of remaining) {
    if (selected.length >= 4) return;
    if (!selected.some((entry) => semanticallyEquivalent(entry.text, candidate.text))) selected.push(candidate);
  }
}

function exceptionRelevance(entry) {
  const text = entry.text.toLowerCase();
  let score = entry.isPublic ? 1000 : entry.isWeakening ? 500 : entry.episodeId ? 100 : 0;
  if (/not blanket|later support|related but not identical|actions differed|contrary|conflict/.test(text)) score += 40;
  if (/exception|not unconditional|not every|retained|repeal most/.test(text)) score += 35;
  if (entry.isPackageLimit || /combined|multiple|package/.test(text)) score += 25;
  if (/does not establish|not itself evidence/.test(text)) score += 5;
  return score;
}

function plural(value, singular) {
  return `${value} ${singular}${value === 1 ? "" : "s"}`;
}
