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

export function buildRecordNarrative({ legislator = {}, positions = [] } = {}) {
  const rows = sortIssueRowsByReadiness(positions || []);
  const interpretedRows = rows.filter((row) => getInterpretedYesNoCount(row) > 0);
  const strongRows = rows.filter((row) => row.readiness?.key === "strong_evidence");
  const mixedRows = rows.filter((row) => row.readiness?.key === "mixed_but_interpretable");
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

  const partyLine = buildPartyContextLine(legislator);
  const strongestLine = buildStrongestIssueLine(strongest);
  const mixedLine = mixedRows.length
    ? `${formatList(mixedRows.slice(0, 2).map((row) => formatDomainLabel(row.domain)))} ${mixedRows.length === 1 ? "is" : "are"} mixed but interpretable.`
    : "";
  const limitedLine = limitedRows.length || notReadyRows.length
    ? `${limitedRows.length + notReadyRows.length} issue ${limitedRows.length + notReadyRows.length === 1 ? "area remains" : "areas remain"} limited or not ready to summarize.`
    : "";

  return {
    headline: `${legislator.name_display || "This official"}'s clearest reviewed pattern is ${formatDomainLabel(strongest.domain)}.`,
    body: [partyLine, strongestLine, mixedLine, limitedLine].filter(Boolean).join(" "),
    evidenceLine: `${totalInterpreted} reviewed Yes/No meanings across ${totalRecorded} recorded issue rows.`,
    strongestDomain: strongest.domain,
    patternRows: buildIssuePatternRows(rows).slice(0, 4),
    limitedCount: limitedRows.length + notReadyRows.length,
  };
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
      };
    });
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

function buildPartyContextLine(legislator) {
  const chamber = String(legislator?.chamber || "").toLowerCase();
  const party = String(legislator?.party || "").toUpperCase();
  const partyName = party === "D" ? "Democrats" : party === "R" ? "Republicans" : "";
  const chamberName = chamber === "senate" ? "Senate" : chamber === "house" ? "House" : "";

  if (!partyName || !chamberName) {
    return "";
  }

  return `In this reviewed sample, the record is shown against ${chamberName} votes and party context where the source data supports it.`;
}

function buildStrongestIssueLine(row) {
  const supportCount = Number(row.interpreted_support_count || 0);
  const opposeCount = Number(row.interpreted_oppose_count || 0);
  const countLine = `${supportCount} for / ${opposeCount} against interpreted measures`;
  if (row.readiness?.key === "strong_evidence") {
    return `${formatDomainLabel(row.domain)} has the clearest pattern: ${countLine}.`;
  }
  return `${formatDomainLabel(row.domain)} is the best available read, but it should stay cautious: ${countLine}.`;
}

function buildPatternLabel({ supportCount, opposeCount, readiness }) {
  if (readiness?.key === "mixed_but_interpretable") {
    return "Mixed";
  }
  if (supportCount > opposeCount) {
    return "Mostly supported";
  }
  if (opposeCount > supportCount) {
    return "Mostly opposed";
  }
  return "Reviewed evidence";
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
