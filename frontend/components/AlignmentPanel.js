"use client";

import { useEffect, useState } from "react";

import { fetchAlignment } from "../lib/api";

export default function AlignmentPanel({ legislator, preferences, onInspectDomain }) {
  const [state, setState] = useState({
    status: "idle",
    payload: null,
    error: null,
  });

  const selectedCount = Object.keys(preferences).length;

  useEffect(() => {
    let active = true;

    if (selectedCount === 0) {
      setState({
        status: "idle",
        payload: null,
        error: null,
      });
      return () => {
        active = false;
      };
    }

    async function loadAlignment() {
      setState({
        status: "loading",
        payload: null,
        error: null,
      });

      try {
        const payload = await fetchAlignment({
          legislatorId: legislator.id,
          preferences,
        });
        if (!active) {
          return;
        }
        setState({
          status: "ready",
          payload,
          error: null,
        });
      } catch (error) {
        if (!active) {
          return;
        }
        setState({
          status: "error",
          payload: null,
          error: "Alignment is unavailable for this record right now.",
        });
      }
    }

    loadAlignment();

    return () => {
      active = false;
    };
  }, [legislator.id, preferences, selectedCount]);

  const rows = state.payload?.alignment || [];

  return (
    <section className="mt-4 rounded-[2rem] border border-stone-200 bg-white px-5 py-5 shadow-[0_16px_40px_rgba(15,23,42,0.08)] lg:px-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-cyan-800">
            Your Issues vs This Record
          </p>
          <h3 className="mt-2 max-w-[760px] font-serif text-[2rem] leading-[1] text-stone-950 sm:text-[2.45rem] sm:leading-[0.98]">
            {buildHeadline({ status: state.status, selectedCount, rows, name: legislator.name_display })}
          </h3>
        </div>
        <p className="max-w-md text-sm leading-6 text-stone-600">
          {selectedCount === 0
            ? "Choose issues above to check this voting record against your stated preferences."
            : "Labels are based only on interpreted votes. Mixed and insufficient-evidence labels keep unclear records visible without forcing a conclusion."}
        </p>
      </div>

      {state.status === "error" ? (
        <p className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm leading-6 text-rose-700">
          {state.error}
        </p>
      ) : null}

      {state.status === "idle" ? (
        <div className="mt-5 rounded-[1.25rem] border border-dashed border-stone-300 bg-stone-50 px-4 py-5 text-sm leading-6 text-stone-600">
          Select at least one issue to see whether the current interpreted record is aligned, not aligned, mixed, or still missing enough evidence.
        </div>
      ) : null}

      {state.status === "loading" ? (
        <div className="mt-5 rounded-[1.25rem] border border-stone-200 bg-stone-50 px-4 py-5 text-sm leading-6 text-stone-600">
          Checking interpreted votes for the selected issues...
        </div>
      ) : null}

      {state.status === "ready" && rows.length === 0 ? (
        <div className="mt-5 rounded-[1.25rem] border border-stone-200 bg-stone-50 px-4 py-5 text-sm leading-6 text-stone-700">
          No issue rows came back for this selection. The record remains available below, but this alignment check does not have enough structured data yet.
        </div>
      ) : null}

      {state.status === "ready" && rows.length > 0 ? (
        <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          {rows.map((row) => (
            <article
              className="rounded-[1.25rem] border border-stone-200 bg-stone-50 px-4 py-4"
              key={row.domain}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-xs uppercase tracking-[0.22em] text-stone-500">
                    {formatDomainLabel(row.domain)}
                  </p>
                  <p className="mt-3 text-[1.55rem] leading-none text-stone-950">
                    {formatAlignmentLabel(row.label)}
                  </p>
                </div>
                <span className={`rounded-full px-3 py-1 text-[11px] uppercase tracking-[0.18em] ${getLabelClass(row.label)}`}>
                  {row.interpreted_count} interpreted
                </span>
              </div>
              <p className="mt-3 text-sm leading-6 text-stone-700">
                {buildRowCopy(row)}
              </p>
              <button
                className="mt-4 rounded-full bg-stone-900 px-4 py-2 text-xs uppercase tracking-[0.2em] text-stone-100"
                onClick={() => onInspectDomain?.(row.domain)}
                type="button"
              >
                Inspect Votes
              </button>
            </article>
          ))}
        </div>
      ) : null}
    </section>
  );
}

function buildHeadline({ status, selectedCount, rows, name }) {
  if (selectedCount === 0) {
    return "Choose your issues, then check the record.";
  }
  if (status === "loading") {
    return `Checking ${name}'s interpreted votes...`;
  }
  if (status === "error") {
    return "Alignment check unavailable.";
  }
  const aligned = rows.filter((row) => row.label === "aligned").length;
  const notAligned = rows.filter((row) => row.label === "not_aligned").length;
  const mixed = rows.filter((row) => row.label === "mixed").length;
  const insufficient = rows.filter((row) => row.label === "insufficient_evidence").length;
  return `${aligned} aligned, ${notAligned} not aligned, ${mixed} mixed, ${insufficient} insufficient.`;
}

function buildRowCopy(row) {
  if (row.label === "insufficient_evidence") {
    return "No interpreted vote-meaning rows are available for this issue yet. Use Inspect Votes to review the classified roll calls behind the read.";
  }
  if (row.label === "mixed") {
    return `${row.aligned_count} aligned and ${row.not_aligned_count} not aligned interpreted votes, so the record is split for this issue.`;
  }
  if (row.preference === "show_record") {
    return `${row.interpreted_count} interpreted votes are available for inspection.`;
  }
  return `${row.aligned_count} aligned and ${row.not_aligned_count} not aligned interpreted votes. ${row.ambiguous_count} votes stayed out of the label.`;
}

function formatAlignmentLabel(label) {
  if (label === "not_aligned") {
    return "Not aligned";
  }
  if (label === "insufficient_evidence") {
    return "Insufficient evidence";
  }
  return label[0].toUpperCase() + label.slice(1);
}

function getLabelClass(label) {
  if (label === "aligned") {
    return "bg-emerald-100 text-emerald-800";
  }
  if (label === "not_aligned") {
    return "bg-rose-100 text-rose-800";
  }
  if (label === "mixed") {
    return "bg-amber-100 text-amber-800";
  }
  return "bg-stone-200 text-stone-700";
}

function formatDomainLabel(domain) {
  return String(domain)
    .split("_")
    .map((segment) => segment[0] + segment.slice(1).toLowerCase())
    .join(" ");
}
