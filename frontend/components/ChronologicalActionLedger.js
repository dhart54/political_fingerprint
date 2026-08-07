"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import ActionReceipt from "./ActionReceipt";
import SemanticIcon from "./SemanticIcon";
import {
  canonicalActionId,
  chronologicalActions,
  filterActions,
  filterActionsByDimensions,
  resolveExactActionRequest,
} from "../lib/frontendPassA.mjs";
import {
  buildLedgerItems,
  completeVisibleRows,
} from "../lib/selectedIssueExperience.mjs";

const INITIAL_BATCH = 12;
const VOTE_FILTERS = [
  ["all", "All"],
  ["yea", "Yea"],
  ["nay", "Nay"],
  ["non_directional", "Present / Not voting"],
];
const TYPE_FILTERS = [
  ["all", "All actions"],
  ["substantive", "Substantive"],
  ["procedural_context", "Procedural / context"],
];

export default function ChronologicalActionLedger({
  highlightedFinding,
  representativeName,
  rows = [],
}) {
  const [voteFilter, setVoteFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");
  const [visibleCount, setVisibleCount] = useState(INITIAL_BATCH);
  const [expandedId, setExpandedId] = useState(null);
  const [activeHighlightedIds, setActiveHighlightedIds] = useState([]);
  const [patternActive, setPatternActive] = useState(false);
  const [linkedActionNotice, setLinkedActionNotice] = useState("");
  const headingRef = useRef(null);
  const ordered = useMemo(() => chronologicalActions(rows), [rows]);
  const requestedHighlightedIds = useMemo(
    () => highlightedFinding?.actionIds || [],
    [highlightedFinding?.actionIds],
  );
  const filtered = useMemo(
    () => patternActive
      ? filterActions(ordered, "highlighted", activeHighlightedIds)
      : filterActionsByDimensions(ordered, {
          vote: voteFilter,
          type: typeFilter,
        }),
    [activeHighlightedIds, ordered, patternActive, typeFilter, voteFilter],
  );
  const visible = useMemo(
    () => completeVisibleRows(filtered, visibleCount),
    [filtered, visibleCount],
  );
  const ledgerItems = useMemo(
    () => buildLedgerItems(visible, { groupRelated: !patternActive }),
    [patternActive, visible],
  );

  useEffect(() => {
    if (!highlightedFinding?.requestedAt) {
      return;
    }
    const resolution = resolveExactActionRequest(
      ordered,
      requestedHighlightedIds,
    );
    setVoteFilter("all");
    setTypeFilter("all");
    setVisibleCount(INITIAL_BATCH);
    setActiveHighlightedIds(resolution.highlightedIds);
    setPatternActive(resolution.filter === "highlighted");
    setExpandedId(resolution.expandedId);
    setLinkedActionNotice(resolution.notice);
    window.requestAnimationFrame(() => {
      document.getElementById("vote-record")?.scrollIntoView({
        behavior: window.matchMedia?.("(prefers-reduced-motion: reduce)").matches
          ? "auto"
          : "smooth",
        block: "start",
      });
      headingRef.current?.focus({ preventScroll: true });
    });
  }, [highlightedFinding?.requestedAt, ordered, requestedHighlightedIds]);

  function clearPattern() {
    setPatternActive(false);
    setActiveHighlightedIds([]);
    setVoteFilter("all");
    setTypeFilter("all");
    setVisibleCount(INITIAL_BATCH);
    setExpandedId(null);
    setLinkedActionNotice("");
  }

  function chooseVoteFilter(value) {
    setVoteFilter(value);
    clearPatternState();
  }

  function chooseTypeFilter(value) {
    setTypeFilter(value);
    clearPatternState();
  }

  function clearPatternState() {
    setPatternActive(false);
    setActiveHighlightedIds([]);
    setVisibleCount(INITIAL_BATCH);
    setExpandedId(null);
    setLinkedActionNotice("");
  }

  return (
    <section className="scroll-mt-24 border-t border-stone-200 py-8 sm:py-10" id="vote-record">
      <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1">
        <h3
          className="font-serif text-3xl leading-tight text-stone-950"
          ref={headingRef}
          tabIndex="-1"
        >
          Vote record
        </h3>
        <p className="text-sm leading-6 text-stone-600">
          {ordered.length} recorded {ordered.length === 1 ? "action" : "actions"} · Newest first · Every vote remains individually expandable
        </p>
      </div>

      {linkedActionNotice ? (
        <p
          aria-live="polite"
          className="mt-5 rounded-lg border border-amber-300 bg-amber-50 p-4 text-sm leading-6 text-amber-950"
          role="status"
        >
          {linkedActionNotice}
        </p>
      ) : null}

      <div className="mt-5 flex flex-wrap gap-x-8 gap-y-4 border-y border-stone-200 py-4">
        <FilterGroup
          label="Vote"
          onChange={chooseVoteFilter}
          options={VOTE_FILTERS}
          selected={voteFilter}
        />
        <FilterGroup
          label="Type"
          onChange={chooseTypeFilter}
          options={TYPE_FILTERS}
          selected={typeFilter}
        />
      </div>

      {patternActive ? (
        <SelectedPatternStrip
          finding={highlightedFinding}
          matchCount={filtered.length}
          onClear={clearPattern}
          total={ordered.length}
        />
      ) : null}

      <p aria-live="polite" className="mt-4 text-sm text-stone-600" role="status">
        {patternActive
          ? `Showing ${visible.length} of ${filtered.length} matching votes.`
          : visible.length < filtered.length
            ? `Showing the first ${visible.length} of ${filtered.length} matching votes.`
            : `Showing all ${filtered.length} matching votes.`}
      </p>

      {ledgerItems.length ? (
        <div className="mt-4 overflow-hidden rounded-xl border border-stone-300 bg-white">
          {ledgerItems.map((item) => item.type === "group" ? (
            <RelatedActionGroup
              expandedId={expandedId}
              item={item}
              key={item.id}
              onToggle={setExpandedId}
              representativeName={representativeName}
            />
          ) : (
            <ActionReceipt
              expanded={expandedId === canonicalActionId(item.row)}
              highlighted={activeHighlightedIds.includes(canonicalActionId(item.row))}
              key={item.id || `${item.row.vote_date}-${item.row.rollcall_number}`}
              onToggle={() => setExpandedId(
                expandedId === canonicalActionId(item.row)
                  ? null
                  : canonicalActionId(item.row),
              )}
              representativeName={representativeName}
              row={item.row}
            />
          ))}
        </div>
      ) : (
        <p className="mt-5 rounded-xl border border-stone-200 bg-stone-50 p-4 text-base text-stone-700">
          No recorded actions match these filters.
        </p>
      )}

      {visible.length < filtered.length ? (
        <button
          className="secondary-button mt-6"
          onClick={() => setVisibleCount((count) => count + INITIAL_BATCH)}
          type="button"
        >
          Show more votes
        </button>
      ) : null}
    </section>
  );
}

function FilterGroup({ label, onChange, options, selected }) {
  return (
    <fieldset className="flex min-w-0 flex-wrap items-center gap-2">
      <legend className="float-left mr-2 py-3 text-sm font-semibold text-stone-900">
        {label}
      </legend>
      {options.map(([value, text]) => (
        <button
          aria-pressed={selected === value}
          className={`filter-button ${selected === value ? "filter-button-selected" : ""}`}
          key={value}
          onClick={() => onChange(value)}
          type="button"
        >
          {text}
        </button>
      ))}
    </fieldset>
  );
}

function SelectedPatternStrip({ finding, matchCount, onClear, total }) {
  const direction = finding?.direction || "mixed";
  const status = finding?.statusLabel || formatDirection(direction);
  const subject = patternSubject(finding?.label, direction);
  const accounting = direction === "mixed" && finding?.episodeCount
    ? `${matchCount} votes within ${finding.episodeCount} ${finding.episodeCount === 1 ? "legislative episode" : "legislative episodes"}`
    : `${matchCount} matching ${matchCount === 1 ? "vote" : "votes"}`;
  return (
    <div className={`pattern-strip pattern-strip-${direction} mt-4 flex flex-wrap items-center justify-between gap-3 px-4 py-3`}>
      <div className={`flex min-w-0 items-center gap-3 pattern-${direction}`}>
        <SemanticIcon kind={direction} />
        <p className="min-w-0 text-sm font-semibold leading-6 text-stone-900">
          <span className="semantic-label">{status}</span>
          <span aria-hidden="true"> · </span>
          <span>{subject}</span>
          <span aria-hidden="true"> · </span>
          <span className="font-medium text-stone-700">{accounting}</span>
        </p>
      </div>
      <button
        className="font-semibold text-teal-900 underline decoration-teal-800/30 underline-offset-4"
        onClick={onClear}
        type="button"
      >
        Show all {total} votes
      </button>
    </div>
  );
}

function RelatedActionGroup({
  expandedId,
  item,
  onToggle,
  representativeName,
}) {
  const composition = item.composition.positions
    .map(({ count, label }) => `${count} ${label}`)
    .join(" · ");
  return (
    <section className="border-b border-stone-300 last:border-b-0" data-testid="related-action-group">
      <header className="border-b border-stone-200 bg-stone-50 px-4 py-3 sm:px-5">
        <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
          <h4 className="text-base font-semibold leading-6 text-stone-950">{item.label}</h4>
          <span className="text-sm text-stone-600">· {item.rows.length} votes</span>
        </div>
        <p className="mt-1 text-sm leading-6 text-stone-600">
          {composition}
          {item.composition.controls
            ? ` · ${item.composition.controls} non-counting ${item.composition.controls === 1 ? "control" : "controls"}`
            : ""}
        </p>
      </header>
      <div>
        {item.rows.map((row) => {
          const actionId = canonicalActionId(row);
          return (
            <ActionReceipt
              expanded={expandedId === actionId}
              highlighted={false}
              key={actionId || `${row.vote_date}-${row.rollcall_number}`}
              onToggle={() => onToggle(expandedId === actionId ? null : actionId)}
              representativeName={representativeName}
              row={row}
            />
          );
        })}
      </div>
    </section>
  );
}

function patternSubject(label, direction) {
  const value = String(label || "Pattern");
  if (direction === "opposition") {
    return value.replace(/^Opposition to\s+/i, "");
  }
  if (direction === "support") {
    return value.replace(/^Support for\s+/i, "");
  }
  return value;
}

function formatDirection(direction) {
  return { opposition: "Opposition", support: "Support", mixed: "Mixed" }[direction]
    || "Pattern";
}
