import {
  actionReceiptId,
  canonicalActionId,
} from "../lib/frontendPassA.mjs";
import { formatDisplayMeasureTitle } from "../lib/measureDisplay.mjs";
import { isProceduralContextRow } from "../lib/proceduralContext.mjs";

export default function ActionReceipt({
  expanded,
  highlighted,
  onToggle,
  row,
}) {
  const id = actionReceiptId(row);
  const actionId = canonicalActionId(row);
  const title = formatDisplayMeasureTitle(
    row.bill_title || row.description || row.question || "Untitled recorded action",
  );
  const position = formatPosition(row.position);
  return (
    <article
      className={`scroll-mt-28 border-b border-stone-200 ${
        highlighted ? "bg-teal-50/70 ring-2 ring-inset ring-teal-700/20" : ""
      }`}
      data-canonical-action-id={actionId}
      id={id}
      tabIndex={highlighted ? -1 : undefined}
    >
      <button
        aria-expanded={expanded}
        aria-label={`${expanded ? "Collapse" : "Expand"} ${title}, ${formatDate(row.vote_date)}, ${position}`}
        className="grid min-h-20 w-full gap-3 px-2 py-5 text-left sm:grid-cols-[7.5rem_minmax(0,1fr)_auto] sm:items-start"
        onClick={onToggle}
        type="button"
      >
        <span className="text-sm font-medium text-stone-600">
          {formatDate(row.vote_date)}
        </span>
        <span>
          <span className="block text-base font-semibold leading-6 text-stone-950">
            {title}
          </span>
          <span className="mt-1 block text-sm leading-6 text-stone-600">
            {formatChamber(row.chamber)} · Roll {row.rollcall_number || "not supplied"}
            {formatActionType(row) ? ` · ${formatActionType(row)}` : ""}
          </span>
          {row.plain_english_summary ? (
            <span className="mt-1 block text-sm leading-6 text-stone-700">
              {row.plain_english_summary}
            </span>
          ) : null}
          <span className="mt-1 block text-xs leading-5 text-stone-500">
            {formatReviewState(row)}
            {formatOutcome(row) ? ` · ${formatOutcome(row)}` : ""}
          </span>
        </span>
        <span className={`vote-pill vote-${normalize(row.position)}`}>
          {position}
        </span>
      </button>
      {expanded ? <ExpandedReceipt row={row} /> : null}
    </article>
  );
}

function ExpandedReceipt({ row }) {
  const sources = normalizeSources(row.source_basis);
  return (
    <div className="grid gap-5 border-t border-stone-200 bg-white px-4 py-6 text-base leading-7 text-stone-700 md:grid-cols-2">
      <ReceiptField label="Policy question" value={row.question || row.description} />
      <ReceiptField
        label="Exact-action meaning"
        value={row.plain_english_summary || row.interpretation_reason}
      />
      <ReceiptField label="Policy-episode relationship" value={row.episode_relationship} />
      <ReceiptField label="What the action would change" value={row.policy_effect || row.what_happened} />
      <ReceiptField label="Outcome and current status" value={formatOutcomeAndStatus(row)} />
      <ReceiptField
        label="Context and source limits"
        value={row.uncertainty_note || row.what_not_to_infer || limitedContext(row)}
      />
      <ReceiptField label="Why this exact action mattered" value={row.why_it_mattered} />
      <div>
        <h4 className="text-sm font-semibold uppercase tracking-[0.1em] text-stone-600">
          Official sources
        </h4>
        <div className="mt-2 flex flex-col items-start gap-2">
          {row.source_url ? (
            <a className="source-link" href={row.source_url} rel="noreferrer" target="_blank">
              Official vote source
            </a>
          ) : (
            <p>Official vote link not supplied.</p>
          )}
          {sources.map((source, index) => (
            <a
              className="source-link"
              href={source.url}
              key={`${source.url}-${index}`}
              rel="noreferrer"
              target="_blank"
            >
              {source.label}
            </a>
          ))}
        </div>
      </div>
      <div>
        <h4 className="text-sm font-semibold uppercase tracking-[0.1em] text-stone-600">
          Receipt reference
        </h4>
        <p className="mt-2 break-all text-sm leading-6 text-stone-600">
          {canonicalActionId(row) || "Canonical action ID not supplied"}
        </p>
      </div>
      <ReceiptReferences
        references={row.provenance_refs || row.receipt_refs}
      />
    </div>
  );
}

