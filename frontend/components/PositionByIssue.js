"use client";

import { useEffect, useState } from "react";

import { fetchLegislatorContact, fetchPositionEvidence, fetchPositions } from "../lib/api";
import { buildIssueOverview } from "../lib/issueOverview.mjs";
import { DOMAIN_LABELS, formatDomainLabel } from "../lib/issueDomains";

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

  const rows = (state.payload?.positions || [])
    .filter((row) => row.recorded_votes > 0)
    .sort((left, right) => right.recorded_votes - left.recorded_votes || right.yea_share - left.yea_share)
    .slice(0, 6);
  const patternRows = buildPatternRows(state.payload?.positions || []);
  const takeaway = buildTakeaway(rows);
  const selectedRow = rows.find((row) => row.domain === selectedDomain) || rows[0] || null;

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
                ? "Reading how this legislator voted inside their most active issue domains."
                : "The site cannot read how this legislator voted inside issue domains right now."}
          </p>
          <div className="mt-4 rounded-[1.5rem] bg-stone-950 px-4 py-4 text-stone-100">
            <p className="text-xs uppercase tracking-[0.28em] text-stone-400">
              How To Read This
            </p>
            <p className="mt-2 text-[15px] leading-7 text-stone-200">
              Each tile starts with the domains where this legislator has the most recorded votes, then shows the yea/nay split and how many votes have cached plain-English meaning. It is descriptive, not a score.
            </p>
          </div>
        </div>

        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {state.status === "error" ? (
            <div className="rounded-[1.5rem] border border-rose-200 bg-rose-50 px-4 py-4 text-sm text-rose-700 md:col-span-2 xl:col-span-3">
              {state.error}
            </div>
          ) : null}
          {state.status === "ready" && rows.length === 0 ? (
            <div className="rounded-[1.5rem] border border-stone-200 bg-stone-50 px-4 py-4 text-sm text-stone-600 md:col-span-2 xl:col-span-3">
              No recorded yea/nay policy-vote splits are available in the current window. This is a coverage note, not an alignment finding.
            </div>
          ) : null}
          {rows.map((row) => (
            <button
              aria-label={`Inspect ${formatDomainLabel(row.domain)} votes`}
              aria-pressed={selectedDomain === row.domain}
              className={`rounded-[1.1rem] border px-4 py-3 text-left shadow-[inset_0_1px_0_rgba(255,255,255,0.72)] transition ${
                selectedDomain === row.domain
                  ? "border-cyan-800 bg-cyan-50"
                  : "border-stone-200 bg-stone-50 hover:border-cyan-700/50"
              }`}
              key={row.domain}
              onClick={() => inspectDomain(row.domain)}
              type="button"
            >
              <div className="flex items-start justify-between gap-3">
                <p className="max-w-[220px] text-[15px] leading-6 text-stone-950">
                  {formatDomainLabel(row.domain)}
                </p>
                <p className="shrink-0 text-sm text-stone-500">{row.recorded_votes} votes</p>
              </div>
              <div className="mt-3 flex flex-col gap-2">
                <span className={`w-fit max-w-full rounded-xl px-3 py-1 text-[11px] uppercase leading-4 tracking-[0.12em] ${getPositionBadgeClass(row)}`}>
                  {getPositionLabel(row)}
                </span>
                <p className="text-[13px] leading-5 text-stone-700">
                  {buildPositionRead(row)}. {buildInterpretationCoverageRead(row)}
                </p>
              </div>
              <div className="mt-3 h-2 overflow-hidden rounded-full bg-stone-200">
                <div className="flex h-full w-full">
                  <div
                    className="bg-emerald-500"
                    style={{ width: `${row.yea_share * 100}%` }}
                  />
                  <div
                    className="bg-rose-500"
                    style={{ width: `${row.nay_share * 100}%` }}
                  />
                </div>
              </div>
            </button>
          ))}
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
            What interpreted votes show
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
          Select an issue card or use Show Votes to inspect the roll calls behind this read. Evidence appears here before any alignment label is treated as meaningful.
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
            {formatBillGroupSummary(evidenceRows.length, billGroups.length)}
          </div>
          <IssueEvidenceSummary
            domain={selectedRow.domain}
            representativeName={legislator?.name_display}
            rows={evidenceRows}
          />
          <CivicActionPanel
            domain={selectedRow.domain}
            evidenceRows={evidenceRows}
            legislator={legislator}
            selectedEvidenceRow={selectedActionRow}
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
                      <span className={`w-fit rounded-full px-3 py-1 text-xs uppercase tracking-[0.2em] ${getVoteBadgeClass(row.position)}`}>
                        {formatVotePosition(row.position)}
                      </span>
                    </div>
                    <InterpretationBreakdown
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
        </div>
      ) : null}
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

