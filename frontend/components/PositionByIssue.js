"use client";

import { useEffect, useState } from "react";

import { fetchLegislatorContact, fetchPositionEvidence, fetchPositions } from "../lib/api";
import { deriveEvidenceGroups } from "../lib/evidenceGrouping.mjs";
import { buildIssueOverview } from "../lib/issueOverview.mjs";
import { groupIssueRowsByReadiness, sortIssueRowsByReadiness } from "../lib/issueReadiness.mjs";
import { isProceduralContextRow } from "../lib/proceduralContext.mjs";
import { DOMAIN_LABELS, formatDomainLabel } from "../lib/issueDomains";
import {
  buildLimitedContextSummary as buildGenericLimitedContextSummary,
  buildVoteCardSummary as buildGenericVoteCardSummary,
} from "../lib/voteCardSummary.mjs";

export default function PositionByIssue({
  evidenceRequest = null,
  legislator = null,
  legislatorId = "leg_alex_morgan",
  title = "How They Vote By Issue",
}) {
  const [state, setState] = useState({
    status: "loading",
    payload: null,
    error: null,
  });
  const [selectedDomain, setSelectedDomain] = useState(null);
  const [evidenceState, setEvidenceState] = useState({
    status: "idle",
    payload: null,
    error: null,
  });

  useEffect(() => {
    let active = true;

    async function loadPositions() {
      try {
        const payload = await fetchPositions({ legislatorId });
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
          error: "Vote-direction data is unavailable for this legislator right now.",
        });
      }
    }

    loadPositions();

    return () => {
      active = false;
    };
  }, [legislatorId]);

  useEffect(() => {
    setSelectedDomain(null);
    setEvidenceState({
      status: "idle",
      payload: null,
      error: null,
    });
  }, [legislatorId]);

  useEffect(() => {
    if (!evidenceRequest?.domain) {
      return;
    }

    inspectDomain(evidenceRequest.domain);
    const element = document.getElementById("position-evidence");
    element?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  }, [evidenceRequest?.requestedAt]);

  const issueRows = sortIssueRowsByReadiness(state.payload?.positions || []);
  const rows = issueRows.filter((row) => row.recorded_votes > 0 || row.readiness.key === "not_enough_to_summarize");
  const readinessGroups = groupIssueRowsByReadiness(state.payload?.positions || []);
  const patternRows = buildPatternRows(state.payload?.positions || []);
  const takeaway = buildTakeaway(rows);
  const selectedRow = rows.find((row) => row.domain === selectedDomain) || rows[0] || null;
  const startPlan = buildSixtySecondPlan(readinessGroups);

  async function inspectDomain(domain) {
    setSelectedDomain(domain);
    setEvidenceState({
      status: "loading",
      payload: null,
      error: null,
    });

    try {
      const payload = await fetchPositionEvidence({ legislatorId, domain });
      setEvidenceState({
        status: "ready",
        payload,
        error: null,
      });
    } catch (error) {
      setEvidenceState({
        status: "error",
        payload: null,
        error: "The vote evidence for this issue is unavailable right now.",
      });
    }
  }

  return (
    <section id="position-by-issue" className="mt-8 rounded-[2rem] border border-stone-200 bg-white p-5 shadow-[0_18px_48px_rgba(15,23,42,0.1)] lg:p-6">
      <div className="grid gap-5 lg:grid-cols-[0.9fr_1.1fr]">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-cyan-800">
            First Read
          </p>
          <h3 className="mt-2 font-serif text-[2rem] leading-[1] text-stone-950 sm:text-[2.7rem] sm:leading-[0.95]">
            {title}
          </h3>
          <p className="mt-3 max-w-xl text-[18px] leading-8 text-stone-900">
            {state.status === "ready"
              ? takeaway
              : state.status === "loading"
                ? "Reading where this legislator's reviewed issue evidence is strongest."
                : "The site cannot read issue readiness for this legislator right now."}
          </p>
          <div className="mt-4 rounded-[1.5rem] bg-stone-950 px-4 py-4 text-stone-100">
            <p className="text-xs uppercase tracking-[0.28em] text-stone-400">
              How To Read This
            </p>
            <p className="mt-2 text-[15px] leading-7 text-stone-200">
              Issue areas are grouped by reviewed evidence strength. Strong and mixed sections come first; limited sections stay visible without being treated as confident summaries. It is descriptive, not a score.
            </p>
          </div>
          {state.status === "ready" ? (
            <SixtySecondPath
              inspectDomain={inspectDomain}
              plan={startPlan}
            />
          ) : null}
        </div>

        <div className="grid gap-3">
          {state.status === "error" ? (
            <div className="rounded-[1.5rem] border border-rose-200 bg-rose-50 px-4 py-4 text-sm text-rose-700">
              {state.error}
            </div>
          ) : null}
          {state.status === "ready" && rows.length === 0 ? (
            <div className="rounded-[1.5rem] border border-stone-200 bg-stone-50 px-4 py-4 text-sm text-stone-600">
              No recorded yea/nay policy-vote splits are available in the current window. This is a coverage note, not an alignment finding.
            </div>
          ) : null}
          {state.status === "ready" ? (
            <IssueReadinessGroups
              groups={readinessGroups}
              inspectDomain={inspectDomain}
              selectedDomain={selectedDomain}
            />
          ) : null}
        </div>
      </div>

      <EvidencePanel
        evidenceState={evidenceState}
        legislator={legislator}
        onInspectDomain={inspectDomain}
        selectedRow={selectedRow}
      />

      <IssuePatternCards
        onInspectDomain={inspectDomain}
        rows={patternRows}
        status={state.status}
      />
    </section>
  );
}

