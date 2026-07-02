import { deriveIssueReadiness, sortIssueRowsByReadiness } from "./issueReadiness.mjs";

export const GUIDED_PREFERENCE_OPTIONS = [
  {
    value: "support_more_action",
    label: "I generally favored these measures",
    alignmentPreference: "support_more_action",
  },
  {
    value: "oppose_more_action",
    label: "I generally favored opposing them",
    alignmentPreference: "oppose_more_action",
  },
  {
    value: "views_differ",
    label: "My views differ by measure",
    alignmentPreference: null,
  },
  {
    value: "not_sure",
    label: "I am not sure",
    alignmentPreference: null,
  },
];

const DOMAIN_THEMES = {
  ECONOMY_TAXES: [
    "budget framework and reconciliation",
    "government funding",
    "small-business eligibility",
    "military and veterans appropriations",
  ],
  HEALTH_SOCIAL: [
    "health coverage and premiums",
    "public-health programs",
    "community services",
  ],
  EDUCATION_WORKFORCE: [
    "schools and workforce programs",
    "student and worker supports",
  ],
  ENVIRONMENT_ENERGY: [
    "energy policy",
    "environmental and land-use measures",
  ],
  NATIONAL_SECURITY_FOREIGN: [
    "defense authorization",
    "foreign military sales",
    "national-security amendments",
  ],
  IMMIGRATION_BORDER: [
    "border operations",
    "immigration enforcement",
    "visa and asylum systems",
  ],
  JUSTICE_PUBLIC_SAFETY: [
    "criminal-law and public-safety measures",
    "law-enforcement reporting",
    "court and policing policy",
  ],
  INFRASTRUCTURE_TECH_TRANSPORT: [
    "transportation and infrastructure",
    "technology and broadband",
  ],
};

const DOMAIN_LABELS = {
  ECONOMY_TAXES: "Economy & Taxes",
  HEALTH_SOCIAL: "Health & Social Services",
  EDUCATION_WORKFORCE: "Education & Workforce",
  ENVIRONMENT_ENERGY: "Environment & Energy",
  NATIONAL_SECURITY_FOREIGN: "National Security & Foreign Policy",
  IMMIGRATION_BORDER: "Immigration & Border Policy",
  JUSTICE_PUBLIC_SAFETY: "Justice & Public Safety",
  INFRASTRUCTURE_TECH_TRANSPORT: "Infrastructure, Tech & Transportation",
};
const DIRECTIONAL_DOMINANCE_SHARE = 2 / 3;

export function buildRecordNarrative({ legislator = {}, positions = [], scope = "all" } = {}) {
  const rows = sortIssueRowsByReadiness(positions || []);
  const interpretedRows = rows.filter((row) => getInterpretedYesNoCount(row) > 0);
  const strongRows = rows.filter((row) => row.readiness?.key === "strong_evidence");
  const mixedRows = rows.filter((row) => row.readiness?.key === "mixed_but_interpretable" && !getDominantDirection(row));
  const limitedRows = rows.filter((row) => row.readiness?.key === "limited_evidence");
  const notReadyRows = rows.filter((row) => row.readiness?.key === "not_enough_to_summarize");
  const strongest = strongRows[0] || mixedRows[0] || limitedRows[0] || null;
  const totalRecorded = rows.reduce((sum, row) => sum + Number(row.recorded_votes || 0), 0);
  const totalInterpreted = rows.reduce((sum, row) => sum + getInterpretedYesNoCount(row), 0);

  if (!strongest) {
    return {
      headline: `${legislator.name_display || "This official"} does not have enough reviewed vote meaning for a clear issue read yet.`,
      body: "Recorded votes may still be visible below, but the profile avoids a broad voting-pattern claim until reviewed vote meaning is available.",
      evidenceLine: `${totalRecorded} recorded issue rows; 0 reviewed Yes/No meanings.`,
      strongestDomain: null,
      patternRows: [],
      limitedCount: limitedRows.length + notReadyRows.length,
    };
  }

  const dominantLine = buildDominantIssueLine(interpretedRows);
  const strongestLine = buildStrongestIssueLine(strongest);
  const mixedLine = mixedRows.length
    ? `${formatList(mixedRows.slice(0, 2).map((row) => formatDomainLabel(row.domain)))} ${mixedRows.length === 1 ? "is" : "are"} mixed but interpretable.`
    : "";
  const limitedLine = limitedRows.length || notReadyRows.length
    ? `${limitedRows.length + notReadyRows.length} issue ${limitedRows.length + notReadyRows.length === 1 ? "area remains" : "areas remain"} limited or not ready to summarize.`
    : "";
  const comparisonLine = scope === "all" ? buildComparisonLine(rows) : "";
  const receiptLine = "Start with the issue cards below, then open representative votes to inspect the record behind each read.";

  return {
    headline: `${legislator.name_display || "This official"}'s clearest reviewed issue read is ${formatDomainLabel(strongest.domain)}.`,
    body: [dominantLine || strongestLine, mixedLine, limitedLine, receiptLine, comparisonLine].filter(Boolean).join(" "),
    evidenceLine: `${totalInterpreted} reviewed Yes/No meanings across ${totalRecorded} recorded issue rows.`,
    strongestDomain: strongest.domain,
    patternRows: buildIssuePatternRows(rows).slice(0, 4),
    limitedCount: limitedRows.length + notReadyRows.length,
  };
}

