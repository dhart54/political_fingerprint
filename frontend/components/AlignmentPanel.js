"use client";

import { useEffect, useState } from "react";

import { fetchAlignment } from "../lib/api";
import { formatDomainLabel } from "../lib/issueDomains";
import { getDirectionalAlignmentPreferences } from "../lib/profileNarrative.mjs";

export default function AlignmentPanel({ legislator, preferences, onInspectDomain, scope = "all" }) {
  const [state, setState] = useState({
    status: "idle",
    payload: null,
    error: null,
  });

  const selectedCount = Object.keys(preferences).length;
  const directionalPreferences = getDirectionalAlignmentPreferences(preferences);
  const directionalCount = Object.keys(directionalPreferences).length;

  useEffect(() => {
    let active = true;

    if (directionalCount === 0) {
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
          preferences: directionalPreferences,
          scope,
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
            preferences: directionalPreferences,
          }),
          error: null,
        });
      }
    }

    loadAlignment();

    return () => {
      active = false;
    };
  }, [legislator.id, preferences, directionalCount, scope]);

  const rows = state.payload?.alignment || [];

  if (selectedCount === 0 || directionalCount === 0) {
    return null;
  }

  return (
    <section className="mt-4 rounded-2xl border border-stone-200 bg-white px-4 py-4 shadow-[0_10px_28px_rgba(15,23,42,0.06)] lg:px-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.22em] text-cyan-800">
            Selected Issue Records
          </p>
          <h3 className="mt-1 max-w-[760px] font-serif text-[1.55rem] leading-[1.05] text-stone-950 sm:text-[2rem]">
            {buildHeadline({ status: state.status, selectedCount: directionalCount, rows, name: legislator.name_display })}
          </h3>
        </div>
        <p className="max-w-md text-sm leading-6 text-stone-600">
          {directionalCount === 0
            ? "Choose issue areas above to inspect reviewed records."
            : `This section compares only your concrete for-or-against reviewed-measure choices with interpreted votes in the ${formatScopeLabel(state.payload?.scope_metadata, scope)} view.`}
        </p>
      </div>

      {state.status === "error" ? (
        <p className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm leading-6 text-rose-700">
          {state.error}
        </p>
      ) : null}

      {state.status === "loading" ? (
        <div className="mt-4 rounded-xl border border-stone-200 bg-stone-50 px-3 py-3 text-sm leading-6 text-stone-600">
          Checking interpreted votes for the selected issues...
        </div>
      ) : null}

      {state.status === "ready" && rows.length === 0 ? (
        <div className="mt-4 rounded-xl border border-stone-200 bg-stone-50 px-3 py-3 text-sm leading-6 text-stone-700">
          The selected issues did not return alignment rows yet. The voting record below is still available for direct inspection.
        </div>
      ) : null}

      {state.status === "ready" && rows.length > 0 ? (
        <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
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

function formatScopeLabel(metadata, scope) {
  if (metadata?.scope_label) {
    return metadata.scope_label.toLowerCase();
  }
  if (scope === "119") {
    return "recent Congress";
  }
  if (scope === "118") {
    return "prior Congress";
  }
  return "full record";
}

function buildHeadline({ status, selectedCount, rows, name }) {
  if (selectedCount === 0) {
    return "Choose issue areas to inspect.";
  }
  if (status === "loading") {
    return `Checking ${name}'s interpreted votes...`;
  }
  if (status === "error") {
    return "Alignment check unavailable.";
  }
  const directionalRows = rows.filter((row) => row.preference !== "show_record");
  const recordOnly = rows.filter((row) => row.preference === "show_record" && row.label !== "insufficient_evidence").length;
  const allRecordOnly = rows.length > 0 && directionalRows.length === 0;
  if (allRecordOnly) {
    const insufficientOnly = rows.filter((row) => row.label === "insufficient_evidence").length;
    return `${recordOnly} reviewed ${recordOnly === 1 ? "record" : "records"} shown, ${insufficientOnly} insufficient ${insufficientOnly === 1 ? "issue" : "issues"}.`;
  }
  const aligned = directionalRows.filter((row) => row.label === "aligned").length;
  const notAligned = directionalRows.filter((row) => row.label === "not_aligned").length;
  const mixed = directionalRows.filter((row) => row.label === "mixed").length;
  const insufficient = rows.filter((row) => row.label === "insufficient_evidence").length;
  const recordOnlyText = recordOnly ? `${recordOnly} reviewed ${recordOnly === 1 ? "record" : "records"}, ` : "";
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
    return "Evidence available";
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
