"use client";

import { useEffect, useState } from "react";

import EditorialIssueExperience from "./EditorialIssueExperience";
import { fetchLegislatorContact, fetchPositionEvidence, fetchPositions } from "../lib/api";
import {
  EDITORIAL_EXPERIENCE_MODE,
  hasEligibleEditorialSlice,
  isEditorialExperienceRow,
  selectEditorialIssueExperience,
} from "../lib/editorialIssueExperience.mjs";
import {
  buildBasicEvidencePresentation,
  issueAvailabilityLabel,
} from "../lib/editorialIssuePublicPresentation.mjs";
import { deriveEvidenceGroups } from "../lib/evidenceGrouping.mjs";
import { groupIssueRowsByReadiness, sortIssueRowsByReadiness } from "../lib/issueReadiness.mjs";
import { formatDisplayMeasureTitle } from "../lib/measureDisplay.mjs";
import { fillMissingInterpretedCounts } from "../lib/positionEvidenceCounts.mjs";
import { isProceduralContextRow } from "../lib/proceduralContext.mjs";
import { buildIssueCardPreview } from "../lib/profileNarrative.mjs";
import { DOMAIN_LABELS, formatDomainLabel } from "../lib/issueDomains";
import {
  buildLimitedContextSummary as buildGenericLimitedContextSummary,
  buildVoteCardSummary as buildGenericVoteCardSummary,
} from "../lib/voteCardSummary.mjs";

const REPRESENTATIVE_VOTE_LIMIT = 8;

export default function PositionByIssue({
  editorialCandidates,
  editorialMode = EDITORIAL_EXPERIENCE_MODE.production,
  evidenceRequest = null,
  fixtureData = null,
  legislator = null,
  legislatorId = "leg_alex_morgan",
  scope = "all",
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
        if (fixtureData?.positions) {
          if (!active) {
            return;
          }
          setState({
            status: "ready",
            payload: fixtureData.positions,
            error: null,
          });
          return;
        }

        const positionsPayload = await fetchPositions({ legislatorId, scope });
        const payload = await fillMissingInterpretedCounts({
          payload: positionsPayload,
          fetchEvidence: (args) => fetchPositionEvidence({ ...args, scope }),
          legislatorId,
        });
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
  }, [fixtureData, legislatorId, scope]);

  useEffect(() => {
    setSelectedDomain(null);
    setEvidenceState({
      status: "idle",
      payload: null,
      error: null,
    });
  }, [legislatorId]);

  useEffect(() => {
    if (!selectedDomain) {
      return;
    }
    inspectDomain(selectedDomain);
  }, [scope]);

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
  const takeaway = buildTakeaway(rows);
  const selectedRow = rows.find((row) => row.domain === selectedDomain) || rows[0] || null;
  const startPlan = buildSixtySecondPlan(readinessGroups);
  const hasSelectedEditorialSlice = Boolean(selectedRow) && hasEligibleEditorialSlice({
    candidates: editorialCandidates,
    domain: selectedRow.domain,
    legislator,
    mode: editorialMode,
  });

  async function inspectDomain(domain) {
    setSelectedDomain(domain);
    setEvidenceState({
      status: "loading",
      payload: null,
      error: null,
    });

    try {
      if (fixtureData?.evidenceByDomain) {
        const payload = fixtureData.evidenceByDomain[domain];
        if (!payload) {
          throw new Error(`No fixture evidence for ${domain}`);
        }
        setEvidenceState({
          status: "ready",
          payload,
          error: null,
        });
        return;
      }

      const payload = await fetchPositionEvidence({ legislatorId, domain, scope });
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
    <section id="position-by-issue" className="mt-4 rounded-2xl border border-stone-200 bg-white p-4 shadow-[0_12px_32px_rgba(15,23,42,0.07)] lg:p-5">
      {!hasSelectedEditorialSlice ? <div className="grid min-w-0 items-start gap-4 xl:grid-cols-[minmax(360px,0.72fr)_minmax(0,1.28fr)]">
        <div className="min-w-0">
          <p className="text-xs uppercase tracking-[0.2em] text-cyan-800">
            Issue Evidence
          </p>
          <h3 className="mt-1 font-serif text-[1.55rem] leading-[1.05] text-stone-950 sm:text-[2rem]">
            {title}
          </h3>
          <p className="mt-2 max-w-xl text-[15px] leading-6 text-stone-800">
            {state.status === "ready"
              ? takeaway
              : state.status === "loading"
                ? "Reading where this legislator's reviewed issue evidence is strongest."
                : "The site cannot read issue readiness for this legislator right now."}
          </p>
          {state.status === "ready" ? (
            <p className="mt-2 text-xs uppercase tracking-[0.14em] text-stone-500">
              {formatScopeLine(state.payload?.scope_metadata)}
            </p>
          ) : null}
          {state.status === "ready" && !selectedDomain && startPlan?.steps?.[0] ? (
            <button
              className="mt-3 rounded-full border border-cyan-900/20 bg-cyan-50 px-4 py-2 text-left text-xs uppercase tracking-[0.15em] text-cyan-950 transition hover:bg-cyan-100"
              onClick={() => inspectDomain(startPlan.steps[0].domain)}
              type="button"
            >
              Start with {formatDomainLabel(startPlan.steps[0].domain)}
            </button>
          ) : null}
        </div>

        <div className="grid min-w-0 content-start gap-3">
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
            <IssueNavigation
              editorialCandidates={editorialCandidates}
              editorialMode={editorialMode}
              inspectDomain={inspectDomain}
              legislator={legislator}
              rows={rows}
              selectedDomain={selectedDomain}
            />
          ) : null}
        </div>
      </div> : state.status === "ready" && rows.length > 1 ? (
        <div className="mb-3">
          <IssueNavigation
            editorialCandidates={editorialCandidates}
            editorialMode={editorialMode}
            inspectDomain={inspectDomain}
            legislator={legislator}
            rows={rows}
            selectedDomain={selectedDomain}
          />
        </div>
      ) : null}

      <EvidencePanel
        editorialCandidates={editorialCandidates}
        editorialMode={editorialMode}
        evidenceState={evidenceState}
        legislator={legislator}
        onInspectDomain={inspectDomain}
        selectedRow={selectedRow}
      />

      {state.status === "ready" ? (
        <section className="mt-4 border-t border-stone-200 pt-4" aria-label="Explore all issue evidence">
          <div className="mb-3">
            <p className="text-xs uppercase tracking-[0.18em] text-cyan-900">Explore other issues</p>
            <p className="mt-1 text-sm leading-6 text-stone-600">Compare where reviewed analysis, vote receipts, or only a limited record is currently available.</p>
          </div>
          <IssueReadinessGroups
            groups={readinessGroups}
            inspectDomain={inspectDomain}
            selectedDomain={selectedDomain}
          />
        </section>
      ) : null}

    </section>
  );
}

