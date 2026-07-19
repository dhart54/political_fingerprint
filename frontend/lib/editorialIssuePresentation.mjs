const SOURCE_GROUP_ORDER = [
  "Vote and legislative status",
  "Bill or resolution text",
  "Nonpartisan analysis",
  "Competing arguments",
  "Additional official evidence",
];

export function buildImportantContext(record) {
  const context = [];
  const seen = new Set();

  appendUnique(context, seen, record.additionalDetail?.laterHistory);
  for (const caveat of record.importantContext || []) {
    if (isMotiveBoundary(caveat) || isArgumentBoundary(caveat)) continue;
    appendUnique(context, seen, caveat);
  }

  appendUnique(
    context,
    seen,
    record.inclusionClass === "not_voting"
      ? "The record does not reveal why the member did not vote."
      : "The vote record does not reveal why the member voted this way.",
  );
  appendUnique(
    context,
    seen,
    "Supporter and opponent arguments are attributed advocacy, not evidence of the member's motive.",
  );
  return context;
}

export function groupOfficialSources(sources = []) {
  const groups = new Map();
  const seen = new Set();

  for (const source of sources) {
    const stableKey = source.stableId || canonicalizeUrl(source.url);
    if (!stableKey || seen.has(stableKey)) continue;
    seen.add(stableKey);
    const groupName = source.group || "Additional official evidence";
    if (!groups.has(groupName)) groups.set(groupName, []);
    groups.get(groupName).push({
      name: source.name,
      locator: source.locator,
      url: source.url,
    });
  }

  return [...groups.entries()]
    .map(([name, items]) => ({ name, items }))
    .sort((left, right) => sourceGroupRank(left.name) - sourceGroupRank(right.name));
}

function sourceGroupRank(name) {
  const index = SOURCE_GROUP_ORDER.indexOf(name);
  return index === -1 ? SOURCE_GROUP_ORDER.length : index;
}

function appendUnique(result, seen, value) {
  const key = normalizeContext(value);
  if (!value || seen.has(key)) return;
  seen.add(key);
  result.push(value);
}

function normalizeContext(value) {
  return String(value || "").toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
}

function isMotiveBoundary(value) {
  return /does not (reveal|explain)|why .+ voted|member's rationale/i.test(value);
}

function isArgumentBoundary(value) {
  return /attributed|argument|advocacy|debate documents competing/i.test(value);
}

function canonicalizeUrl(value) {
  try {
    const url = new URL(value);
    url.hash = "";
    url.pathname = url.pathname.replace(/\/$/, "") || "/";
    return url.toString();
  } catch {
    return String(value || "").trim().replace(/\/$/, "");
  }
}
