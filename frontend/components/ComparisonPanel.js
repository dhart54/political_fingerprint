"use client";

import { startTransition, useDeferredValue, useEffect, useState } from "react";

import { fetchLegislatorComparison, fetchLegislatorSearch } from "../lib/api";

const COMPARISON_OPTIONS = ["ALL", "D", "R"];

export default function ComparisonPanel({
  defaultLeftLegislator,
  defaultRightLegislator,
}) {
  const [comparisonParty, setComparisonParty] = useState("ALL");
  const [query, setQuery] = useState("");
  const deferredQuery = useDeferredValue(query);
  const [selected, setSelected] = useState({
    left: defaultLeftLegislator,
    right: defaultRightLegislator,
  });
  const [searchState, setSearchState] = useState({
    status: "loading",
    results: [],
    error: null,
  });
  const [compareState, setCompareState] = useState({
    status: "loading",
    payload: null,
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
            error: "Comparison search is unavailable right now.",
          });
        });
      }
    }

    loadResults();

    return () => {
      active = false;
    };
  }, [deferredQuery]);

  useEffect(() => {
    let active = true;

    async function loadComparison() {
      setCompareState({
        status: "loading",
        payload: null,
        error: null,
      });

      try {
        const payload = await fetchLegislatorComparison({
          leftLegislatorId: selected.left.id,
          rightLegislatorId: selected.right.id,
          comparisonParty,
        });
        if (!active) {
          return;
        }
        setCompareState({
          status: "ready",
          payload,
          error: null,
        });
      } catch (error) {
        if (!active) {
          return;
        }
        setCompareState({
          status: "error",
          payload: null,
          error: "Comparison data is unavailable right now.",
        });
      }
    }

    loadComparison();

    return () => {
      active = false;
    };
  }, [comparisonParty, selected.left.id, selected.right.id]);

  return (
    <section className="mt-10 rounded-[2.5rem] border border-stone-300/80 bg-white/72 p-6 shadow-[0_20px_80px_rgba(72,52,24,0.12)] backdrop-blur lg:p-8">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-stone-500">
            Comparison Mode
          </p>
          <h2 className="mt-2 font-serif text-3xl text-stone-900">
            Compare behavioral profiles side by side
          </h2>
          <p className="mt-3 max-w-2xl text-base leading-7 text-stone-700">
            Use the same issue-focus, change-over-time, and summary lens on both legislators at once. It stays descriptive and does not rank either side.
          </p>
        </div>
        <div className="flex rounded-full border border-stone-300 bg-stone-100 p-1 shadow-[inset_0_1px_0_rgba(255,255,255,0.75)]">
          {COMPARISON_OPTIONS.map((option) => (
            <button
              className={`rounded-full px-4 py-2 text-xs tracking-[0.25em] transition ${
                comparisonParty === option
                  ? "bg-stone-900 text-stone-100 shadow-[0_6px_18px_rgba(28,25,23,0.18)]"
                  : "text-stone-600 hover:text-stone-900"
              }`}
              key={option}
              onClick={() => setComparisonParty(option)}
              type="button"
            >
              {option}
            </button>
          ))}
        </div>
      </div>

      <div className="mt-6 rounded-[2rem] bg-stone-950 px-5 py-5 text-stone-100">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-stone-400">
              Comparison Status
            </p>
            <p className="mt-3 text-lg text-stone-50">
              {compareState.status === "loading" ? "Loading side-by-side comparison..." : null}
              {compareState.status === "error" ? "Comparison unavailable" : null}
              {compareState.status === "ready"
                ? `${selected.left.name_display} and ${selected.right.name_display} loaded.`
                : null}
            </p>
          </div>
          <p className="text-sm leading-6 text-stone-300">
            {compareState.status === "loading" ? "Fetching fingerprint, drift, and summary data for both sides." : null}
            {compareState.status === "error" ? compareState.error : null}
            {compareState.status === "ready"
              ? `Overlay comparison is set to ${comparisonParty}. Compare issue focus first, then drift and summary.`
              : null}
          </p>
        </div>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[0.88fr_1.12fr]">
        <div className="rounded-[2rem] border border-stone-200 bg-[linear-gradient(180deg,rgba(255,255,255,0.76),rgba(245,241,233,0.94))] px-5 py-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.72)]">
          <p className="text-xs uppercase tracking-[0.3em] text-stone-500">
            Select Legislators
          </p>
          <input
            className="mt-4 h-12 w-full rounded-full border border-stone-300 bg-stone-50 px-5 text-sm text-stone-900 outline-none placeholder:text-stone-500"
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search by legislator name"
            value={query}
          />
          <div className="mt-4 grid max-h-[620px] gap-3 overflow-y-auto pr-1">
            {searchState.status === "error" ? (
              <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-4 text-sm text-rose-700">
                {searchState.error}
              </div>
            ) : null}
            {searchState.status !== "error" && searchState.results.length === 0 ? (
              <div className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-4 text-sm text-stone-600">
                No legislators match this search yet.
              </div>
            ) : null}
            {searchState.results.map((legislator) => (
              <div
                className="flex flex-col gap-3 rounded-[1.5rem] border border-stone-200 bg-white/70 px-4 py-4 sm:flex-row sm:items-center sm:justify-between"
                key={legislator.id}
              >
                <div>
                  <p className="font-serif text-2xl text-stone-900">{legislator.name_display}</p>
                  <p className="mt-1 text-sm text-stone-600">
                    {formatChamber(legislator.chamber)} • {legislator.party} • {legislator.state}
                    {legislator.district ? `-${legislator.district}` : " • Statewide"}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    className={`rounded-full px-4 py-2 text-xs uppercase tracking-[0.22em] ${
                      selected.left.id === legislator.id
                        ? "bg-stone-900 text-stone-100"
                        : "bg-stone-200 text-stone-700"
                    }`}
                    onClick={() => setSelected((current) => ({ ...current, left: legislator }))}
                    type="button"
                  >
                    Left
                  </button>
                  <button
                    className={`rounded-full px-4 py-2 text-xs uppercase tracking-[0.22em] ${
                      selected.right.id === legislator.id
                        ? "bg-stone-900 text-stone-100"
                        : "bg-stone-200 text-stone-700"
                    }`}
                    onClick={() => setSelected((current) => ({ ...current, right: legislator }))}
                    type="button"
                  >
                    Right
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

          <div className="grid gap-4 lg:grid-cols-2">
          <CompareSideCard
            heading="Left"
            side={compareState.payload?.left}
            fallbackLegislator={selected.left}
          />
          <CompareSideCard
            heading="Right"
            side={compareState.payload?.right}
            fallbackLegislator={selected.right}
          />
        </div>
      </div>
    </section>
  );
}

function CompareSideCard({ heading, side, fallbackLegislator }) {
  const legislator = side?.legislator || fallbackLegislator;
  const fingerprintRows = side?.fingerprint?.fingerprint || [];
  const topDomains = fingerprintRows
    .filter((row) => row.vote_share > 0)
    .sort((left, right) => right.vote_share - left.vote_share)
    .slice(0, 2);

  return (
    <article className="rounded-[2rem] border border-stone-200 bg-[linear-gradient(180deg,rgba(255,255,255,0.78),rgba(245,241,233,0.96))] px-5 py-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.72)]">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.28em] text-stone-500">{heading}</p>
          <h3 className="mt-3 font-serif text-3xl text-stone-900">{legislator.name_display}</h3>
          <p className="mt-2 text-[15px] leading-6 text-stone-600">
            {formatChamber(legislator.chamber)} • {legislator.party} • {legislator.state}
            {legislator.district ? `-${legislator.district}` : " • Statewide"}
          </p>
        </div>
      </div>

      <div className="mt-5 grid gap-3">
        <CompareMetric
          label="Fingerprint"
          value={
            topDomains.length
              ? topDomains.map((row) => `${formatDomainLabel(row.domain)} ${(row.vote_share * 100).toFixed(0)}%`).join(" • ")
              : "No eligible domain emphasis available"
          }
        />
        <CompareMetric
          label="Drift"
          value={
            side?.drift
              ? side.drift.insufficient_data
                ? "Insufficient data"
                : String(side.drift.drift_value?.toFixed(2))
              : "--"
          }
        />
        <CompareMetric
          label="Summary"
          value={side?.summary?.summary_text ? truncateSummary(side.summary.summary_text) : "Summary unavailable"}
        />
      </div>
    </article>
  );
}

function CompareMetric({ label, value }) {
  return (
    <div className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.72)]">
      <p className="text-xs uppercase tracking-[0.22em] text-stone-500">{label}</p>
      <p className="mt-3 text-sm leading-6 text-stone-800">{value}</p>
    </div>
  );
}

function formatChamber(chamber) {
  return chamber ? chamber[0].toUpperCase() + chamber.slice(1) : "";
}

function formatDomainLabel(domain) {
  return String(domain)
    .split("_")
    .map((segment) => segment[0] + segment.slice(1).toLowerCase())
    .join(" ");
}

function truncateSummary(summaryText) {
  const normalized = String(summaryText).trim();
  if (normalized.length <= 160) {
    return normalized;
  }
  return `${normalized.slice(0, 157)}...`;
}
