"use client";

import { useEffect, useState } from "react";

import { fetchEditorialPresentations, fetchFingerprint, fetchPositions } from "../lib/api";
import { hasAvailableIssueEvidence } from "../lib/basicEvidencePresentation.mjs";
import { getEditorialPresentation } from "../lib/editorialPresentation.mjs";
import { formatDomainLabel } from "../lib/issueDomains";
import {
  getDomainDescription,
  getEvidenceCoverage,
  getRecordedActionComposition,
  orderIssueRowsByEvidenceUsefulness,
  pluralizeCountNoun,
} from "../lib/issueEvidenceCoverage.mjs";

export default function ProfileQuickRead({ fixtureData = null, legislator, onInspectDomain, onProfileRead, scope = "all" }) {
  const [state, setState] = useState({
    status: "loading",
    fingerprint: null,
    positions: null,
    presentations: null,
    error: null,
  });

  useEffect(() => {
    let active = true;

    async function loadProfileRead() {
      setState({
        status: "loading",
        fingerprint: null,
        positions: null,
        presentations: null,
        error: null,
      });

      try {
        if (fixtureData) {
          const fingerprint = fixtureData.fingerprint || { fingerprint: [] };
          const positions = fixtureData.positions || { positions: [] };
          const presentations = fixtureData.presentations || { presentations: [] };
          if (active) {
            setState({
              status: "ready",
              fingerprint,
              positions,
              presentations,
              error: null,
            });
            onProfileRead?.({
              fingerprint,
              positions,
            });
          }
          return;
        }

        const [fingerprint, positions, presentations] = await Promise.all([
          fetchFingerprint({ legislatorId: legislator.id, scope }),
          fetchPositions({ legislatorId: legislator.id, scope }),
          fetchEditorialPresentations({ legislatorId: legislator.id, scope }).catch(() => ({ presentations: [] })),
        ]);

        if (!active) {
          return;
        }

        setState({
          status: "ready",
          fingerprint,
          positions,
          presentations,
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
          presentations: null,
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
  const availableRows = orderIssueRowsByEvidenceUsefulness(
    positionRows.filter(hasAvailableIssueEvidence),
  );
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
            <IssueEvidenceCard
              key={row.domain}
              onClick={() => onInspectDomain?.(row.domain)}
              presentation={getEditorialPresentation(
                state.presentations,
                row.domain,
                {
                  legislatorId: legislator.id,
                  memberBioguideId: legislator.bioguide_id,
                },
              )}
              row={row}
            />
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

function IssueEvidenceCard({ onClick, presentation, row }) {
  const coverage = getEvidenceCoverage(row);
  const composition = getRecordedActionComposition(row);

  return (
    <button
      aria-label={`Inspect ${formatDomainLabel(row.domain)} votes`}
      className="rounded-xl border border-white/10 bg-white/10 px-3 py-3 text-left transition hover:bg-white/15 focus:outline-none focus:ring-2 focus:ring-cyan-100 focus:ring-offset-2 focus:ring-offset-cyan-950"
      onClick={onClick}
      type="button"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-[11px] uppercase tracking-[0.16em] text-cyan-100">
          {formatDomainLabel(row.domain)}
        </p>
        {presentation ? (
          <span className="rounded-full border border-white/15 bg-white/10 px-2 py-1 text-[10px] uppercase tracking-[0.12em] text-cyan-50">
            {presentation.tier_badge}
          </span>
        ) : null}
      </div>
      <p className="mt-2 text-xs leading-4 text-cyan-50">
        {getDomainDescription(row.domain)}
      </p>
      <p className="mt-2 text-sm font-medium leading-5 text-white">
        {formatAvailableActionCount(row)}
      </p>
      <p className="mt-0.5 text-[11px] leading-4 text-cyan-100">
        {coverage.reviewedYesNo} reviewed substantive Yes/No
      </p>
      {presentation ? (
        <p className="mt-2 rounded-lg border border-white/10 bg-white/5 px-2.5 py-2 text-xs leading-4 text-cyan-50">
          {presentation.teaser}
        </p>
      ) : null}
      <div className="mt-2" role="group" aria-label="Recorded action composition">
        <p className="text-[10px] uppercase tracking-[0.13em] text-cyan-100">
          Recorded action composition
        </p>
        <div aria-hidden="true" className="mt-1 flex h-1.5 overflow-hidden rounded-full bg-white/10">
          {composition.map((item) => (
            <span
              className={getCompositionSegmentClass(item.key)}
              key={item.key}
              style={{ width: `${item.percent}%` }}
            />
          ))}
        </div>
        <ul aria-label="Recorded action composition legend" className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-[10px] leading-4 text-cyan-50">
          {composition.map((item) => (
            <li className="flex items-center gap-1" key={item.key}>
              <span aria-hidden="true" className={`h-2 w-2 rounded-full ${getCompositionSegmentClass(item.key)}`} />
              <span>
                {item.label} <span className="font-medium text-white">{item.count}</span>
              </span>
            </li>
          ))}
        </ul>
      </div>
      <p className="mt-2 text-xs leading-4 text-white underline decoration-white/30 underline-offset-2">
        Open vote evidence
      </p>
    </button>
  );
}

function getCompositionSegmentClass(key) {
  if (key === "yea") {
    return "bg-cyan-200";
  }
  if (key === "nay") {
    return "bg-amber-200";
  }
  return "bg-stone-300";
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
  return `${count} ${pluralizeCountNoun(count, "recorded action")}`;
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
