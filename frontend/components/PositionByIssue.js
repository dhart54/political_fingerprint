"use client";

import { useEffect, useState } from "react";

import { fetchPositions } from "../lib/api";

export default function PositionByIssue({
  legislatorId = "leg_alex_morgan",
  title = "How They Vote By Issue",
}) {
  const [state, setState] = useState({
    status: "loading",
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

  const rows = (state.payload?.positions || [])
    .filter((row) => row.recorded_votes > 0)
    .sort((left, right) => right.recorded_votes - left.recorded_votes || right.yea_share - left.yea_share)
    .slice(0, 6);
  const takeaway = buildTakeaway(rows);

  return (
    <section className="mt-8 rounded-[2.5rem] border border-stone-300/80 bg-white/75 p-5 shadow-[0_20px_80px_rgba(72,52,24,0.12)] backdrop-blur lg:p-6">
      <div className="grid gap-5 lg:grid-cols-[0.9fr_1.1fr]">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-stone-500">
            Position By Issue
          </p>
          <h3 className="mt-2 font-serif text-[2.7rem] leading-[0.95] text-stone-900">
            {title}
          </h3>
          <p className="mt-3 max-w-xl text-[18px] leading-8 text-stone-900">
            {state.status === "ready"
              ? takeaway
              : state.status === "loading"
                ? "Reading how this legislator voted inside their most active issue domains."
                : "The site cannot read how this legislator voted inside issue domains right now."}
          </p>
          <div className="mt-5 rounded-[2rem] bg-stone-950 px-5 py-5 text-stone-100">
            <p className="text-xs uppercase tracking-[0.28em] text-stone-400">
              Why This Matters
            </p>
            <p className="mt-3 text-[16px] leading-7 text-stone-200">
              Issue focus shows what topics absorbed the most votes. This section shows how the legislator actually voted within those topics using recorded yea and nay positions.
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
            <article
              className="rounded-[1.5rem] border border-stone-200 bg-[linear-gradient(180deg,rgba(255,255,255,0.9),rgba(245,241,233,0.92))] px-4 py-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.72)]"
              key={row.domain}
            >
              <div className="flex items-start justify-between gap-3">
                <p className="max-w-[200px] text-[16px] leading-7 text-stone-900">
                  {formatDomainLabel(row.domain)}
                </p>
                <p className="text-sm text-stone-500">{row.recorded_votes} votes</p>
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
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

function formatDomainLabel(domain) {
  return String(domain)
    .split("_")
    .map((segment) => segment[0] + segment.slice(1).toLowerCase())
    .join(" ");
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
