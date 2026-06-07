import { isProceduralContextRow } from "./proceduralContext.mjs";

export function deriveEvidenceGroups(rows = []) {
  if (!Array.isArray(rows) || rows.length === 0) {
    return {
      groups: [],
      summary: emptySummary(),
    };
  }

  const groupsByKey = new Map();

  rows.forEach((row, index) => {
    const key = buildStableGroupKey(row, index);
    const current = groupsByKey.get(key.id) || {
      id: key.id,
      keySource: key.source,
      confidence: key.confidence,
      label: buildGroupLabel(row),
      rows: [],
    };
    current.rows.push(row);
    if (!current.label) {
      current.label = buildGroupLabel(row);
    }
    groupsByKey.set(key.id, current);
  });

  const groups = Array.from(groupsByKey.values()).map(formatGroup);
  const repeatedGroups = groups.filter((group) => group.rowCount > 1);
  const summary = {
    totalRows: rows.length,
    totalGroups: groups.length,
    repeatedGroupCount: repeatedGroups.length,
    countedYesNoRows: groups.reduce((total, group) => total + group.countedYesNoCount, 0),
    ambiguousOrInsufficientRows: groups.reduce((total, group) => total + group.ambiguousOrInsufficientCount, 0),
    notVotingRows: groups.reduce((total, group) => total + group.notVotingCount, 0),
    proceduralRows: groups.reduce((total, group) => total + group.proceduralCount, 0),
    proceduralContextRows: groups.reduce((total, group) => total + group.proceduralContextCount, 0),
    amendmentRows: groups.reduce((total, group) => total + group.amendmentCount, 0),
    repeatedGroups: repeatedGroups.map((group) => ({
      id: group.id,
      label: group.label,
      rowCount: group.rowCount,
      category: group.category,
      rollCalls: group.rollCalls,
    })),
  };

  return {
    groups,
    summary,
  };
}

function formatGroup(group) {
  const rows = group.rows;
  const countedRows = rows.filter(isCountedDirectionalRow);
  const ambiguousRows = rows.filter(isAmbiguousOrInsufficientRow);
  const notVotingRows = rows.filter((row) => row.interpretation_status === "interpreted" && row.position === "not_voting");
  const proceduralRows = rows.filter(isProceduralRow);
  const proceduralContextRows = rows.filter(isProceduralContextRow);
  const amendmentRows = rows.filter(isAmendmentRow);
  const category = categorizeGroup({
    rows,
    countedRows,
    ambiguousRows,
    notVotingRows,
    proceduralRows,
    proceduralContextRows,
    amendmentRows,
  });

  return {
    id: group.id,
    label: group.label || "Reviewed measure",
    keySource: group.keySource,
    confidence: group.confidence,
    category,
    rowCount: rows.length,
    countedYesNoCount: countedRows.length,
    ambiguousOrInsufficientCount: ambiguousRows.length,
    notVotingCount: notVotingRows.length,
    proceduralCount: proceduralRows.length,
    proceduralContextCount: proceduralContextRows.length,
    amendmentCount: amendmentRows.length,
    rollCalls: rows.map((row) => ({
      roll_call_id: row.roll_call_id,
      rollcall_number: row.rollcall_number,
      position: row.position,
      interpretation_status: row.interpretation_status,
      issue_facet: row.issue_facet,
      vote_type: row.vote_context?.vote_type || row.vote_type || "",
      description: row.description || row.question || row.bill_title || row.measure_title || "",
    })),
    scanSummary: buildScanSummary({
      rowCount: rows.length,
      category,
      label: group.label || "reviewed measure",
      countedCount: countedRows.length,
      ambiguousCount: ambiguousRows.length,
      notVotingCount: notVotingRows.length,
      proceduralCount: proceduralRows.length,
      proceduralContextCount: proceduralContextRows.length,
      amendmentCount: amendmentRows.length,
    }),
  };
}

function buildStableGroupKey(row, index) {
  const billKey = buildBillIdentifier(row);
  if (billKey) {
    return {
      id: `bill:${billKey}`,
      source: "bill_identifier",
      confidence: "stable",
    };
  }

  const titleKey = normalizeTitle(getFirstString(row.bill_title, row.measure_title, row.source_bill_title, row.title, row.description));
  if (titleKey) {
    return {
      id: `title:${titleKey}`,
      source: "measure_title",
      confidence: "stable",
    };
  }

  return {
    id: `row:${row.roll_call_id || row.rollcall_number || index}`,
    source: "single_row",
    confidence: "singleton",
  };
}

function buildBillIdentifier(row) {
  const explicit = getFirstString(
    row.source_bill_id,
    row.bill_id,
    row.bill_ref,
    row.bill_identifier,
    row.roll_call_bill_id,
    row.roll_call_bill_ref,
    row.vote_context?.source_bill_id,
    row.vote_context?.bill_id,
    row.vote_context?.bill_ref,
  );
  if (explicit) {
    return normalizeIdentifier(explicit);
  }

  const congress = getFirstString(row.bill_congress, row.vote_context?.bill_congress);
  const billType = getFirstString(row.bill_type, row.vote_context?.bill_type);
  const billNumber = getFirstString(row.bill_number, row.vote_context?.bill_number);
  if (congress && billType && billNumber) {
    return normalizeIdentifier(`${congress}:${billType}:${billNumber}`);
  }

  return "";
}