function ReceiptField({ label, value }) {
  if (!value) {
    return null;
  }
  return (
    <div>
      <h4 className="text-sm font-semibold uppercase tracking-[0.1em] text-stone-600">
        {label}
      </h4>
      <p className="mt-2">{value}</p>
    </div>
  );
}

function ReceiptReferences({ references }) {
  const normalized = (Array.isArray(references) ? references : [])
    .map((reference) => {
      if (typeof reference === "string") {
        return reference;
      }
      if (reference && typeof reference === "object") {
        return reference.label
          || reference.reference
          || reference.receipt_id
          || reference.proposition_id
          || reference.action_id
          || "";
      }
      return "";
    })
    .filter(Boolean);
  if (!normalized.length) {
    return null;
  }
  return (
    <div>
      <h4 className="text-sm font-semibold uppercase tracking-[0.1em] text-stone-600">
        Provenance references
      </h4>
      <ul className="mt-2 space-y-1 text-sm leading-6 text-stone-600">
        {normalized.map((reference) => (
          <li className="break-all" key={reference}>{reference}</li>
        ))}
      </ul>
    </div>
  );
}

function normalizeSources(sourceBasis) {
  return (Array.isArray(sourceBasis) ? sourceBasis : [])
    .map((source) => {
      if (typeof source === "string" && /^https?:\/\//.test(source)) {
        return { label: "Official action-meaning source", url: source };
      }
      if (source && typeof source === "object") {
        const url = source.url || source.source_url;
        if (typeof url === "string" && /^https?:\/\//.test(url)) {
          return {
            label: source.label || source.source_type || "Official action-meaning source",
            url,
          };
        }
      }
      return null;
    })
    .filter(Boolean);
}

function limitedContext(row) {
  if (isProceduralContextRow(row)) {
    return "This procedural or context record does not establish support or opposition on the underlying policy.";
  }
  if (["ambiguous", "insufficient_evidence"].includes(normalize(row.interpretation_status))) {
    return "The supplied evidence does not support a more specific exact-action interpretation.";
  }
  return "";
}

function formatReviewState(row) {
  if (isProceduralContextRow(row)) {
    return "Procedural / context record";
  }
  if (normalize(row.position) === "present") {
    return "Resolved non-directional action";
  }
  if (normalize(row.position) === "not_voting") {
    return "Resolved non-directional status";
  }
  if (normalize(row.interpretation_status) === "interpreted") {
    return "Reviewed exact-action meaning supplied";
  }
  if (normalize(row.interpretation_status) === "ambiguous") {
    return "Limited context";
  }
  if (normalize(row.interpretation_status) === "insufficient_evidence") {
    return "Unresolved evidence";
  }
  return "Vote receipt";
}

function formatOutcome(row) {
  const result = row.vote_context?.final_result;
  if (!result) {
    return "";
  }
  return `Chamber result: ${String(result).replaceAll("_", " ")}`;
}

function formatOutcomeAndStatus(row) {
  return [
    formatOutcome(row),
    row.current_status ? `Current status: ${row.current_status}` : "",
  ].filter(Boolean).join(" · ");
}

function formatActionType(row) {
  const value = row.vote_context?.vote_type || row.vote_type;
  return value
    ? String(value).replaceAll("_", " ").replace(/^\w/, (letter) => letter.toUpperCase())
    : "";
}

function formatPosition(value) {
  const normalized = normalize(value);
  if (normalized === "not_voting") {
    return "Not Voting";
  }
  return normalized
    ? normalized.replaceAll("_", " ").replace(/^\w/, (letter) => letter.toUpperCase())
    : "Recorded";
}

function formatChamber(value) {
  return String(value || "Chamber").replace(/^\w/, (letter) => letter.toUpperCase());
}

function formatDate(value) {
  if (!value) {
    return "Date not supplied";
  }
  const parsed = new Date(`${String(value).slice(0, 10)}T00:00:00`);
  return Number.isNaN(parsed.valueOf())
    ? String(value).slice(0, 10)
    : new Intl.DateTimeFormat("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
      }).format(parsed);
}

function normalize(value) {
  return String(value || "").trim().toLowerCase().replaceAll(" ", "_");
}