function IssueNavigation({ editorialCandidates, editorialMode, inspectDomain, legislator, rows, selectedDomain }) {
  const navRows = (rows || []).filter((row) => row.recorded_votes > 0 || getInterpretedCount(row) > 0);

  if (navRows.length <= 1) {
    return null;
  }

  return (
    <nav aria-label="Issue evidence navigation" className="min-w-0 self-start rounded-xl border border-stone-200 bg-stone-50 px-3 py-2">
      <div className="flex items-center justify-between gap-2">
        <p className="text-[11px] uppercase tracking-[0.16em] text-stone-500">
          Jump to issue
        </p>
        <span className="text-xs text-stone-500">{navRows.length} {navRows.length === 1 ? "area" : "areas"}</span>
      </div>
      <div className="mt-2 flex gap-2 overflow-x-auto pb-1">
        {navRows.map((row) => {
          const hasEditorialSlice = hasEligibleEditorialSlice({
            candidates: editorialCandidates,
            domain: row.domain,
            legislator,
            mode: editorialMode,
          });
          return (
          <button
            aria-current={selectedDomain === row.domain ? "true" : undefined}
            className={`shrink-0 rounded-full border px-3 py-1.5 text-xs transition focus:outline-none focus:ring-2 focus:ring-cyan-800 focus:ring-offset-2 ${
              selectedDomain === row.domain
                ? "border-cyan-800 bg-cyan-900 text-white"
                : "border-stone-200 bg-white text-stone-700 hover:border-cyan-700/50"
            }`}
            key={row.domain}
            onClick={() => inspectDomain(row.domain)}
            type="button"
          >
            <span className="font-medium">{formatDomainLabel(row.domain)}</span>
            <span className="ml-2 opacity-75">{issueAvailabilityLabel({ hasEditorialSlice, row })}</span>
          </button>
          );
        })}
      </div>
    </nav>
  );
}

function IssueReadinessGroups({ groups, inspectDomain, selectedDomain }) {
  const visibleGroups = groups.filter((group) => group.rows.length > 0);

  if (!visibleGroups.length) {
    return null;
  }

  return (
    <div className="grid gap-2.5">
      {visibleGroups.map((group) => (
        <section className={`rounded-xl border px-3 py-3 ${getReadinessGroupContainerClass(group.key)}`} key={group.key}>
          <div className="flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.16em] text-cyan-900">
                {group.label}
              </p>
              <p className="mt-1 text-sm leading-5 text-stone-600">
                {formatReadinessGroupHelp(group.key)}
              </p>
            </div>
            <span className="w-fit rounded-full bg-white px-3 py-1 text-xs uppercase tracking-[0.16em] text-stone-600">
              {group.rows.length} {group.rows.length === 1 ? "issue" : "issues"}
            </span>
          </div>
          {group.key === "limited_evidence" || group.key === "not_enough_to_summarize" ? (
            <CompactIssueList
              inspectDomain={inspectDomain}
              rows={group.rows}
              selectedDomain={selectedDomain}
            />
          ) : (
            <div className="mt-2 grid gap-2 md:grid-cols-2">
              {group.rows.map((row) => (
                <IssueReadinessTile
                  inspectDomain={inspectDomain}
                  key={row.domain}
                  row={row}
                  selectedDomain={selectedDomain}
                />
              ))}
            </div>
          )}
        </section>
      ))}
    </div>
  );
}

