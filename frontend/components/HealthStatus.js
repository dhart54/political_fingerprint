"use client";

import { useEffect, useState } from "react";

import { fetchHealth, getApiBaseUrl } from "../lib/api";

export default function HealthStatus() {
  const [state, setState] = useState({
    status: "checking",
    detail: "Waiting for backend response.",
  });

  useEffect(() => {
    let active = true;

    async function loadHealth() {
      try {
        const payload = await fetchHealth();
        if (!active) {
          return;
        }
        setState({
          status: payload.status === "ok" ? "connected" : "unexpected",
          detail:
            payload.status === "ok"
              ? `Backend health check returned ${payload.status}.`
              : `Backend returned an unexpected payload: ${JSON.stringify(payload)}.`,
        });
      } catch (error) {
        if (!active) {
          return;
        }
        setState({
          status: "offline",
          detail:
            error instanceof Error
              ? error.message
              : "Backend health request failed.",
        });
      }
    }

    loadHealth();

    return () => {
      active = false;
    };
  }, []);

  const tone =
    state.status === "connected"
      ? "text-emerald-700"
      : state.status === "checking"
        ? "text-amber-700"
        : "text-rose-700";

  return (
    <article className="mt-12 rounded-[2rem] border border-stone-300/70 bg-[linear-gradient(135deg,#060505,#16110f)] px-6 py-5 text-stone-100 shadow-[0_18px_60px_rgba(72,52,24,0.18)]">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-stone-400">
            API Connectivity
          </p>
          <p className={`mt-3 text-lg font-medium ${tone}`}>
            {state.status === "connected" ? "Backend reachable" : null}
            {state.status === "checking" ? "Checking backend health" : null}
            {state.status === "offline" ? "Backend unavailable" : null}
            {state.status === "unexpected" ? "Unexpected backend response" : null}
          </p>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-stone-300">
            {state.detail}
          </p>
        </div>
        <p className="text-xs uppercase tracking-[0.25em] text-stone-500">
          {getApiBaseUrl()}
        </p>
      </div>
    </article>
  );
}
