import { editorialIssueSlices } from "./editorialIssueSlices.mjs";

export const EDITORIAL_EXPERIENCE_MODE = Object.freeze({
  production: "production",
  review: "review",
});

export function isEditorialSliceEligible({ candidate, mode = EDITORIAL_EXPERIENCE_MODE.production }) {
  if (!candidate?.publication) return false;
  if (mode === EDITORIAL_EXPERIENCE_MODE.review) return true;
  return candidate.publication.editorialStatus === "human_approved"
    && candidate.publication.benchmarkStatus === "gold_benchmark"
    && candidate.publication.productionEligible === true;
}

export function selectEditorialIssueExperience({
  candidates = editorialIssueSlices,
  domain,
  evidenceRows = [],
  legislator = null,
  mode = EDITORIAL_EXPERIENCE_MODE.production,
}) {
  const candidate = candidates.find((item) => candidateMatches({ candidate: item, domain, evidenceRows, legislator }));
  if (!candidate || !isEditorialSliceEligible({ candidate, mode })) return null;
  return adaptEditorialIssueSlice(candidate, evidenceRows, mode);
}

export function isEditorialExperienceRow(row, experience) {
  return experience?.sourceRowKeys?.includes(rowKey(row)) || false;
}

export function adaptEditorialIssueSlice(candidate, evidenceRows = [], mode = EDITORIAL_EXPERIENCE_MODE.production) {
  const rowsByRoll = new Map(evidenceRows.map((row) => [Number(row.rollcall_number), row]));
  const interpretations = candidate.source.interpretations || [];
  const controls = candidate.source.controls || [];

  return {
    identity: { ...candidate.identity },
    publication: {
      ...candidate.publication,
      isReview: mode === EDITORIAL_EXPERIENCE_MODE.review,
    },
    synthesis: { ...candidate.synthesis },
    indicators: buildIndicators(candidate.source.slice_counts),
    records: [
      ...interpretations.map((entry) => adaptInterpretation(entry, rowsByRoll.get(Number(entry.roll)))),
      ...controls.map((entry) => adaptControl(entry, rowsByRoll.get(Number(entry.roll)))),
    ],
    sourceRowKeys: [...interpretations, ...controls].map((entry) => `${candidate.identity.congress}:${entry.roll}`),
  };
}

function candidateMatches({ candidate, domain, evidenceRows, legislator }) {
  if (candidate.identity.memberId !== legislator?.bioguide_id || candidate.identity.issueId !== domain) return false;
  const expected = [...(candidate.source.interpretations || []), ...(candidate.source.controls || [])];
  return expected.every((entry) => evidenceRows.some((row) => rowKey(row) === `${candidate.identity.congress}:${entry.roll}`));
}

function adaptInterpretation(entry, row = {}) {
  return {
    id: `roll-${entry.roll}`,
    actionIdentity: `House roll call ${entry.roll}`,
    episodeId: entry.measure_id,
    measure: row.description || row.question || entry.measure_id,
    legislativeStage: entry.stage,
    date: row.vote_date,
    memberAction: entry.member_action,
    result: row.vote_context?.final_result,
    lifecycleStatus: entry.ten_second?.member_action_and_result,
    headline: entry.ten_second?.headline,
    practicalChoice: entry.ten_second?.practical_choice,
    actionAndResult: entry.ten_second?.member_action_and_result,
    whatChanged: {
      before: entry.thirty_second?.prior_baseline,
      changeAtStake: entry.thirty_second?.mechanism,
    },
    impactAndOutcome: {
      affected: entry.thirty_second?.affected,
      scaleAndTiming: entry.thirty_second?.scale_or_timing,
      outcome: entry.thirty_second?.what_happened_next,
    },
    arguments: {
      supporters: entry.two_minute?.supporter_argument,
      opponents: entry.two_minute?.opponent_argument,
    },
    institutionalAttribution: entry.two_minute?.argument_boundary,
    additionalDetail: {
      detail: entry.two_minute?.detail,
      laterHistory: entry.two_minute?.later_history,
    },
    importantContext: entry.two_minute?.caveats || [],
    sources: entry.two_minute?.sources || [],
    inclusionClass: entry.member_action === "Not Voting" ? "not_voting" : "substantive",
  };
}

function adaptControl(entry, row = {}) {
  return {
    id: `context-${entry.roll}`,
    actionIdentity: `House roll call ${entry.roll}`,
    episodeId: entry.measure_id,
    measure: row.description || row.question || entry.measure_id,
    legislativeStage: row.vote_type,
    date: row.vote_date,
    memberAction: entry.member_action,
    headline: entry.context_summary,
    practicalChoice: entry.why_not_counted,
    sources: entry.sources || [],
    inclusionClass: "context_only",
  };
}

function buildIndicators(counts = {}) {
  return [
    indicator(counts.substantive_rolls, "substantive vote", "substantive votes"),
    indicator(counts.policy_episodes, "policy episode", "policy episodes"),
    indicator(counts.not_voting_records, "Not Voting", "Not Voting"),
    indicator(counts.context_controls, "context-only record", "context-only records"),
  ].filter(Boolean);
}

function indicator(value, singular, plural) {
  return Number.isFinite(value) ? { key: singular, label: `${value} ${value === 1 ? singular : plural}` } : null;
}

function rowKey(row) {
  return `${row?.congress}:${row?.rollcall_number}`;
}
