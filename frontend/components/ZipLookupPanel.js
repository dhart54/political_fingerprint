"use client";

import { useEffect, useState } from "react";

import { fetchZipLookup } from "../lib/api";

const DEFAULT_ZIP = "27701";

export default function ZipLookupPanel() {
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

  return (
    <section className="mt-8 rounded-[2.5rem] border border-stone-300/80 bg-white/75 p-6 shadow-[0_20px_80px_rgba(72,52,24,0.12)] backdrop-blur lg:p-8">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-stone-500">
            ZIP Lookup
          </p>
          <h3 className="mt-2 font-serif text-3xl text-stone-900">
            Find your House rep and senators
          </h3>
        </div>
        <p className="text-xs uppercase tracking-[0.25em] text-stone-500">
          Try 27701 or 27601
        </p>
      </div>
      <form className="mt-6 flex flex-col gap-3 sm:flex-row" onSubmit={handleLookup}>
        <input
          className="h-12 flex-1 rounded-full border border-stone-300 bg-stone-50 px-5 text-sm text-stone-900 outline-none ring-0 placeholder:text-stone-500"
          inputMode="numeric"
          maxLength={5}
          onChange={(event) => setZipCode(event.target.value.replace(/\D/g, "").slice(0, 5))}
          placeholder="Enter ZIP code"
          value={zipCode}
        />
        <button
          className="h-12 rounded-full bg-stone-900 px-6 text-sm uppercase tracking-[0.25em] text-stone-100"
          type="submit"
        >
          Lookup
        </button>
      </form>
      <div className="mt-6 flex flex-col gap-3 rounded-[2rem] bg-stone-950 px-5 py-5 text-stone-100 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-stone-400">
            Lookup Status
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
            ? `${state.payload.senators.length + (state.payload.house_rep ? 1 : 0)} legislators returned from the fixture mapping.`
            : null}
        </p>
      </div>
      {state.status === "ready" ? (
        <div className="mt-6 grid gap-4 lg:grid-cols-[0.95fr_1.05fr]">
          <LegislatorCard
            accent="bg-amber-100 text-amber-900"
            heading="House Representative"
            legislator={state.payload.house_rep}
          />
          <div className="grid gap-4">
            {state.payload.senators.map((senator) => (
              <LegislatorCard
                accent="bg-emerald-100 text-emerald-900"
                key={senator.id}
                heading="Senator"
                legislator={senator}
              />
            ))}
          </div>
        </div>
      ) : null}
    </section>
  );
}

function LegislatorCard({ accent, heading, legislator }) {
  return (
    <article className="rounded-[2rem] border border-stone-200 bg-[linear-gradient(180deg,rgba(255,255,255,0.76),rgba(245,241,233,0.94))] px-5 py-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.7)]">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-xs uppercase tracking-[0.25em] text-stone-500">{heading}</p>
        <span className={`rounded-full px-3 py-1 text-[11px] uppercase tracking-[0.22em] ${accent}`}>
          {formatParty(legislator.party)}
        </span>
      </div>
      <h4 className="mt-3 font-serif text-2xl text-stone-900">
        {legislator.name_display}
      </h4>
      <p className="mt-2 text-sm text-stone-600">
        {formatChamber(legislator.chamber)} • {legislator.state}
      </p>
      <dl className="mt-5 grid gap-4 sm:grid-cols-2">
        <Meta label="Bioguide" value={legislator.bioguide_id} />
        <Meta label="Party" value={formatParty(legislator.party)} />
        <Meta label="Chamber" value={legislator.chamber} />
        <Meta
          label="District"
          value={legislator.district ? `${legislator.state}-${legislator.district}` : "Statewide"}
        />
      </dl>
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