export function buildComparisonLine(rows = []) {
  const comparisons = (rows || [])
    .map((row) => row.comparison)
    .filter(Boolean);
  const hasBothCongresses = comparisons.some((comparison) =>
    ["consistent", "stronger", "weaker", "different", "not_comparable"].includes(comparison.status),
  );
  if (hasBothCongresses) {
    return "Reviewed votes are available in both Congresses, with Congress-specific counts shown separately below.";
  }
  const singleCongress = comparisons.find((comparison) => comparison.status === "single_congress_only");
  if (singleCongress) {
    return "Some issues have reviewed evidence in only one Congress, so Congress-specific counts are shown separately below.";
  }
  return "Congress-specific counts are shown separately below when reviewed votes are available.";
}

export function buildIssuePatternRows(positions = []) {
  return sortIssueRowsByReadiness(positions || [])
    .filter((row) => getInterpretedTotal(row) > 0)
    .map((row) => {
      const readiness = row.readiness || deriveIssueReadiness(row);
      const supportCount = Number(row.interpreted_support_count || 0);
      const opposeCount = Number(row.interpreted_oppose_count || 0);
      const interpretedYesNo = supportCount + opposeCount;
      return {
        domain: row.domain,
        readiness,
        supportCount,
        opposeCount,
        interpretedYesNo,
        interpretedTotal: getInterpretedTotal(row),
        recordedVotes: Number(row.recorded_votes || 0),
        label: buildPatternLabel({ supportCount, opposeCount, readiness }),
        theme: buildThemeLine(row.domain),
        preview: buildIssueCardPreview({ ...row, readiness }),
      };
    });
}

export function buildIssueCardPreview(row = {}) {
  const readiness = row.readiness || deriveIssueReadiness(row);
  const supportCount = Number(row.interpreted_support_count || 0);
  const opposeCount = Number(row.interpreted_oppose_count || 0);
  const interpretedYesNo = supportCount + opposeCount;
  const recordedVotes = Number(row.recorded_votes || 0);
  const direction = getDominantDirection(row);
  const themeText = buildThemeLine(row.domain);

  if (!interpretedYesNo) {
    return {
      status: readiness.label || "Not enough to summarize",
      countLine: recordedVotes
        ? `No reviewed Yes/No vote meaning is available yet out of ${recordedVotes} recorded ${recordedVotes === 1 ? "vote" : "votes"}.`
        : "No recorded Yes/No votes are available in this issue yet.",
      themeLine: "Evidence may still be visible, but this issue is not ready for a confident summary.",
      receiptLine: "Open available rows and source details before drawing a broader issue-area conclusion.",
    };
  }

  if (direction === "opposed") {
    return {
      status: "Mostly opposed in reviewed sample",
      countLine: `${opposeCount} opposed / ${supportCount} supported across ${interpretedYesNo} reviewed Yes/No ${interpretedYesNo === 1 ? "vote" : "votes"}.`,
      themeLine: `Opposition concentrated in ${themeText}.`,
      receiptLine: "Open for representative votes and the full reviewed list.",
    };
  }

  if (direction === "supported") {
    return {
      status: "Mostly supported in reviewed sample",
      countLine: `${supportCount} supported / ${opposeCount} opposed across ${interpretedYesNo} reviewed Yes/No ${interpretedYesNo === 1 ? "vote" : "votes"}.`,
      themeLine: `Support concentrated in ${themeText}.`,
      receiptLine: "Open for representative votes and the full reviewed list.",
    };
  }

  if (readiness.key === "mixed_but_interpretable") {
    return {
      status: "Mixed but interpretable",
      countLine: `${opposeCount} opposed / ${supportCount} supported across ${interpretedYesNo} reviewed Yes/No ${interpretedYesNo === 1 ? "vote" : "votes"}.`,
      themeLine: `Votes point in more than one direction across ${themeText}.`,
      receiptLine: "Open representative votes before reading this as mostly support or mostly opposition.",
    };
  }

  if (readiness.key === "limited_evidence") {
    return {
      status: "Limited reviewed evidence",
      countLine: `${interpretedYesNo} reviewed Yes/No ${interpretedYesNo === 1 ? "vote is" : "votes are"} available out of ${recordedVotes} recorded ${recordedVotes === 1 ? "vote" : "votes"}.`,
      themeLine: `The available rows concern ${themeText}.`,
      receiptLine: "Open the receipts before treating this as a stable issue pattern.",
    };
  }

  return {
    status: readiness.label || "Reviewed evidence",
    countLine: `${interpretedYesNo} reviewed Yes/No ${interpretedYesNo === 1 ? "vote" : "votes"} out of ${recordedVotes} recorded ${recordedVotes === 1 ? "vote" : "votes"}.`,
    themeLine: `The reviewed rows concern ${themeText}.`,
    receiptLine: "Open for representative votes and the full reviewed list.",
  };
}

