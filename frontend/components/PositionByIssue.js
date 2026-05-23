"use client";

import { useEffect, useState } from "react";

import { fetchLegislatorContact, fetchPositionEvidence, fetchPositions } from "../lib/api";
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
              className={`rounded-[1.25rem] border px-4 py-4 text-left shadow-[inset_0_1px_0_rgba(255,255,255,0.72)] transition ${
                selectedDomain === row.domain
                  ? "border-cyan-800 bg-cyan-50"
                  : "border-stone-200 bg-stone-50 hover:border-cyan-700/50"
              }`}
              key={row.domain}
              onClick={() => inspectDomain(row.domain)}
              type="button"
            >
              <div className="flex items-start justify-between gap-3">
                <p className="max-w-[200px] text-[16px] leading-7 text-stone-900">
                  {formatDomainLabel(row.domain)}
                </p>
                <p className="text-sm text-stone-500">{row.recorded_votes} votes</p>
              </div>
              <div className="mt-3 flex items-center justify-between gap-3">
                <span className={`rounded-full px-3 py-1 text-[11px] uppercase tracking-[0.22em] ${getPositionBadgeClass(row)}`}>
                  {getPositionLabel(row)}
                </span>
                <p className="text-[13px] text-stone-600">
                  {buildPositionRead(row)}
                </p>
              </div>
              <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
                <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-3">
                  <p className="text-[11px] uppercase tracking-[0.22em] text-emerald-700">Yea</p>
                  <p className="mt-2 text-[1.45rem] leading-none text-stone-900">
                    {(row.yea_share * 100).toFixed(0)}%
                  </p>
                </div>
                <div className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-3">
                  <p className="text-[11px] uppercase tracking-[0.22em] text-rose-700">Nay</p>
                  <p className="mt-2 text-[1.45rem] leading-none text-stone-900">
                    {(row.nay_share * 100).toFixed(0)}%
                  </p>
                </div>
              </div>
              <div className="mt-4 h-3 overflow-hidden rounded-full bg-stone-200">
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
              <p className="mt-3 text-xs leading-5 text-stone-500">
                {buildInterpretationCoverageRead(row)}
              </p>
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
          These cards use only cached vote meanings. Missing or ambiguous meanings stay out of the pattern instead of being guessed.
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
                  <p className="text-[11px] uppercase tracking-[0.16em] text-stone-500">For side</p>
                  <p className="mt-2 text-[1.4rem] leading-none text-stone-950">{row.supportCount}</p>
                </div>
                <div className="rounded-xl border border-cyan-900/10 bg-white px-3 py-3">
                  <p className="text-[11px] uppercase tracking-[0.16em] text-stone-500">Against side</p>
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
                    <InterpretationBreakdown row={row} />
                    <div className="mt-3 flex flex-col gap-3 border-t border-stone-200 pt-3 sm:flex-row sm:items-center sm:justify-between">
                      <p className="text-xs uppercase leading-5 tracking-[0.16em] text-stone-500 sm:tracking-[0.18em]">
                        Included as {formatClassificationReason(row.classification_reason)}
                      </p>
                      <div className="flex flex-wrap gap-2">
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
                          Reference Vote
                        </button>
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
  const summary = buildIssueEvidenceSummary(rows, { domain, representativeName });
  if (!summary) {
    return null;
  }

  return (
    <div className="rounded-[1.25rem] border border-cyan-900/10 bg-white px-4 py-4">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-cyan-900">
            High-Level Read
          </p>
          <p className="mt-2 text-base leading-7 text-stone-900">
            {summary.lead}
          </p>
        </div>
        <span className="w-fit rounded-full bg-cyan-50 px-3 py-1 text-[11px] uppercase tracking-[0.16em] text-cyan-950">
          {summary.coverageLabel}
        </span>
      </div>
      <div className="mt-4 grid gap-2 sm:grid-cols-4">
        <SummaryMetric label="For side" value={summary.supportCount} />
        <SummaryMetric label="Against side" value={summary.opposeCount} />
        <SummaryMetric label="Other record" value={summary.otherCount} />
        <SummaryMetric label="Needs caution" value={summary.unresolvedCount} />
      </div>
      {summary.focusText ? (
        <p className="mt-3 text-sm leading-6 text-stone-700">
          {summary.focusText}
        </p>
      ) : null}
      {summary.scopeText ? (
        <p className="mt-2 text-sm leading-6 text-stone-600">
          {summary.scopeText}
        </p>
      ) : null}
      <p className="mt-3 text-xs leading-5 text-stone-500">
        Rows below remain the source of truth for each claim; missing vote meanings are not guessed.
      </p>
    </div>
  );
}

