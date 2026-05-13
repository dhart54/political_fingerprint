"use client";

import { useEffect, useState } from "react";

import { fetchZipLookup } from "../lib/api";

const DEFAULT_ZIP = "27701";

export default function ZipLookupPanel({
  onComparePair,
  onSelectLegislator,
  variant = "standard",
}) {
  const [zipCode, setZipCode] = useState(DEFAULT_ZIP);
  const [state, setState] = useState({
    status: "idle",
    payload: null,
    error: null,
  });

  async function runLookup(nextZipCode) {
    if (nextZipCode.length !== 5) {
      setState({
        status: "error",
        payload: null,
        error: "Enter a valid 5-digit ZIP code.",
      });
      return;
    }

    try {
      setState({
        status: "loading",
        payload: null,
        error: null,
      });

      const payload = await fetchZipLookup({ zipCode: nextZipCode });
      setState({
        status: "ready",
        payload,
        error: null,
      });
    } catch (error) {
      setState({
        status: "error",
        payload: null,
        error: "That ZIP code could not be matched. Try 27701 or 27601 for the current fixture data.",
      });
    }
  }

  useEffect(() => {
    runLookup(DEFAULT_ZIP);
  }, []);

  function handleLookup(event) {
    event.preventDefault();
    runLookup(zipCode);
  }

  const isHero = variant === "hero";
  const sectionClassName = isHero
    ? "rounded-[2rem] border border-cyan-900/15 bg-white p-5 shadow-[0_24px_70px_rgba(15,23,42,0.16)] lg:p-6"
    : "mt-8 rounded-[2rem] border border-stone-200 bg-white p-5 shadow-[0_16px_40px_rgba(15,23,42,0.08)] lg:p-6";

  return (
    <section className={sectionClassName}>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-stone-500">
            Start Here
          </p>
          <h3 className="mt-2 font-serif text-[2.65rem] leading-[0.95] text-stone-950">
            Find your ballot-level officials
          </h3>
          <p className="mt-3 max-w-2xl text-[15px] leading-7 text-stone-700">
            Look up a ZIP, then open a profile or compare your House member with either senator.
          </p>
        </div>
        <p className="text-xs uppercase tracking-[0.25em] text-stone-500">
          Try 27701 or 27601
        </p>
      </div>

      <form className="mt-5 flex flex-col gap-3 sm:flex-row" onSubmit={handleLookup}>
        <input
          className="h-12 flex-1 rounded-full border border-stone-300 bg-stone-50 px-5 text-sm text-stone-900 outline-none ring-0 placeholder:text-stone-500"
          inputMode="numeric"
          maxLength={5}
          onChange={(event) => setZipCode(event.target.value.replace(/\D/g, "").slice(0, 5))}
          placeholder="Enter ZIP code"
          value={zipCode}
        />
        <button
          className="h-12 rounded-full bg-cyan-900 px-6 text-sm uppercase tracking-[0.25em] text-white shadow-[0_10px_24px_rgba(22,78,99,0.22)]"
          type="submit"
        >
          Show My Reps
        </button>
      </form>

      <div className="mt-5 flex flex-col gap-3 rounded-[1.5rem] bg-stone-950 px-5 py-5 text-stone-100 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-stone-400">
            Result
          </p>
          <p className="mt-3 text-lg text-stone-50">
            {state.status === "idle" ? "Ready to lookup" : null}
            {state.status === "loading" ? "Looking up legislators..." : null}
            {state.status === "error" ? "Lookup unavailable" : null}
            {state.status === "ready"
              ? `ZIP ${state.payload.zip} maps to ${state.payload.state}-${state.payload.district}.`
              : null}
          </p>
        </div>
        <p className="text-sm leading-7 text-stone-300">
          {state.status === "idle" ? "Run a ZIP lookup to load representatives." : null}
          {state.status === "loading" ? "Loading House and Senate results." : null}
          {state.status === "error" ? state.error : null}
          {state.status === "ready"
            ? `${state.payload.senators.length + (state.payload.house_rep ? 1 : 0)} officials ready to inspect.`
            : null}
        </p>
      </div>

      {state.status === "ready" ? (
        <div className="mt-5">
          <div className="mb-4 flex flex-wrap gap-3 rounded-[1.25rem] border border-cyan-900/10 bg-cyan-50 px-4 py-4">
            <p className="w-full text-sm leading-6 text-stone-700">
              Good next click: open your House profile, then compare it with either senator.
            </p>
            {state.payload.house_rep && state.payload.senators[0] ? (
              <button
                className="rounded-full bg-cyan-900 px-4 py-2 text-xs uppercase tracking-[0.22em] text-white"
                onClick={() => {
                  onSelectLegislator?.(state.payload.house_rep);
                  onComparePair?.({
                    left: state.payload.house_rep,
                    right: state.payload.senators[0],
                  });
                }}
                type="button"
              >
                House vs Senator
              </button>
            ) : null}
            {state.payload.house_rep && state.payload.senators[1] ? (
              <button
                className="rounded-full bg-white px-4 py-2 text-xs uppercase tracking-[0.22em] text-cyan-900"
                onClick={() => {
                  onSelectLegislator?.(state.payload.house_rep);
                  onComparePair?.({
                    left: state.payload.house_rep,
                    right: state.payload.senators[1],
                  });
                }}
                type="button"
              >
                House vs Other Senator
              </button>
            ) : null}
            {state.payload.senators[0] && state.payload.senators[1] ? (
              <button
                className="rounded-full bg-white px-4 py-2 text-xs uppercase tracking-[0.22em] text-cyan-900"
                onClick={() =>
                  onComparePair?.({
                    left: state.payload.senators[0],
                    right: state.payload.senators[1],
                  })
                }
                type="button"
              >
                Compare Senators
              </button>
            ) : null}
          </div>

          <div className="grid gap-4 lg:grid-cols-[0.95fr_1.05fr]">
            <LegislatorCard
              accent="bg-cyan-100 text-cyan-900"
              heading="House Representative"
              legislator={state.payload.house_rep}
              onSelectLegislator={onSelectLegislator}
            />
            <div className="grid gap-4">
              {state.payload.senators.map((senator) => (
                <LegislatorCard
                  accent="bg-emerald-100 text-emerald-900"
                  key={senator.id}
                  heading="Senator"
                  legislator={senator}
                  onSelectLegislator={onSelectLegislator}
                />
              ))}
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}

function LegislatorCard({ accent, heading, legislator, onSelectLegislator }) {
  return (
    <article className="rounded-[1.5rem] border border-stone-200 bg-white px-5 py-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.7)]">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-xs uppercase tracking-[0.25em] text-stone-500">{heading}</p>
        <span className={`rounded-full px-3 py-1 text-[11px] uppercase tracking-[0.22em] ${accent}`}>
          {formatParty(legislator.party)}
        </span>
      </div>
      <h4 className="mt-3 font-serif text-[2.1rem] leading-[0.98] text-stone-950">
        {legislator.name_display}
      </h4>
      <p className="mt-2 text-sm text-stone-600">
        {formatChamber(legislator.chamber)} - {legislator.state}
      </p>
      <dl className="mt-4 grid gap-4 sm:grid-cols-2">
        <Meta label="Bioguide" value={legislator.bioguide_id} />
        <Meta label="Party" value={formatParty(legislator.party)} />
        <Meta label="Chamber" value={legislator.chamber} />
        <Meta
          label="District"
          value={legislator.district ? `${legislator.state}-${legislator.district}` : "Statewide"}
        />
      </dl>
      {onSelectLegislator ? (
        <div className="mt-4">
          <button
            className="rounded-full bg-stone-900 px-4 py-2 text-xs uppercase tracking-[0.22em] text-stone-100"
            onClick={() => onSelectLegislator(legislator)}
            type="button"
          >
            Open Profile
          </button>
        </div>
      ) : null}
    </article>
  );
}

function Meta({ label, value }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-[0.2em] text-stone-500">{label}</dt>
      <dd className="mt-1 text-sm text-stone-700">{value}</dd>
    </div>
  );
}

function formatChamber(chamber) {
  return chamber ? chamber[0].toUpperCase() + chamber.slice(1) : "";
}

function formatParty(party) {
  return party === "D" ? "Democrat" : party === "R" ? "Republican" : party;
}
