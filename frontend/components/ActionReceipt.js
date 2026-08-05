import {
  actionReceiptId,
  canonicalActionId,
} from "../lib/frontendPassA.mjs";
import { isProceduralContextRow } from "../lib/proceduralContext.mjs";
import {
  buildPublicReceipt,
  publicLimitations,
} from "../lib/publicReceipt.mjs";
import {
  getActionPresentation,
  getPublicChamberResult,
} from "../lib/selectedIssueExperience.mjs";

export default function ActionReceipt({
  expanded,
  highlighted,
  onToggle,
  row,
}) {
  const id = actionReceiptId(row);
  const actionId = canonicalActionId(row);
  const action = getActionPresentation(row);
  const position = formatPosition(action.vote || row.position);
  const outcome = formatOutcome(row);
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
        aria-label={`${expanded ? "Collapse" : "Expand"} ${action.title}, ${formatDate(row.vote_date)}, ${position}`}
        className="grid min-h-20 w-full gap-3 px-2 py-5 text-left sm:grid-cols-[7.5rem_minmax(0,1fr)_auto] sm:items-start"
        onClick={onToggle}
        type="button"
      >
        <span className="text-sm font-medium text-stone-600">
          {formatDate(row.vote_date)}
        </span>
        <span>
          <span className="block text-base font-semibold leading-6 text-stone-950">
            {action.title}
          </span>
          {action.parentMeasure ? (
            <span className="mt-1 block text-sm leading-6 text-stone-700">
              Parent measure: {action.parentMeasure}
            </span>
          ) : null}
          <span className="mt-1 block text-sm leading-6 text-stone-600">
            {formatChamber(row.chamber)} · Roll {row.rollcall_number || "not supplied"}
            {action.actionType ? ` · ${action.actionType}` : ""}
          </span>
          <span className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-xs leading-5 text-stone-500">
            {action.status ? <span>{action.status}</span> : null}
            {outcome ? <span>{outcome}</span> : null}
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
  const receipt = buildPublicReceipt(row);
  const limitations = receipt.limitations.length
    ? receipt.limitations
    : publicLimitations([limitedContext(row)]);
  const sources = [...receipt.voteSources, ...receipt.actionSources];
  return (
    <div className="border-t border-stone-200 bg-stone-50/70 px-4 py-6 sm:px-6 sm:py-8">
      <div className="max-w-3xl">
        <p className="text-xs font-semibold uppercase tracking-[0.12em] text-stone-500">
          Vote details
        </p>
        <div className="mt-5 divide-y divide-stone-200 rounded-xl border border-stone-200 bg-white px-5 sm:px-6">
          <ReceiptField label="Exact-action meaning" value={receipt.exactActionMeaning} />
          <ReceiptField label="What this action would change" value={receipt.proposedChange} />
          <ReceiptField label="Policy question" value={receipt.policyQuestion} />
          <ReceiptField label="Representative vote" value={formatPosition(receipt.representativeVote)} />
          <ReceiptField label="Result and current status" value={formatOutcomeAndStatus(row)} />
          <ReceiptField
            label="Policy-episode relationship"
            value={receipt.episodeRelationship}
          />
          <ReceiptFieldList
            label="Material context or limitations"
            values={limitations}
          />
        </div>
        <div className="mt-5 text-sm leading-6 text-stone-600">
          <h4 className="font-semibold text-stone-800">Official sources</h4>
          <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-2">
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
            {!sources.length ? <p>Official source links not supplied.</p> : null}
          </div>
        </div>
      </div>
    </div>
  );
}

function ReceiptFieldList({ label, values }) {
  const normalized = Array.isArray(values) ? values.filter(Boolean) : [];
  if (!normalized.length) {
    return null;
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
      <h4 className="text-sm font-semibold text-stone-900">{label}</h4>
      <p className="mt-2 max-w-2xl text-base leading-7 text-stone-700">{value}</p>
    </div>
  );
}

function limitedContext(row) {
  const governedControl = row.governed_receipt_control;
  if (governedControl?.status === "noncounting_control") {
    return governedControl.detail
      || "This action is governed as non-counting and does not establish support or opposition.";
  }
  if (isProceduralContextRow(row)) {
    return "This procedural or context action does not establish support or opposition on the underlying policy.";
  }
  if (["ambiguous", "insufficient_evidence"].includes(normalize(row.interpretation_status))) {
    return "The available official material does not support a more specific account of this action.";
  }
  return "";
}

function formatOutcome(row) {
  const result = getPublicChamberResult(row);
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
