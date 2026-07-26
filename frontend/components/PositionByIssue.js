"use client";

import { useEffect, useState } from "react";

import { fetchEditorialPresentations, fetchLegislatorContact, fetchPositionEvidence, fetchPositions } from "../lib/api";
import {
  buildBasicEvidencePresentation,
  hasAvailableIssueEvidence,
} from "../lib/basicEvidencePresentation.mjs";
import { deriveEvidenceGroups } from "../lib/evidenceGrouping.mjs";
import {
  getCanonicalActionId,
  getEditorialPresentation,
  receiptAnchorId,
} from "../lib/editorialPresentation.mjs";
import { formatDisplayMeasureTitle } from "../lib/measureDisplay.mjs";
import { fillMissingInterpretedCounts } from "../lib/positionEvidenceCounts.mjs";
import { isProceduralContextRow } from "../lib/proceduralContext.mjs";
import { DOMAIN_LABELS, formatDomainLabel } from "../lib/issueDomains";
import {
  getEvidenceCoverageLabel,
  orderIssueRowsByEvidenceUsefulness,
} from "../lib/issueEvidenceCoverage.mjs";
import {
  buildLimitedContextSummary as buildGenericLimitedContextSummary,
  buildVoteCardSummary as buildGenericVoteCardSummary,
} from "../lib/voteCardSummary.mjs";

const REPRESENTATIVE_VOTE_LIMIT = 8;

export default function PositionByIssue({
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
    presentations: null,
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
            presentations: fixtureData.presentations || { presentations: [] },
            error: null,
          });
          return;
        }

        const [positionsPayload, presentations] = await Promise.all([
          fetchPositions({ legislatorId, scope }),
          fetchEditorialPresentations({ legislatorId, scope }).catch(() => ({ presentations: [] })),
        ]);
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
          presentations,
          error: null,
        });
      } catch (error) {
        if (!active) {
          return;
        }
        setState({
          status: "error",
          payload: null,
          presentations: null,
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

  const rows = orderIssueRowsByEvidenceUsefulness(
    (state.payload?.positions || []).filter(hasAvailableIssueEvidence),
  );
  const selectedRow = rows.find((row) => row.domain === selectedDomain) || rows[0] || null;
  const selectedPresentation = getEditorialPresentation(
    state.presentations,
    selectedRow?.domain,
  );

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
      <div className="grid min-w-0 items-start gap-4 xl:grid-cols-[minmax(360px,0.72fr)_minmax(0,1.28fr)]">
        <div className="min-w-0">
          <p className="text-xs uppercase tracking-[0.2em] text-cyan-800">
            Issue Evidence
          </p>
          <h3 className="mt-1 font-serif text-[1.55rem] leading-[1.05] text-stone-950 sm:text-[2rem]">
            {title}
          </h3>
          <p className="mt-2 max-w-xl text-[15px] leading-6 text-stone-800">
            {state.status === "ready"
              ? "Select an issue to inspect publication-gated presentation when available and the underlying vote receipts."
              : state.status === "loading"
                ? "Loading this legislator's issue evidence."
                : "The site cannot read issue evidence for this legislator right now."}
          </p>
          {state.status === "ready" ? (
            <p className="mt-2 text-xs uppercase tracking-[0.14em] text-stone-500">
              {formatScopeLine(state.payload?.scope_metadata)}
            </p>
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
              No vote evidence is available in the current window. This is a coverage note, not an alignment finding.
            </div>
          ) : null}
          {state.status === "ready" ? (
            <IssueNavigation
              inspectDomain={inspectDomain}
              rows={rows}
              selectedDomain={selectedDomain}
            />
          ) : null}
        </div>
      </div>

      <EvidencePanel
        evidenceState={evidenceState}
        legislator={legislator}
        onInspectDomain={inspectDomain}
        presentation={selectedPresentation}
        selectedRow={selectedRow}
      />

    </section>
  );
}

function IssueNavigation({ inspectDomain, rows, selectedDomain }) {
  const navRows = (rows || []).filter(hasAvailableIssueEvidence);

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
            <span className="ml-2 opacity-75">{getEvidenceCoverageLabel(row)}</span>
          </button>
          );
        })}
      </div>
    </nav>
  );
}

