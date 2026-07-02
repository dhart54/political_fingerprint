"use client";

import { useEffect, useState } from "react";

import { fetchFingerprint, fetchPositionEvidence, fetchPositions } from "../lib/api";
import { getBestIssueRead } from "../lib/issueReadiness.mjs";
import { formatDomainLabel } from "../lib/issueDomains";
import { fillMissingInterpretedCounts } from "../lib/positionEvidenceCounts.mjs";
import { buildRecordNarrative } from "../lib/profileNarrative.mjs";

export default function ProfileQuickRead({ legislator, onInspectDomain, onProfileRead, scope = "all" }) {
  const [state, setState] = useState({
    status: "loading",
    fingerprint: null,
    positions: null,
    error: null,
  });

  useEffect(() => {
    let active = true;

    async function loadProfileRead() {
      setState({
        status: "loading",
        fingerprint: null,
        positions: null,
        error: null,
      });

      try {
        const [fingerprint, positionsPayload] = await Promise.all([
          fetchFingerprint({ legislatorId: legislator.id, scope }),
          fetchPositions({ legislatorId: legislator.id, scope }),
        ]);
        const positions = await fillMissingInterpretedCounts({
          payload: positionsPayload,
          fetchEvidence: (args) => fetchPositionEvidence({ ...args, scope }),
          legislatorId: legislator.id,
        });

        if (!active) {
          return;
        }

        setState({
          status: "ready",
          fingerprint,
          positions,
          error: null,
        });
        onProfileRead?.({
          fingerprint,
          positions,
        });
      } catch (error) {
        if (!active) {
          return;
        }

        setState({
          status: "error",
          fingerprint: null,
          positions: null,
          error: "The quick read is unavailable right now.",
        });
      }
    }

    loadProfileRead();

    return () => {
      active = false;
    };
  }, [legislator.id, scope]);

  const fingerprintRows = state.fingerprint?.fingerprint || [];
  const positionRows = state.positions?.positions || [];
  const topFocus = buildTopFocus(fingerprintRows);
  const topPosition = buildTopPosition(positionRows);
  const coverage = buildCoverage(fingerprintRows);
  const narrative = buildRecordNarrative({
    legislator,
    positions: positionRows,
    scope,
  });
  const scopeRead = buildScopeRead({ scope, positions: state.positions });

  return (
    <section className="mt-3 rounded-2xl border border-cyan-900/10 bg-[linear-gradient(135deg,#083344,#115e59)] px-4 py-3 text-white shadow-[0_10px_28px_rgba(15,23,42,0.12)] lg:px-5">
      <div className="grid gap-3 xl:grid-cols-[minmax(0,1fr)_minmax(420px,0.8fr)] xl:items-start">
        <div className="min-w-0">
          <p className="text-xs uppercase tracking-[0.2em] text-cyan-100">
            Record Summary
          </p>
          <h3 className="mt-1 max-w-[820px] font-serif text-[1.45rem] leading-[1.08] text-white sm:text-[1.85rem]">
            {state.status === "ready"
              ? narrative.headline
              : buildHeadline({
                  status: state.status,
                  name: legislator.name_display,
                  topFocus,
                  topPosition,
                })}
          </h3>
          <p className="mt-2 max-w-4xl text-[13px] leading-5 text-cyan-50">
            {state.status === "loading"
              ? "Loading the profile summary from the same deterministic data used below."
              : null}
            {state.status === "error" ? state.error : null}
            {state.status === "ready"
              ? narrative.body
              : null}
          </p>
          {state.status === "ready" ? (
            <p className="mt-2 text-[12px] leading-5 text-cyan-100">
              {narrative.evidenceLine}
            </p>
          ) : null}
          {state.status === "ready" && scopeRead ? (
            <p className="mt-2 max-w-4xl rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-[12px] leading-5 text-cyan-50">
              {scopeRead}
            </p>
          ) : null}
        </div>
        <div className="grid shrink-0 gap-2 sm:grid-cols-3">
          <QuickMetric eyebrow="Strongest evidence" value={state.status === "ready" ? topPosition.metricDomain : "--"} />
          <QuickMetric eyebrow="Coverage" value={state.status === "ready" ? coverage.value : "--"} />
          <QuickMetric eyebrow="Record read" value={state.status === "ready" ? topPosition.value : "--"} />
        </div>
      </div>

      {state.status === "ready" && narrative.patternRows.length > 0 ? (
        <div className="mt-3 grid gap-2 border-t border-white/10 pt-3 md:grid-cols-2 xl:grid-cols-4">
          {narrative.patternRows.map((row) => (
            <button
              className="rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-left transition hover:bg-white/15"
              key={row.domain}
              onClick={() => onInspectDomain?.(row.domain)}
              type="button"
            >
              <p className="text-[11px] uppercase tracking-[0.16em] text-cyan-100">
                {formatDomainLabel(row.domain)}
              </p>
              <p className="mt-1 text-sm font-medium leading-5 text-white">
                {row.preview.status}
              </p>
              <p className="mt-1 text-xs leading-4 text-cyan-50">
                {row.preview.countLine}
              </p>
              <p className="mt-1 text-xs leading-4 text-cyan-50">
                {row.preview.themeLine}
              </p>
            </button>
          ))}
        </div>
      ) : null}

      {state.status === "ready" && topPosition.domain !== "NONE" ? (
        <div className="mt-3 flex flex-col gap-2 border-t border-white/10 pt-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm leading-5 text-cyan-50">
            {buildStartHereCopy({ topFocus, topPosition })}
          </p>
          <button
            className="w-fit rounded-full bg-white px-4 py-2 text-xs uppercase tracking-[0.16em] text-cyan-950 transition hover:bg-cyan-50"
            onClick={() => onInspectDomain?.(topPosition.domain)}
            type="button"
          >
            Open Best Read
          </button>
        </div>
      ) : null}
    </section>
  );
}

