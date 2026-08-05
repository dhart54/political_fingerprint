"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import ActionReceipt from "./ActionReceipt";
import {
  canonicalActionId,
  chronologicalActions,
  filterActions,
  resolveExactActionRequest,
} from "../lib/frontendPassA.mjs";
import {
  buildLedgerItems,
  completeVisibleRows,
} from "../lib/selectedIssueExperience.mjs";

const INITIAL_BATCH = 12;
const FILTERS = [
  ["all", "All"],
  ["yea", "Yea"],
  ["nay", "Nay"],
  ["non_directional", "Present / Not Voting"],
  ["substantive", "Substantive"],
  ["procedural_context", "Procedural / context"],
];

export default function ChronologicalActionLedger({
  highlightedFinding,
  rows = [],
}) {
  const [filter, setFilter] = useState("all");
  const [visibleCount, setVisibleCount] = useState(INITIAL_BATCH);
  const [expandedId, setExpandedId] = useState(null);
  const [activeHighlightedIds, setActiveHighlightedIds] = useState([]);
  const [linkedActionNotice, setLinkedActionNotice] = useState("");
  const headingRef = useRef(null);
  const ordered = useMemo(() => chronologicalActions(rows), [rows]);
  const requestedHighlightedIds = useMemo(
    () => highlightedFinding?.actionIds || [],
    [highlightedFinding?.actionIds],
  );
  const filtered = useMemo(
    () => filterActions(ordered, filter, activeHighlightedIds),
    [activeHighlightedIds, filter, ordered],
  );
  const visible = useMemo(
    () => completeVisibleRows(filtered, visibleCount),
    [filtered, visibleCount],
  );
  const ledgerItems = useMemo(
    () => buildLedgerItems(visible, { groupRelated: filter !== "highlighted" }),
    [filter, visible],
  );

  useEffect(() => {
    if (!highlightedFinding?.requestedAt) {
      return;
    }
    const resolution = resolveExactActionRequest(
      ordered,
      requestedHighlightedIds,
    );
    setFilter(resolution.filter);
    setVisibleCount(INITIAL_BATCH);
    setActiveHighlightedIds(resolution.highlightedIds);
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

  function chooseFilter(value) {
    setFilter(value);
    setVisibleCount(INITIAL_BATCH);
    setExpandedId(null);
    setActiveHighlightedIds([]);
    setLinkedActionNotice("");
  }

  return (
    <section className="scroll-mt-24 border-t border-stone-200 py-10 sm:py-12" id="vote-record">
      <p className="eyebrow">Exact vote receipts</p>
      <h3
        className="mt-2 font-serif text-3xl leading-tight text-stone-950"
        ref={headingRef}
        tabIndex="-1"
      >
        Chronological action ledger
      </h3>
      <p className="mt-3 max-w-3xl text-base leading-7 text-stone-700">
        {ordered.length} recorded {ordered.length === 1 ? "action" : "actions"}. Newest first; every action remains independently expandable.
      </p>

      {linkedActionNotice ? (
        <p
          aria-live="polite"
          className="mt-5 rounded-xl border border-amber-300 bg-amber-50 p-4 text-sm leading-6 text-amber-950"
          role="status"
        >
          {linkedActionNotice}
        </p>
      ) : null}

      {filter === "highlighted" ? (
        <div className="mt-5 rounded-xl border border-teal-900/20 bg-teal-50 p-4 text-sm leading-6 text-teal-950">
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-teal-800">
            Selected pattern
          </p>
          <p className="mt-1 text-base font-semibold leading-7">
            {highlightedFinding?.label || "Exact actions"}
          </p>
          <p className="mt-1">
            Showing {filtered.length} exact {filtered.length === 1 ? "action" : "actions"}
            {highlightedFinding?.episodeCount
              ? ` across ${highlightedFinding.episodeCount} ${highlightedFinding.episodeCount === 1 ? "policy episode" : "policy episodes"}`
              : ""}.
            {highlightedFinding?.direction === "mixed"
              ? " Together they form a mixed episode; no single action or stage is presented as the complete episode."
              : " These actions are the bounded evidence for this pattern, not the complete issue record."}
            {" "}The first receipt is open below.
          </p>
          <button
            className="mt-2 font-semibold underline underline-offset-4"
            onClick={() => chooseFilter("all")}
            type="button"
          >
            Return to all {ordered.length} actions
          </button>
        </div>
      ) : (
        <div
          aria-label="Vote record filters"
          className="mt-5 flex flex-wrap gap-2"
          role="group"
        >
          {FILTERS.map(([value, label]) => (
            <button
              aria-pressed={filter === value}
              className={`filter-button ${filter === value ? "filter-button-selected" : ""}`}
              key={value}
              onClick={() => chooseFilter(value)}
              type="button"
            >
              {label}
            </button>
          ))}
        </div>
      )}

      <p aria-live="polite" className="mt-4 text-sm text-stone-600" role="status">
        {filter === "all"
          ? visible.length < filtered.length
            ? `Showing the first ${visible.length}. Each action has an expandable exact vote receipt.`
            : `Showing all ${filtered.length} actions. Each action has an expandable exact vote receipt.`
          : `Showing ${visible.length} of ${filtered.length} matching actions.`}
      </p>

      {ledgerItems.length ? (
        <div className="mt-4 border-t border-stone-200">
          {ledgerItems.map((item) => item.type === "group" ? (
            <RelatedActionGroup
              expandedId={expandedId}
              item={item}
              key={item.id}
              onToggle={setExpandedId}
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
              row={item.row}
            />
          ))}
        </div>
      ) : (
        <p className="mt-5 rounded-xl border border-stone-200 bg-stone-50 p-4 text-base text-stone-700">
          No recorded actions match this filter.
        </p>
      )}

      {visible.length < filtered.length ? (
        <button
          className="secondary-button mt-6"
          onClick={() => setVisibleCount((count) => count + INITIAL_BATCH)}
          type="button"
        >
          Show more actions
        </button>
      ) : null}
    </section>
  );
}

function RelatedActionGroup({ expandedId, item, onToggle }) {
  const composition = item.composition.positions
    .map(({ count, label }) => `${count} ${label}`)
    .join(" · ");
  return (
    <details className="border-b border-stone-300 bg-stone-50/60" data-testid="related-action-group" open>
      <summary className="cursor-pointer px-3 py-5 sm:px-5">
        <span className="block text-xs font-semibold uppercase tracking-[0.12em] text-stone-500">
          Related actions · {item.rows.length} individual votes
        </span>
        <span className="mt-1 block text-lg font-semibold leading-7 text-stone-950">
          {item.label}
        </span>
        <span className="mt-1 block text-sm leading-6 text-stone-600">
          {composition}
          {item.composition.controls
            ? ` · ${item.composition.controls} governed non-counting ${item.composition.controls === 1 ? "control" : "controls"}`
            : ""}
        </span>
        <span className="mt-1 block text-xs leading-5 text-stone-500">
          This is a navigation group, not an aggregate vote. Each action remains separate below.
        </span>
      </summary>
      <div className="border-t border-stone-200 bg-white pl-3 sm:pl-6">
        {item.rows.map((row) => {
          const actionId = canonicalActionId(row);
          return (
            <ActionReceipt
              expanded={expandedId === actionId}
              highlighted={false}
              key={actionId || `${row.vote_date}-${row.rollcall_number}`}
              onToggle={() => onToggle(expandedId === actionId ? null : actionId)}
              row={row}
            />
          );
        })}
      </div>
    </details>
  );
}