function EvidencePanel({ evidenceState, legislator, onInspectDomain, presentation, selectedRow }) {
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
  const evidenceGrouping = deriveEvidenceGroups(evidenceRows);
  const billGroups = groupEvidenceByBill(evidenceRows);
  const proofView = buildProofView(evidenceRows);

  function showSupportingVotes(actionIds) {
    const actionIdSet = new Set(actionIds || []);
    const targetRow = evidenceRows.find((row) => actionIdSet.has(getCanonicalActionId(row)));
    if (!targetRow) {
      return;
    }
    const targetActionId = getCanonicalActionId(targetRow);
    setShowAllVotes(true);
    setSelectedActionRow(targetRow);
    window.requestAnimationFrame(() => {
      window.requestAnimationFrame(() => {
        document.getElementById(receiptAnchorId(targetActionId))?.scrollIntoView({
          behavior: "smooth",
          block: "center",
        });
      });
    });
  }

  return (
    <div id="position-evidence" className="mt-4 scroll-mt-6 rounded-2xl border border-stone-200 bg-stone-50 px-3 py-3 sm:px-4 lg:px-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
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
      </div>

      {evidenceState.status === "idle" ? (
        <p className="mt-4 text-sm leading-7 text-stone-700">
          Start with one of the best-covered issues above, or choose any issue to inspect its receipts.
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
          {presentation ? (
            <EditorialPresentationPanel
              onShowSupportingVotes={showSupportingVotes}
              presentation={presentation}
            />
          ) : null}
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
          {evidenceRows.length > 0 ? (
            <ReviewedVoteList
              billGroups={billGroups}
              evidenceRows={evidenceRows}
              representativeName={legislator?.name_display}
              selectedActionRow={selectedActionRow}
              setSelectedActionRow={setSelectedActionRow}
              showAllVotes={showAllVotes}
              setShowAllVotes={setShowAllVotes}
            />
          ) : null}
          <EvidenceGroupingPreview evidenceGrouping={evidenceGrouping} />
          <EvidenceUtilityPanel
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

function EditorialPresentationPanel({ onShowSupportingVotes, presentation }) {
  const isReceiptsOnly = presentation.tier === "receipts_only";
  const hasAnalysis = !isReceiptsOnly && presentation.conclusion;

  return (
    <section
      className="rounded-xl border border-cyan-900/15 bg-white px-3 py-3 sm:px-4"
      data-presentation-tier={presentation.tier}
      data-testid="editorial-presentation"
    >
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-cyan-900">
            {presentation.tier_badge}
          </p>
          <p className="mt-1 max-w-4xl text-[16px] leading-7 text-stone-950">
            {presentation.teaser}
          </p>
        </div>
        {presentation.reviewed_scope ? (
          <span className="w-fit rounded-full bg-cyan-50 px-3 py-1 text-[11px] uppercase tracking-[0.12em] text-cyan-950">
            Reviewed {presentation.reviewed_scope}th Congress
          </span>
        ) : null}
      </div>

      {presentation.coverage_text ? (
        <p className="mt-3 rounded-lg border border-stone-200 bg-stone-50 px-3 py-2 text-sm leading-6 text-stone-700">
          {presentation.coverage_text}
        </p>
      ) : null}

      {hasAnalysis ? (
        <div className="mt-3 grid gap-3">
          <div className="rounded-xl bg-cyan-950 px-4 py-4 text-white">
            <p className="text-[11px] uppercase tracking-[0.18em] text-cyan-100">
              {presentation.conclusion.headline}
            </p>
            <p className="mt-2 text-[16px] leading-7 text-white">
              {presentation.conclusion.body}
            </p>
          </div>

          {presentation.repeated_patterns?.length ? (
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-cyan-900">
                Repeated patterns
              </p>
              <div className="mt-2 grid gap-2 lg:grid-cols-2">
                {presentation.repeated_patterns.map((pattern) => (
                  <PresentationFinding
                    item={pattern}
                    key={pattern.proposition_id}
                    onShowSupportingVotes={onShowSupportingVotes}
                  />
                ))}
              </div>
            </div>
          ) : null}

          {presentation.policy_trajectories?.length ? (
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-amber-900">
                Limiting trajectory
              </p>
              <div className="mt-2 grid gap-2">
                {presentation.policy_trajectories.map((trajectory) => (
                  <PresentationFinding
                    item={trajectory}
                    key={trajectory.proposition_id}
                    onShowSupportingVotes={onShowSupportingVotes}
                    tone="limiting"
                  />
                ))}
              </div>
            </div>
          ) : null}

          {presentation.limitations?.length ? (
            <div className="grid gap-2 border-t border-stone-200 pt-3 md:grid-cols-2">
              {presentation.limitations.map((limitation) => (
                <div
                  className="rounded-lg border border-stone-200 bg-stone-50 px-3 py-3"
                  key={`${limitation.proposition_id || "limit"}-${limitation.heading}`}
                >
                  <p className="text-[11px] uppercase tracking-[0.15em] text-stone-500">
                    {limitation.heading}
                  </p>
                  <p className="mt-1 text-sm leading-6 text-stone-700">
                    {limitation.body}
                  </p>
                  {limitation.action_ids?.length ? (
                    <SupportingVotesButton
                      actionIds={limitation.action_ids}
                      onClick={onShowSupportingVotes}
                    />
                  ) : null}
                </div>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}

      {presentation.scope_boundary ? (
        <p className="mt-3 border-t border-stone-200 pt-3 text-sm leading-6 text-stone-600">
          {presentation.scope_boundary}
        </p>
      ) : null}
    </section>
  );
}

function PresentationFinding({ item, onShowSupportingVotes, tone = "standard" }) {
  return (
    <article className={`rounded-xl border px-3 py-3 ${tone === "limiting" ? "border-amber-200 bg-amber-50" : "border-cyan-900/10 bg-cyan-50/50"}`}>
      <h5 className="text-base leading-6 text-stone-950">{item.heading}</h5>
      <p className="mt-1 text-sm leading-6 text-stone-700">{item.body}</p>
      <SupportingVotesButton
        actionIds={item.action_ids}
        onClick={onShowSupportingVotes}
      />
    </article>
  );
}

function SupportingVotesButton({ actionIds, onClick }) {
  return (
    <button
      className="mt-3 rounded-full border border-cyan-900/20 bg-white px-3 py-2 text-xs uppercase tracking-[0.14em] text-cyan-950 transition hover:bg-cyan-100 focus:outline-none focus:ring-2 focus:ring-cyan-800 focus:ring-offset-2"
      onClick={() => onClick(actionIds)}
      type="button"
    >
      See supporting votes
    </button>
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
          This issue does not have reviewed substantive Yes/No ready for a first proof set. Open the full vote receipt list to inspect the available context.
        </p>
      </section>
    );
  }

  return (
    <section className="rounded-xl border border-cyan-900/10 bg-white px-3 py-3 sm:px-4">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-cyan-900">
            Reviewed substantive Yes/No
          </p>
          <p className="mt-1 text-sm leading-6 text-stone-700">
            A first set of vote receipts behind this issue. Start here, then expand the full receipt list.
          </p>
        </div>
        <span className="w-fit rounded-full bg-cyan-50 px-3 py-1 text-xs uppercase tracking-[0.14em] text-cyan-950">
          {rows.length} of {proofView.countableRows.length} reviewed substantive Yes/No
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
          {formatContextRowSummary(proofView)} Full context rows remain available in the vote receipt list.
        </p>
      ) : null}
    </section>
  );
}

function ReviewedVoteList({
  billGroups,
  evidenceRows,
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
            Full vote receipt list
          </p>
          <p className="mt-1 text-sm leading-6 text-stone-700">
            All receipts stay available, grouped by bill or measure, with countable and context labels preserved.
          </p>
        </div>
        <button
          aria-expanded={showAllVotes}
          className="w-fit rounded-full border border-cyan-900/20 bg-cyan-50 px-3 py-2 text-xs uppercase tracking-[0.14em] text-cyan-950 transition hover:bg-cyan-100 focus:outline-none focus:ring-2 focus:ring-cyan-800 focus:ring-offset-2"
          onClick={() => setShowAllVotes((current) => !current)}
          type="button"
        >
          {showAllVotes ? "Hide full list" : "Show all vote receipts"}
        </button>
      </div>
      <div className="mt-3 flex flex-wrap gap-2 text-[11px] uppercase tracking-[0.12em] text-stone-600">
        <span className="rounded-full bg-stone-100 px-2.5 py-1">
          {evidenceRows.length} recorded {evidenceRows.length === 1 ? "action" : "actions"}
        </span>
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
          Showing reviewed substantive Yes/No first. Use Show all vote receipts for every grouped receipt in this issue.
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
          {group.rows.length} recorded {group.rows.length === 1 ? "action" : "actions"}
        </span>
      </div>

      <div className="mt-3 grid gap-2">
        {group.rows.map((row) => (
          <VoteEvidenceRow
            anchorReceipt
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

function VoteEvidenceRow({ anchorReceipt = false, representativeName, row, selectedActionRow, setSelectedActionRow }) {
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
  const canonicalActionId = getCanonicalActionId(row);
  const isSelected = canonicalActionId && canonicalActionId === getCanonicalActionId(selectedActionRow);
  const rowToneClass = isProcedural
    ? "border-sky-100 bg-sky-50/70"
    : row.interpretation_status === "interpreted" && row.position !== "not_voting"
      ? "border-cyan-900/15 bg-white"
      : "border-stone-200 bg-stone-50";

  return (
    <article
      className={`scroll-mt-24 rounded-xl border px-3 py-2.5 ${rowToneClass} ${isSelected ? "ring-2 ring-cyan-700 ring-offset-2" : ""}`}
      data-canonical-action-id={canonicalActionId || undefined}
      id={anchorReceipt && canonicalActionId ? receiptAnchorId(canonicalActionId) : undefined}
    >
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
    presentation.present ? `${presentation.present} Present` : null,
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
  const whyItMattered = buildUsefulInterpretationText(row.why_it_mattered) || policyEffectText;
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