function SixtySecondPath({ inspectDomain, plan }) {
  if (!plan) {
    return null;
  }

  return (
    <div className="mt-4 rounded-[1.5rem] border border-cyan-900/10 bg-cyan-50 px-4 py-4">
      <p className="text-xs uppercase tracking-[0.24em] text-cyan-900">
        What You Can Learn In 60 Seconds
      </p>
      <p className="mt-2 text-[15px] leading-7 text-stone-800">
        {plan.summary}
      </p>
      <div className="mt-4 grid gap-2">
        {plan.steps.map((step, index) => (
          <button
            className={`rounded-xl border px-3 py-3 text-left transition focus:outline-none focus:ring-2 focus:ring-cyan-800 focus:ring-offset-2 ${
              step.priority === "primary"
                ? "border-cyan-800 bg-white hover:bg-cyan-50"
                : "border-stone-200 bg-white/80 hover:border-cyan-700/50"
            }`}
            key={`${step.domain}-${step.title}`}
            onClick={() => inspectDomain(step.domain)}
            type="button"
          >
            <div className="flex items-start gap-3">
              <span className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-semibold ${
                step.priority === "primary" ? "bg-cyan-900 text-white" : "bg-stone-200 text-stone-700"
              }`}>
                {index + 1}
              </span>
              <div>
                <p className="text-sm font-semibold leading-6 text-stone-950">
                  {step.title}
                </p>
                <p className="mt-1 text-sm leading-6 text-stone-700">
                  {step.detail}
                </p>
              </div>
            </div>
          </button>
        ))}
      </div>
      {plan.limitedNote ? (
        <p className="mt-3 rounded-xl bg-white/70 px-3 py-2 text-sm leading-6 text-stone-700">
          {plan.limitedNote}
        </p>
      ) : null}
    </div>
  );
}

function IssueReadinessGroups({ groups, inspectDomain, selectedDomain }) {
  const visibleGroups = groups.filter((group) => group.rows.length > 0);

  if (!visibleGroups.length) {
    return null;
  }

  return (
    <div className="grid gap-3">
      {visibleGroups.map((group) => (
        <section className={`rounded-[1.25rem] border px-3 py-3 ${getReadinessGroupContainerClass(group.key)}`} key={group.key}>
          <div className="flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-cyan-900">
                {group.label}
              </p>
              <p className="mt-1 text-sm leading-6 text-stone-600">
                {formatReadinessGroupHelp(group.key)}
              </p>
            </div>
            <span className="w-fit rounded-full bg-white px-3 py-1 text-xs uppercase tracking-[0.16em] text-stone-600">
              {group.rows.length} {group.rows.length === 1 ? "issue" : "issues"}
            </span>
          </div>
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            {group.rows.map((row) => (
              <IssueReadinessTile
                inspectDomain={inspectDomain}
                key={row.domain}
                row={row}
                selectedDomain={selectedDomain}
              />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}

function IssueReadinessTile({ inspectDomain, row, selectedDomain }) {
  const readinessKey = row.readiness?.key;

  return (
    <button
      aria-label={`Inspect ${formatDomainLabel(row.domain)} votes`}
      aria-pressed={selectedDomain === row.domain}
      className={`rounded-[1.1rem] border px-4 py-3 text-left shadow-[inset_0_1px_0_rgba(255,255,255,0.72)] transition ${
        selectedDomain === row.domain
          ? "border-cyan-800 bg-cyan-50"
          : readinessKey === "strong_evidence"
            ? "border-cyan-800/30 bg-white hover:border-cyan-800"
            : readinessKey === "mixed_but_interpretable"
              ? "border-indigo-200 bg-white hover:border-indigo-500"
              : "border-stone-200 bg-white hover:border-cyan-700/50"
      }`}
      onClick={() => inspectDomain(row.domain)}
      type="button"
    >
      <div className="flex items-start justify-between gap-3">
        <p className="max-w-[220px] text-[15px] leading-6 text-stone-950">
          {formatDomainLabel(row.domain)}
        </p>
        <p className="shrink-0 text-sm text-stone-500">{row.recorded_votes || 0} votes</p>
      </div>
      <div className="mt-3 flex flex-col gap-2">
        <span className={`w-fit max-w-full rounded-xl px-3 py-1 text-[11px] uppercase leading-4 tracking-[0.12em] ${getReadinessBadgeClass(row.readiness?.key)}`}>
          {row.readiness?.label || "Not enough to summarize"}
        </span>
        <p className="text-[13px] leading-5 text-stone-700">
          {formatIssueCardEvidenceLine(row)}
        </p>
        <p className="text-[13px] leading-5 text-stone-600">
          {formatIssueCardReason(row)}
        </p>
        <p className="text-[12px] uppercase leading-5 tracking-[0.14em] text-stone-500">
          {formatIssueCardPriority(row.readiness?.key)}
        </p>
      </div>
      <div className="mt-3 h-2 overflow-hidden rounded-full bg-stone-200">
        <div className="flex h-full w-full">
          <div
            className="bg-emerald-500"
            style={{ width: `${(row.yea_share || 0) * 100}%` }}
          />
          <div
            className="bg-rose-500"
            style={{ width: `${(row.nay_share || 0) * 100}%` }}
          />
        </div>
      </div>
    </button>
  );
}

function IssuePatternCards({ onInspectDomain, rows, status }) {
  if (status !== "ready") {
    return null;
  }

  return (
    <div className="mt-5 rounded-[1.5rem] border border-stone-200 bg-white px-3 py-4 sm:px-4 lg:px-5">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.28em] text-stone-500">
            Issue Patterns
          </p>
          <h4 className="mt-2 font-serif text-[1.75rem] leading-none text-stone-950 sm:text-[2rem]">
            Reviewed issue patterns
          </h4>
        </div>
        <p className="max-w-xl text-sm leading-6 text-stone-600">
          These cards use only reviewed vote meanings. Missing or ambiguous meanings stay out of the pattern instead of being guessed.
        </p>
      </div>

      {rows.length === 0 ? (
        <p className="mt-4 rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm leading-6 text-stone-700">
          No interpreted issue patterns are available yet for this official. The evidence rows still show recorded votes and source links.
        </p>
      ) : (
        <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {rows.map((row) => (
            <button
              aria-label={`Open interpreted votes for ${formatDomainLabel(row.domain)}`}
              className="rounded-[1.25rem] border border-stone-200 bg-stone-50 px-4 py-4 text-left transition hover:border-cyan-700/50 hover:bg-cyan-50 focus:outline-none focus:ring-2 focus:ring-cyan-800 focus:ring-offset-2"
              key={row.domain}
              onClick={() => onInspectDomain(row.domain)}
              type="button"
            >
              <p className="text-xs uppercase tracking-[0.22em] text-stone-500">
                {formatDomainLabel(row.domain)}
              </p>
              <p className="mt-3 text-[1.35rem] leading-7 text-stone-950">
                {row.label}
              </p>
              <p className="mt-3 text-sm leading-6 text-stone-700">
                {row.detail}
              </p>
              <div className="mt-4 grid grid-cols-2 gap-2 text-sm">
                <div className="rounded-xl border border-cyan-900/10 bg-white px-3 py-3">
                  <p className="text-[11px] uppercase tracking-[0.16em] text-stone-500">For measures</p>
                  <p className="mt-2 text-[1.4rem] leading-none text-stone-950">{row.supportCount}</p>
                </div>
                <div className="rounded-xl border border-cyan-900/10 bg-white px-3 py-3">
                  <p className="text-[11px] uppercase tracking-[0.16em] text-stone-500">Against measures</p>
                  <p className="mt-2 text-[1.4rem] leading-none text-stone-950">{row.opposeCount}</p>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function EvidencePanel({ evidenceState, legislator, onInspectDomain, selectedRow }) {
  const [selectedActionRow, setSelectedActionRow] = useState(null);

  useEffect(() => {
    setSelectedActionRow(null);
  }, [selectedRow?.domain]);

  if (!selectedRow) {
    return null;
  }

  const evidenceRows = evidenceState.payload?.evidence || [];
  const isSelected = evidenceState.payload?.domain === selectedRow.domain;
  const evidenceGrouping = deriveEvidenceGroups(evidenceRows);
  const billGroups = groupEvidenceByBill(evidenceRows);

  return (
    <div id="position-evidence" className="mt-5 scroll-mt-6 rounded-[1.5rem] border border-stone-200 bg-stone-50 px-3 py-4 sm:px-4 lg:px-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.28em] text-stone-500">
            Evidence
          </p>
          <h4 className="mt-2 font-serif text-[1.75rem] leading-none text-stone-950 sm:text-[2rem]">
            {formatDomainLabel(selectedRow.domain)}
          </h4>
        </div>
        <button
          className="rounded-full bg-stone-900 px-4 py-2 text-xs uppercase tracking-[0.22em] text-stone-100 transition hover:bg-cyan-900 focus:outline-none focus:ring-2 focus:ring-cyan-800 focus:ring-offset-2"
          onClick={() => onInspectDomain(selectedRow.domain)}
          type="button"
        >
          Show Votes
        </button>
      </div>

      {evidenceState.status === "idle" ? (
        <p className="mt-4 text-sm leading-7 text-stone-700">
          Start with the strongest issue card above or use Show Votes to inspect the roll calls behind this read. The clearest sections get summarized first; limited sections stay available as evidence without being forced into a confident pattern.
        </p>
      ) : null}
      {evidenceState.status === "loading" ? (
        <p className="mt-4 text-sm leading-7 text-stone-700">
          Loading underlying votes...
        </p>
      ) : null}
      {evidenceState.status === "error" ? (
        <p className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm leading-6 text-rose-700">
          {evidenceState.error}
        </p>
      ) : null}
      {evidenceState.status === "ready" && isSelected && evidenceRows.length === 0 ? (
        <p className="mt-4 rounded-2xl border border-stone-200 bg-white px-4 py-3 text-sm leading-6 text-stone-700">
          No underlying roll-call rows are available for this issue in the current window. The site leaves this issue unlabeled rather than filling the gap with a guess.
        </p>
      ) : null}
      {evidenceState.status === "ready" && isSelected && evidenceRows.length > 0 ? (
        <div className="mt-4 grid gap-3">
          <div className="rounded-2xl border border-cyan-900/10 bg-cyan-50 px-4 py-4 text-sm leading-6 text-stone-700">
            {formatBillGroupSummary(evidenceGrouping.summary)}
          </div>
          <EvidenceGroupingPreview evidenceGrouping={evidenceGrouping} />
          <IssueEvidenceSummary
            domain={selectedRow.domain}
            representativeName={legislator?.name_display}
            rows={evidenceRows}
          />
          {billGroups.map((group) => (
            <article className="rounded-[1.25rem] border border-stone-200 bg-white px-3 py-4 sm:px-4" key={group.key}>
              <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <p className="text-xs uppercase tracking-[0.24em] text-stone-500">
                    Bill group
                  </p>
                  <h5 className="mt-2 break-words text-base leading-6 text-stone-950 sm:text-[18px] sm:leading-7">
                    {group.title}
                  </h5>
                  <p className="mt-2 text-sm leading-6 text-stone-600">
                    {group.rows.length} {group.rows.length === 1 ? "roll call" : "roll calls"} shown for this bill or measure.
                  </p>
                </div>
                <span className="w-fit rounded-full bg-stone-100 px-3 py-1 text-xs uppercase tracking-[0.2em] text-stone-700">
                  {group.rows.length} rows
                </span>
              </div>

              <div className="mt-4 grid gap-3">
                {group.rows.map((row) => (
                  <div
                    className="rounded-[1.1rem] border border-stone-200 bg-stone-50 px-3 py-3 sm:px-4 sm:py-4"
                    key={`${row.roll_call_id}-${row.position}`}
                  >
                    <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                      <div>
                        <p className="break-words text-xs uppercase tracking-[0.18em] text-stone-500 sm:tracking-[0.24em]">
                          {formatDate(row.vote_date)} - {formatChamber(row.chamber)} Roll {row.rollcall_number}
                        </p>
                        <p className="mt-2 text-[13px] leading-6 text-stone-700 sm:text-sm">
                          {row.description || row.question}
                        </p>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <span className={`w-fit rounded-full px-3 py-1 text-xs uppercase tracking-[0.2em] ${getVoteBadgeClass(row.position)}`}>
                          {formatVotePosition(row.position)}
                        </span>
                        <span className={`w-fit rounded-full px-3 py-1 text-xs uppercase tracking-[0.16em] ${getEvidenceConfidenceBadgeClass(row)}`}>
                          {formatEvidenceConfidenceLabel(row)}
                        </span>
                      </div>
                    </div>
                    <InterpretationBreakdown
                      representativeName={legislator?.name_display}
                      row={row}
                      selectedActionRow={selectedActionRow}
                      setSelectedActionRow={setSelectedActionRow}
                    />
                    <div className="mt-3 flex justify-start border-t border-stone-200 pt-3 sm:justify-end">
                      {row.source_url ? (
                        <a
                          className="w-fit rounded-full border border-cyan-800/20 bg-white px-3 py-2 text-xs uppercase tracking-[0.18em] text-cyan-800 underline-offset-4 transition hover:border-cyan-800 hover:bg-cyan-50 hover:underline"
                          href={row.source_url}
                          rel="noreferrer"
                          target="_blank"
                        >
                          Source
                        </a>
                      ) : (
                        <p className="text-xs uppercase tracking-[0.18em] text-stone-500">No source URL</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </article>
          ))}
          <CivicActionPanel
            domain={selectedRow.domain}
            evidenceRows={evidenceRows}
            legislator={legislator}
            selectedEvidenceRow={selectedActionRow}
          />
        </div>
      ) : null}
    </div>
  );
}

function EvidenceGroupingPreview({ evidenceGrouping }) {
  const groups = evidenceGrouping?.groups || [];
  const repeatedGroups = groups.filter((group) => group.rowCount > 1);
  const limitedGroups = groups.filter((group) => group.category === "limited_context_rows");
  const proceduralContextGroups = groups.filter((group) => group.category === "procedural_context_rows");
  const notVotingGroups = groups.filter((group) => group.category === "not_voting_rows");
  const previewGroups = [...repeatedGroups, ...proceduralContextGroups, ...limitedGroups, ...notVotingGroups]
    .filter((group, index, allGroups) => allGroups.findIndex((candidate) => candidate.id === group.id) === index)
    .slice(0, 4);

  if (!groups.length) {
    return null;
  }

  return (
    <div className="rounded-[1.25rem] border border-stone-200 bg-white px-4 py-4">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-cyan-900">
            Grouped Evidence Preview
          </p>
          <p className="mt-2 text-sm leading-6 text-stone-700">
            {formatEvidenceGroupingOverview(evidenceGrouping.summary)}
          </p>
          <p className="mt-1 text-sm leading-6 text-stone-600">
            Repeated bill groups help show when several rows are about the same package. Procedural-context, limited-context, and not-voting rows remain visible without being counted as support or opposition.
          </p>
        </div>
        <span className="w-fit rounded-full bg-stone-100 px-3 py-1 text-xs uppercase tracking-[0.16em] text-stone-700">
          {groups.length} {groups.length === 1 ? "group" : "groups"}
        </span>
      </div>
      {previewGroups.length ? (
        <div className="mt-3 grid gap-2">
          {previewGroups.map((group) => (
            <div className="rounded-xl border border-stone-200 bg-stone-50 px-3 py-3" key={group.id}>
              <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                <p className="text-sm leading-6 text-stone-900">{group.label}</p>
                <span className="w-fit rounded-full bg-white px-2.5 py-1 text-[11px] uppercase tracking-[0.14em] text-stone-600">
                  {formatEvidenceGroupCategory(group)}
                </span>
              </div>
              <p className="mt-2 text-sm leading-6 text-stone-600">
                {group.scanSummary}
              </p>
            </div>
          ))}
        </div>
      ) : (
        <p className="mt-3 text-sm leading-6 text-stone-600">
          No repeated bill, procedural-context, limited-context, or not-voting clusters were detected in this issue section.
        </p>
      )}
    </div>
  );
}

function CivicActionPanel({ domain, evidenceRows, legislator, selectedEvidenceRow }) {
  const [contactState, setContactState] = useState({
    status: "idle",
    payload: null,
    error: null,
  });
  const representativeName = legislator?.name_display || "this representative";
  const actionContext = buildActionContext({
    domain,
    evidenceRows,
    representativeName,
    selectedEvidenceRow,
  });

  useEffect(() => {
    let active = true;

    if (!legislator?.id) {
      setContactState({
        status: "idle",
        payload: null,
        error: null,
      });
      return () => {
        active = false;
      };
    }

    async function loadContact() {
      setContactState({
        status: "loading",
        payload: null,
        error: null,
      });

      try {
        const payload = await fetchLegislatorContact({ legislatorId: legislator.id });
        if (!active) {
          return;
        }
        setContactState({
          status: "ready",
          payload,
          error: null,
        });
      } catch (error) {
        if (!active) {
          return;
        }
        setContactState({
          status: "error",
          payload: null,
          error: "Official contact metadata is not loaded yet.",
        });
      }
    }

    loadContact();

    return () => {
      active = false;
    };
  }, [legislator?.id]);

  return (
    <div className="rounded-[1.25rem] border border-stone-200 bg-white px-4 py-4">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-cyan-900">
            Contact This Office
          </p>
          <h5 className="mt-2 text-[1.35rem] leading-7 text-stone-950">
            {representativeName}
          </h5>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-stone-600">
            Official contact paths for this representative, kept next to the evidence you are reviewing. The app has not sent or saved anything.
          </p>
        </div>
        <span className="w-fit rounded-full bg-stone-100 px-3 py-1 text-[11px] uppercase tracking-[0.16em] text-stone-700">
          User-directed
        </span>
      </div>

      <div className="mt-4 rounded-2xl border border-stone-200 bg-stone-50 px-4 py-4">
        <ContactMetadataCard contactState={contactState} />
        <p className="text-[11px] uppercase tracking-[0.18em] text-stone-500">
          Evidence context
        </p>
        <p className="mt-2 text-sm leading-6 text-stone-700">
          {actionContext.contextLine}
        </p>
        {actionContext.selectedVoteLine ? (
          <p className="mt-2 rounded-xl border border-cyan-900/10 bg-white px-3 py-3 text-sm leading-6 text-stone-700">
            Selected vote: {actionContext.selectedVoteLine}
          </p>
        ) : (
          <p className="mt-2 text-xs leading-5 text-stone-500">
            Select a vote below to keep it visible here.
          </p>
        )}
      </div>
    </div>
  );
}

function ContactMetadataCard({ contactState }) {
  if (contactState.status === "loading") {
    return (
      <p className="mb-4 rounded-xl border border-stone-200 bg-white px-3 py-3 text-sm leading-6 text-stone-600">
        Loading official contact metadata...
      </p>
    );
  }

  if (contactState.status === "error") {
    return (
      <p className="mb-4 rounded-xl border border-amber-200 bg-amber-50 px-3 py-3 text-sm leading-6 text-amber-900">
        {contactState.error}
      </p>
    );
  }

  const contact = contactState.payload;
  if (!contact || contact.contact_status !== "loaded") {
    return (
      <p className="mb-4 rounded-xl border border-stone-200 bg-white px-3 py-3 text-sm leading-6 text-stone-600">
        Official contact metadata is not loaded for this representative yet.
      </p>
    );
  }

  return (
    <div className="mb-4 rounded-xl border border-cyan-900/10 bg-white px-3 py-3">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-[11px] uppercase tracking-[0.18em] text-stone-500">
            Official contact
          </p>
          <p className="mt-1 text-sm leading-6 text-stone-700">
            {contact.phone ? `Phone: ${contact.phone}` : "Phone not loaded"}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {contact.contact_form_url ? (
            <a
              className="rounded-full border border-cyan-800 bg-cyan-900 px-3 py-2 text-xs uppercase tracking-[0.16em] text-white transition hover:bg-cyan-800 focus:outline-none focus:ring-2 focus:ring-cyan-800 focus:ring-offset-2"
              href={contact.contact_form_url}
              rel="noreferrer"
              target="_blank"
            >
              Open Contact Form
            </a>
          ) : null}
          {contact.official_website_url ? (
            <a
              className="rounded-full border border-stone-300 bg-white px-3 py-2 text-xs uppercase tracking-[0.16em] text-stone-700 transition hover:border-cyan-800 hover:bg-cyan-50"
              href={contact.official_website_url}
              rel="noreferrer"
              target="_blank"
            >
              Official Site
            </a>
          ) : null}
        </div>
      </div>
      <p className="mt-2 text-xs leading-5 text-stone-500">
        Source: {formatContactSource(contact)}.
      </p>
    </div>
  );
}

function IssueEvidenceSummary({ domain, representativeName, rows }) {
  const overview = buildIssueOverview(rows, { domain, representativeName });
  if (!overview) {
    return null;
  }
  const sections = [
    ["What these votes were about", overview.copy.whatTheseVotesWereAbout],
    [`What ${overview.representativeLabel} did`, overview.copy.whatRepresentativeDid],
    ["What pattern that creates", overview.copy.whatPatternThatCreates],
    ["How a voter might read that", overview.copy.howVoterMightRead],
    ["What not to infer", overview.copy.whatNotToInfer],
  ];

  return (
    <div className="rounded-[1.25rem] border border-cyan-900/10 bg-white px-4 py-4">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-cyan-900">
            Issue Overview
          </p>
          <p className="mt-2 max-w-4xl text-[18px] leading-8 text-stone-950">
            {overview.copy.whatTheseVotesWereAbout}
          </p>
        </div>
        <span className="w-fit rounded-full bg-cyan-50 px-3 py-1 text-[11px] uppercase tracking-[0.16em] text-cyan-950">
          {overview.votePattern.interpretedYesNoCount} interpreted votes
        </span>
      </div>
      <div className="mt-3 grid gap-3">
        {sections.slice(1).map(([label, text]) => (
          <div className="rounded-2xl border border-stone-200 bg-stone-50 px-3 py-3" key={label}>
            <p className="text-xs uppercase tracking-[0.2em] text-cyan-900">{label}</p>
            <p className="mt-2 text-sm leading-6 text-stone-800">{text}</p>
          </div>
        ))}
      </div>
      <p className="mt-3 text-xs leading-5 text-stone-500">
        Rows below remain the source of truth for each claim; missing vote meanings are not guessed.
      </p>
    </div>
  );
}

function InterpretationBreakdown({ representativeName, row, selectedActionRow, setSelectedActionRow }) {
  if (!hasInterpretationDetail(row)) {
    return null;
  }

  const isInterpreted = row.interpretation_status === "interpreted";
  const statusLabel = formatInterpretationStatus(row);
  const summaryText = buildUsefulInterpretationText(row.plain_english_summary);
  const policyEffectText = buildUsefulInterpretationText(row.policy_effect);
  const interpretedVoteRead = buildInterpretedVoteRead(row);
  const whatHappened = row.what_happened || summaryText || policyEffectText;
  const whyItMattered = row.why_it_mattered || buildPlainTakeaway(row);
  const voteCardSummary = buildVoteCardSummary(row, { representativeName }) || interpretedVoteRead;
  const limitedContextSummary = buildLimitedContextSummary(row);
  const contextBadges = buildContextBadges(row);
  const voteContextLine = buildVoteContextLine(row);
  const visibleLimitedSummary =
    limitedContextSummary ||
    row.uncertainty_note ||
    row.interpretation_reason ||
    "The available source text is not clear enough to summarize what this vote meant.";

  return (
    <div className="mt-3 grid gap-2">
      {isInterpreted ? (
        <>
          {voteCardSummary ? (
            <InsightCard
              className="border-cyan-900/20 bg-cyan-50"
              label="Vote summary"
              text={voteCardSummary}
              tone={row.position === row.support_position ? "support" : row.position === row.oppose_position ? "oppose" : "neutral"}
            />
          ) : null}
          {whyItMattered ? (
            <InsightCard
              label="Why this mattered"
              text={whyItMattered}
            />
          ) : null}
        </>
      ) : (
        <InsightCard
          className="border-amber-200 bg-amber-50"
          label="Vote summary"
          text={visibleLimitedSummary}
        />
      )}

      <details className="rounded-xl border border-stone-200 bg-white px-3 py-3">
        <summary className="cursor-pointer text-xs uppercase tracking-[0.18em] text-stone-600 marker:text-cyan-900">
          Details
        </summary>
        <div className="mt-3 grid gap-3 border-t border-stone-200 pt-3">
          <div className="flex flex-wrap gap-2">
            <span className={`w-fit rounded-full px-3 py-1 text-[11px] uppercase tracking-[0.18em] ${getInterpretationBadgeClass(row)}`}>
              {statusLabel}
            </span>
            {row.issue_facet ? (
              <span className="rounded-full bg-stone-100 px-3 py-1 text-[11px] uppercase tracking-[0.16em] text-stone-600">
                {formatIssueFacet(row.issue_facet)}
              </span>
            ) : null}
            {contextBadges.map((badge) => (
              <span className="rounded-full bg-cyan-50 px-3 py-1 text-[11px] uppercase tracking-[0.16em] text-cyan-900" key={badge}>
                {badge}
              </span>
            ))}
          </div>
          {voteContextLine ? (
            <p className="rounded-xl bg-stone-50 px-3 py-2 text-xs leading-5 text-stone-600">
              {voteContextLine}
            </p>
          ) : null}
          {isInterpreted ? (
            <>
              <InsightCard
                label="What this vote was"
                text={whatHappened}
              />
              {row.what_not_to_infer ? (
                <InsightCard
                  label="What not to infer"
                  text={row.what_not_to_infer}
                />
              ) : null}
            </>
          ) : null}
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-xs uppercase leading-5 tracking-[0.16em] text-stone-500 sm:tracking-[0.18em]">
              Included as {formatClassificationReason(row.classification_reason)}
            </p>
            <button
              aria-pressed={rowActionKey(selectedActionRow) === rowActionKey(row)}
              className={`w-fit rounded-full border px-3 py-2 text-xs uppercase tracking-[0.18em] transition focus:outline-none focus:ring-2 focus:ring-cyan-800 focus:ring-offset-2 ${
                rowActionKey(selectedActionRow) === rowActionKey(row)
                  ? "border-cyan-900 bg-cyan-900 text-white"
                  : "border-stone-300 bg-white text-stone-700 hover:border-cyan-800 hover:bg-cyan-50"
              }`}
              onClick={() => setSelectedActionRow(row)}
              type="button"
            >
              Official Vote Record
            </button>
          </div>
          <SourceBasisList sourceBasis={row.source_basis} />
        </div>
      </details>
    </div>
  );
}

function SourceBasisList({ sourceBasis }) {
  if (!Array.isArray(sourceBasis) || sourceBasis.length === 0) {
    return null;
  }

  return (
    <div className="mt-3 border-t border-stone-200 pt-3">
      <p className="text-[11px] uppercase tracking-[0.18em] text-stone-500">Source basis</p>
      <div className="mt-2 flex flex-wrap gap-2">
        {sourceBasis.map((item, index) => (
          <span
            className="rounded-full bg-stone-100 px-3 py-1 text-[11px] leading-5 text-stone-700"
            key={`${item.field || "source"}-${index}`}
          >
            {formatSourceBasis(item)}
          </span>
        ))}
      </div>
    </div>
  );
}

function InsightCard({ className = "", label, text, tone = "neutral" }) {
  const toneClass =
    tone === "support"
      ? "border-emerald-200 bg-emerald-50"
      : tone === "oppose"
        ? "border-rose-200 bg-rose-50"
        : "border-stone-200 bg-stone-50";

  if (!text) {
    return null;
  }

  return (
    <div className={`rounded-xl border px-3 py-3 ${toneClass} ${className}`}>
      <p className="text-[11px] uppercase tracking-[0.18em] text-stone-500">{label}</p>
      <p className="mt-2 text-sm leading-6 text-stone-800">{text}</p>
    </div>
  );
}

function buildInterpretedVoteRead(row) {
  if (!row.position || !row.support_position || !row.oppose_position) {
    return "";
  }

  const position = formatVotePosition(row.position);
  if (row.position === "not_voting") {
    return "Not voting on this roll call, so this record does not show a yea or nay position.";
  }

  if (row.position === row.support_position) {
    return `${position}: ${formatRecordedSideMeaning(row.position === "yea" ? row.yea_meaning : row.nay_meaning)}`;
  }
  if (row.position === row.oppose_position) {
    return `${position}: ${formatRecordedSideMeaning(row.position === "yea" ? row.yea_meaning : row.nay_meaning)}`;
  }
  return `${position}.`;
}

function buildVoteCardSummary(row, options = {}) {
  const exactSummary = buildKnownVoteCardSummary(row);
  if (exactSummary) {
    return exactSummary;
  }

  return buildGenericVoteCardSummary(row, options);
}

function buildKnownVoteCardSummary(row) {
  if (extractMemberLabel(row) !== "Foushee") {
    return "";
  }

  const rollNumber = Number(row.rollcall_number);

  if (rollNumber === 50) {
    return "Nay. The House adopted a budget blueprint that helped start a fast-track reconciliation process for later tax, spending, deficit, and debt-limit legislation. Foushee voted against adopting that framework, matching most Democrats. The measure passed narrowly.";
  }
  if (rollNumber === 100) {
    return "Nay. The House agreed to the Senate-amended budget framework, keeping the reconciliation process moving for later tax, spending, deficit, and debt-limit legislation. Foushee voted against agreeing to that framework, matching most Democrats. The measure passed narrowly.";
  }
  if (rollNumber === 156) {
    return "Nay. The House passed a bill that would restrict SBA 7(a) and 504 loan eligibility based on citizenship or lawful-permanent-residency status. Foushee voted against adding those eligibility restrictions, matching most Democrats. The bill passed the House.";
  }
  if (rollNumber === 182) {
    return "Nay. The House passed an FY2026 funding bill for military construction, military housing, veterans benefits, Veterans Affairs programs, and related agencies. Foushee voted against passing that funding bill, matching most Democrats. The measure passed the House.";
  }
  if (rollNumber === 281) {
    return "Nay. The House passed a temporary funding bill to keep most federal agencies operating while regular appropriations bills were unfinished. Foushee voted against passing that temporary funding bill, matching most Democrats. The measure passed narrowly.";
  }
  if (rollNumber === 285) {
    return "Nay. The House agreed to a Senate-amended funding package that ended the 2025 shutdown and sent the measure to the President. Foushee voted against accepting that shutdown-ending package, matching most Democrats. The measure passed and became law.";
  }
  if (rollNumber === 310) {
    return "Not Voting. The House passed a bill that would require the Small Business Administration to keep its annual small-business regulatory budget at zero or below. Foushee was recorded as not voting, so this row explains the bill's meaning but does not count as support or opposition. The bill passed the House.";
  }

  return "";
}

function buildLimitedContextSummary(row) {
  const rollNumber = Number(row?.rollcall_number);
  const position = formatVotePosition(row?.position);
  const genericSummary = buildGenericLimitedContextSummary(row);

  if (isProceduralContextRow(row) && genericSummary) {
    return genericSummary;
  }

  if (rollNumber === 180) {
    return `${position}. Limited-context row. This was an en bloc appropriations amendment, but the available source text does not explain the full practical change. It remains visible below but is not counted in the summarized vote pattern.`;
  }
  if (rollNumber === 263) {
    return `${position}. Limited-context row. This was a motion to instruct conferees, not final passage of the underlying appropriations bill. It remains visible below but is not counted in the summarized vote pattern.`;
  }

  return genericSummary;
}

function extractMemberLabel(row) {
  const memberContext = String(row?.member_vote_context || "");
  const match = memberContext.match(/^([A-Z][A-Za-z.'-]+)/);
  return match?.[1] || "This representative";
}

function buildPlainTakeaway(row) {
  const summary = buildUsefulInterpretationText(row.plain_english_summary);
  const effect = buildUsefulInterpretationText(row.policy_effect);
  const text = `${summary} ${effect}`.toLowerCase();

  if (text.includes("budget blueprint") || text.includes("reconciliation")) {
    return "This vote helped set the rules for a later fast-track budget bill that could affect taxes, spending, deficits, and the debt limit.";
  }
  if (text.includes("shutdown") || text.includes("continuing appropriations") || text.includes("short-term funding")) {
    if (text.includes("back pay") || text.includes("reduction-in-force")) {
      return "This vote was about ending a shutdown, paying federal workers, and deciding how agencies would operate while longer-term funding was still unresolved.";
    }
    return "This vote was about avoiding a shutdown by keeping most federal agencies temporarily funded while longer-term spending bills were unfinished.";
  }
  if (text.includes("small business administration") || text.includes("sba")) {
    if (text.includes("loan")) {
      return "This vote was about restricting access to certain SBA-backed small-business loans based on immigration or residency status.";
    }
    return "This vote was about limiting net new SBA rulemaking costs for small businesses.";
  }
  if (text.includes("military construction") || text.includes("veterans affairs")) {
    return "This vote was about funding military construction, military housing, and veterans-related agencies and programs.";
  }

  return effect || summary;
}

function formatRecordedSideMeaning(value) {
  return String(value || "Recorded position did not map cleanly to the stored yea/nay meaning.")
    .replace(/^A Yea vote /i, "")
    .replace(/^A Nay vote /i, "")
    .trim();
}

function buildUsefulInterpretationText(value) {
  return String(value || "")
    .replace(/^This was a vote on (adopting|passing|agreeing to) (the|a) (resolution|bill|measure)\.?\s*/i, "")
    .replace(/^This was a vote on (adopting|passing|agreeing to) .+?\.\s*/i, "")
    .trim();
}

function groupEvidenceByBill(rows) {
  const groups = new Map();

  rows.forEach((row) => {
    const title = row.bill_title || row.question || "Unlabeled bill or measure";
    const key = title.toLowerCase();
    const current = groups.get(key) || {
      key,
      title,
      rows: [],
    };
    current.rows.push(row);
    groups.set(key, current);
  });

  return Array.from(groups.values());
}

function rowActionKey(row) {
  if (!row) {
    return "";
  }

  return `${row.roll_call_id}-${row.position}`;
}

function formatBillGroupSummary(rollCallCount, billCount) {
  if (typeof rollCallCount === "object" && rollCallCount !== null) {
    return formatEvidenceGroupingOverview(rollCallCount);
  }

  return `${rollCallCount} ${rollCallCount === 1 ? "roll-call vote" : "roll-call votes"} shown across ${billCount} ${
    billCount === 1 ? "bill or measure" : "bills or measures"
  }. Repeated rows can be amendments or related actions on the same bill.`;
}

function formatEvidenceGroupingOverview(summary) {
  const totalRows = summary?.totalRows || 0;
  const totalGroups = summary?.totalGroups || 0;
  const repeatedGroupCount = summary?.repeatedGroupCount || 0;
  const limitedCount = summary?.ambiguousOrInsufficientRows || 0;
  const proceduralContextCount = summary?.proceduralContextRows || 0;
  const notVotingCount = summary?.notVotingRows || 0;
  const parts = [
    `${totalRows} ${totalRows === 1 ? "evidence row" : "evidence rows"} shown across ${totalGroups} ${totalGroups === 1 ? "bill or measure group" : "bill or measure groups"}`,
  ];

  if (repeatedGroupCount) {
    parts.push(`${repeatedGroupCount} repeated ${repeatedGroupCount === 1 ? "group" : "groups"} detected`);
  }
  if (limitedCount) {
    parts.push(`${limitedCount} limited-context ${limitedCount === 1 ? "row" : "rows"} kept separate`);
  }
  if (proceduralContextCount) {
    parts.push(`${proceduralContextCount} procedural-context ${proceduralContextCount === 1 ? "row" : "rows"} shown for floor process only`);
  }
  if (notVotingCount) {
    parts.push(`${notVotingCount} not-voting ${notVotingCount === 1 ? "row" : "rows"} not counted as support or opposition`);
  }

  return `${parts.join("; ")}.`;
}

function formatEvidenceGroupCategory(group) {
  const category = group?.category || group;
  const label = buildVoterFacingGroupLabel(group);
  if (label) {
    return label;
  }

  const labels = {
    limited_context_rows: "Limited context",
    not_voting_rows: "Not voting",
    procedural_context_rows: "Procedural context",
    primary_bill_or_measure: "Primary measure",
    related_amendments: "Related amendments",
    related_floor_or_procedural_votes: "Related procedural votes",
  };

  return labels[category] || "Evidence group";
}

function buildVoterFacingGroupLabel(group) {
  const text = `${group?.label || ""} ${group?.rollCalls?.map((row) => `${row.issue_facet || ""} ${row.description || ""}`).join(" ") || ""}`.toLowerCase();

  if (text.includes("budget") && text.includes("reconciliation")) {
    return "Budget framework / reconciliation setup";
  }
  if (text.includes("sba") && text.includes("loan")) {
    return "SBA loan eligibility";
  }
  if (text.includes("military construction") || text.includes("veterans affairs")) {
    return "Military construction and VA funding";
  }
  if (text.includes("continuing appropriations") || text.includes("shutdown")) {
    return "Temporary funding / shutdown package";
  }
  if (text.includes("regulatory") && text.includes("sba")) {
    return "SBA regulatory-cost cap";
  }

  return "";
}

function buildSixtySecondPlan(groups) {
  const groupByKey = new Map((groups || []).map((group) => [group.key, group]));
  const strong = groupByKey.get("strong_evidence")?.rows?.[0] || null;
  const mixed = groupByKey.get("mixed_but_interpretable")?.rows?.[0] || null;
  const limitedRows = groupByKey.get("limited_evidence")?.rows || [];
  const notReadyRows = groupByKey.get("not_enough_to_summarize")?.rows || [];
  const firstStart = strong || mixed || limitedRows[0] || notReadyRows[0] || null;

  if (!firstStart) {
    return null;
  }

  const steps = [
    {
      domain: firstStart.domain,
      priority: "primary",
      title: strong
        ? `Start with ${formatDomainLabel(strong.domain)}`
        : mixed
          ? `Start with ${formatDomainLabel(mixed.domain)}`
          : `Start with ${formatDomainLabel(firstStart.domain)}`,
      detail: strong
        ? "This is the clearest reviewed issue read available for this representative."
        : mixed
          ? "This has enough reviewed vote meaning to inspect, but the pattern is mixed."
          : "Only limited evidence is available, so read the evidence before drawing a broader conclusion.",
    },
  ];

  if (mixed && mixed.domain !== firstStart.domain) {
    steps.push({
      domain: mixed.domain,
      priority: "secondary",
      title: `Then compare ${formatDomainLabel(mixed.domain)}`,
      detail: "This section is useful because reviewed votes point in more than one direction.",
    });
  }

  const limitedTarget = limitedRows.find((row) => row.domain !== firstStart.domain);
  if (limitedTarget) {
    steps.push({
      domain: limitedTarget.domain,
      priority: "secondary",
      title: `Use ${formatDomainLabel(limitedTarget.domain)} as a caution check`,
      detail: "This section remains visible, but it should not be read as a stable issue pattern yet.",
    });
  }

  return {
    summary: strong
      ? `Start with ${formatDomainLabel(strong.domain)} for the clearest reviewed record, then use mixed or limited sections to understand where the evidence gets thinner.`
      : "No strong issue read is available yet. The page still shows the best available evidence first and labels where the record is limited.",
    steps: steps.slice(0, 3),
    limitedNote: buildLimitedReadinessNote(limitedRows.length, notReadyRows.length),
  };
}

function buildLimitedReadinessNote(limitedCount, notReadyCount) {
  const pieces = [];
  if (limitedCount) {
    pieces.push(`${limitedCount} limited ${limitedCount === 1 ? "section is" : "sections are"} lower priority because reviewed vote meaning is thin`);
  }
  if (notReadyCount) {
    pieces.push(`${notReadyCount} ${notReadyCount === 1 ? "section does" : "sections do"} not have enough reviewed vote meaning to summarize`);
  }
  if (!pieces.length) {
    return "";
  }
  return `${pieces.join("; ")}.`;
}

function getReadinessGroupContainerClass(key) {
  if (key === "strong_evidence") {
    return "border-cyan-800/30 bg-cyan-50";
  }
  if (key === "mixed_but_interpretable") {
    return "border-indigo-200 bg-indigo-50";
  }
  if (key === "limited_evidence") {
    return "border-amber-200 bg-amber-50";
  }
  return "border-stone-200 bg-stone-50";
}

function formatIssueCardPriority(key) {
  if (key === "strong_evidence") {
    return "Best place to start";
  }
  if (key === "mixed_but_interpretable") {
    return "Useful comparison read";
  }
  if (key === "limited_evidence") {
    return "Lower priority: read cautiously";
  }
  return "Evidence visible, not ready to summarize";
}

function formatIssueCardEvidenceLine(row) {
  const interpretedYeaNay = (row.interpreted_support_count || 0) + (row.interpreted_oppose_count || 0);
  const recordedVotes = row.recorded_votes || 0;

  if (!interpretedYeaNay) {
    return recordedVotes
      ? `No reviewed Yes/No vote meaning is available yet out of ${recordedVotes} recorded ${recordedVotes === 1 ? "vote" : "votes"}.`
      : "No recorded Yes/No votes are available in this issue yet.";
  }

  return `${interpretedYeaNay} reviewed Yes/No ${interpretedYeaNay === 1 ? "vote" : "votes"} out of ${recordedVotes} recorded ${recordedVotes === 1 ? "vote" : "votes"}.`;
}

function formatIssueCardReason(row) {
  const key = row.readiness?.key;
  if (key === "strong_evidence") {
    return "Best place to start.";
  }
  if (key === "mixed_but_interpretable") {
    return "Reviewed votes point in more than one direction. Useful comparison read.";
  }
  if (key === "limited_evidence") {
    return "Reviewed vote meaning is thin. Read cautiously.";
  }
  return "Evidence may still be visible, but this issue is not ready for a confident summary.";
}

function formatChamber(chamber) {
  return chamber ? chamber[0].toUpperCase() + chamber.slice(1) : "";
}

function formatDate(value) {
  if (!value) {
    return "Unknown date";
  }
  return String(value).slice(0, 10);
}

function formatVotePosition(position) {
  if (position === "not_voting") {
    return "Not voting";
  }
  return String(position)
    .split("_")
    .map((segment) => segment[0].toUpperCase() + segment.slice(1))
    .join(" ");
}

function getVoteBadgeClass(position) {
  if (position === "yea") {
    return "bg-emerald-100 text-emerald-800";
  }
  if (position === "nay") {
    return "bg-rose-100 text-rose-800";
  }
  return "bg-stone-200 text-stone-700";
}

function formatEvidenceConfidenceLabel(row) {
  if (row.position === "not_voting") {
    return "Not counted";
  }
  if (isProceduralContextRow(row)) {
    return "Procedural context";
  }
  if (row.interpretation_status === "interpreted") {
    return "Reviewed meaning";
  }
  if (row.interpretation_status === "ambiguous") {
    return "Limited context";
  }
  if (row.interpretation_status === "insufficient_evidence") {
    return "Needs source support";
  }
  return "Evidence only";
}

function getEvidenceConfidenceBadgeClass(row) {
  if (row.position === "not_voting") {
    return "bg-stone-200 text-stone-700";
  }
  if (isProceduralContextRow(row)) {
    return "bg-sky-100 text-sky-900";
  }
  if (row.interpretation_status === "interpreted") {
    return "bg-cyan-100 text-cyan-900";
  }
  if (row.interpretation_status === "ambiguous") {
    return "bg-amber-100 text-amber-900";
  }
  if (row.interpretation_status === "insufficient_evidence") {
    return "bg-stone-200 text-stone-700";
  }
  return "bg-stone-100 text-stone-600";
}

function buildTakeaway(rows) {
  if (!rows.length) {
    return "There is not enough reviewed issue evidence in the current window to show a confident issue read.";
  }

  const bestRead = rows.find((row) => row.readiness?.key === "strong_evidence");
  const mixedRead = rows.find((row) => row.readiness?.key === "mixed_but_interpretable");
  const firstLimited = rows.find((row) => row.readiness?.key === "limited_evidence");

  if (bestRead && mixedRead) {
    return `The strongest reviewed issue read is ${formatDomainLabel(bestRead.domain)}. ${formatDomainLabel(mixedRead.domain)} is also useful, but the interpreted votes are mixed.`;
  }
  if (bestRead) {
    return `The strongest reviewed issue read is ${formatDomainLabel(bestRead.domain)}. Limited sections remain visible below without being treated as confident summaries.`;
  }
  if (mixedRead) {
    return `${formatDomainLabel(mixedRead.domain)} has enough reviewed evidence to inspect, but the vote pattern is mixed rather than one-directional.`;
  }
  if (firstLimited) {
    return `The available issue reads are limited. Start with ${formatDomainLabel(firstLimited.domain)} if you want to inspect the strongest available evidence, but do not treat it as a confident issue pattern.`;
  }

  return "The current issue sections are visible as evidence, but none have enough reviewed vote meaning for a confident summary yet.";
}

function buildPatternRows(rows) {
  return [...rows]
    .filter((row) => (row.interpreted_total || 0) > 0)
    .sort(
      (left, right) =>
        (right.interpreted_total || 0) - (left.interpreted_total || 0) ||
        Math.abs((right.interpreted_support_count || 0) - (right.interpreted_oppose_count || 0)) -
          Math.abs((left.interpreted_support_count || 0) - (left.interpreted_oppose_count || 0)),
    )
    .slice(0, 3)
    .map((row) => {
      const supportCount = row.interpreted_support_count || 0;
      const opposeCount = row.interpreted_oppose_count || 0;
      const otherCount = row.interpreted_other_count || 0;
      const recordedVotes = row.recorded_votes || 0;
      const interpretedRecordedVotes = supportCount + opposeCount;
      const coverageText = `${interpretedRecordedVotes} of ${recordedVotes} recorded yes/no votes have reviewed meaning`;
      let label = "Mixed record in votes shown";

      if (supportCount > opposeCount && opposeCount === 0) {
        label = "Mostly for interpreted measures";
      } else if (opposeCount > supportCount && supportCount === 0) {
        label = "Mostly against interpreted measures";
      } else if (supportCount > opposeCount) {
        label = "Mostly for interpreted measures";
      } else if (opposeCount > supportCount) {
        label = "Mostly against interpreted measures";
      }

      return {
        domain: row.domain,
        label,
        supportCount,
        opposeCount,
        detail: `${coverageText}. ${formatOtherInterpretedCount(otherCount)}`,
      };
    });
}

function formatPartyName(party) {
  const labels = {
    D: "Democrat",
    R: "Republican",
    I: "Independent",
  };

  return labels[party] || String(party || "party member");
}

function buildActionContext({ domain, evidenceRows, representativeName, selectedEvidenceRow }) {
  const interpretedRows = evidenceRows.filter((row) => row.interpretation_status === "interpreted");
  const supportCount = interpretedRows.filter((row) => row.position === row.support_position).length;
  const opposeCount = interpretedRows.filter((row) => row.position === row.oppose_position).length;
  const otherCount = interpretedRows.length - supportCount - opposeCount;
  const cautiousCount = evidenceRows.filter((row) => row.interpretation_status && row.interpretation_status !== "interpreted").length;
  const issueLabel = formatDomainLabel(domain);
  const contextLine = `${representativeName}'s ${issueLabel} evidence currently shows ${supportCount} votes for interpreted measures, ${opposeCount} votes against interpreted measures, ${otherCount} rows without a yea/nay position, and ${cautiousCount} rows with limited vote meaning among the evidence shown here.`;
  const example = selectedEvidenceRow || interpretedRows.find((row) => row.position === "yea" || row.position === "nay") || interpretedRows[0] || evidenceRows[0] || null;
  const exampleLine = formatActionVoteLine(example);
  const selectedVoteLine = selectedEvidenceRow ? formatActionVoteLine(selectedEvidenceRow) : "";
  const selectedVoteMeaning = selectedEvidenceRow ? buildSelectedVoteMeaning(selectedEvidenceRow) : "";

  return {
    contextLine,
    exampleLine,
    issueLabel,
    selectedVoteLine,
    selectedVoteMeaning,
  };
}

function formatActionVoteLine(row) {
  if (!row) {
    return "";
  }

  return `${formatDate(row.vote_date)} ${formatChamber(row.chamber)} Roll ${row.rollcall_number}: ${row.description || row.question}`;
}

function buildSelectedVoteMeaning(row) {
  if (!row || row.interpretation_status !== "interpreted") {
    return "";
  }

  return buildInterpretedVoteRead(row);
}

function formatOtherInterpretedCount(count) {
  if (!count) {
    return "No interpreted votes used another recorded position.";
  }
  return `${count} additional interpreted ${count === 1 ? "roll call used" : "roll calls used"} another recorded position, such as not voting.`;
}

function formatSourceBasis(item) {
  if (!item || typeof item !== "object") {
    return "Source basis recorded";
  }

  return item.source || item.field || "Source basis recorded";
}

function formatContactSource(contact) {
  const sourceType = String(contact?.source_type || "official source").replaceAll("_", " ");
  const retrievedAt = contact?.source_retrieved_at ? `retrieved ${String(contact.source_retrieved_at).slice(0, 10)}` : "retrieval date not loaded";
  return `${sourceType}, ${retrievedAt}`;
}

function formatClassificationReason(reason) {
  if (reason === "policy_vote") {
    return "eligible policy vote";
  }

  return String(reason || "eligible vote").replaceAll("_", " ");
}

function hasInterpretationDetail(row) {
  return Boolean(
    row.plain_english_summary ||
      row.yea_meaning ||
      row.nay_meaning ||
      row.policy_effect ||
      row.uncertainty_note ||
      row.interpretation_reason,
  );
}

function formatInterpretationStatus(statusInput) {
  if (isProceduralContextRow(statusInput)) {
    return "Procedural Context";
  }
  const status = typeof statusInput === "object" ? statusInput?.interpretation_status : statusInput;
  if (status === "interpreted") {
    return "Plain-English";
  }
  if (status === "ambiguous") {
    return "Ambiguous";
  }
  if (status === "insufficient_evidence") {
    return "Needs More Evidence";
  }
  return "Not Reviewed";
}

function getInterpretationBadgeClass(statusInput) {
  if (isProceduralContextRow(statusInput)) {
    return "bg-sky-100 text-sky-900";
  }
  const status = typeof statusInput === "object" ? statusInput?.interpretation_status : statusInput;
  if (status === "interpreted") {
    return "bg-cyan-900 text-white";
  }
  if (status === "ambiguous") {
    return "bg-amber-100 text-amber-900";
  }
  return "bg-stone-200 text-stone-700";
}

function formatIssueFacet(value) {
  return String(value || "")
    .split("_")
    .filter(Boolean)
    .map((segment) => segment[0].toUpperCase() + segment.slice(1))
    .join(" ");
}

function buildContextBadges(row) {
  const badges = [];
  const voteType = row.vote_context?.vote_type;

  if (voteType) {
    badges.push(formatVoteType(voteType));
  }
  if (row.interpretation_status === "interpreted") {
    badges.push("Plain-English interpretation available");
  }
  if (row.interpretation_status === "ambiguous") {
    badges.push("Limited source context");
  }
  if (row.interpretation_status === "insufficient_evidence") {
    badges.push("Limited source context");
  }
  if (isProceduralContextRow(row)) {
    badges.push("Procedural context only");
  }
  if (row.vote_context?.member_voted_with_party_majority === true) {
    badges.push("Voted with most of their party");
  } else if (row.vote_context?.member_voted_with_party_majority === false) {
    badges.push("Broke with most of their party");
  }
  if (row.vote_context?.member_voted_with_winning_side === true) {
    badges.push("Voted with the winning side");
  } else if (row.vote_context?.member_voted_with_winning_side === false) {
    badges.push("Voted against the final outcome");
  }

  return Array.from(new Set(badges));
}

function buildVoteContextLine(row) {
  const context = row.vote_context;
  if (!context) {
    return "";
  }

  const pieces = [];
  if (context.final_result && context.vote_margin !== null && context.vote_margin !== undefined) {
    pieces.push(`Outcome: ${formatFinalResult(context.final_result)} by ${context.vote_margin} ${context.vote_margin === 1 ? "vote" : "votes"}`);
  } else if (context.final_result) {
    pieces.push(`Outcome: ${formatFinalResult(context.final_result)}`);
  }

  if (context.member_party_majority_position && context.member_party) {
    pieces.push(`Most ${formatPartyName(context.member_party)}s voted ${formatContextPosition(context.member_party_majority_position)}`);
  }

  if (!pieces.length) {
    return "";
  }

  return pieces.join(". ") + ".";
}

function formatFinalResult(value) {
  const labels = {
    failed: "failed",
    no_yea_nay_majority: "had no yea/nay majority",
    passed: "passed",
  };

  return labels[value] || String(value || "recorded").replaceAll("_", " ");
}

function formatContextPosition(value) {
  const labels = {
    nay: "Nay",
    not_voting: "Not Voting",
    present: "Present",
    yea: "Yea",
  };

  return labels[value] || String(value || "unknown").replaceAll("_", " ");
}

function formatVoteType(value) {
  const labels = {
    final_passage: "Final passage",
    amendment: "Amendment vote",
    rule: "Rule vote",
    motion: "Motion vote",
    concurrence: "Concurrence vote",
    procedural: "Procedural vote",
    nomination: "Nomination vote",
    appropriations: "Appropriations vote",
    cra_disapproval: "CRA disapproval vote",
    other: "Other vote type",
  };

  return labels[value] || String(value || "Vote context")
    .split("_")
    .map((segment) => segment[0].toUpperCase() + segment.slice(1))
    .join(" ");
}

function getPositionLabel(row) {
  const interpretedYeaNay = (row.interpreted_support_count || 0) + (row.interpreted_oppose_count || 0);
  if (!interpretedYeaNay) {
    return "Too little interpreted evidence";
  }

  const gap = Math.abs(row.yea_share - row.nay_share);
  if (gap < 0.15) {
    return "Mixed record in votes shown";
  }

  return row.yea_share >= row.nay_share ? "Mostly Yea in votes shown" : "Mostly Nay in votes shown";
}

function getPositionBadgeClass(row) {
  const label = getPositionLabel(row);
  if (label === "Mostly Yea in votes shown") {
    return "bg-emerald-100 text-emerald-800";
  }
  if (label === "Mostly Nay in votes shown") {
    return "bg-rose-100 text-rose-800";
  }
  return "bg-stone-200 text-stone-700";
}

function getReadinessBadgeClass(key) {
  if (key === "strong_evidence") {
    return "bg-cyan-900 text-white";
  }
  if (key === "mixed_but_interpretable") {
    return "bg-indigo-100 text-indigo-900";
  }
  if (key === "limited_evidence") {
    return "bg-amber-100 text-amber-900";
  }
  return "bg-stone-200 text-stone-700";
}

function formatReadinessGroupHelp(key) {
  if (key === "strong_evidence") {
    return "Enough reviewed vote meaning is available for a clear issue read.";
  }
  if (key === "mixed_but_interpretable") {
    return "Enough reviewed vote meaning is available, but the votes point in more than one direction.";
  }
  if (key === "limited_evidence") {
    return "Some reviewed evidence is available, but the section should stay cautious.";
  }
  return "Evidence rows may still be visible, but the issue should not get a confident summary yet.";
}

function buildPositionRead(row) {
  const label = getPositionLabel(row);
  if (label === "Too little interpreted evidence") {
    return `${row.recorded_votes || 0} recorded votes`;
  }
  if (label === "Mixed record in votes shown") {
    return `${(row.yea_share * 100).toFixed(0)}% yea / ${(row.nay_share * 100).toFixed(0)}% nay`;
  }

  const strongerShare = Math.max(row.yea_share, row.nay_share);
  return `${(strongerShare * 100).toFixed(0)}% of recorded votes`;
}

function buildInterpretationCoverageRead(row) {
  const interpretedYeaNay = (row.interpreted_support_count || 0) + (row.interpreted_oppose_count || 0);
  const recordedVotes = row.recorded_votes || 0;

  if (!recordedVotes) {
    return "No recorded yea/nay votes in this issue.";
  }
  if (!interpretedYeaNay) {
    return "No interpreted yea/nay vote meanings yet; open evidence to inspect raw roll calls.";
  }
  if (interpretedYeaNay === recordedVotes) {
    return `${interpretedYeaNay} of ${recordedVotes} recorded yes/no votes have reviewed meaning.`;
  }
  return `${interpretedYeaNay} of ${recordedVotes} recorded yes/no votes have reviewed meaning; the rest stay visible but uninterpreted.`;
}
