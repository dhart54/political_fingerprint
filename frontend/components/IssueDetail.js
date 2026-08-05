"use client";

import { useEffect, useMemo, useState } from "react";

import ChronologicalActionLedger from "./ChronologicalActionLedger";
import PolicyEpisodeSection from "./PolicyEpisodeSection";
import ReviewedAnalysisSection from "./ReviewedAnalysisSection";
import { fetchPositionEvidence } from "../lib/api";
import { formatDomainLabel } from "../lib/issueDomains";
import { getDomainDescription } from "../lib/issueEvidenceCoverage.mjs";
import { buildSelectedIssueModel } from "../lib/selectedIssueExperience.mjs";

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
  const selectedIssue = useMemo(() => buildSelectedIssueModel({
    presentation,
    rows: state.rows,
    scope,
  }), [presentation, scope, state.rows]);

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

  function showExactActions(actionIds, label, metadata = {}) {
    setHighlightedFinding({
      actionIds,
      label,
      ...metadata,
      requestedAt: Date.now(),
    });
  }

  return (
    <section
      aria-labelledby="selected-issue-heading"
      className="mt-10 border-t border-stone-300"
      data-testid="issue-detail"
      id="issue-detail"
    >
      <header className="py-10 sm:py-12">
        <p className="eyebrow">Selected issue</p>
        <h2
          className="mt-2 max-w-4xl font-serif text-4xl leading-tight text-stone-950 sm:text-5xl"
          id="selected-issue-heading"
          tabIndex="-1"
        >
          {formatDomainLabel(issue)}
        </h2>
        <p className="mt-4 max-w-4xl text-lg leading-8 text-stone-700">
          {getDomainDescription(issue)}
        </p>

        {state.status === "ready" ? (
          <dl className="mt-7 grid max-w-4xl gap-px overflow-hidden rounded-xl border border-stone-200 bg-stone-200 sm:grid-cols-2">
            <ScopeCell
              description={selectedIssue.evidence.countText}
              label="Recorded actions shown"
              value={selectedIssue.evidence.label}
            />
            <ScopeCell
              description={selectedIssue.interpretation
                ? `${selectedIssue.interpretation.actionCount} reviewed actions · ${selectedIssue.interpretation.episodeCount} policy episodes`
                : "Exact vote receipts are available without a reviewed synthesis."}
              label="Reviewed interpretation"
              value={selectedIssue.interpretation?.scope || "Not published for this scope"}
            />
          </dl>
        ) : null}
      </header>

      <ReviewedAnalysisSection
        onSeeActions={showExactActions}
        presentation={presentation}
        rows={state.rows}
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

function ScopeCell({ description, label, value }) {
  return (
    <div className="bg-stone-50 px-5 py-4">
      <dt className="text-xs font-semibold uppercase tracking-[0.12em] text-stone-500">
        {label}
      </dt>
      <dd className="mt-1 text-base font-semibold leading-6 text-stone-950">{value}</dd>
      <dd className="mt-1 text-sm leading-6 text-stone-600">{description}</dd>
    </div>
  );
}