function QuickMetric({ eyebrow, value }) {
  return (
    <article className="rounded-xl border border-white/10 bg-white/10 px-3 py-2 shadow-[inset_0_1px_0_rgba(255,255,255,0.12)]">
      <p className="text-[11px] uppercase tracking-[0.18em] text-cyan-100">{eyebrow}</p>
      <p className="mt-1 text-[1.15rem] leading-none text-white">{value}</p>
    </article>
  );
}

function buildHeadline({ status, name, topFocus, topPosition }) {
  if (status === "loading") {
    return `Reading ${name}'s voting record...`;
  }

  if (status === "error") {
    return `The quick read for ${name} is unavailable.`;
  }

  if (topFocus.domain === "NONE") {
    return `${name} does not have enough eligible policy votes for a clear read yet.`;
  }

  if (topPosition.domain === "NONE") {
    return `${name}'s profile has recorded votes, but no issue area has enough reviewed vote meaning for a confident first read yet.`;
  }

  if (topFocus.domain !== topPosition.domain) {
    return `Start with ${formatDomainLabel(topPosition.domain)}. It has the clearest reviewed vote meaning in this profile.`;
  }

  return `Start with ${formatDomainLabel(topPosition.domain)}. It has both the clearest reviewed vote meaning and the largest recorded-vote footprint in this profile.`;
}

function buildStartHereCopy({ topFocus, topPosition }) {
  const bestIssue = formatDomainLabel(topPosition.domain);
  if (topFocus.domain !== topPosition.domain && topFocus.domain !== "NONE") {
    return `Open ${bestIssue} first. It has the clearest reviewed vote meaning; ${topFocus.label} has more recorded votes but is not the best first read.`;
  }
  return `Open ${bestIssue} first. It is the clearest reviewed issue read, and limited issue sections are intentionally lower priority.`;
}

function buildTopFocus(rows) {
  const strongest = [...rows]
    .filter((row) => (row?.vote_share || 0) > 0)
    .sort((left, right) => (right.vote_share || 0) - (left.vote_share || 0))[0];

  if (!strongest) {
    return {
      domain: "NONE",
      label: "No strong issue focus",
      value: "0%",
    };
  }

  return {
    domain: strongest.domain,
    label: formatDomainLabel(strongest.domain),
    value: `${((strongest.vote_share || 0) * 100).toFixed(0)}%`,
  };
}

function buildTopPosition(rows) {
  const strongest = getBestIssueRead(rows);

  if (!strongest) {
    return {
      shortLabel: "no confident issue read",
      domain: "NONE",
      label: "No issue has enough reviewed Yes/No vote meaning for a confident read in the current window.",
      metricDomain: "--",
      value: "--",
    };
  }

  const interpretedYeaNay = (strongest.interpreted_support_count || 0) + (strongest.interpreted_oppose_count || 0);
  const gap = Math.abs((strongest.yea_share || 0) - (strongest.nay_share || 0));
  let direction = "Mixed record in votes shown";
  if (!interpretedYeaNay) {
    direction = "Too little interpreted evidence";
  } else if (gap >= 0.15) {
    direction = strongest.yea_share >= strongest.nay_share ? "Mostly Yea in votes shown" : "Mostly Nay in votes shown";
  }
  return {
    shortLabel: `${strongest.readiness?.label || direction} in ${formatDomainLabel(strongest.domain)}`,
    domain: strongest.domain,
    label: `${formatDomainLabel(strongest.domain)} has ${strongest.recorded_votes} recorded votes in this window; ${interpretedYeaNay} reviewed Yes/No votes can be summarized.`,
    metricDomain: formatDomainLabel(strongest.domain),
    value:
      strongest.readiness?.key === "mixed_but_interpretable"
        ? "Mixed but interpretable"
        : strongest.readiness?.key === "limited_evidence"
          ? "Limited reviewed evidence"
          : "Strong reviewed sample",
  };
}

function buildCoverage(rows) {
  const totalVotes = rows[0]?.total_votes || 0;
  return {
    label: `${totalVotes} eligible votes in the selected profile scope.`,
    value: `${totalVotes} votes`,
  };
}

function buildScopeRead({ scope, positions }) {
  const metadata = positions?.scope_metadata;
  const coverage = metadata?.congresses?.length
    ? `Includes votes from ${formatYearRange(metadata.window_start, metadata.window_end)}.`
    : "";
  if (scope !== "all") {
    return [metadata?.scope_label ? `${metadata.scope_label} (${metadata.requested_congresses?.join(", ")}th).` : "", coverage]
      .filter(Boolean)
      .join(" ");
  }

  if (metadata?.congresses?.length > 1) {
    return `${coverage} Congress-specific counts are shown separately below.`.trim();
  }
  return coverage;
}

function formatYearRange(start, end) {
  const startYear = start ? String(start).slice(0, 4) : "";
  const endYear = end ? String(end).slice(0, 4) : "";
  if (startYear && endYear && startYear !== endYear) {
    return `${startYear}-${endYear}`;
  }
  return startYear || endYear || "the selected period";
}
