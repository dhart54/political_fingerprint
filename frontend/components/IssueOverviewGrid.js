import { formatDomainLabel } from "../lib/issueDomains";
import {
  getDomainDescription,
  getRecordedActionComposition,
} from "../lib/issueEvidenceCoverage.mjs";

export default function IssueOverviewGrid({
  mode,
  onSelect,
  rows,
  selectedIssue,
}) {
  if (!rows.length) {
    return (
      <p className="mt-6 rounded-2xl border border-stone-200 bg-white p-5 text-base leading-7 text-stone-700">
        {mode === "reviewed_analysis"
          ? "No plain-language issue summary is available in this representative and Congress scope. Vote receipts remain available under the other views."
          : "No recorded issue actions are available in this Congress scope."}
      </p>
    );
  }

  return (
    <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {rows.map((row, index) => (
        <IssueCard
          isRecommended={mode === "recommended" && index === 0}
          isSelected={selectedIssue === row.domain}
          key={row.domain}
          onSelect={onSelect}
          row={row}
        />
      ))}
    </div>
  );
}

function IssueCard({ isRecommended, isSelected, onSelect, row }) {
  const composition = getRecordedActionComposition(row);
  const label = formatDomainLabel(row.domain);
  const status = row.analysisAvailable
    ? "Issue summary available"
    : "Vote receipts available";
  return (
    <article
      className={`flex min-h-[24rem] flex-col rounded-2xl border bg-white p-5 transition ${
        isSelected
          ? "border-teal-800 ring-2 ring-teal-800/15"
          : "border-stone-200 hover:border-teal-700/50"
      }`}
      data-testid="issue-card"
    >
      <div className="flex min-h-7 items-start justify-between gap-3">
        {isRecommended ? (
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-teal-800">
            Recommended starting point
          </p>
        ) : <span />}
        <span className={`status-pill ${row.analysisAvailable ? "status-reviewed" : "status-basic"}`}>
          {status}
        </span>
      </div>
      <h3 className="mt-4 font-serif text-2xl leading-tight text-stone-950">
        {label}
      </h3>
      <p className="mt-3 text-base leading-7 text-stone-700">
        {getDomainDescription(row.domain)}
      </p>
      <div className="mt-5 grid grid-cols-2 gap-3 border-y border-stone-200 py-4">
        <Metric label="recorded actions" value={row.totalRecordedActions} />
        <Metric
          label="substantive Yea/Nay receipts"
          value={row.substantiveEvidenceCount}
        />
      </div>
      <div className="mt-4" role="group" aria-label={`${label} recorded action composition`}>
        <p className="text-xs font-semibold uppercase tracking-[0.12em] text-stone-500">
          Recorded action composition
        </p>
        <div aria-hidden="true" className="mt-2 flex h-2 overflow-hidden rounded-full bg-stone-100">
          {composition.map((item) => (
            <span
              className={compositionClass(item.key)}
              key={item.key}
              style={{ width: `${item.percent}%` }}
            />
          ))}
        </div>
        <ul className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-xs leading-5 text-stone-600">
          {composition.map((item) => (
            <li key={item.key}>
              {item.label} <strong className="font-semibold text-stone-900">{item.count}</strong>
            </li>
          ))}
        </ul>
      </div>
      {row.analysisAvailable ? (
        <p className="mt-4 line-clamp-2 text-sm leading-6 text-teal-950">
          {row.presentation.review_state.scope_bounded_teaser?.text
            || row.presentation.teaser
            || "A plain-language issue summary is available for this scope."}
        </p>
      ) : (
        <p className="mt-4 text-sm leading-6 text-stone-600">
          Open the issue to browse its chronological exact vote record.
        </p>
      )}
      <button
        aria-current={isSelected ? "true" : undefined}
        aria-label={`${row.analysisAvailable ? "Explore" : "Browse vote record for"} ${label}`}
        className="mt-auto pt-5 text-left text-sm font-semibold text-teal-900 underline decoration-teal-700/30 underline-offset-4 hover:decoration-teal-800"
        onClick={() => onSelect(row.domain)}
        type="button"
      >
        {row.analysisAvailable ? "Explore issue" : "Browse vote record"}
      </button>
    </article>
  );
}

function Metric({ label, value }) {
  return (
    <div>
      <p className="font-serif text-3xl leading-none text-stone-950">{value}</p>
      <p className="mt-1 text-xs leading-5 text-stone-600">{label}</p>
    </div>
  );
}

function compositionClass(key) {
  if (key === "yea") {
    return "bg-emerald-500/65";
  }
  if (key === "nay") {
    return "bg-rose-400/65";
  }
  return "bg-stone-400/60";
}
