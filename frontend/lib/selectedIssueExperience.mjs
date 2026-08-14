import { canonicalActionId, scopeLabel } from "./frontendPassA.mjs";
import { isProceduralContextRow } from "./proceduralContext.mjs";

export function buildSelectedIssueModel({ presentation, rows = [], scope = "all" }) {
  const reviewState = presentation?.review_state || null;
  const hasInterpretation = Boolean(
    reviewState && presentation?.tier !== "receipts_only",
  );
  const congresses = hasInterpretation
    ? (reviewState.congress_scope || []).map(Number).filter(Number.isFinite)
    : [];
  const interpretationScope = hasInterpretation
    ? [formatCongressScope(congresses), formatReviewScope(reviewState.review_scope)]
      .filter(Boolean)
      .join(" · ")
    : "No reviewed interpretation for this scope";
  const selectedCongress = scope === "all" ? null : Number(scope);
  const scopesAlign = Boolean(
    selectedCongress
    && congresses.length === 1
    && congresses[0] === selectedCongress,
  );
  return {
    evidence: {
      count: rows.length,
      label: scopeLabel(scope),
      countText: `${rows.length} recorded ${rows.length === 1 ? "action" : "actions"} currently visible`,
    },
    interpretation: hasInterpretation
      ? {
          scope: interpretationScope,
          congressLabel: formatCongressScope(congresses),
          type: reviewTypeLabel(reviewState.review_scope),
          actionCount: nonNegativeNumber(reviewState.total_recorded_actions),
          episodeCount: nonNegativeNumber(reviewState.complete_episode_count),
          congresses,
        }
      : null,
    scopesAlign,
  };
}

export function buildPatternIndex(presentation, rows = []) {
  if (!presentation?.review_state || presentation.tier === "receipts_only") {
    return [];
  }
  const episodeByAction = buildEpisodeIndex(presentation, rows);
  const items = [
    ...(presentation.repeated_patterns || []),
    ...(presentation.policy_trajectories || []),
  ];
  return items.map((item) => {
    const actionIds = uniqueStrings(item.action_ids);
    const episodeIds = uniqueStrings(
      actionIds.map((actionId) => episodeByAction.get(actionId)),
    );
    return {
      ...item,
      actionIds,
      actionCount: actionIds.length,
      episodeCount: episodeIds.length || null,
      statusLabel: formatDirection(item.direction),
    };
  });
}

export function buildFindingIndex(
  presentation,
  rows = [],
  field = "repeated_patterns",
) {
  if (!presentation?.review_state || presentation.tier === "receipts_only") {
    return [];
  }
  const episodeByAction = buildEpisodeIndex(presentation, rows);
  return (presentation?.[field] || []).map((item) => {
    const actionIds = uniqueStrings(item.action_ids);
    const suppliedEpisodeIds = uniqueStrings(item.episode_ids);
    const episodeIds = suppliedEpisodeIds.length
      ? suppliedEpisodeIds
      : uniqueStrings(actionIds.map((actionId) => episodeByAction.get(actionId)));
    return {
      ...item,
      actionIds,
      actionCount: actionIds.length,
      episodeCount: episodeIds.length || null,
      statusLabel: item.direction_label
        || (item.direction ? formatDirection(item.direction) : "Bounded finding"),
      showDirection: item.show_direction !== false && Boolean(item.direction),
    };
  });
}

export function buildLedgerItems(rows = [], { groupRelated = true } = {}) {
  if (!groupRelated) {
    return rows.map((row) => ({
      id: canonicalActionId(row),
      type: "action",
      row,
    }));
  }
  const buckets = new Map();
  const sequence = [];
  rows.forEach((row, index) => {
    const identity = relatedActionIdentity(row);
    if (!identity) {
      sequence.push({
        id: canonicalActionId(row) || `action-${index}`,
        type: "action",
        row,
      });
      return;
    }
    let bucket = buckets.get(identity.id);
    if (!bucket) {
      bucket = {
        id: identity.id,
        type: "group",
        label: identity.label,
        rows: [],
      };
      buckets.set(identity.id, bucket);
      sequence.push(bucket);
    }
    bucket.rows.push(row);
  });
  return sequence.flatMap((item) => {
    if (item.type !== "group" || item.rows.length < 2) {
      const row = item.type === "group" ? item.rows[0] : item.row;
      return [{ id: canonicalActionId(row), type: "action", row }];
    }
    return [{
      ...item,
      composition: groupComposition(item.rows),
    }];
  });
}

