"use client";

import { useEffect, useState } from "react";

import { fetchDrift, fetchFingerprint, fetchPositions } from "../lib/api";
import { getBestIssueRead } from "../lib/issueReadiness.mjs";
import { formatDomainLabel } from "../lib/issueDomains";

export default function ProfileQuickRead({ legislator, onInspectDomain }) {
  const [state, setState] = useState({
    status: "loading",
    fingerprint: null,
    positions: null,
    drift: null,
    error: null,
  });

  useEffect(() => {
    let active = true;

    async function loadProfileRead() {
      setState({
        status: "loading",
        fingerprint: null,
        positions: null,
        drift: null,
        error: null,
      });

      try {
        const [fingerprint, positions, drift] = await Promise.all([
          fetchFingerprint({ legislatorId: legislator.id }),
          fetchPositions({ legislatorId: legislator.id }),
          fetchDrift({ legislatorId: legislator.id }),
        ]);

        if (!active) {
          return;
        }

        setState({
          status: "ready",
          fingerprint,
          positions,
          drift,
          error: null,
        });
      } catch (error) {
        if (!active) {
          return;
        }

        setState({
          status: "error",
          fingerprint: null,
          positions: null,
          drift: null,
          error: "The quick read is unavailable right now.",
        });
      }
    }

    loadProfileRead();

    return () => {
      active = false;
    };
  }, [legislator.id]);

  const fingerprintRows = state.fingerprint?.fingerprint || [];
  const positionRows = state.positions?.positions || [];
  const topFocus = buildTopFocus(fingerprintRows);
  const topPosition = buildTopPosition(positionRows);
  const coverage = buildCoverage(fingerprintRows);
  const drift = buildDriftRead(state.drift);
  const sixtySecondRead = buildSixtySecondRead({
    status: state.status,
    topFocus,
    topPosition,
    coverage,
    drift,
  });

  return (
    <section className="mt-4 rounded-2xl border border-cyan-900/10 bg-[linear-gradient(135deg,#083344,#115e59)] px-4 py-4 text-white shadow-[0_14px_36px_rgba(15,23,42,0.14)] lg:px-5">
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.1fr)_minmax(340px,0.9fr)] lg:items-start">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-cyan-100">
            Quick Read
          </p>
          <h3 className="mt-2 max-w-[780px] font-serif text-[1.85rem] leading-[1.05] text-white sm:text-[2.25rem]">
            {buildHeadline({
              status: state.status,
              name: legislator.name_display,
              topFocus,
              topPosition,
            })}
          </h3>
          <p className="mt-3 max-w-3xl text-[14px] leading-6 text-cyan-50">
            {state.status === "loading"
              ? "Loading the profile summary from the same deterministic data used below."
              : null}
            {state.status === "error" ? state.error : null}
            {state.status === "ready"
              ? sixtySecondRead
              : null}
          </p>
        </div>
        <div className="grid gap-2 sm:grid-cols-3 lg:grid-cols-1">
          <QuickCard
            eyebrow="Best issue read"
            label={state.status === "ready" ? topPosition.label : "Loading"}
            onInspect={
              state.status === "ready" && topPosition.domain !== "NONE"
                ? () => onInspectDomain?.(topPosition.domain)
                : null
            }
            value={state.status === "ready" ? topPosition.value : "--"}
          />
          <QuickCard
            eyebrow="Coverage"
            label={state.status === "ready" ? coverage.label : "Loading"}
            value={state.status === "ready" ? coverage.value : "--"}
          />
          <QuickCard
            eyebrow="Change context"
            label={state.status === "ready" ? drift.label : "Loading"}
            value={state.status === "ready" ? drift.value : "--"}
          />
        </div>
      </div>

      {state.status === "ready" && topPosition.domain !== "NONE" ? (
        <div className="mt-3 rounded-xl border border-white/10 bg-white/10 px-3 py-3">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-cyan-100">
                Start Here
              </p>
              <p className="mt-1 text-[15px] leading-6 text-white">
                {buildStartHereCopy({ topFocus, topPosition })}
              </p>
            </div>
            <button
              className="w-fit rounded-full bg-white px-4 py-2 text-xs uppercase tracking-[0.18em] text-cyan-950 transition hover:bg-cyan-50"
              onClick={() => onInspectDomain?.(topPosition.domain)}
              type="button"
            >
              Open Best Read
            </button>
          </div>
        </div>
      ) : null}
    </section>
  );
}

function QuickCard({ eyebrow, label, onInspect, value }) {
  return (
    <article className="rounded-xl border border-white/10 bg-white/10 px-3 py-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.12)]">
      <p className="text-[11px] uppercase tracking-[0.18em] text-cyan-100">{eyebrow}</p>
      <p className="mt-2 text-[1.35rem] leading-none text-white">{value}</p>
      <p className="mt-2 text-xs leading-5 text-cyan-50">{label}</p>
      {onInspect ? (
        <button
          className="mt-3 rounded-full border border-white/20 bg-white/10 px-3 py-2 text-[11px] uppercase tracking-[0.16em] text-white transition hover:bg-white/20"
          onClick={onInspect}
          type="button"
        >
          Open Votes
        </button>
      ) : null}
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

function buildSixtySecondRead({ status, topFocus, topPosition, coverage, drift }) {
  if (status !== "ready") {
    return "";
  }
  if (topPosition.domain === "NONE") {
    return "In 60 seconds, you can see where evidence exists, where it is too limited, and why the page avoids a confident issue read.";
  }
  if (topFocus.domain !== topPosition.domain) {
    return `In 60 seconds, start with ${formatDomainLabel(topPosition.domain)} for reviewed vote meaning. ${topFocus.label} has more recorded votes, but the clearest evidence is elsewhere. ${coverage.value}; ${drift.label}`;
  }
  return `In 60 seconds, start with ${formatDomainLabel(topPosition.domain)} because it has the clearest reviewed vote meaning. ${coverage.value}; ${drift.label}`;
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
    value:
      strongest.readiness?.key === "mixed_but_interpretable"
        ? "Mixed"
        : strongest.readiness?.key === "limited_evidence"
          ? "Limited"
          : "Strong",
  };
}

function buildCoverage(rows) {
  const totalVotes = rows[0]?.total_votes || 0;
  return {
    label: `${totalVotes} eligible votes in the current two-year window.`,
    value: `${totalVotes} votes`,
  };
}

function buildDriftRead(drift) {
  if (!drift) {
    return {
      label: "Change-over-time data is not available.",
      value: "--",
    };
  }

  if (drift.insufficient_data) {
    return {
      label: "Not enough eligible votes to compare early and recent issue mix.",
      value: "Insufficient",
    };
  }

  const driftValue = drift.drift_value || 0;
  if (driftValue >= 0.6) {
    return {
      label: `Issue mix changed noticeably across the two-year window (${driftValue.toFixed(2)}).`,
      value: "Shifted mix",
    };
  }
  if (driftValue >= 0.3) {
    return {
      label: `Issue mix changed somewhat across the two-year window (${driftValue.toFixed(2)}).`,
      value: "Some shift",
    };
  }
  return {
    label: `Issue mix looks broadly steady across the two-year window (${driftValue.toFixed(2)}).`,
    value: "Steady mix",
  };
}
