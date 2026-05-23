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
          status: "ready",
          payload: buildFallbackAlignmentPayload({
            legislatorId: legislator.id,
            preferences,
          }),
          error: null,
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
            : "For neutral issue checks, the app shows reviewed records without calling them aligned or not aligned. Alignment labels appear only when you choose a direction."}
        </p>
      </div>

      {state.status === "error" ? (
        <p className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm leading-6 text-rose-700">
          {state.error}
        </p>
      ) : null}

      {state.status === "idle" ? (
        <div className="mt-5 rounded-[1.25rem] border border-dashed border-stone-300 bg-stone-50 px-4 py-5 text-sm leading-6 text-stone-600">
          Select at least one issue to inspect interpreted records. Choose a direction only when you want an aligned or not-aligned label.
        </div>
      ) : null}

      {state.status === "loading" ? (
        <div className="mt-5 rounded-[1.25rem] border border-stone-200 bg-stone-50 px-4 py-5 text-sm leading-6 text-stone-600">
          Checking interpreted votes for the selected issues...
        </div>
      ) : null}

      {state.status === "ready" && rows.length === 0 ? (
        <div className="mt-5 rounded-[1.25rem] border border-stone-200 bg-stone-50 px-4 py-5 text-sm leading-6 text-stone-700">
          The selected issues did not return alignment rows yet. The voting record below is still available for direct inspection.
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
                    {formatDisplayLabel(row)}
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

function buildFallbackAlignmentPayload({ legislatorId, preferences }) {
  return {
    legislator_id: legislatorId,
    preferences,
    alignment: Object.entries(preferences).map(([domain, preference]) => ({
      domain,
      preference,
      label: "insufficient_evidence",
      aligned_count: 0,
      not_aligned_count: 0,
      interpreted_count: 0,
      ambiguous_count: 0,
      evidence_count: 0,
      evidence_roll_call_ids: [],
    })),
  };
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
  const directionalRows = rows.filter((row) => row.preference !== "show_record");
  const recordOnly = rows.filter((row) => row.preference === "show_record" && row.label !== "insufficient_evidence").length;
  const aligned = directionalRows.filter((row) => row.label === "aligned").length;
  const notAligned = directionalRows.filter((row) => row.label === "not_aligned").length;
  const mixed = directionalRows.filter((row) => row.label === "mixed").length;
  const insufficient = rows.filter((row) => row.label === "insufficient_evidence").length;
  const recordOnlyText = recordOnly ? `${recordOnly} record shown, ` : "";
  return `${recordOnlyText}${aligned} aligned, ${notAligned} not aligned, ${mixed} mixed, ${insufficient} insufficient.`;
}

function buildRowCopy(row) {
  if (row.label === "insufficient_evidence") {
    return "This issue does not yet have enough source-grounded vote meaning to label alignment. Use Inspect Votes to review any classified roll calls behind the issue.";
  }
  if (row.preference === "show_record") {
    return `${row.interpreted_count} interpreted ${row.interpreted_count === 1 ? "vote is" : "votes are"} available for inspection. No for/against preference was selected, so this is a record view rather than an alignment label.`;
  }
  if (row.label === "mixed") {
    return `${row.aligned_count} aligned and ${row.not_aligned_count} not aligned interpreted votes, so the record is split for this issue.`;
  }
  return `${row.aligned_count} aligned and ${row.not_aligned_count} not aligned interpreted votes. ${row.ambiguous_count} votes stayed out of the label.`;
}

function formatDisplayLabel(row) {
  if (row.preference === "show_record" && row.label !== "insufficient_evidence") {
    return "Record shown";
  }

  return formatAlignmentLabel(row.label);
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