export function completeVisibleRows(rows = [], requestedCount = 12) {
  const initial = rows.slice(0, Math.max(0, requestedCount));
  const selectedGroups = new Set(
    initial.map(relatedActionIdentity).filter(Boolean).map((item) => item.id),
  );
  if (!selectedGroups.size) {
    return initial;
  }
  return rows.filter((row, index) => {
    if (index < requestedCount) {
      return true;
    }
    const identity = relatedActionIdentity(row);
    return identity && selectedGroups.has(identity.id);
  });
}

export function getActionPresentation(row = {}) {
  const projection = row.governed_receipt_projection || null;
  const actionType = formatActionType(
    row.vote_context?.vote_type || row.vote_type,
  );
  const billTitle = firstText(
    row.bill_title,
    row.parent_bill_display,
    row.measure_title,
    row.source_bill_title,
  );
  const suppliedActionLabel = firstText(
    row.amendment_purpose,
    row.action_label,
  );
  const officialActionLabel = firstSpecificText(row.description);
  const approvedMeaningTitle = conciseApprovedLead(
    projection?.exact_action_meaning,
  );
  const title = suppliedActionLabel
    || billTitle
    || officialActionLabel
    || approvedMeaningTitle
    || `${actionType || "Recorded action"} · Roll ${row.rollcall_number || "not supplied"}`;
  return {
    actionType,
    parentMeasure: billTitle && normalizeText(billTitle) !== normalizeText(title)
      ? billTitle
      : "",
    status: publicActionStatus(row),
    title,
    vote: projection?.member_action || row.position || "",
  };
}

export function publicActionStatus(row = {}) {
  if (row.governed_receipt_control?.status === "noncounting_control") {
    return "Non-counting control";
  }
  if (isProceduralContextRow(row)) {
    return "Procedural / context";
  }
  const status = normalizeText(row.interpretation_status);
  if (status === "ambiguous") {
    return "Limited context";
  }
  if (status === "insufficient evidence") {
    return "Unresolved evidence";
  }
  return "";
}

export function publicActionStatusKind(label = "") {
  return {
    "Procedural / context": "procedural",
    "Non-counting control": "noncounting",
    "Limited context": "limited",
    "Unresolved evidence": "unresolved",
  }[label] || "";
}

export function getPublicChamberResult(row = {}) {
  return firstText(
    row.vote_context?.final_result,
    row.final_result,
    row.vote_result,
  );
}

function buildEpisodeIndex(presentation, rows) {
  const result = new Map();
  for (const receipt of presentation?.exact_action_receipts || []) {
    if (receipt?.canonical_action_id && receipt?.episode_id) {
      result.set(receipt.canonical_action_id, receipt.episode_id);
    }
  }
  for (const row of rows) {
    const actionId = canonicalActionId(row);
    const episodeId = row.governed_receipt_projection?.episode_id;
    if (actionId && episodeId) {
      result.set(actionId, episodeId);
    }
  }
  return result;
}

