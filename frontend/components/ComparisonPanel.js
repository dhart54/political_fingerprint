"use client";

import { startTransition, useDeferredValue, useEffect, useState } from "react";

import { fetchAlignment, fetchLegislatorComparison, fetchLegislatorSearch } from "../lib/api";

const COMPARISON_OPTIONS = ["ALL", "D", "R"];

export default function ComparisonPanel({
  defaultLeftLegislator,
  defaultRightLegislator,
  onInspectDomain,
  preferences = {},
  seedPair,
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
  const [alignmentState, setAlignmentState] = useState({
    status: "idle",
    left: null,
    right: null,
    error: null,
  });

  useEffect(() => {
    if (!seedPair?.left || !seedPair?.right) {
      return;
    }

    setSelected({
      left: seedPair.left,
      right: seedPair.right,
    });
  }, [seedPair?.left?.id, seedPair?.right?.id]);

  useEffect(() => {
    setSelected((current) => {
      if (!defaultLeftLegislator?.id || current.left.id === defaultLeftLegislator.id) {
        return current;
      }

      return {
        ...current,
        left: defaultLeftLegislator,
      };
    });
  }, [defaultLeftLegislator?.id]);

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

  useEffect(() => {
    let active = true;
    const preferenceCount = Object.keys(preferences).length;

    if (preferenceCount === 0) {
      setAlignmentState({
        status: "idle",
        left: null,
        right: null,
        error: null,
      });
      return () => {
        active = false;
      };
    }

    async function loadAlignment() {
      setAlignmentState({
        status: "loading",
        left: null,
        right: null,
        error: null,
      });

      try {
        const [left, right] = await Promise.all([
          fetchAlignment({ legislatorId: selected.left.id, preferences }),
          fetchAlignment({ legislatorId: selected.right.id, preferences }),
        ]);
        if (!active) {
          return;
        }
        setAlignmentState({
          status: "ready",
          left,
          right,
          error: null,
        });
      } catch (error) {
        if (!active) {
          return;
        }
        setAlignmentState({
          status: "ready",
          left: buildFallbackAlignmentPayload({
            legislatorId: selected.left.id,
            preferences,
          }),
          right: buildFallbackAlignmentPayload({
            legislatorId: selected.right.id,
            preferences,
          }),
          error: null,
        });
      }
    }

    loadAlignment();

    return () => {
      active = false;
    };
  }, [selected.left.id, selected.right.id, preferences]);

  const comparisonInsight =
    compareState.status === "ready"
      ? buildComparisonInsight(compareState.payload)
      : null;

  return (
    <section className="mt-8 rounded-[2.5rem] border border-stone-300/80 bg-white/72 p-5 shadow-[0_20px_80px_rgba(72,52,24,0.12)] backdrop-blur xl:p-6">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-stone-500">
            Issue Comparison
          </p>
          <h2 className="mt-2 max-w-[820px] font-serif text-[2rem] leading-[1] text-stone-900 sm:text-[2.35rem] sm:leading-[0.95]">
            Compare both records against the same issues
          </h2>
          <p className="mt-3 max-w-2xl text-[15px] leading-7 text-stone-700">
            This section keeps your selected issues first. Vote direction and issue focus are available as supporting context only, so the comparison stays descriptive and does not rank either side.
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

      <div className="mt-5 rounded-[2rem] bg-stone-950 px-5 py-5 text-stone-100">
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
            {compareState.status === "loading" ? "Fetching issue focus and vote-direction data for both sides." : null}
            {compareState.status === "error" ? compareState.error : null}
            {compareState.status === "ready"
              ? `Overlay comparison is set to ${comparisonParty}. ${Object.keys(preferences).length ? "Your issue selections are applied to both sides." : "Select issues above to add an alignment read for both sides."}`
              : null}
          </p>
          {alignmentState.status === "error" ? (
            <p className="mt-3 text-sm leading-6 text-rose-200">{alignmentState.error}</p>
          ) : null}
        </div>
        {comparisonInsight ? (
          <div className="mt-4 rounded-[1.5rem] border border-stone-800 bg-stone-900/70 px-4 py-4 text-sm leading-7 text-stone-200">
            <p className="text-xs uppercase tracking-[0.26em] text-stone-400">
              Context Note
            </p>
            <p className="mt-2 text-[18px] leading-8 text-stone-100">{comparisonInsight}</p>
            <p className="mt-2 text-[13px] leading-6 text-stone-400">
              This note is secondary to the issue labels above. It describes a visible difference in the available record without scoring either legislator.
            </p>
          </div>
        ) : null}
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-[0.72fr_1.28fr]">
        <div className="rounded-[2rem] border border-stone-200 bg-[linear-gradient(180deg,rgba(255,255,255,0.76),rgba(245,241,233,0.94))] px-5 py-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.72)]">
          <p className="text-xs uppercase tracking-[0.3em] text-stone-500">
            Select Legislators
          </p>
          <input
            aria-label="Search legislators to compare"
            className="mt-4 h-12 w-full rounded-full border border-stone-300 bg-stone-50 px-5 text-sm text-stone-900 outline-none placeholder:text-stone-500"
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search by legislator name"
            value={query}
          />
          <div className="mt-4 grid max-h-[430px] gap-3 overflow-y-auto pr-1">
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
                  <p className="font-serif text-[1.5rem] leading-tight text-stone-900">{legislator.name_display}</p>
                  <p className="mt-1 text-[13px] text-stone-600">
                    {formatChamber(legislator.chamber)} - {legislator.party} - {legislator.state}
                    {legislator.district ? `-${legislator.district}` : " - Statewide"}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    className={`rounded-full px-4 py-2 text-xs uppercase tracking-[0.22em] ${
                      selected.left.id === legislator.id
                        ? "bg-stone-900 text-stone-100"
                        : "bg-stone-200 text-stone-700"
                    }`}
                    aria-label={`Set ${legislator.name_display} as the left comparison record`}
                    aria-pressed={selected.left.id === legislator.id}
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
                    aria-label={`Set ${legislator.name_display} as the right comparison record`}
                    aria-pressed={selected.right.id === legislator.id}
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

          <div className="grid gap-4 xl:grid-cols-2">
          <CompareSideCard
            heading="Left"
            alignment={alignmentState.left}
            side={compareState.payload?.left}
            fallbackLegislator={selected.left}
            onInspectDomain={onInspectDomain}
          />
          <CompareSideCard
            heading="Right"
            alignment={alignmentState.right}
            side={compareState.payload?.right}
            fallbackLegislator={selected.right}
            onInspectDomain={onInspectDomain}
          />
        </div>
      </div>
    </section>
  );
}

function buildFallbackAlignmentPayload({ legislatorId, preferences }) {
  return {
    legislator_id: legislatorId,
    preferences,
    alignment: Object.entries(preferences).map(([domain, preference]) => ({
      domain,
      preference,
      label: "insufficient_evidence",
      aligned_count: 0,
      not_aligned_count: 0,
      interpreted_count: 0,
      ambiguous_count: 0,
      evidence_count: 0,
      evidence_roll_call_ids: [],
    })),
  };
}

function CompareSideCard({ alignment, heading, side, fallbackLegislator, onInspectDomain }) {
  const legislator = side?.legislator || fallbackLegislator;
  const fingerprintRows = side?.fingerprint?.fingerprint || [];
  const positionRows = side?.position?.positions || [];
  const topDomains = fingerprintRows
    .filter((row) => row.vote_share > 0)
    .sort((left, right) => right.vote_share - left.vote_share)
    .slice(0, 2);
  const topPosition = buildTopPositionSummary(positionRows);

  return (
    <article className="rounded-[2rem] border border-stone-200 bg-[linear-gradient(180deg,rgba(255,255,255,0.78),rgba(245,241,233,0.96))] px-4 py-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.72)]">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.28em] text-stone-500">{heading}</p>
          <h3 className="mt-3 font-serif text-[1.8rem] leading-[1] text-stone-900 sm:text-[2.15rem] sm:leading-[0.95]">{legislator.name_display}</h3>
          <p className="mt-2 text-[14px] leading-5 text-stone-600">
            {formatChamber(legislator.chamber)} - {legislator.party} - {legislator.state}
            {legislator.district ? `-${legislator.district}` : " - Statewide"}
          </p>
        </div>
      </div>

      <div className="mt-4 grid gap-3">
        <IssueAlignmentRows
          alignment={alignment}
          legislator={legislator}
          onInspectDomain={onInspectDomain}
        />
        <details className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.72)]">
          <summary className="cursor-pointer text-xs uppercase tracking-[0.22em] text-stone-600">
            Supporting Context
          </summary>
          <div className="mt-4 grid gap-3">
            <CompareMetric
              label="Vote Direction"
              value={topPosition}
            />
            <CompareMetric
              label="Issue Focus"
              value={
                topDomains.length
                  ? topDomains.map((row) => `${formatDomainLabel(row.domain)} ${(row.vote_share * 100).toFixed(0)}%`).join(" / ")
                  : "No eligible domain emphasis available"
              }
            />
          </div>
        </details>
      </div>
    </article>
  );
}

