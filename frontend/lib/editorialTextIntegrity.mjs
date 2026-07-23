const PERIOD_MARKER = "\uE000";
const PROTECTED_ABBREVIATIONS = [
  /\bH\.\s*Con\.\s*Res\.(?=\s*\d)/gi,
  /\bH\.\s*Res\.(?=\s*\d)/gi,
  /\bH\.R\.(?=\s*\d)/gi,
  /\bS\.(?=\s*\d)/gi,
  /\bD\.C\./gi,
  /\bU\.S\./gi,
  /\b(?:Mr|Mrs|Ms|Dr|Rep|Sen|Gov|No)\./gi,
  /\b[A-Z]\.(?=\s*[A-Z][a-z])/g,
];

const DANGLING_ENDINGS = new Set([
  "a", "an", "and", "at", "by", "for", "from", "in", "of", "on", "or", "the", "to", "with",
]);

export function firstCompleteSentence(value = "") {
  const text = String(value || "").trim();
  if (!text) return "";
  const protectedText = protectAbbreviations(text);
  const boundary = protectedText.search(/(?<=[.!?])\s+(?=[A-Z0-9"'(])/);
  return restoreAbbreviations(boundary === -1 ? protectedText : protectedText.slice(0, boundary)).trim();
}

export function publicSentenceDefects(value = "") {
  const text = String(value || "").trim();
  const defects = [];
  if (!text) return ["PUBLIC_SENTENCE_EMPTY"];
  if (/(?:\bH\.R\.|\bS\.|\bD\.C\.|\bU\.S\.|\bH\.\s*(?:Con\.\s*)?Res\.)$/i.test(text)) {
    defects.push("PUBLIC_SENTENCE_ABBREVIATION_FRAGMENT");
  }
  if (count(text, "(") !== count(text, ")")) defects.push("PUBLIC_SENTENCE_UNMATCHED_PARENTHESIS");
  if (/[:;]\s*$/.test(text)) defects.push("PUBLIC_SENTENCE_UNFINISHED_CONSTRUCTION");
  const finalWord = text.replace(/[.!?"')]+$/g, "").trim().split(/\s+/).at(-1)?.toLowerCase();
  if (DANGLING_ENDINGS.has(finalWord)) defects.push("PUBLIC_SENTENCE_DANGLING_WORD");
  return defects;
}

export function formatPublicDateRange(startValue, endValue = startValue, locale = "en-US") {
  const start = parseIsoDate(startValue);
  const end = parseIsoDate(endValue);
  if (!start || !end) return "";
  if (start.getTime() === end.getTime()) return formatFullDate(start, locale);
  if (locale !== "en-US") {
    const formatter = new Intl.DateTimeFormat(locale, { dateStyle: "medium", timeZone: "UTC" });
    return `${formatter.format(start)}–${formatter.format(end)}`;
  }
  const startMonth = monthName(start);
  const endMonth = monthName(end);
  const startDay = start.getUTCDate();
  const endDay = end.getUTCDate();
  const startYear = start.getUTCFullYear();
  const endYear = end.getUTCFullYear();
  if (startYear === endYear && start.getUTCMonth() === end.getUTCMonth()) {
    return `${startMonth} ${startDay}–${endDay}, ${startYear}`;
  }
  if (startYear === endYear) return `${startMonth} ${startDay}–${endMonth} ${endDay}, ${startYear}`;
  return `${startMonth} ${startDay}, ${startYear}–${endMonth} ${endDay}, ${endYear}`;
}

export function hasRawIsoDateRange(value = "") {
  return /\b\d{4}-\d{2}-\d{2}\s*(?:–|-|to)\s*\d{4}-\d{2}-\d{2}\b/.test(String(value || ""));
}

function protectAbbreviations(value) {
  return PROTECTED_ABBREVIATIONS.reduce(
    (text, pattern) => text.replace(pattern, (match) => match.replaceAll(".", PERIOD_MARKER)),
    value,
  );
}

function restoreAbbreviations(value) {
  return value.replaceAll(PERIOD_MARKER, ".");
}

function parseIsoDate(value) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(String(value || ""))) return null;
  const date = new Date(`${value}T00:00:00Z`);
  return Number.isNaN(date.getTime()) ? null : date;
}

function formatFullDate(date, locale) {
  if (locale !== "en-US") {
    return new Intl.DateTimeFormat(locale, { dateStyle: "medium", timeZone: "UTC" }).format(date);
  }
  return `${monthName(date)} ${date.getUTCDate()}, ${date.getUTCFullYear()}`;
}

function monthName(date) {
  return ["Jan.", "Feb.", "March", "April", "May", "June", "July", "Aug.", "Sep.", "Oct.", "Nov.", "Dec."][date.getUTCMonth()];
}

function count(value, token) {
  return String(value).split(token).length - 1;
}
