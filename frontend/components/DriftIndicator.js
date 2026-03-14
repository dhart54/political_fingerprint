"use client";

import { useEffect, useState } from "react";

import { fetchDrift } from "../lib/api";

export default function DriftIndicator({
  legislatorId = "leg_alex_morgan",
  title = "Change Over Time",
}) {
  const [state, setState] = useState({
    status: "loading",
    payload: null,
    error: null,
  });

  useEffect(() => {
    let active = true;

    async function loadDrift() {
      try {
        const payload = await fetchDrift({ legislatorId });
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
          error: "Drift data is unavailable for this legislator right now.",
        });
      }
    }

    loadDrift();

    return () => {
      active = false;
    };
  }, [legislatorId]);

  const driftValue = state.payload?.drift_value ?? 0;
  const percent = Math.min(100, Math.max(0, driftValue * 100));
  const driftTakeaway = buildDriftTakeaway({
    status: state.status,
    insufficientData: state.payload?.insufficient_data,
    driftValue,
  });

  return (
    <section className="mt-8 grid gap-5 rounded-[2.25rem] border border-stone-300/80 bg-[linear-gradient(135deg,#060505,#171311_55%,#090706)] px-5 py-5 text-stone-100 shadow-[0_20px_80px_rgba(72,52,24,0.18)] lg:grid-cols-[0.84fr_1.16fr] lg:p-6">
      <div>
        <p className="text-xs uppercase tracking-[0.3em] text-stone-400">
          {title}
        </p>
        <h3 className="mt-3 font-serif text-[2.7rem] leading-[0.95] text-stone-50">
          {state.status === "loading" ? "Reading change over time..." : null}
          {state.status === "error" ? "Drift unavailable" : null}
          {state.status === "ready" && state.payload?.insufficient_data
            ? "Insufficient data"
            : null}
          {state.status === "ready" && !state.payload?.insufficient_data
            ? `Change score ${driftValue.toFixed(2)}`
            : null}
        </h3>
        <p className="mt-4 max-w-md text-[18px] leading-8 text-stone-100">
          {driftTakeaway}
        </p>
        <p className="mt-3 max-w-md text-[15px] leading-7 text-stone-300">
          {state.status === "loading" ? "Waiting for the backend drift response." : null}
          {state.status === "error" ? `${state.error} Try reloading the page or selecting another legislator.` : null}
          {state.status === "ready" && state.payload?.insufficient_data
            ? "There are not yet enough eligible votes in this window to say whether this legislator's issue emphasis is stable or changing."
            : null}
          {state.status === "ready" && !state.payload?.insufficient_data
            ? "This compares the early and recent halves of the 730-day window to show whether the legislator's issue mix stayed similar or moved."
            : null}
        </p>
        {state.status === "ready" && !state.payload?.insufficient_data ? (
          <div className="mt-4 inline-flex rounded-full border border-emerald-400/20 bg-emerald-400/8 px-4 py-2 text-xs uppercase tracking-[0.23em] text-emerald-200">
            Real drift signal available
          </div>
        ) : null}
      </div>
      <div className="flex flex-col justify-between">
        <div className="rounded-[2rem] border border-white/6 bg-white/8 p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]">
          <div className="flex items-end justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.25em] text-stone-400">
                Change Gauge
              </p>
              <p className="mt-2 text-4xl font-semibold text-stone-50">
                {state.status === "ready" && !state.payload?.insufficient_data
                  ? driftValue.toFixed(2)
                  : "--"}
              </p>
            </div>
            <p className="text-[15px] text-stone-300">
              {state.status === "ready"
                ? `${state.payload?.early_total_votes ?? 0} early / ${state.payload?.recent_total_votes ?? 0} recent`
                : ""}
            </p>
          </div>
          <div className="mt-5 h-4 rounded-full bg-stone-800">
            <div
              className={`h-4 rounded-full ${
                state.payload?.insufficient_data
                  ? "bg-[repeating-linear-gradient(90deg,#a8a29e_0,#a8a29e_24px,#78716c_24px,#78716c_36px)]"
                  : "bg-[linear-gradient(90deg,#34d399,#10b981)]"
              }`}
              style={{ width: `${state.payload?.insufficient_data ? 100 : percent}%` }}
            />
          </div>
        </div>
        <dl className="mt-4 grid gap-3 sm:grid-cols-3">
          <Metric label="Window" value="730 days" />
          <Metric
            label="Early"
            value={state.status === "ready" ? `${state.payload?.early_total_votes ?? 0} votes` : "--"}
          />
          <Metric
            label="Recent"
            value={state.status === "ready" ? `${state.payload?.recent_total_votes ?? 0} votes` : "--"}
          />
        </dl>
      </div>
    </section>
  );
}

function Metric({ label, value }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/6 px-4 py-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
      <dt className="text-xs uppercase tracking-[0.25em] text-stone-400">{label}</dt>
      <dd className="mt-2 text-[1.9rem] leading-none text-stone-50">{value}</dd>
    </div>
  );
}

function buildDriftTakeaway({ status, insufficientData, driftValue }) {
  if (status === "loading") {
    return "Checking whether this legislator's issue mix has stayed steady or moved.";
  }

  if (status === "error") {
    return "The site cannot tell yet whether this voting pattern stayed steady or shifted.";
  }

  if (insufficientData) {
    return "There are not enough eligible votes yet to tell whether this voting pattern stayed consistent.";
  }

  if (driftValue >= 0.6) {
    return "This voting record shifted noticeably between the earlier and more recent parts of the window.";
  }

  if (driftValue >= 0.3) {
    return "This voting record changed somewhat over the current two-year window.";
  }

  return "This voting record stayed relatively stable over the current two-year window.";
}
