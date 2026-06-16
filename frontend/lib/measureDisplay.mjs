const DISPLAY_LABEL_RULES = [
  {
    pattern: /concurrent resolution on the budget for fiscal year 2025|congressional budget for fiscal year 2025|fy2025 congressional budget/i,
    label: "FY2025 Congressional Budget Resolution",
  },
  {
    pattern: /military construction.*veterans affairs.*appropriations.*2026|military construction and veterans affairs appropriations act,? 2026/i,
    label: "Military Construction and VA Appropriations Act, 2026",
  },
  {
    pattern: /continuing appropriations|temporary government funding|further continuing appropriations|government funding/i,
    label: "Temporary Government Funding Package",
  },
  {
    pattern: /small business.*regulatory|small business regulatory reduction/i,
    label: "Small Business Regulatory Reduction Act",
  },
  {
    pattern: /national defense authorization act.*2026|defense authorization.*2026/i,
    label: "National Defense Authorization Act, 2026",
  },
  {
    pattern: /halt.*fentanyl/i,
    label: "HALT Fentanyl Act",
  },
  {
    pattern: /lower health care premiums/i,
    label: "Lower Health Care Premiums Act",
  },
];

export function formatDisplayMeasureTitle(value, { maxLength = 82 } = {}) {
  const title = String(value || "").replace(/\s+/g, " ").trim();

  if (!title) {
    return "Recorded vote";
  }

  const amendmentLabel = extractAmendmentLabel(title);
  const baseTitle = title.replace(/^on (agreeing to|the) amendment[:\s-]*/i, "").trim();
  const rule = DISPLAY_LABEL_RULES.find((candidate) => candidate.pattern.test(baseTitle));
  const label = rule?.label || shortenOfficialTitle(baseTitle, maxLength);

  return amendmentLabel ? `${amendmentLabel}: ${label}` : label;
}

function extractAmendmentLabel(title) {
  const match = title.match(/\b(?:S\.?\s*Amdt\.?|Amendment)\s*No\.?\s*([0-9]+)/i);
  if (match?.[1]) {
    return `Amendment ${match[1]}`;
  }
  return /\bamendment\b/i.test(title) ? "Amendment" : "";
}

function shortenOfficialTitle(title, maxLength) {
  if (title.length <= maxLength) {
    return title;
  }

  const cleaned = title
    .replace(/^Providing for consideration of the bill\s*/i, "Rule for ")
    .replace(/^A bill to\s+/i, "")
    .replace(/^To\s+/i, "")
    .replace(/\s*,\s*and for other purposes\.?$/i, "")
    .trim();

  if (cleaned.length <= maxLength) {
    return cleaned;
  }

  return `${cleaned.slice(0, Math.max(24, maxLength - 3)).trim()}...`;
}
