"use client";

import { useEffect, useState } from "react";

import ChronologicalActionLedger from "./ChronologicalActionLedger";
import PolicyEpisodeSection from "./PolicyEpisodeSection";
import ReviewedAnalysisSection from "./ReviewedAnalysisSection";
import { fetchPositionEvidence } from "../lib/api";
import { formatDomainLabel } from "../lib/issueDomains";
import { getDomainDescription } from "../lib/issueEvidenceCoverage.mjs";
import { scopeLabel } from "../lib/frontendPassA.mjs";

export default function IssueDetail({
  fixtureEvidence = null,
  issue,
  legislatorId,
  presentation,
  scope,
}) {
  const [state, setState] = useState({
    status: "loading",
    rows: [],
    error: null,
  });
  const [highlightedFinding, setHighlightedFinding] = useState(null);

  useEffect(() => {
    let active = true;
    setHighlightedFinding(null);
    setState({ status: "loading", rows: [], error: null });
    async function load() {
      try {
        const payload = fixtureEvidence
          || await fetchPositionEvidence({ legislatorId, domain: issue, scope });
        if (active) {
          setState({
            status: "ready",
            rows: payload?.evidence || [],
            error: null,
          });
        }
      } catch {
        if (active) {
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
  }, [fixtureEvidence, issue, legislatorId, scope]);

  function showExactActions(actionIds, label) {
    setHighlightedFinding({
      actionIds,
      label,
      requestedAt: Date.now(),
    });
  }

  return (
    <section
      aria-labelledby="selected-issue-heading"
      className="mt-8 rounded-[1.75rem] border border-stone-200 bg-white px-5 sm:px-8"
      data-testid="issue-detail"
      id="issue-detail"
    >
      <div className="py-9">
        <p className="eyebrow">Selected issue</p>
        <h2
          className="mt-2 font-serif text-4xl leading-tight text-stone-950"
          id="selected-issue-heading"
          tabIndex="-1"
        >
          {formatDomainLabel(issue)}
        </h2>
        <h3 className="mt-7 font-serif text-3xl leading-tight text-stone-950">
          What this issue covers
        </h3>
        <p className="mt-3 max-w-4xl text-lg leading-8 text-stone-700">
          {getDomainDescription(issue)}
        </p>
        <p className="mt-4 text-sm font-medium text-stone-600">
          Vote-record scope: {scopeLabel(scope)}
          {presentation?.review_state
            ? ` · Reviewed analysis scope: ${presentation.review_state.congress_scope.map((value) => `${value}th Congress`).join(", ")} ${formatReviewScope(presentation.review_state.review_scope)}`
            : " · No public reviewed analysis is supplied for this scope"}
        </p>
      </div>

      <ReviewedAnalysisSection
        onSeeActions={showExactActions}
        presentation={presentation}
      />
      <PolicyEpisodeSection episodes={presentation?.policy_episodes || []} />

      {state.status === "loading" ? (
        <p className="border-t border-stone-200 py-10 text-base text-stone-700" role="status">
          Loading chronological vote receipts…
        </p>
      ) : null}
      {state.status === "error" ? (
        <p className="border-t border-stone-200 py-10 text-base text-rose-800" role="alert">
          {state.error}
        </p>
      ) : null}
      {state.status === "ready" ? (
        <ChronologicalActionLedger
          highlightedFinding={highlightedFinding}
          rows={state.rows}
        />
      ) : null}
    </section>
  );
}

function formatReviewScope(value) {
  if (value === "benchmark_sample") {
    return "benchmark sample";
  }
  if (value === "bounded_partial_record") {
    return "bounded partial record";
  }
  if (value === "full_defined_issue_record") {
    return "full defined issue record";
  }
  return "review scope";
}