function IssueAlignmentRows({ alignment, legislator, onInspectDomain }) {
  if (!alignment) {
    return (
      <div className="rounded-2xl border border-dashed border-stone-300 bg-stone-50 px-4 py-4 text-sm leading-6 text-stone-600">
        Select issues above to add a side-by-side read for this official.
      </div>
    );
  }

  const rows = alignment.alignment || [];
  if (!rows.length) {
    return (
      <div className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-4 text-sm leading-6 text-stone-700">
        No selected issue rows are available for this comparison side yet. The profile record remains available for direct inspection.
      </div>
    );
  }

  return (
    <div className="grid gap-3">
      <div className="rounded-2xl border border-stone-200 bg-white px-4 py-4">
        <p className="text-xs uppercase tracking-[0.22em] text-stone-500">Your Issues</p>
        <p className="mt-3 text-sm leading-6 text-stone-800">{buildAlignmentSummary(alignment)}</p>
      </div>
      {rows.map((row) => (
        <article
          className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.72)]"
          key={row.domain}
        >
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.22em] text-stone-500">
                {formatDomainLabel(row.domain)}
              </p>
              <p className="mt-2 text-[1.25rem] leading-7 text-stone-950">
                {formatAlignmentLabel(row.label)}
              </p>
            </div>
            <span className={`w-fit rounded-full px-3 py-1 text-[11px] uppercase tracking-[0.18em] ${getLabelClass(row.label)}`}>
              {row.interpreted_count} interpreted
            </span>
          </div>
          <p className="mt-3 text-sm leading-6 text-stone-700">
            {buildIssueRowCopy(row)}
          </p>
          <button
            className="mt-4 rounded-full bg-stone-900 px-4 py-2 text-xs uppercase tracking-[0.18em] text-stone-100"
            onClick={() => onInspectDomain?.(legislator, row.domain)}
            type="button"
          >
            Inspect Votes
          </button>
        </article>
      ))}
    </div>
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

