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
  const projection = row.governed_receipt_projection || null;
  const title = formatDisplayMeasureTitle(
    row.bill_title || row.description || row.question || "Untitled recorded action",
  );
  const position = formatPosition(projection?.member_action || row.position);
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
          {projection?.exact_action_meaning || row.plain_english_summary ? (
            <span className="mt-1 block text-sm leading-6 text-stone-700">
              {projection?.exact_action_meaning || row.plain_english_summary}
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
  const projection = row.governed_receipt_projection || null;
  const voteSources = projection
    ? normalizeSources(projection.vote_sources, "Official vote source")
    : row.source_url
      ? [{ label: "Official vote source", url: row.source_url }]
      : [];
  const meaningSources = normalizeSources(
    projection?.action_meaning_sources || row.source_basis,
    "Official action-meaning source",
  );
  const references = projection
    ? [
        projection.action_interpretation_id,
        `Interpretation digest: ${projection.action_interpretation_sha256}`,
        ...projection.interpretation_receipt_refs,
      ]
    : row.provenance_refs || row.receipt_refs;
  return (
    <div className="border-t border-stone-200 bg-stone-50/70 px-4 py-6 sm:px-6 sm:py-8">
      <div className="max-w-3xl">
        <p className="text-xs font-semibold uppercase tracking-[0.12em] text-stone-500">
          Expanded vote receipt
        </p>
        <div className="mt-5 divide-y divide-stone-200 rounded-xl border border-stone-200 bg-white px-5 sm:px-6">
          <ReceiptField
            label="Exact-action meaning"
            value={projection?.exact_action_meaning || row.plain_english_summary || row.interpretation_reason}
          />
          <ReceiptField
            label="What this action would change"
            value={projection ? null : row.policy_effect || row.what_happened}
          />
          <ReceiptField
            label={projection ? "Governed policy question" : "Question put to a vote"}
            value={projection?.policy_question || row.question || row.description}
          />
          <ReceiptField label="Result and current status" value={formatOutcomeAndStatus(row)} />
          <ReceiptField
            label="Why this action mattered"
            value={projection ? null : row.why_it_mattered}
          />
          <ReceiptField
            label={projection ? "Governed policy episode" : "Policy-episode relationship"}
            value={projection?.episode_id || row.episode_relationship}
          />
          <ReceiptFieldList
            label="Context and source limits"
            values={projection?.caveats}
            fallback={row.uncertainty_note || row.what_not_to_infer || limitedContext(row)}
          />
        </div>
        <div className="mt-5 grid gap-5 text-sm leading-6 text-stone-600 sm:grid-cols-2">
          <div>
            <h4 className="font-semibold text-stone-800">Official sources</h4>
            <div className="mt-2 flex flex-col items-start gap-2">
              {[...voteSources, ...meaningSources].map((source, index) => (
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
              {!voteSources.length && !meaningSources.length ? (
                <p>Official vote link not supplied.</p>
              ) : null}
            </div>
          </div>
          <div>
            <h4 className="font-semibold text-stone-800">Receipt reference</h4>
            <p className="mt-2 break-all">
              {canonicalActionId(row) || "Canonical action ID not supplied"}
            </p>
          </div>
          <ReceiptReferences
            references={references}
          />
        </div>
      </div>
    </div>
  );
}

function ReceiptFieldList({ fallback, label, values }) {
  const normalized = Array.isArray(values) ? values.filter(Boolean) : [];
  if (!normalized.length) {
    return <ReceiptField label={label} value={fallback} />;
  }
  return (
    <div className="py-5">
      <h4 className="text-sm font-semibold text-stone-900">{label}</h4>
      <ul className="mt-2 max-w-2xl space-y-2 text-base leading-7 text-stone-700">
        {normalized.map((value) => <li key={value}>{value}</li>)}
      </ul>
    </div>
  );
}

function ReceiptField({ label, value }) {
  if (!value) {
    return null;
  }
  return (
    <div className="py-5">
      <h4 className="text-sm font-semibold text-stone-900">
        {label}
      </h4>
      <p className="mt-2 max-w-2xl text-base leading-7 text-stone-700">{value}</p>
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
    <div className="sm:col-span-2">
      <h4 className="font-semibold text-stone-800">
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

function normalizeSources(sourceBasis, fallbackLabel) {
  return (Array.isArray(sourceBasis) ? sourceBasis : [])
    .map((source) => {
      if (typeof source === "string" && /^https?:\/\//.test(source)) {
        return { label: fallbackLabel, url: source };
      }
      if (source && typeof source === "object") {
        const url = source.url || source.source_url;
        if (typeof url === "string" && /^https?:\/\//.test(url)) {
          return {
            label: [
              source.label || source.name || source.source_type || fallbackLabel,
              source.source_id,
            ].filter(Boolean).join(" · "),
            url,
          };
        }
      }
      return null;
    })
    .filter(Boolean);
}

function limitedContext(row) {
  const governedControl = row.governed_receipt_control;
  if (governedControl?.status === "noncounting_control") {
    return governedControl.detail
      || "This governed control remains visible but does not count as support or opposition.";
  }
  if (isProceduralContextRow(row)) {
    return "This procedural or context record does not establish support or opposition on the underlying policy.";
  }
  if (["ambiguous", "insufficient_evidence"].includes(normalize(row.interpretation_status))) {
    return "The supplied evidence does not support a more specific exact-action interpretation.";
  }
  return "";
}

function formatReviewState(row) {
  if (row.governed_receipt_control?.status === "noncounting_control") {
    return "Governed non-counting control";
  }
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
