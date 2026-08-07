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
  publicActionStatusKind,
} from "../lib/selectedIssueExperience.mjs";
import SemanticIcon from "./SemanticIcon";

export default function ActionReceipt({
  expanded,
  highlighted,
  onToggle,
  representativeName,
  row,
}) {
  const id = actionReceiptId(row);
  const actionId = canonicalActionId(row);
  const action = getActionPresentation(row);
  const position = formatPosition(action.vote || row.position);
  return (
    <article
      className={`scroll-mt-28 border-b border-stone-200 last:border-b-0 ${
        highlighted ? "bg-teal-50/70 ring-2 ring-inset ring-teal-700/20" : ""
      }`}
      data-canonical-action-id={actionId}
      id={id}
      tabIndex={highlighted ? -1 : undefined}
    >
      <button
        aria-expanded={expanded}
        aria-label={`${expanded ? "Collapse" : "Expand"} ${action.title}, ${formatDate(row.vote_date)}, ${position}`}
        className="grid min-h-16 w-full grid-cols-[minmax(0,1fr)_auto_auto] items-start gap-x-3 gap-y-1 px-3 py-3 text-left sm:grid-cols-[7.5rem_minmax(0,1fr)_auto_auto] sm:px-4"
        onClick={onToggle}
        type="button"
      >
        <span className="col-span-2 text-sm font-medium text-stone-600 sm:col-span-1 sm:col-start-1 sm:row-start-1">
          {formatDate(row.vote_date)}
        </span>
        <span className="col-start-1 row-start-2 min-w-0 sm:col-start-2 sm:row-start-1">
          <span className="block text-base font-semibold leading-6 text-stone-950">
            {action.title}
          </span>
          {action.parentMeasure ? (
            <span className="mt-0.5 block text-sm leading-5 text-stone-600">
              Parent measure: {action.parentMeasure}
            </span>
          ) : null}
          <span className="mt-0.5 block text-sm leading-5 text-stone-600">
            {formatChamber(row.chamber)} · Roll {row.rollcall_number || "not supplied"}
            {action.actionType ? ` · ${action.actionType}` : ""}
          </span>
          {action.status ? <ActionStatus label={action.status} /> : null}
        </span>
        <span className={`vote-pill vote-${normalize(row.position)} col-start-2 row-start-2 sm:col-start-3 sm:row-start-1`}>
          {position}
        </span>
        <span
          aria-hidden="true"
          className="col-start-3 row-start-2 pt-1 text-lg leading-none text-stone-600 sm:col-start-4 sm:row-start-1"
        >
          {expanded ? "⌃" : "⌄"}
        </span>
      </button>
      {expanded ? (
        <ExpandedReceipt representativeName={representativeName} row={row} />
      ) : null}
    </article>
  );
}

function ActionStatus({ label }) {
  const kind = publicActionStatusKind(label);
  if (!kind) {
    return null;
  }
  return (
    <span
      className="mt-1 flex items-center gap-1.5 text-xs font-semibold leading-5 text-stone-600"
      data-action-status={kind}
    >
      <SemanticIcon kind={kind} />
      <span>{label}</span>
    </span>
  );
}

function ExpandedReceipt({ representativeName, row }) {
  const receipt = buildPublicReceipt(row);
  const limitations = receipt.limitations.length
    ? receipt.limitations
    : publicLimitations([limitedContext(row)]);
  const sources = [...receipt.voteSources, ...receipt.actionSources];
  const about = receipt.exactActionMeaning
    || receipt.proposedChange
    || receipt.policyQuestion;
  const proposal = receipt.exactActionMeaning
    ? receipt.proposedChange || receipt.policyQuestion
    : "";
  const result = formatReadableResult(row);
  const sectionCount = [
    about,
    proposal,
    receipt.representativeVote || result,
    limitations.length,
    sources.length,
  ].filter(Boolean).length;
  return (
    <div className="border-t border-stone-200 bg-stone-50/70 px-4 py-5 sm:px-5">
      <div className={`grid gap-x-6 md:grid-cols-2 xl:gap-x-0 xl:divide-x xl:divide-stone-200 ${DETAIL_GRID_COLUMNS[sectionCount] || "xl:grid-cols-5"}`}>
        <DetailSection heading="What this vote was about" value={about} />
        <DetailSection heading="What the proposal would do" value={proposal} />
        <VoteResultSection
          position={formatPosition(receipt.representativeVote)}
          representativeName={representativeName}
          result={result}
        />
        <ContextSection values={limitations} />
        <SourcesSection sources={sources} />
      </div>
    </div>
  );
}