function InterpretationBreakdown({ row, selectedActionRow, setSelectedActionRow }) {
  if (!hasInterpretationDetail(row)) {
    return null;
  }

  const isInterpreted = row.interpretation_status === "interpreted";
  const statusLabel = formatInterpretationStatus(row.interpretation_status);
  const summaryText = buildUsefulInterpretationText(row.plain_english_summary);
  const policyEffectText = buildUsefulInterpretationText(row.policy_effect);
  const interpretedVoteRead = buildInterpretedVoteRead(row);
  const whatHappened = row.what_happened || summaryText || policyEffectText;
  const whyItMattered = row.why_it_mattered || buildPlainTakeaway(row);
  const voteCardSummary = buildVoteCardSummary(row) || interpretedVoteRead;
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
            <span className={`w-fit rounded-full px-3 py-1 text-[11px] uppercase tracking-[0.18em] ${getInterpretationBadgeClass(row.interpretation_status)}`}>
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

function buildVoteCardSummary(row) {
  const exactSummary = buildKnownVoteCardSummary(row);
  if (exactSummary) {
    return exactSummary;
  }

  if (!row || row.interpretation_status !== "interpreted") {
    return "";
  }

  const position = formatVotePosition(row.position);
  const action = cleanSummarySentence(row.what_happened || buildUsefulInterpretationText(row.plain_english_summary));
  const stakes = cleanSummarySentence(row.why_it_mattered || buildPlainTakeaway(row));
  const voteMeaning = buildPlainVoteMeaning(row);
  const context = buildPlainPartyOutcomeContext(row);

  return [position, action, stakes, voteMeaning, context]
    .filter(Boolean)
    .map((piece, index) => (index === 0 ? `${piece}.` : ensurePeriod(piece)))
    .join(" ");
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

  if (rollNumber === 180) {
    return `${position}. Limited-context row. This was an en bloc appropriations amendment, but the available source text does not explain the full practical change. It remains visible below but is not counted in the summarized vote pattern.`;
  }
  if (rollNumber === 263) {
    return `${position}. Limited-context row. This was a motion to instruct conferees, not final passage of the underlying appropriations bill. It remains visible below but is not counted in the summarized vote pattern.`;
  }

  return "";
}

function buildPlainVoteMeaning(row) {
  const memberLabel = extractMemberLabel(row);
  const facet = String(row.issue_facet || "");

  if (row.position === "not_voting") {
    return `${memberLabel} was recorded as not voting, so this row does not count as support or opposition.`;
  }

  const votedAgainst = row.position === row.oppose_position;
  const votedFor = row.position === row.support_position;
  const direction = votedAgainst ? "against" : votedFor ? "for" : "on";

  if (facet === "budget_reconciliation_and_debt_limit") {
    return `${memberLabel} voted ${direction} that budget framework`;
  }
  if (facet === "small_business_loan_eligibility") {
    return `${memberLabel} voted ${direction} adding those eligibility restrictions`;
  }
  if (facet === "military_construction_and_va_appropriations") {
    return `${memberLabel} voted ${direction} that military construction and Veterans Affairs funding bill`;
  }
  if (facet === "temporary_government_funding") {
    return `${memberLabel} voted ${direction} that temporary funding bill`;
  }
  if (facet === "government_funding_and_shutdown") {
    return `${memberLabel} voted ${direction} that shutdown-ending funding package`;
  }
  if (facet === "small_business_regulation") {
    return `${memberLabel} voted ${direction} that SBA regulatory-cost cap bill`;
  }

  return `${memberLabel} voted ${direction} the interpreted measure`;
}

function buildPlainPartyOutcomeContext(row) {
  const context = row.vote_context;
  const pieces = [];

  if (context?.member_voted_with_party_majority === true) {
    const partyName = context.member_party ? formatPartyName(context.member_party) : "party";
    pieces.push(`matching most House ${partyName}s`);
  } else if (context?.member_voted_with_party_majority === false) {
    const partyName = context.member_party ? formatPartyName(context.member_party) : "party";
    pieces.push(`not matching most House ${partyName}s`);
  }

  const outcome = buildPlainOutcomeSentence(row);
  if (pieces.length && outcome) {
    return `${pieces.join(", ")}. ${outcome}`;
  }
  if (pieces.length) {
    return pieces.join(", ");
  }
  return outcome;
}

function buildPlainOutcomeSentence(row) {
  const context = row.vote_context;
  if (!context?.final_result) {
    return "";
  }

  if (context.final_result === "failed") {
    return "The measure failed.";
  }
  if (context.final_result !== "passed") {
    return "";
  }
  if (Number(context.vote_margin) > 0 && Number(context.vote_margin) <= 5) {
    return "The measure passed narrowly.";
  }
  if (context.vote_type === "final_passage") {
    return "The bill passed the House.";
  }
  return "The measure passed.";
}

function extractMemberLabel(row) {
  const memberContext = String(row?.member_vote_context || "");
  const match = memberContext.match(/^([A-Z][A-Za-z.'-]+)/);
  return match?.[1] || "This representative";
}

function cleanSummarySentence(value) {
  return String(value || "")
    .replace(/\.$/, "")
    .trim();
}

function ensurePeriod(value) {
  const text = String(value || "").trim();
  if (!text) {
    return "";
  }
  return /[.!?]$/.test(text) ? text : `${text}.`;
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
  return `${rollCallCount} ${rollCallCount === 1 ? "roll-call vote" : "roll-call votes"} shown across ${billCount} ${
    billCount === 1 ? "bill or measure" : "bills or measures"
  }. Repeated rows can be amendments or related actions on the same bill.`;
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

function buildTakeaway(rows) {
  if (!rows.length) {
    return "There are not enough recorded yea and nay votes in the current window to show a clear position pattern by issue.";
  }

  const strongest = rows[0];
  const strongestLabel = getPositionLabel(strongest).toLowerCase();
  const strongestShare = Math.max(strongest.yea_share, strongest.nay_share);
  const second = rows[1];

  if (second) {
    return `In the strongest recorded domains, this section shows ${strongestLabel} for ${formatDomainLabel(strongest.domain)} (${(strongestShare * 100).toFixed(
      0,
    )}% of recorded yea/nay votes) and additional recorded positions in ${formatDomainLabel(second.domain)}.`;
  }

  return `The clearest vote-direction sample in this window is ${strongestLabel} for ${formatDomainLabel(
    strongest.domain,
  )}, across ${strongest.recorded_votes} recorded votes.`;
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

function formatInterpretationStatus(status) {
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

function getInterpretationBadgeClass(status) {
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
