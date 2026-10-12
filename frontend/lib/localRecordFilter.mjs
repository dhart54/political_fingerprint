import { getActionPresentation } from "./selectedIssueExperience.mjs";

const IDENTIFIERS = [
  ["hconres", /\bh\s*\.?\s*con\s*\.?\s*res\s*\.?\s*(\d+)\b/g],
  ["sconres", /\bs\s*\.?\s*con\s*\.?\s*res\s*\.?\s*(\d+)\b/g],
  ["hjres", /\bh\s*\.?\s*j\s*\.?\s*res\s*\.?\s*(\d+)\b/g],
  ["sjres", /\bs\s*\.?\s*j\s*\.?\s*res\s*\.?\s*(\d+)\b/g],
  ["hres", /\bh\s*\.?\s*res\s*\.?\s*(\d+)\b/g],
  ["sres", /\bs\s*\.?\s*res\s*\.?\s*(\d+)\b/g],
  ["hr", /\bh\s*\.?\s*r\s*\.?\s*(\d+)\b/g],
  ["s", /\bs\s*\.?\s*(\d+)\b/g],
  ["roll", /\broll\s*(?:call\s*)?(?:no\.?\s*|#\s*)?(\d+)\b/g],
];
const IDENTIFIER_QUERY = /\b(?:hconres|sconres|hjres|sjres|hres|sres|hr|s|roll) \d+\b/g;
const PREFIXES = new Set(IDENTIFIERS.map(([prefix]) => prefix));

export function normalizeLocalRecordQuery(value = "") {
  let text = String(value).normalize("NFKC").toLowerCase();
  for (const [prefix, pattern] of IDENTIFIERS) {
    text = text.replace(pattern, (_, number) => `${prefix} ${number.replace(/^0+(?=\d)/, "")}`);
  }
  return text.replace(/[^\p{L}\p{N}]+/gu, " ").trim().replace(/\s+/g, " ");
}

// A view-only subsequence of the caller's already loaded records. No ranking,
// hidden interpretation/provenance fields, network calls or record mutation.
export function filterLoadedReceipts(rows = [], query = "") {
  const normalized = normalizeLocalRecordQuery(query);
  if (!normalized) return rows;
  const identifiers = normalized.match(IDENTIFIER_QUERY) || [];
  const words = normalized.replace(IDENTIFIER_QUERY, " ").split(/\s+/).filter(Boolean);
  return rows.filter((row) => {
    const action = getActionPresentation(row);
    const fields = [action.title, action.parentMeasure, `${row.chamber || "chamber"} Roll ${row.rollcall_number || "not supplied"}`]
      .map(normalizeLocalRecordQuery);
    return identifiers.every((identifier) => fields.some((field) => ` ${field} `.includes(` ${identifier} `)))
      && words.every((word) => fields.some((field) => /^\d+$/.test(word) || PREFIXES.has(word)
        ? field.split(" ").includes(word) : field.includes(word)));
  });
}
