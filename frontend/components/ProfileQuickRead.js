"use client";

import { useEffect, useState } from "react";

import { fetchDrift, fetchFingerprint, fetchPositions } from "../lib/api";
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
  const confidence = buildConfidence(fingerprintRows);
  const drift = buildDriftRead(state.drift);

  return (
    <section className="mt-4 rounded-[2rem] border border-cyan-900/10 bg-[linear-gradient(135deg,#083344,#115e59)] px-5 py-5 text-white shadow-[0_18px_48px_rgba(15,23,42,0.16)] lg:px-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-cyan-100">
            Quick Read
          </p>
          <h3 className="mt-2 max-w-[760px] font-serif text-[2rem] leading-[1] text-white sm:text-[2.45rem] sm:leading-[0.98]">
            {buildHeadline({
              status: state.status,
              name: legislator.name_display,
              topFocus,
              topPosition,
            })}
          </h3>
        </div>
        <p className="max-w-md text-[14px] leading-6 text-cyan-50">
          {state.status === "loading"
            ? "Loading the profile summary from the same deterministic data used below."
            : null}
          {state.status === "error" ? state.error : null}
          {state.status === "ready"
            ? "A voter-friendly read of issue focus, vote direction, data volume, and change over time."
            : null}
        </p>
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <QuickCard
          eyebrow="What They Vote On"
          label={state.status === "ready" ? topFocus.label : "Loading"}
          onInspect={
            state.status === "ready" && topFocus.domain !== "NONE"
              ? () => onInspectDomain?.(topFocus.domain)
              : null
          }
          value={state.status === "ready" ? topFocus.value : "--"}
        />
        <QuickCard
          eyebrow="How They Vote There"
          label={state.status === "ready" ? topPosition.label : "Loading"}
          onInspect={
            state.status === "ready" && topPosition.domain !== "NONE"
              ? () => onInspectDomain?.(topPosition.domain)
              : null
          }
          value={state.status === "ready" ? topPosition.value : "--"}
        />
        <QuickCard
          eyebrow="Data Confidence"
          label={state.status === "ready" ? confidence.label : "Loading"}
          value={state.status === "ready" ? confidence.value : "--"}
        />
        <QuickCard
          eyebrow="Change Over Time"
          label={state.status === "ready" ? drift.label : "Loading"}
          value={state.status === "ready" ? drift.value : "--"}
        />
      </div>
    </section>
  );
}

function QuickCard({ eyebrow, label, onInspect, value }) {
  return (
    <article className="rounded-[1.25rem] border border-white/10 bg-white/10 px-4 py-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.12)]">
      <p className="text-xs uppercase tracking-[0.24em] text-cyan-100">{eyebrow}</p>
      <p className="mt-3 text-[1.65rem] leading-none text-white">{value}</p>
      <p className="mt-3 text-sm leading-6 text-cyan-50">{label}</p>
      {onInspect ? (
        <button
          className="mt-4 rounded-full border border-white/20 bg-white/10 px-4 py-2 text-xs uppercase tracking-[0.18em] text-white transition hover:bg-white/20"
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
    return `${name} does not have enough eligible policy votes for a strong read yet.`;
  }

  return `${name}'s recent record centers on ${topFocus.label.toLowerCase()}, with ${topPosition.shortLabel.toLowerCase()} as the clearest vote-direction signal.`;
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
  const strongest = [...rows]
    .filter((row) => (row?.recorded_votes || 0) > 0)
    .sort((left, right) => (right.recorded_votes || 0) - (left.recorded_votes || 0))[0];

  if (!strongest) {
    return {
      shortLabel: "no clear vote direction",
      domain: "NONE",
      label: "No yea/nay split is available in the current window.",
      value: "--",
    };
  }

  const gap = Math.abs((strongest.yea_share || 0) - (strongest.nay_share || 0));
  const direction =
    gap < 0.15 ? "Mixed" : strongest.yea_share >= strongest.nay_share ? "Leans yea" : "Leans nay";
  const strongerShare = Math.max(strongest.yea_share || 0, strongest.nay_share || 0);

  return {
    shortLabel: `${direction} in ${formatDomainLabel(strongest.domain)}`,
    domain: strongest.domain,
    label: `${formatDomainLabel(strongest.domain)} has ${strongest.recorded_votes} recorded votes in this window.`,
    value: direction === "Mixed" ? "Mixed" : `${(strongerShare * 100).toFixed(0)}%`,
  };
}

function buildConfidence(rows) {
  const totalVotes = rows[0]?.total_votes || 0;
  if (totalVotes >= 50) {
    return {
      label: `${totalVotes} eligible votes in the current two-year window.`,
      value: "Strong",
    };
  }
  if (totalVotes >= 20) {
    return {
      label: `${totalVotes} eligible votes in the current two-year window.`,
      value: "Usable",
    };
  }
  return {
    label: `${totalVotes} eligible votes in the current two-year window.`,
    value: "Thin",
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
      label: `Drift score ${driftValue.toFixed(2)} across the two-year window.`,
      value: "Shifted",
    };
  }
  if (driftValue >= 0.3) {
    return {
      label: `Drift score ${driftValue.toFixed(2)} across the two-year window.`,
      value: "Changed",
    };
  }
  return {
    label: `Drift score ${driftValue.toFixed(2)} across the two-year window.`,
    value: "Steady",
  };
}