function DetailSection({ heading, value }) {
  if (!value) {
    return null;
  }
  return (
    <section className="min-w-0 border-t border-stone-200 py-4 first:border-t-0 first:pt-0 md:border-t-0 md:py-0 xl:px-5 xl:first:pl-0">
      <h4 className="text-sm font-semibold text-stone-950">{heading}</h4>
      <p className="mt-2 text-sm leading-6 text-stone-700">{value}</p>
    </section>
  );
}

function VoteResultSection({ position, representativeName, result }) {
  if (!position && !result) {
    return null;
  }
  return (
    <section className="min-w-0 border-t border-stone-200 py-4 first:border-t-0 first:pt-0 md:border-t-0 md:py-0 xl:px-5">
      {position ? (
        <>
          <h4 className="text-sm font-semibold text-stone-950">
            How {representativeName || "the representative"} voted
          </h4>
          <span className={`vote-pill vote-${normalize(position)} mt-2`}>{position}</span>
        </>
      ) : null}
      {result ? (
        <div className={position ? "mt-4" : ""}>
          <h4 className="text-sm font-semibold text-stone-950">Result</h4>
          <p className="mt-1 text-sm leading-6 text-stone-700">{result}</p>
        </div>
      ) : null}
    </section>
  );
}

function ContextSection({ values }) {
  if (!values.length) {
    return null;
  }
  return (
    <section className="min-w-0 border-t border-stone-200 py-4 first:border-t-0 first:pt-0 md:border-t-0 md:py-0 xl:px-5">
      <h4 className="text-sm font-semibold text-stone-950">Important context</h4>
      <ul className="mt-2 list-disc space-y-1 pl-4 text-sm leading-6 text-stone-700">
        {values.map((value) => <li key={value}>{value}</li>)}
      </ul>
    </section>
  );
}

function SourcesSection({ sources }) {
  if (!sources.length) {
    return null;
  }
  return (
    <section className="min-w-0 border-t border-stone-200 py-4 first:border-t-0 first:pt-0 md:border-t-0 md:py-0 xl:px-5">
      <h4 className="text-sm font-semibold text-stone-950">Official sources</h4>
      <div className="mt-2 flex flex-col items-start gap-3">
        {sources.map((source, index) => (
          <a
            className="source-link inline-flex items-center gap-2 text-sm"
            href={source.url}
            key={`${source.url}-${index}`}
            rel="noreferrer"
            target="_blank"
          >
            <SemanticIcon
              className="h-5 w-5 shrink-0"
              kind={source.label === "Official vote" ? "vote-source" : "document-source"}
            />
            <span>{source.label}</span>
          </a>
        ))}
      </div>
    </section>
  );
}

function limitedContext(row) {
  const governedControl = row.governed_receipt_control;
  if (governedControl?.status === "noncounting_control") {
    return governedControl.detail
      || "This action is non-counting and does not establish support or opposition.";
  }
  if (isProceduralContextRow(row)) {
    return "This procedural or context action does not establish support or opposition on the underlying policy.";
  }
  if (["ambiguous", "insufficient_evidence"].includes(normalize(row.interpretation_status))) {
    return "The available official material does not support a more specific account of this action.";
  }
  return "";
}

function formatReadableResult(row) {
  const supplied = getPublicChamberResult(row);
  const status = row.current_status
    ? `Current status: ${String(row.current_status).replaceAll("_", " ")}`
    : "";
  if (!supplied) {
    return status;
  }
  const result = String(supplied).replaceAll("_", " ");
  const readable = ["passed", "failed"].includes(result.toLowerCase())
    ? `${capitalize(result)} in the ${formatChamber(row.chamber)}`
    : capitalize(result);
  return [readable, status].filter(Boolean).join(" · ");
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
  return String(value || "chamber").replace(/^\w/, (letter) => letter.toUpperCase());
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

function capitalize(value) {
  return String(value || "").replace(/^\w/, (letter) => letter.toUpperCase());
}

function normalize(value) {
  return String(value || "").trim().toLowerCase().replaceAll(" ", "_");
}

const DETAIL_GRID_COLUMNS = {
  1: "xl:grid-cols-1",
  2: "xl:grid-cols-2",
  3: "xl:grid-cols-3",
  4: "xl:grid-cols-4",
  5: "xl:grid-cols-5",
};
