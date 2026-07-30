"use client";

import { useState } from "react";

import {
  fetchLegislatorSearch,
  fetchZipLookup,
} from "../lib/api";

export default function RepresentativeFinder({
  compact = false,
  onCancel = null,
  onSelect,
}) {
  const [zip, setZip] = useState("");
  const [name, setName] = useState("");
  const [state, setState] = useState({
    status: "idle",
    mode: null,
    results: [],
    message: "Search by ZIP code or representative name.",
  });

  async function searchZip(event) {
    event.preventDefault();
    if (!/^\d{5}$/.test(zip)) {
      setState({
        status: "error",
        mode: "zip",
        results: [],
        message: "Enter a valid 5-digit ZIP code.",
      });
      return;
    }
    setState({
      status: "loading",
      mode: "zip",
      results: [],
      message: "Looking up representatives…",
    });
    try {
      const payload = await fetchZipLookup({ zipCode: zip });
      const results = [
        ...(payload?.house_rep ? [payload.house_rep] : []),
        ...(payload?.senators || []),
      ].filter(Boolean);
      setState({
        status: "ready",
        mode: "zip",
        results,
        message: results.length
          ? `Found ${results.length} federal ${results.length === 1 ? "representative" : "representatives"} for ${zip}.`
          : `No representative record is available for ${zip}.`,
      });
    } catch {
      setState({
        status: "error",
        mode: "zip",
        results: [],
        message: "ZIP lookup is unavailable right now. Try a name search.",
      });
    }
  }

  async function searchName(event) {
    event.preventDefault();
    const query = name.trim();
    if (query.length < 2) {
      setState({
        status: "error",
        mode: "name",
        results: [],
        message: "Enter at least two letters of a representative’s name.",
      });
      return;
    }
    setState({
      status: "loading",
      mode: "name",
      results: [],
      message: "Searching representative records…",
    });
    try {
      const payload = await fetchLegislatorSearch({ query });
      const results = (payload?.results || []).slice(0, 12);
      setState({
        status: "ready",
        mode: "name",
        results,
        message: results.length
          ? `Found ${results.length} ${results.length === 1 ? "match" : "matches"}.`
          : `No representatives matched “${query}.”`,
      });
    } catch {
      setState({
        status: "error",
        mode: "name",
        results: [],
        message: "Name search is unavailable right now. Please try again.",
      });
    }
  }

  return (
    <section
      aria-labelledby="representative-finder-heading"
      className={`border border-stone-200 bg-white ${
        compact
          ? "rounded-2xl p-4 sm:p-5"
          : "rounded-[1.75rem] p-5 shadow-[0_18px_48px_rgba(31,41,55,0.06)] sm:p-7 lg:p-8"
      }`}
      data-testid="representative-finder"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="eyebrow">Find your representative</p>
          <h2
            className="mt-2 font-serif text-3xl leading-tight text-stone-950 sm:text-4xl"
            id="representative-finder-heading"
          >
            Start with a person, not a score.
          </h2>
          <p className="mt-3 max-w-2xl text-base leading-7 text-stone-700">
            Search a ZIP code or name, then explore recorded actions issue by issue.
          </p>
        </div>
        {onCancel ? (
          <button className="secondary-button shrink-0" onClick={onCancel} type="button">
            Close
          </button>
        ) : null}
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <form className="rounded-2xl border border-stone-200 bg-stone-50 p-4" onSubmit={searchZip}>
          <label className="text-sm font-semibold text-stone-900" htmlFor="pass-a-zip">
            Search by ZIP
          </label>
          <div className="mt-2 flex flex-col gap-2 sm:flex-row">
            <input
              autoComplete="postal-code"
              className="field"
              id="pass-a-zip"
              inputMode="numeric"
              maxLength={5}
              onChange={(event) => setZip(event.target.value.replace(/\D/g, "").slice(0, 5))}
              placeholder="e.g. 27701"
              value={zip}
            />
            <button className="primary-button" type="submit">
              Find by ZIP
            </button>
          </div>
        </form>

        <form className="rounded-2xl border border-stone-200 bg-stone-50 p-4" onSubmit={searchName}>
          <label className="text-sm font-semibold text-stone-900" htmlFor="pass-a-name">
            Search by name
          </label>
          <div className="mt-2 flex flex-col gap-2 sm:flex-row">
            <input
              autoComplete="off"
              className="field"
              id="pass-a-name"
              onChange={(event) => setName(event.target.value)}
              placeholder="Representative name"
              value={name}
            />
            <button className="primary-button" type="submit">
              Search names
            </button>
          </div>
        </form>
      </div>

      <p
        aria-live="polite"
        className={`mt-4 text-sm leading-6 ${
          state.status === "error" ? "text-rose-800" : "text-stone-600"
        }`}
        role={state.status === "error" ? "alert" : "status"}
      >
        {state.message}
      </p>

      {state.results.length ? (
        <div
          aria-label="Representative search results"
          className="mt-3 grid max-h-[22rem] gap-2 overflow-y-auto pr-1 sm:grid-cols-2"
          role="list"
        >
          {state.results.map((representative) => (
            <div key={representative.id} role="listitem">
              <button
                aria-label={`Select ${representative.name_display}, ${formatOffice(representative)}`}
                className="group min-h-20 w-full rounded-xl border border-stone-200 bg-white p-3 text-left transition hover:border-teal-700 focus-visible:border-teal-800"
                onClick={() => onSelect(representative)}
                type="button"
              >
                <span className="block text-base font-semibold text-stone-950 group-hover:text-teal-900">
                  {representative.name_display}
                </span>
                <span className="mt-1 block text-sm leading-5 text-stone-600">
                  {formatOffice(representative)}
                </span>
              </button>
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}

function formatOffice(representative) {
  const chamber = representative.chamber === "senate" ? "U.S. Senate" : "U.S. House";
  const place = representative.district
    ? `${representative.state} district ${String(representative.district).replace(/^0/, "")}`
    : `${representative.state}, statewide`;
  return `${chamber} · ${place} · ${formatParty(representative.party)}`;
}

function formatParty(party) {
  return { D: "Democratic", R: "Republican", I: "Independent" }[party]
    || String(party || "Party not listed");
}