function buildAlignmentSummary(alignment) {
  if (!alignment) {
    return "Select issues above to add this read.";
  }

  const rows = alignment.alignment || [];
  if (!rows.length) {
    return "No issue preferences selected.";
  }

  const aligned = rows.filter((row) => row.label === "aligned").length;
  const notAligned = rows.filter((row) => row.label === "not_aligned").length;
  const mixed = rows.filter((row) => row.label === "mixed").length;
  const insufficient = rows.filter((row) => row.label === "insufficient_evidence").length;

  return `${aligned} aligned / ${notAligned} not aligned / ${mixed} mixed / ${insufficient} insufficient`;
}

function buildIssueRowCopy(row) {
  if (row.label === "insufficient_evidence") {
    return "This official does not yet have enough source-grounded vote meaning on this issue for an alignment label. Inspect Votes shows the available roll-call record.";
  }
  if (row.label === "mixed") {
    return `${row.aligned_count} aligned and ${row.not_aligned_count} not aligned interpreted votes are available.`;
  }
  if (row.preference === "show_record") {
    return `${row.interpreted_count} interpreted votes are available for this issue.`;
  }
  return `${row.aligned_count} aligned and ${row.not_aligned_count} not aligned interpreted votes are available.`;
}

function formatAlignmentLabel(label) {
  if (label === "not_aligned") {
    return "Not aligned";
  }
  if (label === "insufficient_evidence") {
    return "Insufficient evidence";
  }
  return String(label)[0].toUpperCase() + String(label).slice(1);
}

function getLabelClass(label) {
  if (label === "aligned") {
    return "bg-emerald-100 text-emerald-800";
  }
  if (label === "not_aligned") {
    return "bg-rose-100 text-rose-800";
  }
  if (label === "mixed") {
    return "bg-amber-100 text-amber-800";
  }
  return "bg-stone-200 text-stone-700";
}

