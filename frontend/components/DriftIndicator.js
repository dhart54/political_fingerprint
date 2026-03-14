"use client";

import { useEffect, useState } from "react";

import { fetchDrift } from "../lib/api";

export default function DriftIndicator({
  legislatorId = "leg_alex_morgan",
  title = "Stability / Drift",
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

  return (
    <section className="mt-8 grid gap-6 rounded-[2.25rem] border border-stone-300/80 bg-[linear-gradient(135deg,#060505,#171311_55%,#090706)] px-6 py-6 text-stone-100 shadow-[0_20px_80px_rgba(72,52,24,0.18)] lg:grid-cols-[0.88fr_1.12fr] lg:p-8">
      <div>
        <p className="text-xs uppercase tracking-[0.3em] text-stone-400">
          {title}
        </p>
        <h3 className="mt-3 font-serif text-3xl text-stone-50">
          {state.status === "loading" ? "Loading drift..." : null}
          {state.status === "error" ? "Drift unavailable" : null}
          {state.status === "ready" && state.payload?.insufficient_data
            ? "Insufficient data"
            : null}
          {state.status === "ready" && !state.payload?.insufficient_data
            ? `Drift ${driftValue.toFixed(2)}`
            : null}
        </h3>
        <p className="mt-4 max-w-md text-sm leading-6 text-stone-300">
          {state.status === "loading" ? "Waiting for the backend drift response." : null}
          {state.status === "error" ? `${state.error} Try reloading the page or selecting another legislator.` : null}
          {state.status === "ready" && state.payload?.insufficient_data
            ? "The current fixture-backed data stays below the locked 20-vote threshold, so drift is reported as unavailable rather than estimated."
            : null}
          {state.status === "ready" && !state.payload?.insufficient_data
            ? "Drift compares the early 365-day vote-share vector to the recent 365-day vote-share vector using deterministic L1 distance."
            : null}
        </p>
        {state.status === "ready" && !state.payload?.insufficient_data ? (
          <div className="mt-5 inline-flex rounded-full border border-emerald-400/20 bg-emerald-400/8 px-4 py-2 text-xs uppercase tracking-[0.23em] text-emerald-200">
            Real drift signal available
          </div>
        ) : null}
      </div>
      <div className="flex flex-col justify-between">
        <div className="rounded-[2rem] border border-white/6 bg-white/8 p-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]">
          <div className="flex items-end justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.25em] text-stone-400">
                Drift Gauge
              </p>
              <p className="mt-2 text-5xl font-semibold text-stone-50">
                {state.status === "ready" && !state.payload?.insufficient_data
                  ? driftValue.toFixed(2)
                  : "--"}
              </p>
            </div>
            <p className="text-sm text-stone-300">
              {state.status === "ready"
                ? `${state.payload?.early_total_votes ?? 0} early / ${state.payload?.recent_total_votes ?? 0} recent`
                : ""}
            </p>
          </div>
          <div className="mt-6 h-4 rounded-full bg-stone-800">
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
        <dl className="mt-6 grid gap-3 sm:grid-cols-3">
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
    <div className="rounded-2xl border border-white/10 bg-white/6 px-4 py-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
      <dt className="text-xs uppercase tracking-[0.25em] text-stone-400">{label}</dt>
      <dd className="mt-3 text-2xl text-stone-50">{value}</dd>
    </div>
  );
}