function categorizeGroup({ countedRows, ambiguousRows, notVotingRows, proceduralRows, proceduralContextRows, amendmentRows }) {
  if (proceduralContextRows.length && proceduralContextRows.length === countedRows.length + ambiguousRows.length + notVotingRows.length) {
    return "procedural_context_rows";
  }
  if (ambiguousRows.length && ambiguousRows.length === countedRows.length + ambiguousRows.length + notVotingRows.length) {
    return "limited_context_rows";
  }
  if (notVotingRows.length && notVotingRows.length === countedRows.length + ambiguousRows.length + notVotingRows.length) {
    return "not_voting_rows";
  }
  if (proceduralRows.length) {
    return "related_floor_or_procedural_votes";
  }
  if (amendmentRows.length) {
    return "related_amendments";
  }
  return "primary_bill_or_measure";
}

function buildScanSummary({
  rowCount,
  category,
  label,
  countedCount,
  ambiguousCount,
  notVotingCount,
  proceduralCount,
  amendmentCount,
}) {
  const countPhrase = `${rowCount} ${rowCount === 1 ? "row" : "rows"}`;
  const verb = rowCount === 1 ? "relates" : "relate";
  const remainVerb = rowCount === 1 ? "remains" : "remain";
  const explainVerb = rowCount === 1 ? "explains" : "explain";

  if (category === "limited_context_rows") {
    return `${countPhrase} ${remainVerb} visible as limited-context evidence for ${label}; ${rowCount === 1 ? "it is" : "they are"} not counted in the summarized pattern.`;
  }
  if (category === "procedural_context_rows") {
    return `${countPhrase} ${remainVerb} visible as procedural context for ${label}; ${rowCount === 1 ? "it explains" : "they explain"} floor process and ${rowCount === 1 ? "is" : "are"} not counted as support or opposition.`;
  }
  if (category === "not_voting_rows") {
    return `${countPhrase} ${explainVerb} ${label}, but not-voting rows are not counted as support or opposition.`;
  }
  if (category === "related_floor_or_procedural_votes") {
    return `${countPhrase} ${verb} to ${label}, including ${proceduralCount} procedural ${proceduralCount === 1 ? "row" : "rows"} that should not be treated as final policy votes.`;
  }
  if (category === "related_amendments") {
    return `${countPhrase} ${verb} to ${label}, including ${amendmentCount} amendment ${amendmentCount === 1 ? "row" : "rows"} that should be read with their evidence limits.`;
  }

  const caveats = [];
  if (ambiguousCount) {
    caveats.push(`${ambiguousCount} limited`);
  }
  if (notVotingCount) {
    caveats.push(`${notVotingCount} not voting`);
  }

  return `${countPhrase} ${verb} to ${label}; ${countedCount} counted in the summarized Yes/No pattern${caveats.length ? `, with ${caveats.join(" and ")} ${caveats.length === 1 ? "row" : "rows"} kept separate` : ""}.`;
}

function isCountedDirectionalRow(row) {
  return (
    row.interpretation_status === "interpreted" &&
    (row.position === "yea" || row.position === "nay") &&
    (row.position === row.support_position || row.position === row.oppose_position)
  );
}

function isAmbiguousOrInsufficientRow(row) {
  return row.interpretation_status === "ambiguous" || row.interpretation_status === "insufficient_evidence";
}

function isProceduralRow(row) {
  const text = `${row.issue_facet || ""} ${row.description || ""} ${row.question || ""} ${row.vote_context?.vote_type || row.vote_type || ""}`.toLowerCase();
  return isProceduralContextRow(row) || /\b(procedure|procedural|floor rule|rule|motion to commit|motion|conference instruction|instruct conferees|concurrence)\b/.test(text);
}

function isAmendmentRow(row) {
  const text = `${row.issue_facet || ""} ${row.description || ""} ${row.question || ""} ${row.vote_context?.vote_type || row.vote_type || ""}`.toLowerCase();
  return /\bamendment\b/.test(text);
}

function buildGroupLabel(row) {
  return cleanLabel(getFirstString(row.bill_title, row.measure_title, row.source_bill_title, row.title, row.description, row.question, row.issue_facet)) || "Reviewed measure";
}

function normalizeTitle(value) {
  const cleaned = cleanLabel(value)
    .toLowerCase()
    .replace(/\b(on passage|passage|adoption|motion to|ordering the previous question)\b/g, "")
    .replace(/[^a-z0-9]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();

  if (!cleaned || cleaned.length < 8) {
    return "";
  }
  return cleaned;
}

function normalizeIdentifier(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, ":")
    .replace(/^:+|:+$/g, "");
}

function cleanLabel(value) {
  return String(value || "")
    .replace(/\s+/g, " ")
    .trim();
}

function getFirstString(...values) {
  for (const value of values) {
    if (value !== null && value !== undefined && String(value).trim()) {
      return String(value).trim();
    }
  }
  return "";
}

function emptySummary() {
  return {
    totalRows: 0,
    totalGroups: 0,
    repeatedGroupCount: 0,
    countedYesNoRows: 0,
    ambiguousOrInsufficientRows: 0,
    notVotingRows: 0,
    proceduralRows: 0,
    proceduralContextRows: 0,
    amendmentRows: 0,
    repeatedGroups: [],
  };
}