function relatedActionIdentity(row) {
  if (!row) {
    return null;
  }
  const explicit = firstText(
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
  const parentDisplay = firstText(row.parent_bill_display);
  const parentParts = [row.parent_bill_type, row.parent_bill_number]
    .filter((value) => value !== null && value !== undefined && String(value).trim());
  const billTitle = firstText(row.bill_title, row.measure_title, row.source_bill_title);
  const label = billTitle || parentDisplay;
  if (explicit) {
    return { id: `bill:${normalizeKey(explicit)}`, label: label || explicit };
  }
  if (parentParts.length === 2) {
    return {
      id: `parent:${Number(row.congress) || "scope"}:${normalizeKey(parentParts.join(":"))}`,
      label: label || parentDisplay || parentParts.join(" ").toUpperCase(),
    };
  }
  if (isSpecificMeasureTitle(label)) {
    return {
      id: `title:${Number(row.congress) || "scope"}:${normalizeKey(label)}`,
      label,
    };
  }
  return null;
}

function groupComposition(rows) {
  const counts = new Map();
  let controls = 0;
  for (const row of rows) {
    const vote = normalizeText(
      row.governed_receipt_projection?.member_action || row.position,
    );
    const label = vote === "not voting"
      ? "Not Voting"
      : vote.replace(/^\w/, (letter) => letter.toUpperCase()) || "Recorded";
    counts.set(label, (counts.get(label) || 0) + 1);
    if (row.governed_receipt_control?.status === "noncounting_control") {
      controls += 1;
    }
  }
  return {
    controls,
    positions: [...counts.entries()].map(([label, count]) => ({ label, count })),
  };
}

function conciseApprovedLead(value) {
  const text = String(value || "").replace(/\s+/g, " ").trim();
  if (!text) {
    return "";
  }
  const sentenceBoundary = text.search(/[.!?](?=\s+[A-Z]|$)/);
  const boundary = [text.indexOf(","), text.indexOf(";"), sentenceBoundary]
    .filter((index) => index > 0)
    .sort((left, right) => left - right)[0];
  const clause = boundary ? text.slice(0, boundary).trim() : text;
  if (clause.length <= 120) {
    return clause;
  }
  const lastSpace = clause.lastIndexOf(" ", 117);
  return `${clause.slice(0, lastSpace > 40 ? lastSpace : 117).trim()}…`;
}

function reviewTypeLabel(value) {
  if (value === "full_defined_issue_record") {
    return "Full reviewed record";
  }
  if (value === "benchmark_sample") {
    return "Reviewed record sample";
  }
  if (value === "bounded_partial_record") {
    return "Bounded reviewed record";
  }
  return "Reviewed record";
}

function formatReviewScope(value) {
  if (value === "full_defined_issue_record") {
    return "full defined issue record";
  }
  if (value === "benchmark_sample") {
    return "bounded record sample";
  }
  if (value === "bounded_partial_record") {
    return "bounded partial record";
  }
  return "reviewed record";
}

function formatCongressScope(scope) {
  return scope.map((congress) => `${congress}th Congress`).join(", ");
}

function formatDirection(value) {
  if (value === "support") {
    return "Support";
  }
  if (value === "opposition") {
    return "Opposition";
  }
  if (value === "mixed") {
    return "Mixed";
  }
  return "Record pattern";
}

function formatActionType(value) {
  return String(value || "")
    .trim()
    .replaceAll("_", " ")
    .replace(/^\w/, (letter) => letter.toUpperCase());
}

function firstSpecificText(...values) {
  return values.map((value) => String(value || "").trim()).find((value) => (
    value
    && value.length <= 140
    && !/^(?:house|senate) roll \d+$/i.test(value)
    && !/^the (?:house|senate) choice was whether\b/i.test(value)
    && !/^(?:on )?(?:agreeing to|passage of|motion to|final passage|the amendment|the bill)/i.test(value)
  )) || "";
}

function isSpecificMeasureTitle(value) {
  const normalized = String(value || "").trim();
  return Boolean(
    normalized.length >= 12
    && !/^(?:house|senate) roll|^(?:on )?(?:agreeing|passage|motion)|^amendment$/i.test(normalized),
  );
}

function firstText(...values) {
  return values.map((value) => String(value || "").trim()).find(Boolean) || "";
}

function normalizeKey(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, ":")
    .replace(/^:+|:+$/g, "");
}

function normalizeText(value) {
  return String(value || "").trim().toLowerCase().replaceAll("_", " ");
}

function nonNegativeNumber(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : 0;
}

function uniqueStrings(values) {
  return [...new Set((Array.isArray(values) ? values : []).filter((value) => (
    typeof value === "string" && value.trim()
  )))];
}
