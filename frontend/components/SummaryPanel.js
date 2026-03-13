"use client";

import { useEffect, useState } from "react";

import { fetchSummary } from "../lib/api";

export default function SummaryPanel({
  legislatorId = "leg_alex_morgan",
  title = "Plain-Language Summary",
}) {
  const [state, setState] = useState({
    status: "loading",
    payload: null,
    error: null,
  });

  useEffect(() => {
    let active = true;

    async function loadSummary() {
      try {
        const payload = await fetchSummary({ legislatorId });
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
          error: error instanceof Error ? error.message : "Summary request failed.",
        });
      }
    }

    loadSummary();

    return () => {
      active = false;
    };
  }, [legislatorId]);

  return (
    <section className="mt-8 rounded-[2.5rem] border border-stone-300/80 bg-white/75 p-6 shadow-[0_20px_80px_rgba(72,52,24,0.12)] backdrop-blur lg:p-8">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-stone-500">
            {title}
          </p>
          <h3 className="mt-2 font-serif text-3xl text-stone-900">
            Neutral, cached narrative
          </h3>
        </div>
        <p className="text-xs uppercase tracking-[0.25em] text-stone-500">
          {state.status === "ready" ? state.payload?.generation_method : "loading"}
        </p>
      </div>
      <div className="mt-6 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <article className="rounded-[2rem] bg-[linear-gradient(180deg,#100d0b,#171311)] px-6 py-6 text-stone-100 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
          <p className="text-xs uppercase tracking-[0.28em] text-stone-400">
            Generated Narrative
          </p>
          <p className="mt-4 text-[17px] leading-9 text-stone-200">
            {state.status === "loading" ? "Loading summary..." : null}
            {state.status === "error" ? state.error : null}
            {state.status === "ready" ? state.payload?.summary_text : null}
          </p>
        </article>
        <div className="grid gap-4">
          <MetaCard
            label="Window End"
            value={state.status === "ready" ? state.payload?.window_end : "--"}
          />
          <MetaCard
            label="Version"
            value={state.status === "ready" ? state.payload?.classification_version : "--"}
          />
          <MetaCard
            label="Created"
            value={state.status === "ready" ? state.payload?.created_at : "--"}
          />
        </div>
      </div>
    </section>
  );
}

function MetaCard({ label, value }) {
  return (
    <div className="rounded-2xl border border-stone-200 bg-stone-50 px-5 py-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.72)]">
      <p className="text-xs uppercase tracking-[0.25em] text-stone-500">{label}</p>
      <p className="mt-3 text-sm leading-6 text-stone-700 break-words">{value}</p>
    </div>
  );
}
