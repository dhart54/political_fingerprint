"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import ActionReceipt from "./ActionReceipt";
import {
  canonicalActionId,
  chronologicalActions,
  filterActions,
} from "../lib/frontendPassA.mjs";

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
  const headingRef = useRef(null);
  const ordered = useMemo(() => chronologicalActions(rows), [rows]);
  const highlightedIds = useMemo(
    () => highlightedFinding?.actionIds || [],
    [highlightedFinding?.actionIds],
  );
  const filtered = useMemo(
    () => filterActions(ordered, filter, highlightedIds),
    [filter, highlightedIds, ordered],
  );
  const visible = filtered.slice(0, visibleCount);

  useEffect(() => {
    if (!highlightedFinding?.requestedAt) {
      return;
    }
    const matching = filterActions(ordered, "highlighted", highlightedIds);
    setFilter("highlighted");
    setVisibleCount(INITIAL_BATCH);
    setExpandedId(matching.length ? canonicalActionId(matching[0]) : null);
    window.requestAnimationFrame(() => {
      document.getElementById("vote-record")?.scrollIntoView({
        behavior: window.matchMedia?.("(prefers-reduced-motion: reduce)").matches
          ? "auto"
          : "smooth",
        block: "start",
      });
      headingRef.current?.focus({ preventScroll: true });
    });
  }, [highlightedFinding?.requestedAt, highlightedIds, ordered]);

  function chooseFilter(value) {
    setFilter(value);
    setVisibleCount(INITIAL_BATCH);
    setExpandedId(null);
  }

  return (
    <section className="scroll-mt-24 border-t border-stone-200 py-10" id="vote-record">
      <p className="eyebrow">Exact vote receipts</p>
      <h3
        className="mt-2 font-serif text-3xl leading-tight text-stone-950"
        ref={headingRef}
        tabIndex="-1"
      >
        Chronological action ledger
      </h3>
      <p className="mt-3 max-w-3xl text-base leading-7 text-stone-700">
        Newest actions appear first. All {ordered.length} recorded {ordered.length === 1 ? "action remains" : "actions remain"} available.
      </p>

      {filter === "highlighted" ? (
        <div className="mt-5 rounded-xl border border-teal-900/20 bg-teal-50 p-4 text-sm leading-6 text-teal-950">
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-teal-800">
            Selected reviewed finding
          </p>
          <p className="mt-1 text-base font-semibold leading-7">
            {highlightedFinding?.label || "Exact actions"}
          </p>
          <p className="mt-1">
            Showing {filtered.length} exact {filtered.length === 1 ? "action" : "actions"} supplied for this bounded finding.
            {" "}The first receipt is open below. These actions are not presented as the complete issue record.
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
        Showing {Math.min(visible.length, filtered.length)} of {filtered.length} matching actions
        {filter === "all" ? ` (${ordered.length} total)` : ""}.
      </p>

      {visible.length ? (
        <div className="mt-4 border-t border-stone-200">
          {visible.map((row) => {
            const actionId = canonicalActionId(row);
            return (
              <ActionReceipt
                expanded={expandedId === actionId}
                highlighted={highlightedIds.includes(actionId)}
                key={actionId || `${row.vote_date}-${row.rollcall_number}`}
                onToggle={() => setExpandedId(expandedId === actionId ? null : actionId)}
                row={row}
              />
            );
          })}
        </div>
      ) : (
        <p className="mt-5 rounded-xl border border-stone-200 bg-stone-50 p-4 text-base text-stone-700">
          No recorded actions match this filter.
        </p>
      )}

      {visibleCount < filtered.length ? (
        <button
          className="secondary-button mt-6"
          onClick={() => setVisibleCount((count) => count + INITIAL_BATCH)}
          type="button"
        >
          Show {Math.min(INITIAL_BATCH, filtered.length - visibleCount)} more
        </button>
      ) : null}
    </section>
  );
}
