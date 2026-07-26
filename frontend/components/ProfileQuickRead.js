"use client";

import { useEffect, useState } from "react";

import { fetchFingerprint, fetchPositions } from "../lib/api";
import { hasAvailableIssueEvidence } from "../lib/basicEvidencePresentation.mjs";
import { formatDomainLabel } from "../lib/issueDomains";

export default function ProfileQuickRead({ fixtureData = null, legislator, onInspectDomain, onProfileRead, scope = "all" }) {
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
        if (fixtureData) {
          const fingerprint = fixtureData.fingerprint || { fingerprint: [] };
          const positions = fixtureData.positions || { positions: [] };
          if (active) {
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
          }
          return;
        }

        const [fingerprint, positions] = await Promise.all([
          fetchFingerprint({ legislatorId: legislator.id, scope }),
          fetchPositions({ legislatorId: legislator.id, scope }),
        ]);

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
  }, [fixtureData, legislator.id, scope]);

  const positionRows = state.positions?.positions || [];
  const availableRows = positionRows.filter(hasAvailableIssueEvidence);
  const coverage = buildCoverage(availableRows);
  const scopeRead = buildScopeRead({ scope, positions: state.positions });

  return (
    <section className="mt-3 rounded-2xl border border-cyan-900/10 bg-[linear-gradient(135deg,#083344,#115e59)] px-4 py-3 text-white shadow-[0_10px_28px_rgba(15,23,42,0.12)] lg:px-5">
      <div className="grid gap-3 xl:grid-cols-[minmax(0,1fr)_minmax(420px,0.8fr)] xl:items-start">
        <div className="min-w-0">
          <p className="text-xs uppercase tracking-[0.2em] text-cyan-100">
            Record Coverage
          </p>
          <h3 className="mt-1 max-w-[820px] font-serif text-[1.45rem] leading-[1.08] text-white sm:text-[1.85rem]">
            {state.status === "ready"
              ? `${legislator.name_display}'s available issue records`
              : buildHeadline({ status: state.status, name: legislator.name_display })}
          </h3>
          <p className="mt-2 max-w-4xl text-[13px] leading-5 text-cyan-50">
            {state.status === "loading"
              ? "Loading available vote records from the same evidence used below."
              : null}
            {state.status === "error" ? state.error : null}
            {state.status === "ready"
              ? coverage.description
              : null}
          </p>
          {state.status === "ready" && scopeRead ? (
            <p className="mt-2 max-w-4xl rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-[12px] leading-5 text-cyan-50">
              {scopeRead}
            </p>
          ) : null}
        </div>
        <div className="grid shrink-0 gap-2 sm:grid-cols-3">
          <QuickMetric eyebrow="Available actions" value={state.status === "ready" ? coverage.voteCount : "--"} />
          <QuickMetric eyebrow="Issue areas" value={state.status === "ready" ? coverage.issueCount : "--"} />
          <QuickMetric eyebrow="Evidence view" value={state.status === "ready" ? "Vote receipts" : "--"} />
        </div>
      </div>

      {state.status === "ready" && availableRows.length > 0 ? (
        <div className="mt-3 grid gap-2 border-t border-white/10 pt-3 md:grid-cols-2 xl:grid-cols-4">
          {availableRows.map((row) => (
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
                {formatAvailableActionCount(row)}
              </p>
              <p className="mt-1 text-xs leading-4 text-cyan-50">
                Open vote evidence
              </p>
            </button>
          ))}
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

function buildHeadline({ status, name }) {
  if (status === "loading") {
    return `Reading ${name}'s voting record...`;
  }

  if (status === "error") {
    return `The quick read for ${name} is unavailable.`;
  }
  return `${name}'s available issue records`;
}

function buildCoverage(rows) {
  const totalVotes = rows.reduce((total, row) => total + getAvailableActionCount(row), 0);
  const issueCount = rows.length;
  return {
    description: issueCount
      ? `${totalVotes} recorded ${totalVotes === 1 ? "action is" : "actions are"} available across ${issueCount} issue ${issueCount === 1 ? "area" : "areas"}. Open an issue to inspect its vote receipts. These counts do not combine the actions into an analytical conclusion.`
      : "No vote records are available in the selected profile scope.",
    issueCount: String(issueCount),
    voteCount: String(totalVotes),
  };
}

function formatAvailableActionCount(row) {
  const count = getAvailableActionCount(row);
  return `${count} recorded ${count === 1 ? "action" : "actions"}`;
}

function getAvailableActionCount(row) {
  const total = Number(row?.total_votes);
  if (Number.isFinite(total) && total >= 0) {
    return total;
  }
  return Number(row?.yea_count || 0) + Number(row?.nay_count || 0) + Number(row?.other_count || 0);
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