function CompactIssueList({ inspectDomain, rows, selectedDomain }) {
  return (
    <div className="mt-2 divide-y divide-stone-200 overflow-hidden rounded-xl border border-stone-200 bg-white">
      {rows.map((row) => (
        <button
          aria-label={`Inspect ${formatDomainLabel(row.domain)} votes`}
          aria-pressed={selectedDomain === row.domain}
          className={`grid w-full gap-1 px-3 py-2.5 text-left transition sm:grid-cols-[minmax(0,1fr)_auto_auto] sm:items-center sm:gap-3 ${
            selectedDomain === row.domain ? "bg-cyan-50" : "hover:bg-stone-50"
          }`}
          key={row.domain}
          onClick={() => inspectDomain(row.domain)}
          type="button"
        >
          <span className="text-sm font-medium leading-5 text-stone-950">
            {formatDomainLabel(row.domain)}
          </span>
          <span className="text-xs uppercase tracking-[0.12em] text-stone-500">
            {row.recorded_votes || 0} votes
          </span>
          <span className={`w-fit rounded-full px-2.5 py-1 text-[11px] uppercase tracking-[0.1em] ${getReadinessBadgeClass(row.readiness?.key)}`}>
            {(row.interpreted_support_count || 0) + (row.interpreted_oppose_count || 0)} reviewed
          </span>
        </button>
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
      className={`rounded-xl border px-3 py-2.5 text-left shadow-[inset_0_1px_0_rgba(255,255,255,0.72)] transition ${
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
        <p className="max-w-[220px] text-sm leading-5 text-stone-950">
          {formatDomainLabel(row.domain)}
        </p>
        <p className="shrink-0 text-sm text-stone-500">{row.recorded_votes || 0} votes</p>
      </div>
      <div className="mt-2 flex flex-col gap-1.5">
        <span className={`w-fit max-w-full rounded-xl px-3 py-1 text-[11px] uppercase leading-4 tracking-[0.12em] ${getReadinessBadgeClass(row.readiness?.key)}`}>
          {formatIssueCardStatusLabel(row)}
        </span>
        <p className="text-[13px] leading-5 text-stone-700">
          {formatIssueCardEvidenceLine(row)}
        </p>
        <p className="text-[13px] leading-5 text-stone-600">
          {formatIssueCardReason(row)}
        </p>
        <p className="text-[11px] uppercase leading-4 tracking-[0.12em] text-stone-500">
          {formatIssueCardPriority(row)}
        </p>
      </div>
      <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-stone-200">
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
  if (status !== "ready" || rows.length === 0) {
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
    </div>
  );
}

function EvidencePanel({ editorialCandidates, editorialMode, evidenceState, legislator, onInspectDomain, selectedRow }) {
  const [selectedActionRow, setSelectedActionRow] = useState(null);
  const [showAllVotes, setShowAllVotes] = useState(false);

  useEffect(() => {
    setSelectedActionRow(null);
    setShowAllVotes(false);
  }, [selectedRow?.domain]);

  if (!selectedRow) {
    return null;
  }

  const evidenceRows = evidenceState.payload?.evidence || [];
  const isSelected = evidenceState.payload?.domain === selectedRow.domain;
  const editorialExperience = selectEditorialIssueExperience({
    candidates: editorialCandidates,
    domain: selectedRow.domain,
    evidenceRows,
    legislator,
    mode: editorialMode,
  });
  const additionalEvidenceRows = editorialExperience
    ? evidenceRows.filter((row) => !isEditorialExperienceRow(row, editorialExperience))
    : evidenceRows;
  const evidenceGrouping = deriveEvidenceGroups(evidenceRows);
  const billGroups = groupEvidenceByBill(additionalEvidenceRows);
  const proofView = buildProofView(evidenceRows);

  return (
    <div id="position-evidence" className="mt-4 scroll-mt-6 rounded-2xl border border-stone-200 bg-stone-50 px-3 py-3 sm:px-4 lg:px-5">
      {!editorialExperience ? <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.22em] text-stone-500">
            Evidence
          </p>
          <h4 className="mt-1 font-serif text-[1.6rem] leading-none text-stone-950 sm:text-[1.85rem]">
            {formatDomainLabel(selectedRow.domain)}
          </h4>
        </div>
        <button
          className="rounded-full bg-stone-900 px-3 py-2 text-xs uppercase tracking-[0.16em] text-stone-100 transition hover:bg-cyan-900 focus:outline-none focus:ring-2 focus:ring-cyan-800 focus:ring-offset-2"
          onClick={() => onInspectDomain(selectedRow.domain)}
          type="button"
        >
          Show Votes
        </button>
      </div> : null}

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
        <div className="mt-3 grid gap-3">
          {editorialExperience ? (
            <EditorialIssueExperience experience={editorialExperience} />
          ) : (
            <>
              <IssueEvidenceSummary
                domain={selectedRow.domain}
                representativeName={legislator?.name_display}
                rows={evidenceRows}
              />
              <RepresentativeVotesSection
                proofView={proofView}
                representativeName={legislator?.name_display}
                selectedActionRow={selectedActionRow}
                setSelectedActionRow={setSelectedActionRow}
              />
            </>
          )}
          {!editorialExperience && additionalEvidenceRows.length > 0 ? (
            <ReviewedVoteList
              billGroups={billGroups}
              evidenceRows={additionalEvidenceRows}
              hasEditorialSlice={Boolean(editorialExperience)}
              representativeName={legislator?.name_display}
              selectedActionRow={selectedActionRow}
              setSelectedActionRow={setSelectedActionRow}
              showAllVotes={showAllVotes}
              setShowAllVotes={setShowAllVotes}
            />
          ) : null}
          {!editorialExperience ? <EvidenceGroupingPreview evidenceGrouping={evidenceGrouping} /> : null}
          {!editorialExperience ? (
            <EvidenceUtilityPanel
              domain={selectedRow.domain}
              evidenceRows={evidenceRows}
              legislator={legislator}
              selectedEvidenceRow={selectedActionRow}
            />
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

function RepresentativeVotesSection({ proofView, representativeName, selectedActionRow, setSelectedActionRow }) {
  const rows = proofView.representativeRows;

  if (!rows.length) {
    return (
      <section className="rounded-xl border border-stone-200 bg-white px-3 py-3 sm:px-4">
        <p className="text-xs uppercase tracking-[0.18em] text-cyan-900">
          Representative votes
        </p>
        <p className="mt-1 text-sm leading-6 text-stone-700">
          This issue does not have countable Yes/No votes ready for a first proof set. Open the full reviewed vote list to inspect the available context.
        </p>
      </section>
    );
  }

  return (
    <section className="rounded-xl border border-cyan-900/10 bg-white px-3 py-3 sm:px-4">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-cyan-900">
            Representative votes
          </p>
          <p className="mt-1 text-sm leading-6 text-stone-700">
            A first set of votes behind this read. Start here, then expand the full reviewed vote list.
          </p>
        </div>
        <span className="w-fit rounded-full bg-cyan-50 px-3 py-1 text-xs uppercase tracking-[0.14em] text-cyan-950">
          {rows.length} of {proofView.countableRows.length} countable Yes/No votes
        </span>
      </div>
      <div className="mt-3 grid gap-2">
        {rows.map((row) => (
          <VoteEvidenceRow
            key={`representative-${row.roll_call_id}-${row.position}`}
            representativeName={representativeName}
            row={row}
            selectedActionRow={selectedActionRow}
            setSelectedActionRow={setSelectedActionRow}
          />
        ))}
      </div>
      {proofView.contextRows.length ? (
        <p className="mt-3 rounded-lg border border-stone-200 bg-stone-50 px-3 py-2 text-sm leading-6 text-stone-700">
          {formatContextRowSummary(proofView)} Full context rows remain available in the reviewed vote list.
        </p>
      ) : null}
    </section>
  );
}

function ReviewedVoteList({
  billGroups,
  evidenceRows,
  hasEditorialSlice = false,
  representativeName,
  selectedActionRow,
  setSelectedActionRow,
  showAllVotes,
  setShowAllVotes,
}) {
  return (
    <section className="rounded-xl border border-stone-200 bg-white px-3 py-3 sm:px-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-cyan-900">
            {hasEditorialSlice ? "Additional reviewed vote list" : "Full reviewed vote list"}
          </p>
          <p className="mt-1 text-sm leading-6 text-stone-700">
            {hasEditorialSlice
              ? "The remaining receipts stay available here, grouped by bill or measure, with context and counting labels preserved."
              : "All receipts stay available, grouped by bill or measure, with countable and context labels preserved."}
          </p>
        </div>
        <button
          aria-expanded={showAllVotes}
          className="w-fit rounded-full border border-cyan-900/20 bg-cyan-50 px-3 py-2 text-xs uppercase tracking-[0.14em] text-cyan-950 transition hover:bg-cyan-100 focus:outline-none focus:ring-2 focus:ring-cyan-800 focus:ring-offset-2"
          onClick={() => setShowAllVotes((current) => !current)}
          type="button"
        >
          {showAllVotes ? "Hide full list" : "Show all reviewed votes"}
        </button>
      </div>
      <div className="mt-3 flex flex-wrap gap-2 text-[11px] uppercase tracking-[0.12em] text-stone-600">
        <span className="rounded-full bg-stone-100 px-2.5 py-1">{evidenceRows.length} reviewed votes</span>
        <span className="rounded-full bg-cyan-50 px-2.5 py-1">{billGroups.length} evidence groups</span>
      </div>
      {showAllVotes ? (
        <div className="mt-3 grid gap-3">
          {billGroups.map((group) => (
            <BillEvidenceGroup
              group={group}
              key={group.key}
              representativeName={representativeName}
              selectedActionRow={selectedActionRow}
              setSelectedActionRow={setSelectedActionRow}
            />
          ))}
        </div>
      ) : (
        <p className="mt-3 rounded-lg border border-stone-200 bg-stone-50 px-3 py-2 text-sm leading-6 text-stone-700">
          Showing representative votes first. Use Show all reviewed votes for every grouped receipt in this issue.
        </p>
      )}
    </section>
  );
}

function BillEvidenceGroup({ group, representativeName, selectedActionRow, setSelectedActionRow }) {
  return (
    <article className={`rounded-xl border px-3 py-3 sm:px-4 ${getBillGroupContainerClass(group)}`}>
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-stone-500">
            {formatEvidenceGroupCategory(group)}
          </p>
          <h5 className="mt-1 break-words text-base leading-6 text-stone-950">
            {formatDisplayMeasureTitle(group.title)}
          </h5>
          <p className="mt-1 text-sm leading-5 text-stone-600">
            {formatBillGroupScanLine(group)}
          </p>
        </div>
        <span className="w-fit rounded-full bg-stone-100 px-3 py-1 text-xs uppercase tracking-[0.16em] text-stone-700">
          {group.rows.length} reviewed {group.rows.length === 1 ? "vote" : "votes"}
        </span>
      </div>

      <div className="mt-3 grid gap-2">
        {group.rows.map((row) => (
          <VoteEvidenceRow
            key={`${row.roll_call_id}-${row.position}`}
            representativeName={representativeName}
            row={row}
            selectedActionRow={selectedActionRow}
            setSelectedActionRow={setSelectedActionRow}
          />
        ))}
      </div>
    </article>
  );
}

function VoteEvidenceRow({ representativeName, row, selectedActionRow, setSelectedActionRow }) {
  const isProcedural = isProceduralContextRow(row);
  const scanSummary =
    buildVoteCardSummary(row, { representativeName }) ||
    buildLimitedContextSummary(row) ||
    row.plain_english_summary ||
    row.description ||
    row.question ||
    "Recorded vote row.";
  const voteType = row.vote_context?.vote_type || row.vote_type;
  const typeLabel = voteType ? formatVoteType(voteType) : "";
  const confidenceLabel = formatEvidenceConfidenceLabel(row);
  const rowToneClass = isProcedural
    ? "border-sky-100 bg-sky-50/70"
    : row.interpretation_status === "interpreted" && row.position !== "not_voting"
      ? "border-cyan-900/15 bg-white"
      : "border-stone-200 bg-stone-50";

  return (
    <article className={`rounded-xl border px-3 py-2.5 ${rowToneClass}`}>
      <div className="grid gap-2 md:grid-cols-[minmax(0,1fr)_auto] md:items-start">
        <div>
          <p className="break-words text-[11px] uppercase tracking-[0.16em] text-stone-500">
            {formatDate(row.vote_date)} - {formatChamber(row.chamber)} Roll {row.rollcall_number}
            {typeLabel ? ` - ${typeLabel}` : ""}
          </p>
          <p className="mt-1 break-words text-sm leading-5 text-stone-950">
            {formatDisplayMeasureTitle(row.description || row.question)}
          </p>
          <p className="mt-1 text-sm leading-6 text-stone-700">
            {scanSummary}
          </p>
        </div>
        <div className="flex flex-wrap gap-2 md:justify-end">
          <span className={`w-fit rounded-full px-3 py-1 text-xs uppercase tracking-[0.16em] ${getVoteBadgeClass(row.position)}`}>
            {formatVotePosition(row.position)}
          </span>
          <span className={`w-fit rounded-full px-3 py-1 text-[11px] uppercase tracking-[0.14em] ${getEvidenceConfidenceBadgeClass(row)}`}>
            {confidenceLabel}
          </span>
        </div>
      </div>

      <details className="mt-2 rounded-lg border border-stone-200 bg-white/80 px-3 py-2">
        <summary className="cursor-pointer text-[11px] uppercase tracking-[0.16em] text-stone-600 marker:text-cyan-900">
          Source, caveats, and full context
        </summary>
        <div className="mt-3 border-t border-stone-200 pt-3">
          <InterpretationBreakdown
            representativeName={representativeName}
            row={row}
            selectedActionRow={selectedActionRow}
            setSelectedActionRow={setSelectedActionRow}
          />
          <p className="mt-3 text-xs leading-5 text-stone-500">
            Full official title: {row.description || row.question || "Unavailable"}
          </p>
          <div className="mt-3 flex justify-start border-t border-stone-200 pt-3 sm:justify-end">
            {row.source_url ? (
              <a
                className="w-fit rounded-full border border-cyan-800/20 bg-white px-3 py-2 text-xs uppercase tracking-[0.16em] text-cyan-800 underline-offset-4 transition hover:border-cyan-800 hover:bg-cyan-50 hover:underline"
                href={row.source_url}
                rel="noreferrer"
                target="_blank"
              >
                Source
              </a>
            ) : (
              <p className="text-xs uppercase tracking-[0.16em] text-stone-500">No source URL</p>
            )}
          </div>
        </div>
      </details>
    </article>
  );
}

function EvidenceGroupingPreview({ evidenceGrouping }) {
  const groups = evidenceGrouping?.groups || [];
  const previewGroups = groups
    .slice()
    .sort((left, right) => scoreEvidenceGroup(right) - scoreEvidenceGroup(left) || String(left.label || "").localeCompare(String(right.label || "")))
    .slice(0, 6);

  if (!groups.length) {
    return null;
  }

  return (
    <div className="rounded-xl border border-stone-200 bg-white px-3 py-3">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-cyan-900">
            Evidence group overview
          </p>
          <p className="mt-1 text-sm leading-5 text-stone-700">
            {formatCompactEvidenceGroupingOverview(evidenceGrouping.summary)}
          </p>
        </div>
        <span className="w-fit rounded-full bg-stone-100 px-3 py-1 text-xs uppercase tracking-[0.16em] text-stone-700">
          {groups.length} {groups.length === 1 ? "group" : "groups"}
        </span>
      </div>
      {previewGroups.length ? (
        <div className="mt-3 grid gap-2 lg:grid-cols-2">
          {previewGroups.map((group) => (
            <div className="rounded-xl border border-stone-200 bg-stone-50 px-3 py-2.5" key={group.id}>
              <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                <p className="text-sm leading-5 text-stone-900">{formatDisplayMeasureTitle(group.label)}</p>
                <span className="w-fit rounded-full bg-white px-2.5 py-1 text-[11px] uppercase tracking-[0.14em] text-stone-600">
                  {formatEvidenceGroupCategory(group)}
                </span>
              </div>
              <div className="mt-2 flex flex-wrap gap-1.5 text-[11px] uppercase tracking-[0.1em] text-stone-600">
                <span className="rounded-full bg-white px-2 py-1">{group.countedYesNoCount} countable</span>
                {group.proceduralContextCount ? <span className="rounded-full bg-sky-50 px-2 py-1">{group.proceduralContextCount} procedural</span> : null}
                {group.ambiguousOrInsufficientCount ? <span className="rounded-full bg-amber-50 px-2 py-1">{group.ambiguousOrInsufficientCount} limited</span> : null}
                {group.notVotingCount ? <span className="rounded-full bg-stone-100 px-2 py-1">{group.notVotingCount} not voting</span> : null}
              </div>
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

function EvidenceUtilityPanel({ domain, evidenceRows, legislator, selectedEvidenceRow }) {
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
    <details className="rounded-xl border border-stone-200 bg-white px-3 py-3">
      <summary className="cursor-pointer text-sm font-medium text-stone-900 marker:text-cyan-900">
        Evidence tools: contact and selected-vote context
      </summary>
      <div className="mt-3 rounded-xl border border-stone-200 bg-stone-50 px-3 py-3">
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
    </details>
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

function IssueEvidenceSummary({ rows }) {
  const presentation = buildBasicEvidencePresentation(rows);
  const details = [
    presentation.substantiveVotes ? `${presentation.substantiveVotes} substantive Yes/No ${presentation.substantiveVotes === 1 ? "vote" : "votes"}` : null,
    presentation.notVoting ? `${presentation.notVoting} Not Voting` : null,
    presentation.proceduralRecords ? `${presentation.proceduralRecords} procedural ${presentation.proceduralRecords === 1 ? "record" : "records"}` : null,
    presentation.limitedRecords ? `${presentation.limitedRecords} limited-context ${presentation.limitedRecords === 1 ? "record" : "records"}` : null,
  ].filter(Boolean);

  return (
    <div className="rounded-xl border border-cyan-900/10 bg-white px-3 py-3 sm:px-4" data-coverage-state={presentation.state} data-public-surface="basic-evidence" data-testid="basic-evidence-summary">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-cyan-900">
            {presentation.label}
          </p>
          <p className="mt-1 max-w-4xl text-[16px] leading-7 text-stone-950">
            {presentation.message}
          </p>
        </div>
        {details.length ? (
          <span className="w-fit rounded-full bg-cyan-50 px-3 py-1 text-[11px] uppercase tracking-[0.12em] text-cyan-950">
            {rows.length} available {rows.length === 1 ? "record" : "records"}
          </span>
        ) : null}
      </div>
      {details.length ? (
        <div aria-label="Available record details" className="mt-3 flex flex-wrap gap-2">
          {details.map((detail) => <span className="rounded-full border border-stone-200 bg-stone-50 px-3 py-1.5 text-xs text-stone-700" key={detail}>{detail}</span>)}
        </div>
      ) : null}
      <p className="mt-3 border-t border-stone-200 pt-3 text-sm leading-6 text-stone-600">
        Open the votes below for practical explanations and official receipts. A fully researched issue interpretation is a separate layer and is not inferred from these counts alone.
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
        </div>
      </details>
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
  return buildGenericVoteCardSummary(row, options);
}

function buildLimitedContextSummary(row) {
  return buildGenericLimitedContextSummary(row);
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

  return Array.from(groups.values())
    .map((group) => {
      const sortedRows = [...group.rows].sort(compareEvidenceRows);
      return {
        ...group,
        rows: sortedRows,
        category: categorizeBillEvidenceGroup(sortedRows),
        countedRows: sortedRows.filter(isCountedSubstantiveEvidenceRow).length,
        proceduralContextRows: sortedRows.filter(isProceduralContextRow).length,
        limitedRows: sortedRows.filter(isLimitedEvidenceRow).length,
        notVotingRows: sortedRows.filter((row) => row.position === "not_voting").length,
        evidenceScore: Math.max(...sortedRows.map(scoreEvidenceRow), 0),
      };
    })
    .sort((left, right) => (
      right.evidenceScore - left.evidenceScore ||
      right.countedRows - left.countedRows ||
      right.rows.length - left.rows.length ||
      String(left.title || "").localeCompare(String(right.title || ""))
    ));
}

function compareEvidenceRows(left, right) {
  return (
    scoreEvidenceRow(right) - scoreEvidenceRow(left) ||
    Number(left.rollcall_number || 0) - Number(right.rollcall_number || 0) ||
    String(left.position || "").localeCompare(String(right.position || ""))
  );
}

function buildProofView(rows) {
  const sortedRows = [...(rows || [])].sort(compareEvidenceRows);
  const countableRows = sortedRows.filter(isCountedSubstantiveEvidenceRow);
  const contextRows = sortedRows.filter((row) => !isCountedSubstantiveEvidenceRow(row));
  const representativeRows = (countableRows.length ? countableRows : sortedRows).slice(0, REPRESENTATIVE_VOTE_LIMIT);

  return {
    countableRows,
    contextRows,
    representativeRows,
    limitedRows: sortedRows.filter(isLimitedEvidenceRow),
    notVotingRows: sortedRows.filter((row) => row.position === "not_voting"),
    proceduralContextRows: sortedRows.filter(isProceduralContextRow),
  };
}

function formatContextRowSummary(proofView) {
  const parts = [];
  if (proofView.limitedRows.length) {
    parts.push(`${proofView.limitedRows.length} limited or context ${proofView.limitedRows.length === 1 ? "vote" : "votes"}`);
  }
  if (proofView.proceduralContextRows.length) {
    parts.push(`${proofView.proceduralContextRows.length} procedural context ${proofView.proceduralContextRows.length === 1 ? "vote" : "votes"}`);
  }
  if (proofView.notVotingRows.length) {
    parts.push(`${proofView.notVotingRows.length} not voting / present ${proofView.notVotingRows.length === 1 ? "vote" : "votes"}`);
  }

  if (!parts.length) {
    return "No limited, procedural, or not-voting context rows are included in this issue.";
  }

  return `${capitalizeSentence(parts.join(", "))} are not treated as countable Yes/No findings.`;
}

function capitalizeSentence(value) {
  const text = String(value || "");
  return text ? `${text[0].toUpperCase()}${text.slice(1)}` : "";
}

function scoreEvidenceRow(row) {
  if (row?.interpretation_status === "interpreted" && row?.position !== "not_voting" && !isProceduralContextRow(row)) {
    return 5;
  }
  if (row?.interpretation_status === "interpreted" && row?.position === "not_voting") {
    return 3;
  }
  if (isProceduralContextRow(row)) {
    return 2;
  }
  if (isLimitedEvidenceRow(row)) {
    return 1;
  }
  return 0;
}

function isCountedSubstantiveEvidenceRow(row) {
  return row?.interpretation_status === "interpreted" &&
    row?.position !== "not_voting" &&
    row?.support_position &&
    row?.oppose_position &&
    !isProceduralContextRow(row);
}

function isLimitedEvidenceRow(row) {
  return row?.interpretation_status === "ambiguous" || row?.interpretation_status === "insufficient_evidence";
}

function categorizeBillEvidenceGroup(rows) {
  if (!rows.length) {
    return "primary_bill_or_measure";
  }
  if (rows.every(isProceduralContextRow)) {
    return "procedural_context_rows";
  }
  if (rows.every((row) => row.position === "not_voting")) {
    return "not_voting_rows";
  }
  if (rows.every(isLimitedEvidenceRow)) {
    return "limited_context_rows";
  }
  if (rows.some((row) => row.vote_context?.vote_type === "amendment" || row.vote_type === "amendment")) {
    return "related_amendments";
  }
  if (rows.some(isProceduralContextRow)) {
    return "related_floor_or_procedural_votes";
  }
  return "primary_bill_or_measure";
}

function getBillGroupContainerClass(group) {
  if (group.category === "procedural_context_rows") {
    return "border-sky-100 bg-sky-50/60";
  }
  if (group.category === "limited_context_rows" || group.category === "not_voting_rows") {
    return "border-stone-200 bg-stone-50";
  }
  return "border-stone-200 bg-white";
}

function formatBillGroupScanLine(group) {
  const parts = [
    `${group.rows.length} ${group.rows.length === 1 ? "roll call" : "roll calls"}`,
  ];
  if (group.countedRows) {
    parts.push(`${group.countedRows} countable interpreted`);
  }
  if (group.proceduralContextRows) {
    parts.push(`${group.proceduralContextRows} procedural context`);
  }
  if (group.limitedRows) {
    parts.push(`${group.limitedRows} limited`);
  }
  if (group.notVotingRows) {
    parts.push(`${group.notVotingRows} not voting`);
  }
  return `${parts.join(" - ")}.`;
}

function rowActionKey(row) {
  if (!row) {
    return "";
  }

  return `${row.roll_call_id}-${row.position}`;
}

function formatBillGroupSummary(rollCallCount, billCount) {
  if (typeof rollCallCount === "object" && rollCallCount !== null) {
    return formatCompactEvidenceGroupingOverview(rollCallCount);
  }

  return `${rollCallCount} ${rollCallCount === 1 ? "roll-call vote" : "roll-call votes"} shown across ${billCount} ${
    billCount === 1 ? "bill or measure" : "bills or measures"
  }. Repeated rows can be amendments or related actions on the same bill.`;
}

function formatCompactEvidenceGroupingOverview(summary) {
  const totalRows = summary?.totalRows || 0;
  const totalGroups = summary?.totalGroups || 0;
  const countedCount = summary?.countedYesNoRows || 0;
  const limitedCount = summary?.ambiguousOrInsufficientRows || 0;
  const proceduralContextCount = summary?.proceduralContextRows || 0;
  const notVotingCount = summary?.notVotingRows || 0;
  const parts = [
    `${countedCount} countable Yes/No`,
    `${totalRows} ${totalRows === 1 ? "row" : "rows"}`,
    `${totalGroups} ${totalGroups === 1 ? "group" : "groups"}`,
  ];

  if (limitedCount) {
    parts.push(`${limitedCount} limited`);
  }
  if (proceduralContextCount) {
    parts.push(`${proceduralContextCount} procedural context`);
  }
  if (notVotingCount) {
    parts.push(`${notVotingCount} not voting`);
  }

  return `${parts.join(" · ")}. Context rows remain visible but do not drive support/opposition summaries.`;
}

function scoreEvidenceGroup(group) {
  return (
    (group.countedYesNoCount || 0) * 8 +
    (group.amendmentCount || 0) * 3 +
    (group.proceduralContextCount || 0) * 2 +
    (group.ambiguousOrInsufficientCount || 0) +
    (group.notVotingCount || 0) +
    (group.rowCount || 0)
  );
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
        ? buildIssueCardPreview(strong).themeLine || "This is the clearest reviewed issue read available for this representative."
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

const DIRECTIONAL_DOMINANCE_SHARE = 2 / 3;

function formatIssueCardPriority(row) {
  return buildIssueCardPreview(row).receiptLine;
}

function getInterpretedCount(row) {
  return Number(row?.interpreted_support_count || 0) + Number(row?.interpreted_oppose_count || 0);
}

function formatIssueCardEvidenceLine(row) {
  return buildIssueCardPreview(row).countLine;
}

function formatIssueCardReason(row) {
  return buildIssueCardPreview(row).themeLine;
}

function formatIssueCardStatusLabel(row) {
  return buildIssueCardPreview(row).status;
}

function getDominantIssueDirection(row) {
  const supportCount = Number(row?.interpreted_support_count || 0);
  const opposeCount = Number(row?.interpreted_oppose_count || 0);
  const total = supportCount + opposeCount;
  if (!total) {
    return "";
  }
  if (supportCount / total >= DIRECTIONAL_DOMINANCE_SHARE) {
    return "supported";
  }
  if (opposeCount / total >= DIRECTIONAL_DOMINANCE_SHARE) {
    return "opposed";
  }
  return "";
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

function formatScopeLine(metadata) {
  if (!metadata) {
    return "Selected record scope";
  }
  const label = metadata.scope_label || "Selected record";
  const congresses = (metadata.congresses || metadata.requested_congresses || [])
    .map((congress) => `${congress}th`)
    .join(" + ");
  const windowText = metadata.window_start && metadata.window_end
    ? `votes from ${String(metadata.window_start).slice(0, 4)}-${String(metadata.window_end).slice(0, 4)}`
    : "selected vote window";
  return [label, congresses, windowText].filter(Boolean).join(" - ");
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

      const dominantDirection = getDominantIssueDirection(row);
      if (dominantDirection === "supported") {
        label = "Mostly for interpreted measures";
      } else if (dominantDirection === "opposed") {
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

function formatContactSource(contact) {
  const sourceType = String(contact?.source_type || "official source").replaceAll("_", " ");
  const retrievedAt = contact?.source_retrieved_at ? `retrieved ${String(contact.source_retrieved_at).slice(0, 10)}` : "retrieval date not loaded";
  return `${sourceType}, ${retrievedAt}`;
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
  if (row.interpretation_status === "ambiguous") {
    badges.push("Limited source context");
  }
  if (row.interpretation_status === "insufficient_evidence") {
    badges.push("Limited source context");
  }
  if (isProceduralContextRow(row)) {
    badges.push("Procedural context only");
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
