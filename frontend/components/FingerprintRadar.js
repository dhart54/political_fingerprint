"use client";

import { useEffect, useState } from "react";

import { fetchFingerprint } from "../lib/api";

const COMPARISON_OPTIONS = ["ALL", "D", "R"];
const SVG_WIDTH = 560;
const SVG_HEIGHT = 500;
const CENTER_X = SVG_WIDTH / 2;
const CENTER_Y = 256;
const RADIUS = 156;
const LABEL_DISTANCE = 1.22;

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
          error: error instanceof Error ? error.message : "Fingerprint request failed.",
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

  return (
    <section className="mt-14 grid gap-8 rounded-[2.5rem] border border-stone-300/80 bg-white/72 p-6 shadow-[0_20px_80px_rgba(72,52,24,0.12)] backdrop-blur lg:grid-cols-[1.18fr_0.82fr] lg:p-8">
      <div>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-stone-500">
              Fingerprint Radar
            </p>
            <h2 className="mt-2 font-serif text-3xl text-stone-900">
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
        <div className="mt-8 flex justify-center overflow-x-auto rounded-[2rem] bg-[linear-gradient(180deg,rgba(255,255,255,0.7),rgba(244,239,231,0.55))] px-2 py-4">
          <svg
            aria-label="Fingerprint radar chart"
            className="h-[460px] w-[520px] min-w-[520px]"
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
            {medianPolygon ? (
              <polygon
                fill="rgba(20,83,45,0.14)"
                points={medianPolygon}
                stroke="#166534"
                strokeDasharray="6 6"
                strokeWidth="2"
              />
            ) : null}
            {fingerprintPolygon ? (
              <polygon
                fill="rgba(161,98,7,0.22)"
                points={fingerprintPolygon}
                stroke="#a16207"
                strokeWidth="3"
              />
            ) : null}
          </svg>
        </div>
      </div>
      <div className="flex flex-col justify-between gap-6">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-stone-500">
            Overlay
          </p>
          <p className="mt-3 max-w-md text-sm leading-6 text-stone-700">
            The amber shape is the legislator fingerprint. The green dashed overlay is the chamber median for the selected comparison party.
          </p>
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
          <p className="mt-2 text-sm leading-6 text-stone-300">
            {state.status === "loading" ? "Waiting for the backend fingerprint response." : null}
            {state.status === "error" ? state.error : null}
            {state.status === "ready"
              ? `Comparison overlay: ${comparisonParty}. Total eligible votes in the current fingerprint: ${fingerprintRows[0]?.total_votes ?? 0}.`
              : null}
          </p>
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          {fingerprintRows.map((row) => (
            <div
              key={row.domain}
              className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.7)]"
            >
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-medium text-stone-800">
                  {formatDomainLabel(row.domain)}
                </p>
                <p className="text-sm text-stone-600">
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
