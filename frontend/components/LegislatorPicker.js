"use client";

import { startTransition, useDeferredValue, useEffect, useState } from "react";

import { fetchLegislatorSearch } from "../lib/api";

export default function LegislatorPicker({ selectedLegislator, onSelect }) {
  const [query, setQuery] = useState("");
  const deferredQuery = useDeferredValue(query);
  const [searchState, setSearchState] = useState({
    status: "loading",
    results: [],
    error: null,
  });

  useEffect(() => {
    let active = true;

    startTransition(() => {
      setSearchState((current) => ({
        ...current,
        status: "loading",
        error: null,
      }));
    });

    async function loadResults() {
      try {
        const payload = await fetchLegislatorSearch({ query: deferredQuery.trim() });
        if (!active) {
          return;
        }
        startTransition(() => {
          setSearchState({
            status: "ready",
            results: payload.results,
            error: null,
          });
        });
      } catch (error) {
        if (!active) {
          return;
        }
        startTransition(() => {
          setSearchState({
            status: "error",
            results: [],
            error: "Legislator search is unavailable right now. Try reloading the page or checking the backend connection.",
          });
        });
      }
    }

    loadResults();

    return () => {
      active = false;
    };
  }, [deferredQuery]);

  return (
    <section className="mt-7 rounded-[2rem] border border-stone-300/70 bg-white/70 p-5 shadow-[0_14px_40px_rgba(72,52,24,0.07)] backdrop-blur">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-stone-500">
            Switch Official
          </p>
          <h3 className="mt-2 font-serif text-[2rem] leading-none text-stone-950">
            Search another record
          </h3>
          <p className="mt-2 max-w-2xl text-[15px] leading-7 text-stone-700">
            The current page is showing {selectedLegislator.name_display}. Search by name if you want to inspect a different official with the same issue checks.
          </p>
        </div>
        <p className="text-xs uppercase tracking-[0.25em] text-stone-500">
          {searchState.status === "ready"
            ? `${searchState.results.length} results`
            : searchState.status === "loading"
              ? "Searching"
              : "Search error"}
        </p>
      </div>

      <input
        aria-label="Search legislators"
        className="mt-4 h-12 w-full rounded-full border border-stone-300 bg-stone-50 px-5 text-sm text-stone-900 outline-none placeholder:text-stone-500"
        onChange={(event) => setQuery(event.target.value)}
        placeholder="Search legislators"
        value={query}
      />

      <div className="mt-4 grid max-h-[360px] gap-3 overflow-y-auto pr-1 md:grid-cols-2 xl:grid-cols-4">
        {searchState.status === "error" ? (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-4 text-sm text-rose-700 md:col-span-2 xl:col-span-4">
            {searchState.error}
          </div>
        ) : null}
        {searchState.status !== "error" && searchState.results.length === 0 ? (
          <div className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-4 text-sm text-stone-600 md:col-span-2 xl:col-span-4">
            No legislators match this search. Try a broader name.
          </div>
        ) : null}
        {searchState.results.map((legislator) => {
          const isSelected = legislator.id === selectedLegislator.id;
          return (
            <button
              className={`rounded-[1.25rem] border px-4 py-4 text-left transition ${
                isSelected
                  ? "border-stone-900 bg-stone-900 text-stone-100 shadow-[0_10px_24px_rgba(28,25,23,0.14)]"
                  : "border-stone-200 bg-stone-50 text-stone-900 hover:border-stone-400"
              }`}
              key={legislator.id}
              aria-pressed={isSelected}
              onClick={() => onSelect(legislator)}
              type="button"
            >
              <p className={`text-xs uppercase tracking-[0.22em] ${isSelected ? "text-stone-400" : "text-stone-500"}`}>
                {formatChamber(legislator.chamber)}
              </p>
              <p className="mt-2 text-[1.25rem] leading-6">
                {legislator.name_display}
              </p>
              <p className={`mt-2 text-[14px] leading-5 ${isSelected ? "text-stone-300" : "text-stone-600"}`}>
                {legislator.party} - {legislator.state}
                {legislator.district ? `-${legislator.district}` : " - Statewide"}
              </p>
            </button>
          );
        })}
      </div>
    </section>
  );
}

function formatChamber(chamber) {
  return chamber ? chamber[0].toUpperCase() + chamber.slice(1) : "";
}
