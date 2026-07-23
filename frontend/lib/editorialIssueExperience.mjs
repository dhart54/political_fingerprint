import { productionEditorialIssueSlices } from "./editorialIssueProductionSlices.mjs";
import { buildPublicEditorialPresentation } from "./editorialIssuePublicPresentation.mjs";
import {
  buildMemberActionOverlay,
  buildSharedLegislativeAction,
  inclusionClassForStatus,
  MEMBER_ACTION_STATUS,
} from "./editorialSharedEvidence.mjs";

export const EDITORIAL_EXPERIENCE_MODE = Object.freeze({
  production: "production",
  review: "review",
});

export function isEditorialSliceEligible({ candidate, mode = EDITORIAL_EXPERIENCE_MODE.production }) {
  if (!candidate?.publication) return false;
  if (mode === EDITORIAL_EXPERIENCE_MODE.review) return true;
  return candidate.publication.editorialStatus === "human_approved"
    && candidate.publication.benchmarkStatus === "gold_benchmark"
    && candidate.publication.productionEligible === true
    && sourceContentIsApproved(candidate.source);
}

export function selectEditorialIssueExperience({
  candidates = productionEditorialIssueSlices,
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
  const records = interpretations.map((entry) => adaptInterpretation(candidate, entry, rowsByRoll.get(Number(entry.roll))));
  const episodeContract = candidate.episodePresentation || { episodes: [], featuredEpisodeIds: [] };
  const episodes = buildEpisodes(candidate, episodeContract, records);
  const episodeIds = new Set(episodes.map((episode) => episode.id));
  const ungroupedRecords = records.filter((record) => !record.episodeId || !episodeIds.has(record.episodeId));
  const proceduralRecords = controls.map((entry) => adaptControl(candidate, entry, rowsByRoll.get(Number(entry.roll))));

  return {
    identity: { ...candidate.identity },
    publicPresentation: buildPublicEditorialPresentation(candidate, evidenceRows),
    reviewContext: mode === EDITORIAL_EXPERIENCE_MODE.review
      ? { isReview: true, label: candidate.publication.reviewLabel }
      : null,
    indicators: buildIndicators(candidate.source.slice_counts),
    episodes,
    featuredEpisodes: episodeContract.featuredEpisodeIds
      .map((episodeId) => episodes.find((episode) => episode.id === episodeId))
      .filter(Boolean)
      .slice(0, 5),
    completeRecord: buildCompleteRecord(episodes),
    ungroupedRecords,
    proceduralRecords,
    records: [...records, ...proceduralRecords],
    sourceRowKeys: [...interpretations, ...controls].map((entry) => `${candidate.identity.congress}:${entry.roll}`),
  };
}

export function hasEligibleEditorialSlice({ candidates = productionEditorialIssueSlices, domain, legislator, mode = EDITORIAL_EXPERIENCE_MODE.production }) {
  return candidates.some((candidate) => (
    candidate?.identity?.memberId === legislator?.bioguide_id
    && candidate?.identity?.issueId === domain
    && isEditorialSliceEligible({ candidate, mode })
  ));
}

function candidateMatches({ candidate, domain, evidenceRows, legislator }) {
  if (candidate.identity.memberId !== legislator?.bioguide_id || candidate.identity.issueId !== domain) return false;
  const expected = [...(candidate.source.interpretations || []), ...(candidate.source.controls || [])];
  return expected.every((entry) => (
    ["not yet serving", "not_yet_serving", "no longer serving", "no_longer_serving", "missing evidence", "missing_evidence"]
      .includes(String(entry.action_status || "").toLowerCase())
    || evidenceRows.some((row) => rowKey(row) === `${candidate.identity.congress}:${entry.roll}`)
  ));
}

function adaptInterpretation(candidate, entry, row = {}) {
  const episodeId = explicitEpisodeId(candidate, entry);
  const episodeMeta = candidate.episodePresentation?.episodes?.find((episode) => episode.id === episodeId);
  const shared = buildSharedLegislativeAction(entry, row, { episodeId, policyFamilyId: episodeMeta?.policyFamilyId });
  const overlay = buildMemberActionOverlay(entry, candidate.identity.memberDisplayName);
  return {
    ...shared,
    memberAction: overlay.label,
    actionStatus: overlay.status,
    result: row.vote_context?.final_result,
    lifecycleStatus: entry.ten_second?.member_action_and_result,
    headline: overlay.headline,
    actionAndResult: overlay.actionAndResult,
    inclusionClass: inclusionClassForStatus(overlay.status),
  };
}

function adaptControl(candidate, entry, row = {}) {
  return {
    id: `context-${entry.roll}`,
    roll: Number(entry.roll),
    actionIdentity: `House roll call ${entry.roll}`,
    episodeId: explicitEpisodeId(candidate, entry),
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
  ].filter((item) => item && !item.label.startsWith("0 "));
}

function indicator(value, singular, plural) {
  return Number.isFinite(value) ? { key: singular, label: `${value} ${value === 1 ? singular : plural}` } : null;
}

function sourceContentIsApproved(source) {
  if (source?.human_approval_status !== "human_approved") return false;
  const records = [...(source.interpretations || []), ...(source.controls || [])];
  return records.every((record) => record.human_approval_status === undefined || record.human_approval_status === "human_approved");
}

function explicitEpisodeId(candidate, entry) {
  return entry.episode_id ?? candidate.episodeByRoll?.[entry.roll] ?? null;
}

function buildEpisodes(candidate, contract, records) {
  return (contract.episodes || []).map((metadata) => {
    const recordsByRoll = new Map(records.filter((record) => record.episodeId === metadata.id).map((record) => [record.roll, record]));
    const actions = (metadata.rolls || []).map((roll) => recordsByRoll.get(roll)).filter(Boolean);
    const trajectory = candidate.memberEpisodeTrajectories?.find((item) => item.episode_id === metadata.id);
    return Object.freeze({
      ...metadata,
      periodLabel: metadata.periodLabel || `${ordinal(candidate.identity.congress)} Congress`,
      dateSpan: dateSpan(actions),
      memberTrajectory: trajectory?.member_trajectory || defaultTrajectory(actions),
      actions,
      actionCount: actions.length,
      coverageStatus: trajectory?.coverage_status || episodeCoverage(actions),
    });
  });
}

export function buildCompleteRecord(episodes = []) {
  const families = new Map();
  for (const episode of episodes) {
    const familyId = episode.policyFamilyId || episode.id;
    if (!families.has(familyId)) families.set(familyId, { id: familyId, congresses: new Map() });
    const family = families.get(familyId);
    if (!family.congresses.has(episode.congress)) family.congresses.set(episode.congress, []);
    family.congresses.get(episode.congress).push(episode);
  }
  return [...families.values()].map((family) => ({
    id: family.id,
    congresses: [...family.congresses.entries()].map(([congress, familyEpisodes]) => ({ congress, episodes: familyEpisodes })),
  }));
}

function episodeCoverage(actions) {
  if (!actions.length || actions.every((item) => item.actionStatus === MEMBER_ACTION_STATUS.missingEvidence)) return "missing";
  if (actions.some((item) => [MEMBER_ACTION_STATUS.missingEvidence, MEMBER_ACTION_STATUS.notVoting, MEMBER_ACTION_STATUS.present].includes(item.actionStatus))) return "partial";
  return "complete";
}

function defaultTrajectory(actions) {
  return actions.map((record) => record.memberAction).join(" → ");
}

function dateSpan(actions) {
  const dates = actions.map((item) => item.date).filter(Boolean).sort();
  if (!dates.length) return "";
  return dates.length === 1 ? dates[0] : `${dates[0]} – ${dates.at(-1)}`;
}

function ordinal(value) {
  const mod100 = value % 100;
  const suffix = mod100 >= 11 && mod100 <= 13 ? "th" : ({ 1: "st", 2: "nd", 3: "rd" }[value % 10] || "th");
  return `${value}${suffix}`;
}

function rowKey(row) {
  return `${row?.congress}:${row?.rollcall_number}`;
}
