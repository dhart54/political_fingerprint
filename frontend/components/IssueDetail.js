"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import ChronologicalActionLedger from "./ChronologicalActionLedger";
import PolicyEpisodeSection from "./PolicyEpisodeSection";
import ReviewedAnalysisSection from "./ReviewedAnalysisSection";
import SemanticIcon from "./SemanticIcon";
import RecordCardFinding from "./RecordCardFinding";
import { recordCardUrl } from "../lib/recordCard.mjs";
import { fetchPositionEvidence } from "../lib/api";
import { formatDomainLabel } from "../lib/issueDomains";
import { getDomainDescription } from "../lib/issueEvidenceCoverage.mjs";
import { buildSelectedIssueModel } from "../lib/selectedIssueExperience.mjs";

export default function IssueDetail({
  fixtureEvidence = null,
  issue,
  legislatorId,
  presentation,
  representativeName,
  scope,
  fetchEvidence = fetchPositionEvidence,
  cardFinding = null,
  cardFindingRequested = false,
  cardFindingView = null,
  allowFindingArrivalFocus = true,
  presentationStatus = "ready",
  routePath = "/",
}) {
  const [state, setState] = useState({
    status: "loading",
    rows: [],
    error: null,
  });
  const [highlightedFinding, setHighlightedFinding] = useState(null);
  const [retryAttempt, setRetryAttempt] = useState(0);
  const requestPending = useRef(false);
  const retryButton = useRef(null);
  const receiptStatus = useRef(null);
  const issueSection = useRef(null);
  const restoreRetryFocus = useRef(false);
  const findingPending = cardFindingRequested && presentationStatus === "loading";
  const selectedIssue = useMemo(() => buildSelectedIssueModel({
    presentation,
    rows: state.rows,
    scope,
  }), [presentation, scope, state.rows]);

  useEffect(() => {
    setHighlightedFinding(null);
  }, [fetchEvidence, fixtureEvidence, issue, legislatorId, scope]);

  useEffect(() => {
    let active = true;
    requestPending.current = true;
    restoreRetryFocus.current = false;
    setState({ status: "loading", rows: [], error: null });
    async function load() {
      try {
        const payload = fixtureEvidence
          || await fetchEvidence({ legislatorId, domain: issue, scope });
        if ((payload?.legislator_id && payload.legislator_id !== legislatorId) || (payload?.domain && payload.domain !== issue) || (payload?.scope && payload.scope !== scope) || !Array.isArray(payload?.evidence)) throw new Error("Receipt identity or shape mismatch");
        if (active) {
          requestPending.current = false;
          restoreRetryFocus.current = retryAttempt > 0 && document.activeElement === retryButton.current;
          setState({
            status: "ready",
            rows: payload?.evidence || [],
            error: null,
            focusOnArrival: retryAttempt === 0 || restoreRetryFocus.current,
          });
        }
      } catch {
        if (active) {
          requestPending.current = false;
          setState({
            status: "error",
            rows: [],
            error: "The exact vote receipts for this issue are unavailable right now.",
          });
        }
      }
    }
    load();
    return () => {
      active = false;
    };
  }, [fetchEvidence, fixtureEvidence, issue, legislatorId, retryAttempt, scope]);

  useEffect(() => {
    if (state.status !== "ready") return;
    // The ledger captures this option when it mounts. Consume it even when
    // receipts are hidden, so a later explicit navigation gets normal focus.
    setState((current) => current.status === "ready" && current.focusOnArrival === false
      ? { ...current, focusOnArrival: true } : current);
    if (!restoreRetryFocus.current) return;
    restoreRetryFocus.current = false;
    // The retry control disappears on success. Move its focus only if the
    // reader was still on that control when the current request completed.
    const target = issueSection.current?.querySelector("#vote-record h3")
      || issueSection.current?.querySelector("#finding-detail-heading");
    (target || receiptStatus.current)?.focus({ preventScroll: true });
  }, [state.status]);

  function retryReceipts() {
    if (state.status !== "error" || requestPending.current) return;
    // Guard synchronously, before React commits the loading announcement.
    requestPending.current = true;
    setRetryAttempt((attempt) => attempt + 1);
  }

  useEffect(() => {
    if (!cardFinding || cardFindingView === "receipts" || !allowFindingArrivalFocus) return;
    const frame = requestAnimationFrame(() => {
      document.getElementById("finding-detail")?.scrollIntoView({ behavior: window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
      document.getElementById("finding-detail-heading")?.focus({ preventScroll: true });
    });
    return () => cancelAnimationFrame(frame);
  }, [allowFindingArrivalFocus, cardFinding, cardFindingView]);

  const linkedFinding = useMemo(() => cardFinding && cardFindingView === "receipts" ? {
    actionIds: cardFinding.action_ids,
    label: cardFinding.sourceFinding.title || cardFinding.sourceFinding.heading,
    evidenceCountLabel: cardFinding.evidence_label,
    // Retain the accepted finding's own direction display contract.
    direction: cardFinding.sourceFinding.direction,
    showDirection: cardFinding.sourceFinding.show_direction,
    requestedAt: `${cardFinding.finding_id}:receipts`,
  } : null, [cardFinding, cardFindingView]);

  function showExactActions(actionIds, label, metadata = {}) {
    setHighlightedFinding({
      actionIds,
      label,
      ...metadata,
      requestedAt: Date.now(),
    });
  }

  function showCompleteRecord(event) {
    if (event && (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey)) return;
    event?.preventDefault();
    window.history.pushState({}, "", recordCardUrl(window.location.href, { legislatorId, scope, issue, hash: "vote-record" }));
    window.dispatchEvent(new PopStateEvent("popstate"));
  }

  return (
    <section
      aria-labelledby="selected-issue-heading"
      className="mt-10 border-t border-stone-300"
      data-testid="issue-detail"
      id="issue-detail"
      ref={issueSection}
    >
      <header className={`scroll-mt-24 ${cardFindingRequested ? "py-5" : "py-10 sm:py-12"}`} id="issue-summary">
        <p className="eyebrow">Selected issue</p>
        <h2
          className="mt-2 max-w-4xl font-serif text-4xl leading-tight text-stone-950 sm:text-5xl"
          id="selected-issue-heading"
          tabIndex="-1"
        >
          {formatDomainLabel(issue)}
        </h2>
        {!cardFindingRequested ? <p className="mt-4 max-w-4xl text-lg leading-8 text-stone-700">
          {getDomainDescription(issue)}
        </p> : null}

        {state.status === "ready" && !cardFindingRequested ? (
          <dl className="mt-7 grid max-w-5xl gap-px overflow-hidden rounded-xl border border-stone-300 bg-stone-300 sm:grid-cols-2">
            <ScopeCell
              description={selectedIssue.evidence.countText}
              icon="recorded"
              label="Recorded actions shown"
              value={selectedIssue.evidence.label}
            />
            <ScopeCell
              description={selectedIssue.interpretation
                ? issueSummaryAccounting(selectedIssue.interpretation)
                : state.rows.length
                  ? "Vote receipts remain available"
                  : "No vote receipts are available in this scope."}
              icon="summary"
              label="Issue summary covers"
              value={selectedIssue.interpretation?.congressLabel || (presentationStatus === "loading" ? "Issue summary loading" : presentationStatus === "ready" ? "No issue summary for this scope" : "Issue summary unavailable")}
            />
          </dl>
        ) : null}
        {state.status === "ready" && !cardFindingRequested && selectedIssue.interpretation && selectedIssue.evidence.notYetReviewedCount > 0 ? (
          <p className="mt-3 max-w-4xl text-sm leading-6 text-stone-600">
            {selectedIssue.evidence.notYetReviewedCount} additional recorded {selectedIssue.evidence.notYetReviewedCount === 1 ? "action is" : "actions are"} available below and not yet included in the reviewed interpretation.
          </p>
        ) : null}
      </header>

      {cardFinding ? <RecordCardFinding entry={cardFinding} legislatorId={legislatorId} scope={scope} receiptsVisible={cardFindingView === "receipts"} routePath={routePath} /> : null}
      {cardFindingRequested ? <div className="py-5 text-base leading-7 text-stone-700">
        {findingPending ? <p role="status">The linked reviewed finding is still loading.</p>
          : !cardFinding ? <p role="status">This finding link does not match the available reviewed source. Browse the complete issue record below.</p> : null}
        <a className="font-semibold text-teal-900 underline" href={recordCardUrl(routePath, { legislatorId, scope, issue, hash: "vote-record" })} onClick={showCompleteRecord}>Browse the complete issue record</a>
      </div> : null}
      {!cardFinding ? <ReviewedAnalysisSection
        onSeeActions={showExactActions}
        presentation={presentation}
        rows={state.rows}
      /> : null}
      {!cardFinding ? <PolicyEpisodeSection episodes={presentation?.policy_episodes || []} /> : null}

      <p
        aria-atomic="true"
        aria-live="polite"
        className={state.status === "loading" ? "border-t border-stone-200 py-10 text-base text-stone-700" : "sr-only"}
        id="receipt-load-status"
        ref={receiptStatus}
        role="status"
        tabIndex="-1"
      >
        {state.status === "loading" ? retryAttempt ? "Retrying chronological vote receipts." : "Loading chronological vote receipts…" : state.status === "ready" && retryAttempt ? "Vote receipts loaded." : ""}
      </p>
      {state.status === "error" ? (
        <p className="border-t border-stone-200 pt-10 text-base text-rose-800" role="alert">
          {state.error}
        </p>
      ) : null}
      {state.status === "error" || (state.status === "loading" && retryAttempt > 0) ? (
        <div className="pb-10 pt-4">
          <button
            aria-describedby="receipt-load-status"
            aria-disabled={state.status === "loading"}
            className="secondary-button"
            onClick={retryReceipts}
            ref={retryButton}
            type="button"
          >
            Retry vote receipts
          </button>
        </div>
      ) : null}
      {state.status === "ready" && !findingPending && (!cardFinding || cardFindingView === "receipts") ? (
        <ChronologicalActionLedger
          focusOnArrival={state.focusOnArrival}
          allowFindingArrivalFocus={allowFindingArrivalFocus}
          contactContext={routePath === "/" ? { legislatorId, identity: `${legislatorId}:${issue}:${scope}` } : null}
          key={linkedFinding?.requestedAt || "all"}
          highlightedFinding={linkedFinding || highlightedFinding}
          onClearFinding={cardFinding ? () => showCompleteRecord() : undefined}
          representativeName={representativeName}
          rows={state.rows}
        />
      ) : null}
    </section>
  );
}

function issueSummaryAccounting(interpretation) {
  const actionText = `${interpretation.actionCount} recorded ${interpretation.actionCount === 1 ? "action" : "actions"} in scope`;
  if (!interpretation.findingCount || !interpretation.supportingVoteCount) {
    return actionText;
  }
  return `${actionText} · ${interpretation.findingCount} findings supported by ${interpretation.supportingVoteCount} votes`;
}

function ScopeCell({ description, icon, label, value }) {
  return (
    <div className="flex gap-4 bg-stone-50 px-5 py-5 sm:px-6">
      <SemanticIcon className="mt-1 h-8 w-8 shrink-0 text-teal-800" kind={icon} />
      <div>
        <dt className="text-sm font-medium leading-5 text-stone-600">{label}</dt>
        <dd className="mt-1 text-base font-semibold leading-6 text-stone-950">{value}</dd>
        <dd className="mt-1 text-sm leading-6 text-stone-600">{description}</dd>
      </div>
    </div>
  );
}
