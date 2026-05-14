"use client";

import { useEffect, useState } from "react";

import { fetchPositionEvidence, fetchPositions } from "../lib/api";

export default function PositionByIssue({
  evidenceRequest = null,
  legislatorId = "leg_alex_morgan",
  title = "How They Vote By Issue",
}) {
  const [state, setState] = useState({
    status: "loading",
    payload: null,
    error: null,
  });
  const [selectedDomain, setSelectedDomain] = useState(null);
  const [evidenceState, setEvidenceState] = useState({
    status: "idle",
    payload: null,
    error: null,
  });

  useEffect(() => {
    let active = true;

    async function loadPositions() {
      try {
        const payload = await fetchPositions({ legislatorId });
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
          error: "Vote-direction data is unavailable for this legislator right now.",
        });
      }
    }

    loadPositions();

    return () => {
      active = false;
    };
  }, [legislatorId]);

  useEffect(() => {
    if (!evidenceRequest?.domain) {
      return;
    }

    inspectDomain(evidenceRequest.domain);
    const element = document.getElementById("position-evidence");
    element?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  }, [evidenceRequest?.requestedAt]);

  useEffect(() => {
    setSelectedDomain(null);
    setEvidenceState({
      status: "idle",
      payload: null,
      error: null,
    });
  }, [legislatorId]);

  const rows = (state.payload?.positions || [])
    .filter((row) => row.recorded_votes > 0)
    .sort((left, right) => right.recorded_votes - left.recorded_votes || right.yea_share - left.yea_share)
    .slice(0, 6);
  const takeaway = buildTakeaway(rows);
  const selectedRow = rows.find((row) => row.domain === selectedDomain) || rows[0] || null;

  async function inspectDomain(domain) {
    setSelectedDomain(domain);
    setEvidenceState({
      status: "loading",
      payload: null,
      error: null,
    });

    try {
      const payload = await fetchPositionEvidence({ legislatorId, domain });
      setEvidenceState({
        status: "ready",
        payload,
        error: null,
      });
    } catch (error) {
      setEvidenceState({
        status: "error",
        payload: null,
        error: "The vote evidence for this issue is unavailable right now.",
      });
    }
  }

  return (
    <section id="position-by-issue" className="mt-8 rounded-[2rem] border border-stone-200 bg-white p-5 shadow-[0_18px_48px_rgba(15,23,42,0.1)] lg:p-6">
      <div className="grid gap-5 lg:grid-cols-[0.9fr_1.1fr]">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-cyan-800">
            First Read
          </p>
          <h3 className="mt-2 font-serif text-[2.7rem] leading-[0.95] text-stone-950">
            {title}
          </h3>
          <p className="mt-3 max-w-xl text-[18px] leading-8 text-stone-900">
            {state.status === "ready"
              ? takeaway
              : state.status === "loading"
                ? "Reading how this legislator voted inside their most active issue domains."
                : "The site cannot read how this legislator voted inside issue domains right now."}
          </p>
          <div className="mt-4 rounded-[1.5rem] bg-stone-950 px-4 py-4 text-stone-100">
            <p className="text-xs uppercase tracking-[0.28em] text-stone-400">
              How To Read This
            </p>
            <p className="mt-2 text-[15px] leading-7 text-stone-200">
              Each tile starts with the domains where this legislator has the most recorded votes, then shows the yea/nay split inside that domain. It is descriptive, not a score.
            </p>
          </div>
        </div>

        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {state.status === "error" ? (
            <div className="rounded-[1.5rem] border border-rose-200 bg-rose-50 px-4 py-4 text-sm text-rose-700 md:col-span-2 xl:col-span-3">
              {state.error}
            </div>
          ) : null}
          {state.status === "ready" && rows.length === 0 ? (
            <div className="rounded-[1.5rem] border border-stone-200 bg-stone-50 px-4 py-4 text-sm text-stone-600 md:col-span-2 xl:col-span-3">
              No recorded yea/nay splits are available in the current window.
            </div>
          ) : null}
          {rows.map((row) => (
            <button
              className={`rounded-[1.25rem] border px-4 py-4 text-left shadow-[inset_0_1px_0_rgba(255,255,255,0.72)] transition ${
                selectedDomain === row.domain
                  ? "border-cyan-800 bg-cyan-50"
                  : "border-stone-200 bg-stone-50 hover:border-cyan-700/50"
              }`}
              key={row.domain}
              onClick={() => inspectDomain(row.domain)}
              type="button"
            >
              <div className="flex items-start justify-between gap-3">
                <p className="max-w-[200px] text-[16px] leading-7 text-stone-900">
                  {formatDomainLabel(row.domain)}
                </p>
                <p className="text-sm text-stone-500">{row.recorded_votes} votes</p>
              </div>
              <div className="mt-3 flex items-center justify-between gap-3">
                <span className={`rounded-full px-3 py-1 text-[11px] uppercase tracking-[0.22em] ${getPositionBadgeClass(row)}`}>
                  {getPositionLabel(row)}
                </span>
                <p className="text-[13px] text-stone-600">
                  {buildPositionRead(row)}
                </p>
              </div>
              <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
                <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-3">
                  <p className="text-[11px] uppercase tracking-[0.22em] text-emerald-700">Yea</p>
                  <p className="mt-2 text-[1.45rem] leading-none text-stone-900">
                    {(row.yea_share * 100).toFixed(0)}%
                  </p>
                </div>
                <div className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-3">
                  <p className="text-[11px] uppercase tracking-[0.22em] text-rose-700">Nay</p>
                  <p className="mt-2 text-[1.45rem] leading-none text-stone-900">
                    {(row.nay_share * 100).toFixed(0)}%
                  </p>
                </div>
              </div>
              <div className="mt-4 h-3 overflow-hidden rounded-full bg-stone-200">
                <div className="flex h-full w-full">
                  <div
                    className="bg-emerald-500"
                    style={{ width: `${row.yea_share * 100}%` }}
                  />
                  <div
                    className="bg-rose-500"
                    style={{ width: `${row.nay_share * 100}%` }}
                  />
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      <EvidencePanel
        evidenceState={evidenceState}
        onInspectDomain={inspectDomain}
        selectedRow={selectedRow}
      />
    </section>
  );
}

function EvidencePanel({ evidenceState, onInspectDomain, selectedRow }) {
  if (!selectedRow) {
    return null;
  }

  const evidenceRows = evidenceState.payload?.evidence || [];
  const isSelected = evidenceState.payload?.domain === selectedRow.domain;

  return (
    <div id="position-evidence" className="mt-5 scroll-mt-6 rounded-[1.5rem] border border-stone-200 bg-stone-50 px-4 py-4 lg:px-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.28em] text-stone-500">
            Evidence
          </p>
          <h4 className="mt-2 font-serif text-[2rem] leading-none text-stone-950">
            {formatDomainLabel(selectedRow.domain)}
          </h4>
        </div>
        <button
          className="rounded-full bg-stone-900 px-4 py-2 text-xs uppercase tracking-[0.22em] text-stone-100"
          onClick={() => onInspectDomain(selectedRow.domain)}
          type="button"
        >
          Show Votes
        </button>
      </div>

      {evidenceState.status === "idle" ? (
        <p className="mt-4 text-sm leading-7 text-stone-700">
          Select an issue card or use Show Votes to inspect the roll calls behind this read.
        </p>
      ) : null}
      {evidenceState.status === "loading" ? (
        <p className="mt-4 text-sm leading-7 text-stone-700">
          Loading underlying votes...
        </p>
      ) : null}
      {evidenceState.status === "error" ? (
        <p className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm leading-6 text-rose-700">
          {evidenceState.error}
        </p>
      ) : null}
      {evidenceState.status === "ready" && isSelected && evidenceRows.length === 0 ? (
        <p className="mt-4 rounded-2xl border border-stone-200 bg-white px-4 py-3 text-sm leading-6 text-stone-700">
          No underlying vote rows are available for this issue in the current window.
        </p>
      ) : null}
      {evidenceState.status === "ready" && isSelected && evidenceRows.length > 0 ? (
        <div className="mt-4 grid gap-3">
          {evidenceRows.map((row) => (
            <article
              className="rounded-[1.1rem] border border-stone-200 bg-white px-4 py-4"
              key={`${row.roll_call_id}-${row.position}`}
            >
              <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                <div>
                  <p className="text-xs uppercase tracking-[0.24em] text-stone-500">
                    {formatDate(row.vote_date)} - {formatChamber(row.chamber)} Roll {row.rollcall_number}
                  </p>
                  <h5 className="mt-2 text-[17px] leading-7 text-stone-950">
                    {row.bill_title || row.question}
                  </h5>
                  <p className="mt-2 text-sm leading-6 text-stone-700">
                    {row.description}
                  </p>
                </div>
                <span className={`w-fit rounded-full px-3 py-1 text-xs uppercase tracking-[0.2em] ${getVoteBadgeClass(row.position)}`}>
                  {formatVotePosition(row.position)}
                </span>
              </div>
              <div className="mt-3 grid gap-3 sm:grid-cols-2">
                <Meta label="Classification" value={row.classification_reason} />
                <Meta label="Source" value={row.source_url || "No source URL"} />
              </div>
            </article>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function formatDomainLabel(domain) {
  return String(domain)
    .split("_")
    .map((segment) => segment[0] + segment.slice(1).toLowerCase())
    .join(" ");
}

function formatChamber(chamber) {
  return chamber ? chamber[0].toUpperCase() + chamber.slice(1) : "";
}

function formatDate(value) {
  if (!value) {
    return "Unknown date";
  }
  return String(value).slice(0, 10);
}

function formatVotePosition(position) {
  if (position === "not_voting") {
    return "Not voting";
  }
  return String(position)
    .split("_")
    .map((segment) => segment[0].toUpperCase() + segment.slice(1))
    .join(" ");
}

function getVoteBadgeClass(position) {
  if (position === "yea") {
    return "bg-emerald-100 text-emerald-800";
  }
  if (position === "nay") {
    return "bg-rose-100 text-rose-800";
  }
  return "bg-stone-200 text-stone-700";
}

function Meta({ label, value }) {
  return (
    <div className="rounded-xl border border-stone-200 bg-stone-50 px-3 py-3">
      <p className="text-xs uppercase tracking-[0.2em] text-stone-500">{label}</p>
      <p className="mt-2 break-words text-sm leading-6 text-stone-700">{value}</p>
    </div>
  );
}

function buildTakeaway(rows) {
  if (!rows.length) {
    return "There are not enough recorded yea and nay votes in the current window to show a clear position pattern by issue.";
  }

  const strongest = rows[0];
  const leaning = strongest.yea_share >= strongest.nay_share ? "more often voted yea" : "more often voted nay";
  const leaningShare = Math.max(strongest.yea_share, strongest.nay_share);
  const second = rows[1];

  if (second) {
    return `In the strongest recorded domains, this legislator ${leaning} on ${formatDomainLabel(strongest.domain)} (${(leaningShare * 100).toFixed(
      0,
    )}%) and also shows recorded positions in ${formatDomainLabel(second.domain)}.`;
  }

  return `The clearest recorded position pattern in this window is ${formatDomainLabel(strongest.domain)}, where this legislator ${leaning} ${(leaningShare * 100).toFixed(
    0,
  )}% of the time.`;
}

function getPositionLabel(row) {
  const gap = Math.abs(row.yea_share - row.nay_share);
  if (gap < 0.15) {
    return "Mixed";
  }

  return row.yea_share >= row.nay_share ? "Leans Yea" : "Leans Nay";
}

function getPositionBadgeClass(row) {
  const label = getPositionLabel(row);
  if (label === "Leans Yea") {
    return "bg-emerald-100 text-emerald-800";
  }
  if (label === "Leans Nay") {
    return "bg-rose-100 text-rose-800";
  }
  return "bg-stone-200 text-stone-700";
}

function buildPositionRead(row) {
  const label = getPositionLabel(row);
  if (label === "Mixed") {
    return `${(row.yea_share * 100).toFixed(0)}% yea / ${(row.nay_share * 100).toFixed(0)}% nay`;
  }

  const strongerShare = Math.max(row.yea_share, row.nay_share);
  return `${(strongerShare * 100).toFixed(0)}% of recorded votes`;
}
