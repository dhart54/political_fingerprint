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
    <section className="mt-7 rounded-[2.5rem] border border-stone-300/70 bg-white/65 p-4 shadow-[0_18px_60px_rgba(72,52,24,0.08)] backdrop-blur lg:p-5">
      <div className="grid gap-4 xl:grid-cols-[0.72fr_1.28fr]">
        <div className="rounded-[2rem] bg-[linear-gradient(180deg,#0f0c0a,#17120f)] px-5 py-5 text-stone-100 shadow-[inset_0_1px_0_rgba(255,255,255,0.05)] xl:min-h-[272px]">
          <p className="text-xs uppercase tracking-[0.3em] text-stone-400">
            Active Legislator
          </p>
          <h2 className="mt-2 font-serif text-[2.3rem] leading-[0.95] text-stone-50">
            {selectedLegislator.name_display}
          </h2>
          <p className="mt-2 text-[15px] leading-6 text-stone-300">
            {formatChamber(selectedLegislator.chamber)} • {selectedLegislator.party} • {selectedLegislator.state}
            {selectedLegislator.district ? `-${selectedLegislator.district}` : ""}
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <Tag>{selectedLegislator.party === "D" ? "Democrat" : selectedLegislator.party === "R" ? "Republican" : selectedLegislator.party}</Tag>
            <Tag>{selectedLegislator.chamber === "house" ? "House member" : "Senator"}</Tag>
            <Tag>{selectedLegislator.district ? `${selectedLegislator.state}-${selectedLegislator.district}` : `${selectedLegislator.state} statewide`}</Tag>
          </div>
          <p className="mt-4 max-w-md text-[14px] leading-6 text-stone-300">
            Start here to inspect one voting record in depth. The sections below show issue focus, change over time, and the clearest takeaways from the current window.
          </p>
        </div>
        <div>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-stone-500">
                Legislator Search
              </p>
              <p className="mt-2 text-[15px] leading-7 text-stone-700">
                Search by name to swap in a different legislator and instantly update the behavioral profile below.
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
            className="mt-4 h-12 w-full rounded-full border border-stone-300 bg-stone-50 px-5 text-sm text-stone-900 outline-none placeholder:text-stone-500"
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search legislators"
            value={query}
          />
          <div className="mt-4 grid max-h-[470px] gap-3 overflow-y-auto pr-1 sm:grid-cols-2 2xl:grid-cols-3">
            {searchState.status === "error" ? (
              <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-4 text-sm text-rose-700 sm:col-span-2 xl:col-span-3">
                {searchState.error}
              </div>
            ) : null}
            {searchState.status !== "error" && searchState.results.length === 0 ? (
              <div className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-4 text-sm text-stone-600 sm:col-span-2 xl:col-span-3">
                No legislators match this search. Try a broader name.
              </div>
            ) : null}
            {searchState.results.map((legislator) => {
              const isSelected = legislator.id === selectedLegislator.id;
              return (
                <button
                  className={`rounded-[1.5rem] border px-4 py-4 text-left transition ${
                    isSelected
                      ? "border-stone-900 bg-stone-900 text-stone-100 shadow-[0_12px_28px_rgba(28,25,23,0.16)]"
                      : "border-stone-200 bg-[linear-gradient(180deg,rgba(255,255,255,0.76),rgba(245,241,233,0.94))] text-stone-900 shadow-[inset_0_1px_0_rgba(255,255,255,0.72)] hover:border-stone-400"
                  }`}
                  key={legislator.id}
                  onClick={() => onSelect(legislator)}
                  type="button"
                  >
                  <div className="flex items-start justify-between gap-3">
                    <p className={`text-xs uppercase tracking-[0.24em] ${isSelected ? "text-stone-400" : "text-stone-500"}`}>
                    {formatChamber(legislator.chamber)}
                    </p>
                    <span className={`rounded-full px-2.5 py-1 text-[10px] uppercase tracking-[0.2em] ${isSelected ? "bg-white/10 text-stone-300" : "bg-stone-100 text-stone-600"}`}>
                      {legislator.party}
                    </span>
                  </div>
                  <p className="mt-2 font-serif text-[1.35rem] leading-[1.04]">
                    {legislator.name_display}
                  </p>
                  <p className={`mt-2 text-[14px] leading-5 ${isSelected ? "text-stone-300" : "text-stone-600"}`}>
                    {legislator.party} • {legislator.state}
                    {legislator.district ? `-${legislator.district}` : " • Statewide"}
                  </p>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}

function formatChamber(chamber) {
  return chamber ? chamber[0].toUpperCase() + chamber.slice(1) : "";
}

function Tag({ children }) {
  return (
    <span className="rounded-full border border-white/10 bg-white/6 px-3 py-1.5 text-[11px] uppercase tracking-[0.2em] text-stone-300">
      {children}
    </span>
  );
}
