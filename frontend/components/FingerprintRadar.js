"use client";

import { useEffect, useState } from "react";

import { fetchFingerprint } from "../lib/api";

const COMPARISON_OPTIONS = ["ALL", "D", "R"];
const SVG_WIDTH = 560;
const SVG_HEIGHT = 480;
const CENTER_X = SVG_WIDTH / 2;
const CENTER_Y = 248;
const RADIUS = 152;
const LABEL_DISTANCE = 1.25;

export default function FingerprintRadar({
  legislatorId = "leg_alex_morgan",
  title = "Alex Morgan",
}) {
  const [comparisonParty, setComparisonParty] = useState("ALL");
  const [state, setState] = useState({
    status: "loading",
    payload: null,
    error: null,
  });

  useEffect(() => {
    let active = true;

    async function loadFingerprint() {
      setState((current) => ({
        ...current,
        status: "loading",
        error: null,
      }));

      try {
        const payload = await fetchFingerprint({ legislatorId, comparisonParty });
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
          error: "Fingerprint data is unavailable for this legislator right now.",
        });
      }
    }

    loadFingerprint();

    return () => {
      active = false;
    };
  }, [comparisonParty, legislatorId]);

  const fingerprintRows = state.payload?.fingerprint || [];
  const fingerprintPolygon = buildPolygonPoints(fingerprintRows, "vote_share");
  const medianPolygon = buildPolygonPoints(fingerprintRows, "median_share");
  const topDomains = [...fingerprintRows]
    .sort((left, right) => right.vote_share - left.vote_share)
    .filter((row) => row.vote_share > 0)
    .slice(0, 2);
  const focusSummary = buildFocusSummary(topDomains);

  return (
    <section className="mt-12 grid gap-6 rounded-[2.5rem] border border-stone-300/80 bg-white/72 p-6 shadow-[0_20px_80px_rgba(72,52,24,0.12)] backdrop-blur lg:grid-cols-[1.1fr_0.9fr] lg:p-7">
      <div>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-stone-500">
              Issue Focus
            </p>
            <h2 className="mt-2 font-serif text-[2.65rem] leading-[0.95] text-stone-900">
              {title}
            </h2>
          </div>
          <div className="flex rounded-full border border-stone-300 bg-stone-100 p-1 shadow-[inset_0_1px_0_rgba(255,255,255,0.75)]">
            {COMPARISON_OPTIONS.map((option) => (
              <button
                key={option}
                className={`rounded-full px-4 py-2 text-xs tracking-[0.25em] transition ${
                  comparisonParty === option
                    ? "bg-stone-900 text-stone-100 shadow-[0_6px_18px_rgba(28,25,23,0.18)]"
                    : "text-stone-600 hover:text-stone-900"
                }`}
                onClick={() => setComparisonParty(option)}
                type="button"
              >
                {option}
              </button>
            ))}
          </div>
        </div>
        <div className="mt-6 flex justify-center overflow-x-auto rounded-[2rem] bg-[linear-gradient(180deg,rgba(255,255,255,0.74),rgba(244,239,231,0.56))] px-3 py-4">
          <svg
            aria-label="Fingerprint radar chart"
            className="h-[450px] w-[540px] min-w-[540px]"
            viewBox={`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`}
          >
            {[0.2, 0.4, 0.6, 0.8, 1].map((ratio) => (
              <polygon
                key={ratio}
                fill="none"
                points={buildGridPolygon(ratio)}
                stroke="rgba(120,113,108,0.28)"
                strokeWidth="1"
              />
            ))}
            {fingerprintRows.map((row, index) => {
              const { x, y } = getAxisPoint(index, LABEL_DISTANCE);
              const line = getAxisPoint(index, 1);
              const lines = formatDomainLabel(row.domain).split(" ");
              return (
                <g key={row.domain}>
                  <line
                    x1={CENTER_X}
                    y1={CENTER_Y}
                    x2={line.x}
                    y2={line.y}
                    stroke="rgba(120,113,108,0.35)"
                    strokeWidth="1"
                  />
                  <text
                    fill="#57534e"
                    fontSize="13"
                    textAnchor={x < CENTER_X - 10 ? "end" : x > CENTER_X + 10 ? "start" : "middle"}
                    x={x}
                    y={y}
                  >
                    {lines.map((lineLabel, lineIndex) => (
                      <tspan
                        dy={lineIndex === 0 ? 0 : 16}
                        key={`${row.domain}-${lineLabel}`}
                        x={x}
                      >
                        {lineLabel}
                      </tspan>
                    ))}
                  </text>
                </g>
              );
            })}
            {fingerprintPolygon ? (
              <polygon
                fill="rgba(161,98,7,0.22)"
                points={fingerprintPolygon}
                stroke="#a16207"
                strokeWidth="3"
              />
            ) : null}
            {medianPolygon ? (
              <>
                <polygon
                  fill="rgba(16,185,129,0.08)"
                  points={medianPolygon}
                  stroke="rgba(4,120,87,0.26)"
                  strokeWidth="8"
                />
                <polygon
                  fill="none"
                  points={medianPolygon}
                  stroke="#047857"
                  strokeDasharray="10 8"
                  strokeLinecap="round"
                  strokeWidth="4"
                />
              </>
            ) : null}
          </svg>
        </div>
      </div>
        <div className="flex flex-col justify-between gap-6">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-stone-500">
              Reading The Chart
            </p>
          <p className="mt-3 max-w-md text-base leading-7 text-stone-700">
            The amber shape shows where this legislator's recent eligible votes are concentrated. The green dashed overlay shows the chamber median for the selected comparison group.
          </p>
          {state.status === "ready" ? (
            <p className="mt-3 max-w-md text-base leading-7 text-stone-900">
              {focusSummary}
            </p>
          ) : null}
          <div className="mt-4 flex flex-wrap gap-4">
            <LegendSwatch
              label="Legislator fingerprint"
              sampleClassName="bg-amber-700"
            />
            <LegendSwatch
              dashed
              label="Chamber median overlay"
              sampleClassName="bg-emerald-700"
            />
          </div>
          </div>
        <div className="grid gap-3 sm:grid-cols-3">
          <HighlightCard
            label="Eligible Votes"
            value={state.status === "ready" ? String(fingerprintRows[0]?.total_votes ?? 0) : "--"}
          />
          <HighlightCard
            label="Top Domain"
            value={state.status === "ready" ? formatDomainLabel(topDomains[0]?.domain || "NONE") : "--"}
          />
          <HighlightCard
            label="Overlay"
            value={comparisonParty}
          />
        </div>
        <div className="grid gap-3 sm:grid-cols-3">
          <ProvenanceCard
            label="Last Updated"
            value={state.status === "ready" ? formatTimestamp(state.payload?.last_updated) : "--"}
          />
          <ProvenanceCard
            label="Window End"
            value={state.status === "ready" ? state.payload?.window_end : "--"}
          />
          <ProvenanceCard
            label="Version"
            value={state.status === "ready" ? state.payload?.classification_version : "--"}
          />
        </div>
        <div className="rounded-[2rem] bg-stone-950 px-5 py-5 text-stone-100">
          <p className="text-xs uppercase tracking-[0.3em] text-stone-400">
            Status
          </p>
          <p className="mt-3 text-lg text-stone-50">
            {state.status === "loading" ? "Loading fingerprint..." : null}
            {state.status === "error" ? "Fingerprint unavailable" : null}
            {state.status === "ready" ? `Loaded ${fingerprintRows.length} domains.` : null}
          </p>
          <p className="mt-2 text-base leading-7 text-stone-300">
            {state.status === "loading" ? "Waiting for the backend fingerprint response." : null}
            {state.status === "error" ? `${state.error} Try choosing another legislator or checking the backend.` : null}
            {state.status === "ready"
              ? `This profile is based on ${fingerprintRows[0]?.total_votes ?? 0} eligible votes in the current 730-day window. Comparison overlay: ${comparisonParty}.`
              : null}
          </p>
        </div>
        <article className="rounded-[1.8rem] border border-amber-200 bg-amber-50/80 px-4 py-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.75)]">
          <p className="text-xs uppercase tracking-[0.25em] text-amber-800">
            What It Means
          </p>
          <p className="mt-3 text-base leading-7 text-stone-700">
            This does not score ideology. It shows which issue domains absorb the largest share of this legislator's eligible policy votes over the last two years.
          </p>
        </article>
        <div className="grid gap-3 sm:grid-cols-2">
          {state.status === "ready" && fingerprintRows.length === 0 ? (
            <div className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-4 text-sm text-stone-600 sm:col-span-2">
              No fingerprint rows are available for this legislator yet.
            </div>
          ) : null}
          {fingerprintRows.map((row) => (
            <div
              key={row.domain}
              className={`rounded-2xl border px-4 py-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.7)] ${
                row.vote_share > 0
                  ? "border-amber-200 bg-amber-50/55"
                  : "border-stone-200 bg-stone-50"
              }`}
            >
              <div className="flex items-center justify-between gap-3">
                <p className="text-[15px] font-medium text-stone-800">
                  {formatDomainLabel(row.domain)}
                </p>
                <p className="text-[15px] text-stone-600">
                  {(row.vote_share * 100).toFixed(0)}%
                </p>
              </div>
              <div className="mt-3 h-2 rounded-full bg-stone-200">
                <div
                  className="h-2 rounded-full bg-amber-700"
                  style={{ width: `${row.vote_share * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function buildPolygonPoints(rows, valueKey) {
  if (!rows.length) {
    return "";
  }

  return rows
    .map((row, index) => {
      const { x, y } = getAxisPoint(index, row[valueKey]);
      return `${x},${y}`;
    })
    .join(" ");
}

function buildGridPolygon(ratio) {
  return Array.from({ length: 8 }, (_, index) => {
    const { x, y } = getAxisPoint(index, ratio);
    return `${x},${y}`;
  }).join(" ");
}

function getAxisPoint(index, ratio) {
  const angle = (-Math.PI / 2) + (index * (Math.PI * 2)) / 8;
  const distance = RADIUS * ratio;
  return {
    x: CENTER_X + Math.cos(angle) * distance,
    y: CENTER_Y + Math.sin(angle) * distance,
  };
}

function formatDomainLabel(domain) {
  return domain
    .split("_")
    .map((segment) => segment[0] + segment.slice(1).toLowerCase())
    .join(" ");
}

function buildFocusSummary(topDomains) {
  if (!topDomains.length) {
    return "No eligible issue-focus signal is available in the current two-year window.";
  }

  if (topDomains.length === 1) {
    return `Right now, the clearest concentration is ${formatDomainLabel(topDomains[0].domain)} at ${(topDomains[0].vote_share * 100).toFixed(0)}% of eligible votes.`;
  }

  return `Right now, the clearest concentrations are ${formatDomainLabel(topDomains[0].domain)} at ${(topDomains[0].vote_share * 100).toFixed(0)}% and ${formatDomainLabel(topDomains[1].domain)} at ${(topDomains[1].vote_share * 100).toFixed(0)}% of eligible votes.`;
}

function ProvenanceCard({ label, value }) {
  return (
    <div className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.72)]">
      <p className="text-xs uppercase tracking-[0.22em] text-stone-500">{label}</p>
      <p className="mt-3 text-sm leading-6 text-stone-800 break-words">{value}</p>
    </div>
  );
}

function HighlightCard({ label, value }) {
  return (
    <div className="rounded-2xl border border-stone-200 bg-[linear-gradient(180deg,rgba(255,255,255,0.78),rgba(245,241,233,0.95))] px-4 py-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.75)]">
      <p className="text-xs uppercase tracking-[0.25em] text-stone-500">{label}</p>
      <p className="mt-3 text-lg leading-6 text-stone-900">{value}</p>
    </div>
  );
}

function LegendSwatch({ dashed = false, label, sampleClassName }) {
  return (
    <div className="flex items-center gap-2">
      <span
        aria-hidden="true"
        className={`block h-[4px] w-10 rounded-full ${sampleClassName}`}
        style={
          dashed
            ? {
                backgroundColor: "transparent",
                backgroundImage:
                  "repeating-linear-gradient(90deg, #047857 0 12px, transparent 12px 20px)",
              }
            : undefined
        }
      />
      <span className="text-[11px] uppercase tracking-[0.18em] text-stone-600">
        {label}
      </span>
    </div>
  );
}

function formatTimestamp(value) {
  if (!value) {
    return "--";
  }

  return String(value).replace("T", " ").replace("+00:00", " UTC");
}