function SummaryMetric({ label, value }) {
  return (
    <div className="rounded-xl border border-stone-200 bg-stone-50 px-3 py-3">
      <p className="font-serif text-[1.65rem] leading-none text-stone-950">{value}</p>
      <p className="mt-1 text-[11px] uppercase tracking-[0.15em] text-stone-500">{label}</p>
    </div>
  );
}

function InterpretationBreakdown({ row }) {
  if (!hasInterpretationDetail(row)) {
    return null;
  }

  const isInterpreted = row.interpretation_status === "interpreted";
  const statusLabel = formatInterpretationStatus(row.interpretation_status);
  const summaryText = buildUsefulInterpretationText(row.plain_english_summary);
  const policyEffectText = buildUsefulInterpretationText(row.policy_effect);
  const interpretedVoteRead = buildInterpretedVoteRead(row);
  const plainTakeaway = buildPlainTakeaway(row);

  return (
    <div className="mt-3 rounded-2xl border border-cyan-900/10 bg-white px-3 py-3 sm:px-4">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-xs uppercase tracking-[0.22em] text-cyan-900">
          DC-Speak Breakdown
        </p>
        <span className={`w-fit rounded-full px-3 py-1 text-[11px] uppercase tracking-[0.18em] ${getInterpretationBadgeClass(row.interpretation_status)}`}>
          {statusLabel}
        </span>
      </div>

      {isInterpreted ? (
        <>
          {plainTakeaway ? (
            <InsightCard
              className="mt-3 border-cyan-900/20 bg-cyan-50"
              label="Why this mattered"
              text={plainTakeaway}
            />
          ) : null}
          <div className="mt-2 grid gap-2 lg:grid-cols-[1.1fr_0.9fr]">
            <InsightCard
              label="What this vote was"
              text={summaryText || policyEffectText}
            />
            {interpretedVoteRead ? (
              <InsightCard
                label="Their vote"
                text={interpretedVoteRead}
                tone={row.position === row.support_position ? "support" : row.position === row.oppose_position ? "oppose" : "neutral"}
              />
            ) : null}
          </div>
        </>
      ) : (
        <p className="mt-3 text-sm leading-6 text-stone-700">
          {row.uncertainty_note || row.interpretation_reason || "The available source text is not clear enough to summarize what this vote meant."}
        </p>
      )}

      <div className="mt-3 flex flex-wrap gap-2">
        {row.issue_facet ? (
          <span className="rounded-full bg-stone-100 px-3 py-1 text-[11px] uppercase tracking-[0.16em] text-stone-600">
            {formatIssueFacet(row.issue_facet)}
          </span>
        ) : null}
        {row.confidence ? (
          <span className="rounded-full bg-cyan-50 px-3 py-1 text-[11px] uppercase tracking-[0.16em] text-cyan-900">
            {formatConfidence(row.confidence)} confidence
          </span>
        ) : null}
      </div>
      <SourceBasisList sourceBasis={row.source_basis} />
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
  const leaning = strongest.yea_share >= strongest.nay_share ? "more often voted yea" : "more often voted nay";
  const leaningShare = Math.max(strongest.yea_share, strongest.nay_share);
  const second = rows[1];

  if (second) {
    return `In the strongest recorded domains, this legislator ${leaning} on ${formatDomainLabel(strongest.domain)} (${(leaningShare * 100).toFixed(
      0,
    )}%) and also shows recorded positions in ${formatDomainLabel(second.domain)}.`;
  }

  return `The clearest recorded position pattern in this window is ${formatDomainLabel(strongest.domain)}, where this legislator ${leaning} ${(leaningShare * 100).toFixed(
    0,
  )}% of the time.`;
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
      const coverageText = `${interpretedRecordedVotes} of ${recordedVotes} recorded yea/nay votes have a cached vote meaning`;
      let label = "Split interpreted record";

      if (supportCount > opposeCount && opposeCount === 0) {
        label = "Recorded for-side votes";
      } else if (opposeCount > supportCount && supportCount === 0) {
        label = "Recorded against-side votes";
      } else if (supportCount > opposeCount) {
        label = "More for-side than against-side";
      } else if (opposeCount > supportCount) {
        label = "More against-side than for-side";
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

const ISSUE_FACET_READS = {
  budget_reconciliation_and_debt_limit: "budget-reconciliation instructions tied to taxes, spending, deficits, and the debt limit",
  government_funding_and_shutdown: "a shutdown-ending federal funding package",
  temporary_government_funding: "short-term federal funding while regular appropriations were unfinished",
  small_business_loan_eligibility: "SBA loan eligibility restrictions based on citizenship or residency status",
  small_business_regulation: "SBA regulatory-cost limits for small businesses",
  military_construction_and_va_appropriations: "military construction, military housing, and veterans affairs appropriations",
  appropriations_amendment: "an appropriations amendment",
  conference_instruction: "a conference instruction",
  fentanyl_scheduling_and_penalties: "fentanyl scheduling and penalty changes",
  federal_law_enforcement_equipment: "federal law-enforcement equipment transfers",
  law_enforcement_safety_reporting: "law-enforcement safety reporting",
  dc_police_pursuit_policy: "D.C. police pursuit policy",
  dc_policing_reform_repeal: "repeal of a D.C. policing reform law",
  dc_immigration_information_sharing: "D.C. immigration information-sharing rules",
  school_foreign_funding_and_contract_restrictions: "school restrictions tied to foreign funding and contracts",
  school_foreign_influence_parent_notifications: "parent-notification requirements for foreign influence in schools",
  federal_employee_collective_bargaining: "federal employee collective-bargaining rules",
  medicaid_payment_rules_for_minor_health_procedures: "Medicaid payment rules for minor health procedures",
  hydrogen_vehicle_safety_standards: "hydrogen vehicle safety standards",
  natural_gas_pipeline_and_lng_review_coordination: "natural-gas pipeline and LNG review coordination",
};

function buildIssueEvidenceSummary(rows, { domain = "", representativeName = "" } = {}) {
  if (!rows.length) {
    return null;
  }

  const interpretedRows = rows.filter((row) => row.interpretation_status === "interpreted");
  const supportCount = interpretedRows.filter((row) => row.position === row.support_position).length;
  const opposeCount = interpretedRows.filter((row) => row.position === row.oppose_position).length;
  const otherCount = interpretedRows.length - supportCount - opposeCount;
  const unresolvedCount = rows.filter((row) => row.interpretation_status && row.interpretation_status !== "interpreted").length;
  const directionalRows = interpretedRows.filter(
    (row) => (row.position === "yea" || row.position === "nay") && (row.position === row.support_position || row.position === row.oppose_position),
  );
  const supportRows = directionalRows.filter((row) => row.position === row.support_position);
  const opposeRows = directionalRows.filter((row) => row.position === row.oppose_position);
  const recordedCount = directionalRows.length;
  const issueLabel = formatDomainLabel(domain || rows[0]?.primary_domain || "this issue");
  const personLabel = formatRepresentativeReference(representativeName);
  const focusText = buildIssueFocusText({ issueLabel, opposeRows, otherCount, supportRows });
  const scopeText = buildIssueScopeText({
    directionalCount: recordedCount,
    issueLabel,
    otherCount,
    rowCount: rows.length,
    unresolvedCount,
  });

  const lead = buildDirectionalLead({
    issueLabel,
    opposeCount,
    otherCount,
    personLabel,
    supportCount,
  });

  return {
    coverageLabel: `${recordedCount} interpreted yea/nay`,
    focusText,
    lead,
    opposeCount,
    otherCount,
    scopeText,
    supportCount,
    unresolvedCount,
  };
}

function buildDirectionalLead({ issueLabel, opposeCount, otherCount, personLabel, supportCount }) {
  const directionalCount = supportCount + opposeCount;

  if (directionalCount === 1 && supportCount === 1) {
    return `This is a limited read: among the interpreted ${issueLabel} votes shown here, ${formatPossessive(personLabel)} one recorded yea/nay vote was for the interpreted measure.`;
  }
  if (directionalCount === 1 && opposeCount === 1) {
    return `This is a limited read: among the interpreted ${issueLabel} votes shown here, ${formatPossessive(personLabel)} one recorded yea/nay vote was against the interpreted measure.`;
  }
  if (supportCount > opposeCount && opposeCount === 0) {
    return `Among the interpreted ${issueLabel} votes shown here, ${formatPossessive(personLabel)} recorded yea/nay votes were all for the interpreted measures.`;
  }
  if (opposeCount > supportCount && supportCount === 0) {
    return `Among the interpreted ${issueLabel} votes shown here, ${formatPossessive(personLabel)} recorded yea/nay votes were all against the interpreted measures.`;
  }
  if (supportCount > opposeCount) {
    return `Among the interpreted ${issueLabel} votes shown here, ${personLabel} recorded ${supportCount} for-side votes and ${opposeCount} against-side votes.`;
  }
  if (opposeCount > supportCount) {
    return `Among the interpreted ${issueLabel} votes shown here, ${personLabel} recorded ${opposeCount} against-side votes and ${supportCount} for-side votes.`;
  }
  if (supportCount === opposeCount && supportCount > 0) {
    return `Among the interpreted ${issueLabel} votes shown here, ${formatPossessive(personLabel)} recorded yea/nay votes were split: ${supportCount} for and ${opposeCount} against.`;
  }
  if (otherCount > 0) {
    return `The interpreted ${issueLabel} rows shown here do not include a recorded yea or nay position for ${personLabel}.`;
  }

  return `The interpreted ${issueLabel} votes shown here are mixed.`;
}

function buildIssueFocusText({ issueLabel, opposeRows, otherCount, supportRows }) {
  const supportReads = buildMeasureReads(supportRows);
  const opposeReads = buildMeasureReads(opposeRows);

  let read = "";
  if (supportReads.length && !opposeReads.length) {
    read =
      supportRows.length === 1
        ? `In plain terms, that vote was for ${formatList(supportReads)}.`
        : `In plain terms, those votes were for ${formatList(supportReads)}.`;
  } else if (opposeReads.length && !supportReads.length) {
    read =
      opposeRows.length === 1
        ? `In plain terms, that vote was against ${formatList(opposeReads)}.`
        : `In plain terms, those votes were against ${formatList(opposeReads)}.`;
  } else if (supportReads.length && opposeReads.length) {
    read = `In plain terms, the for-side votes concerned ${formatList(supportReads)}, while the against-side votes concerned ${formatList(opposeReads)}.`;
  }

  if (!read) {
    return "";
  }

  const otherText = otherCount
    ? ` ${otherCount} interpreted ${otherCount === 1 ? "row uses" : "rows use"} another recorded position, such as not voting.`
    : "";

  return `${read}${otherText}`;
}

function buildIssueScopeText({ directionalCount, issueLabel, otherCount, rowCount, unresolvedCount }) {
  const pieces = [
    `This conclusion is based on ${directionalCount} interpreted yea/nay ${directionalCount === 1 ? "vote" : "votes"} among ${rowCount} roll-call ${rowCount === 1 ? "row" : "rows"} shown.`,
  ];

  if (directionalCount === 1) {
    pieces.push("Treat it as a narrow signal until more interpreted votes are loaded for this issue.");
  }

  if (otherCount) {
    pieces.push(`${otherCount} interpreted ${otherCount === 1 ? "row has" : "rows have"} another recorded position.`);
  }
  if (unresolvedCount) {
    pieces.push(`${unresolvedCount} procedural or ambiguous ${unresolvedCount === 1 ? "row stays" : "rows stay"} visible but outside the for/against read.`);
  }

  pieces.push(`It describes this ${issueLabel} evidence section only, not a broad ideology score or voting recommendation.`);

  return pieces.join(" ");
}

function buildMeasureReads(rows) {
  const reads = [];

  rows.forEach((row) => {
    const read = buildMeasureRead(row);
    if (read && !reads.includes(read)) {
      reads.push(read);
    }
  });

  if (reads.length <= 5) {
    return reads;
  }

  return [...reads.slice(0, 4), `${reads.length - 4} other interpreted ${reads.length - 4 === 1 ? "measure" : "measures"}`];
}

function buildMeasureRead(row) {
  const facet = String(row.issue_facet || "").trim();
  if (ISSUE_FACET_READS[facet]) {
    return ISSUE_FACET_READS[facet];
  }

  const takeaway = buildPlainTakeaway(row)
    .replace(/^This vote was about\s+/i, "")
    .replace(/^This vote helped set the rules for\s+/i, "rules for ")
    .replace(/\.$/, "")
    .trim();
  if (takeaway) {
    return takeaway[0].toLowerCase() + takeaway.slice(1);
  }

  if (facet) {
    return formatIssueFacet(facet).toLowerCase();
  }

  return String(row.bill_title || row.description || row.question || "the interpreted measure").trim();
}

function formatRepresentativeReference(name) {
  const cleaned = String(name || "").trim();
  if (!cleaned) {
    return "this representative";
  }

  const parts = cleaned.split(/\s+/).filter(Boolean);
  return parts.length > 1 ? parts[parts.length - 1] : cleaned;
}

function formatPossessive(name) {
  if (name === "this representative") {
    return "this representative's";
  }
  return name.endsWith("s") ? `${name}'` : `${name}'s`;
}

function formatList(values) {
  if (values.length === 1) {
    return values[0];
  }
  if (values.length === 2) {
    return `${values[0]} and ${values[1]}`;
  }
  return `${values.slice(0, -1).join(", ")}, and ${values[values.length - 1]}`;
}

function buildActionContext({ domain, evidenceRows, representativeName, selectedEvidenceRow }) {
  const interpretedRows = evidenceRows.filter((row) => row.interpretation_status === "interpreted");
  const supportCount = interpretedRows.filter((row) => row.position === row.support_position).length;
  const opposeCount = interpretedRows.filter((row) => row.position === row.oppose_position).length;
  const otherCount = interpretedRows.length - supportCount - opposeCount;
  const cautiousCount = evidenceRows.filter((row) => row.interpretation_status && row.interpretation_status !== "interpreted").length;
  const issueLabel = formatDomainLabel(domain);
  const contextLine = `${representativeName}'s ${issueLabel} evidence currently shows ${supportCount} for-side, ${opposeCount} against-side, ${otherCount} other-record, and ${cautiousCount} caution rows among the cached vote meanings shown here.`;
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
    return "Interpreted";
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

function formatConfidence(value) {
  return String(value || "unknown")
    .split("_")
    .map((segment) => segment[0].toUpperCase() + segment.slice(1))
    .join(" ");
}

function getPositionLabel(row) {
  const gap = Math.abs(row.yea_share - row.nay_share);
  if (gap < 0.15) {
    return "Mixed";
  }

  return row.yea_share >= row.nay_share ? "Leans Yea" : "Leans Nay";
}

function getPositionBadgeClass(row) {
  const label = getPositionLabel(row);
  if (label === "Leans Yea") {
    return "bg-emerald-100 text-emerald-800";
  }
  if (label === "Leans Nay") {
    return "bg-rose-100 text-rose-800";
  }
  return "bg-stone-200 text-stone-700";
}

function buildPositionRead(row) {
  const label = getPositionLabel(row);
  if (label === "Mixed") {
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
    return "0 interpreted yea/nay meanings cached; open evidence to inspect raw roll calls.";
  }
  if (interpretedYeaNay === recordedVotes) {
    return `${interpretedYeaNay} of ${recordedVotes} recorded yea/nay votes have cached vote meaning.`;
  }
  return `${interpretedYeaNay} of ${recordedVotes} recorded yea/nay votes have cached vote meaning; the rest stay visible but uninterpreted.`;
}