export function buildConcretePreferencePrompt(row) {
  if (!row || getInterpretedYesNoCount(row) < 3) {
    return {
      canAsk: false,
      prompt: "This issue does not yet have enough reviewed Yes/No vote meaning for a single preference prompt.",
      themes: [],
    };
  }

  const themes = DOMAIN_THEMES[row.domain] || ["the reviewed measures in this issue"];
  return {
    canAsk: true,
    prompt: `The reviewed ${formatDomainLabel(row.domain)} votes included ${formatList(themes.slice(0, 4))}.`,
    themes,
  };
}

export function getDirectionalAlignmentPreferences(preferences = {}) {
  return Object.fromEntries(
    Object.entries(preferences).filter(([, value]) =>
      GUIDED_PREFERENCE_OPTIONS.some((option) => option.value === value && option.alignmentPreference),
    ),
  );
}

export function isDirectionalPreference(value) {
  return Boolean(GUIDED_PREFERENCE_OPTIONS.find((option) => option.value === value)?.alignmentPreference);
}

function getInterpretedYesNoCount(row) {
  return Number(row?.interpreted_support_count || 0) + Number(row?.interpreted_oppose_count || 0);
}

function getInterpretedTotal(row) {
  return getInterpretedYesNoCount(row) + Number(row?.interpreted_other_count || 0);
}

function buildStrongestIssueLine(row) {
  const supportCount = Number(row.interpreted_support_count || 0);
  const opposeCount = Number(row.interpreted_oppose_count || 0);
  const countLine = `${supportCount} for / ${opposeCount} against interpreted measures`;
  const dominantDirection = getDominantDirection(row);
  if (dominantDirection) {
    return `${formatDomainLabel(row.domain)} has the clearest pattern: mostly ${dominantDirection} in the reviewed sample (${countLine}).`;
  }
  if (row.readiness?.key === "strong_evidence") {
    return `${formatDomainLabel(row.domain)} has the clearest pattern: ${countLine}.`;
  }
  return `${formatDomainLabel(row.domain)} is the best available read, but it should stay cautious: ${countLine}.`;
}

function buildDominantIssueLine(rows) {
  const dominantRows = (rows || []).filter((row) => getDominantDirection(row));
  if (!dominantRows.length) {
    return "";
  }

  const opposedRows = dominantRows.filter((row) => getDominantDirection(row) === "opposed");
  const supportedRows = dominantRows.filter((row) => getDominantDirection(row) === "supported");
  const parts = [];

  if (opposedRows.length) {
    parts.push(`mostly opposed reads in ${formatList(opposedRows.slice(0, 3).map((row) => formatDomainLabel(row.domain)))}`);
  }
  if (supportedRows.length) {
    parts.push(`mostly supported reads in ${formatList(supportedRows.slice(0, 3).map((row) => formatDomainLabel(row.domain)))}`);
  }

  const shownCount = Math.min(opposedRows.length, 3) + Math.min(supportedRows.length, 3);
  const additionalCount = dominantRows.length - shownCount;
  const additionalText = additionalCount > 0 ? `, plus ${additionalCount} additional dominant ${additionalCount === 1 ? "issue read" : "issue reads"}` : "";
  return `This reviewed sample shows ${formatList(parts)}${additionalText}.`;
}

function buildPatternLabel({ supportCount, opposeCount, readiness }) {
  const dominantDirection = getDominantDirection({ interpreted_support_count: supportCount, interpreted_oppose_count: opposeCount });
  if (dominantDirection === "supported") {
    return "Mostly supported";
  }
  if (dominantDirection === "opposed") {
    return "Mostly opposed";
  }
  if (readiness?.key === "mixed_but_interpretable") {
    return "Mixed";
  }
  return "Reviewed evidence";
}

function getDominantDirection(row) {
  const supportCount = Number(row?.interpreted_support_count || 0);
  const opposeCount = Number(row?.interpreted_oppose_count || 0);
  const total = supportCount + opposeCount;
  if (!total) {
    return "";
  }
  if (supportCount / total >= DIRECTIONAL_DOMINANCE_SHARE) {
    return "supported";
  }
  if (opposeCount / total >= DIRECTIONAL_DOMINANCE_SHARE) {
    return "opposed";
  }
  return "";
}

function buildThemeLine(domain) {
  const themes = DOMAIN_THEMES[domain] || [];
  if (!themes.length) {
    return "Reviewed measures in this issue.";
  }
  return formatList(themes.slice(0, 3));
}

function formatDomainLabel(domain) {
  if (DOMAIN_LABELS[domain]) {
    return DOMAIN_LABELS[domain];
  }
  return String(domain || "issue")
    .split("_")
    .filter(Boolean)
    .map((segment) => segment[0] + segment.slice(1).toLowerCase())
    .join(" ")
    .replace("And", "&");
}

function formatList(items) {
  const values = (items || []).filter(Boolean);
  if (values.length <= 1) {
    return values[0] || "";
  }
  if (values.length === 2) {
    return `${values[0]} and ${values[1]}`;
  }
  return `${values.slice(0, -1).join(", ")}, and ${values[values.length - 1]}`;
}
