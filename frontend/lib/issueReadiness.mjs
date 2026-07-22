export const ISSUE_READINESS_ORDER = [
  "strong_evidence",
  "mixed_but_interpretable",
  "limited_evidence",
  "not_enough_to_summarize",
];

export const ISSUE_READINESS_LABELS = {
  strong_evidence: "Clear vote pattern",
  mixed_but_interpretable: "Evidence in more than one direction",
  limited_evidence: "Limited vote evidence",
  not_enough_to_summarize: "Receipts only",
};

export const ISSUE_READINESS_GROUP_LABELS = {
  strong_evidence: "Clearest vote evidence",
  mixed_but_interpretable: "Evidence in more than one direction",
  limited_evidence: "Limited vote evidence",
  not_enough_to_summarize: "Receipts only",
};

const MIN_INTERPRETED_YES_NO_FOR_READ = 3;
const DIRECTIONAL_DOMINANCE_SHARE = 2 / 3;

export function deriveIssueReadiness(row) {
  const recordedVotes = Number(row?.recorded_votes || 0);
  const supportCount = Number(row?.interpreted_support_count || 0);
  const opposeCount = Number(row?.interpreted_oppose_count || 0);
  const interpretedOtherCount = Number(row?.interpreted_other_count || 0);
  const interpretedYesNoCount = supportCount + opposeCount;
  const interpretedTotal = interpretedYesNoCount + interpretedOtherCount;
  const coverageShare = recordedVotes ? interpretedYesNoCount / recordedVotes : 0;
  const mixed = supportCount > 0 && opposeCount > 0;
  const dominant =
    interpretedYesNoCount > 0 &&
    Math.max(supportCount, opposeCount) / interpretedYesNoCount >= DIRECTIONAL_DOMINANCE_SHARE;

  if (!recordedVotes || !interpretedYesNoCount) {
    return {
      key: "not_enough_to_summarize",
      label: ISSUE_READINESS_LABELS.not_enough_to_summarize,
      interpretedYesNoCount,
      interpretedTotal,
      coverageShare,
      reason: recordedVotes
        ? "Recorded votes are visible, but reviewed Yes/No vote meaning is not loaded yet."
        : "No recorded Yes/No votes are loaded for this issue in the current window.",
    };
  }

  if (interpretedYesNoCount < MIN_INTERPRETED_YES_NO_FOR_READ) {
    return {
      key: "limited_evidence",
      label: ISSUE_READINESS_LABELS.limited_evidence,
      interpretedYesNoCount,
      interpretedTotal,
      coverageShare,
      reason: `${interpretedYesNoCount} reviewed Yes/No ${interpretedYesNoCount === 1 ? "vote is" : "votes are"} available, so this issue should stay cautious.`,
    };
  }

  if (mixed && !dominant) {
    return {
      key: "mixed_but_interpretable",
      label: ISSUE_READINESS_LABELS.mixed_but_interpretable,
      interpretedYesNoCount,
      interpretedTotal,
      coverageShare,
      reason: "Reviewed votes point in more than one direction, so this issue is useful but not a single-direction read.",
    };
  }

  return {
    key: "strong_evidence",
    label: ISSUE_READINESS_LABELS.strong_evidence,
    interpretedYesNoCount,
    interpretedTotal,
    coverageShare,
    reason: dominant
      ? "Enough reviewed Yes/No vote meaning is available and one side predominates in this reviewed sample."
      : "Enough reviewed Yes/No vote meaning is available for a clear issue read.",
  };
}

export function groupIssueRowsByReadiness(rows) {
  const groups = ISSUE_READINESS_ORDER.map((key) => ({
    key,
    label: ISSUE_READINESS_GROUP_LABELS[key],
    readinessLabel: ISSUE_READINESS_LABELS[key],
    rows: [],
  }));
  const groupByKey = new Map(groups.map((group) => [group.key, group]));

  for (const row of rows || []) {
    const readiness = deriveIssueReadiness(row);
    groupByKey.get(readiness.key)?.rows.push({
      ...row,
      readiness,
    });
  }

  for (const group of groups) {
    group.rows.sort(compareIssueRowsWithinReadiness);
  }

  return groups;
}

export function sortIssueRowsByReadiness(rows) {
  const groups = groupIssueRowsByReadiness(rows);
  return groups.flatMap((group) => group.rows);
}

export function getBestIssueRead(rows) {
  return sortIssueRowsByReadiness(rows).find((row) => row.readiness.key !== "not_enough_to_summarize") || null;
}

export function summarizeReadinessGroups(groups) {
  return groups.map((group) => ({
    key: group.key,
    label: group.label,
    readinessLabel: group.readinessLabel,
    count: group.rows.length,
    domains: group.rows.map((row) => row.domain),
  }));
}

function compareIssueRowsWithinReadiness(left, right) {
  return (
    Number(right.readiness?.interpretedYesNoCount || 0) - Number(left.readiness?.interpretedYesNoCount || 0) ||
    Number(right.recorded_votes || 0) - Number(left.recorded_votes || 0) ||
    String(left.domain || "").localeCompare(String(right.domain || ""))
  );
}