function buildComparisonInsight(payload) {
  const leftRows = payload?.left?.fingerprint?.fingerprint || [];
  const rightRows = payload?.right?.fingerprint?.fingerprint || [];
  const leftPositionRows = payload?.left?.position?.positions || [];
  const rightPositionRows = payload?.right?.position?.positions || [];

  const positionInsight = buildPositionComparisonInsight({
    leftName: payload?.left?.legislator?.name_display,
    rightName: payload?.right?.legislator?.name_display,
    leftRows: leftPositionRows,
    rightRows: rightPositionRows,
  });
  if (positionInsight) {
    return positionInsight;
  }

  if (!leftRows.length || !rightRows.length) {
    return "There is not enough issue-focus data yet to describe a visible difference.";
  }

  const differences = leftRows
    .map((leftRow) => {
      const rightRow = rightRows.find((candidate) => candidate.domain === leftRow.domain);
      return {
        domain: leftRow.domain,
        leftShare: leftRow.vote_share || 0,
        rightShare: rightRow?.vote_share || 0,
      };
    })
    .map((row) => ({
      ...row,
      gap: Math.abs(row.leftShare - row.rightShare),
    }))
    .sort((left, right) => right.gap - left.gap);

  const biggest = differences[0];
  if (!biggest || biggest.gap <= 0) {
    return "These two legislators currently look similar on issue focus, so this view does not show a clear difference in what kinds of issues dominated their recent votes.";
  }

  const leader =
    biggest.leftShare > biggest.rightShare ? payload.left.legislator.name_display : payload.right.legislator.name_display;
  const trailing =
    biggest.leftShare > biggest.rightShare ? payload.right.legislator.name_display : payload.left.legislator.name_display;
  const leaderShare = Math.max(biggest.leftShare, biggest.rightShare);
  const trailingShare = Math.min(biggest.leftShare, biggest.rightShare);

  return `One visible issue-focus difference is that ${leader} has more vote emphasis on ${formatDomainLabel(biggest.domain)}: ${Math.round(
    leaderShare * 100,
  )}% of eligible votes versus ${Math.round(trailingShare * 100)}% for ${trailing}.`;
}

function buildPositionComparisonInsight({ leftName, rightName, leftRows, rightRows }) {
  if (!leftRows.length || !rightRows.length) {
    return null;
  }

  const differences = leftRows
    .map((leftRow) => {
      const rightRow = rightRows.find((candidate) => candidate.domain === leftRow.domain);
      const leftRecorded = leftRow?.recorded_votes || 0;
      const rightRecorded = rightRow?.recorded_votes || 0;
      if (!rightRow || leftRecorded === 0 || rightRecorded === 0) {
        return null;
      }
      return {
        domain: leftRow.domain,
        leftYeaShare: leftRow.yea_share || 0,
        rightYeaShare: rightRow.yea_share || 0,
        gap: Math.abs((leftRow.yea_share || 0) - (rightRow.yea_share || 0)),
      };
    })
    .filter(Boolean)
    .sort((left, right) => right.gap - left.gap);

  const biggest = differences[0];
  if (!biggest || biggest.gap < 0.2) {
    return null;
  }

  const leader = biggest.leftYeaShare > biggest.rightYeaShare ? leftName : rightName;
  const trailing = biggest.leftYeaShare > biggest.rightYeaShare ? rightName : leftName;
  const leaderShare = Math.max(biggest.leftYeaShare, biggest.rightYeaShare);
  const trailingShare = Math.min(biggest.leftYeaShare, biggest.rightYeaShare);

  return `One visible voting-direction difference is in ${formatDomainLabel(biggest.domain)}: ${leader} voted yea ${(leaderShare * 100).toFixed(
    0,
  )}% of the time versus ${(trailingShare * 100).toFixed(0)}% for ${trailing}.`;
}

function buildTopPositionSummary(positionRows) {
  const strongest = [...positionRows]
    .filter((row) => (row?.recorded_votes || 0) > 0)
    .sort((left, right) => (right.recorded_votes || 0) - (left.recorded_votes || 0))[0];

  if (!strongest) {
    return "No yea/nay split available in the current issue window.";
  }

  return `${formatDomainLabel(strongest.domain)}: ${(strongest.yea_share * 100).toFixed(0)}% yea / ${(strongest.nay_share * 100).toFixed(
    0,
  )}% nay`;
}
