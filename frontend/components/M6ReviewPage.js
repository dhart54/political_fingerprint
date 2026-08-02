"use client";

import { useMemo, useState } from "react";

import ChronologicalActionLedger from "./ChronologicalActionLedger";
import ReviewedAnalysisSection from "./ReviewedAnalysisSection";

export default function M6ReviewPage({ fixture }) {
  const [highlightedFinding, setHighlightedFinding] = useState(null);
  const rows = useMemo(() => fixture.ledger.map(toEvidenceRow), [fixture.ledger]);

  function showExactActions(actionIds, label) {
    setHighlightedFinding({ actionIds, label, requestedAt: Date.now() });
  }

  return (
    <main className="min-h-screen bg-[#f7f3e9] text-stone-900">
      <header className="border-b border-stone-200 bg-[#fbf8f1]">
        <div className="mx-auto flex max-w-[90rem] flex-wrap items-center justify-between gap-3 px-4 py-4 sm:px-6 lg:px-10">
          <p className="font-serif text-xl font-semibold text-stone-950">Political Fingerprint</p>
          <p className="rounded-full border border-amber-400 bg-amber-50 px-3 py-1 text-sm font-semibold text-amber-950">
            Review only · not public or production eligible
          </p>
        </div>
      </header>
      <div className="mx-auto max-w-[90rem] px-4 py-8 sm:px-6 lg:px-10">
        <section aria-labelledby="review-title" className="max-w-5xl py-5">
          <p className="eyebrow">Valerie P. Foushee · Justice &amp; Public Safety · 119th Congress</p>
          <h1 className="mt-3 font-serif text-5xl leading-[1.05] text-stone-950 sm:text-6xl" id="review-title">
            {fixture.presentation.conclusion.headline}
          </h1>
          <p className="mt-5 max-w-4xl text-lg leading-8 text-stone-700">{fixture.presentation.coverage_text}</p>
        </section>

        <section aria-labelledby="analysis-title" className="rounded-[1.75rem] border border-stone-200 bg-white px-5 sm:px-8">
          <h2 className="sr-only" id="analysis-title">Full-record issue analysis</h2>
          <ReviewedAnalysisSection onSeeActions={showExactActions} presentation={fixture.presentation} />

          <details className="border-t border-stone-200 py-8">
            <summary className="cursor-pointer text-lg font-semibold text-stone-950">Other notable choices and complete accounting</summary>
            <p className="mt-3 max-w-4xl text-base leading-7 text-stone-700">
              {fixture.other_notable_copy}
            </p>
          </details>

          <LaunchRiskDisclosure risks={fixture.launch_risks} />
          <ChronologicalActionLedger highlightedFinding={highlightedFinding} rows={rows} />
        </section>
      </div>
    </main>
  );
}

function LaunchRiskDisclosure({ risks }) {
  return (
    <section aria-labelledby="launch-risk-title" className="border-t border-stone-200 py-10" id="launch-risk-review">
      <p className="eyebrow">Launch-review boundary</p>
      <h2 className="mt-2 font-serif text-3xl leading-tight text-stone-950" id="launch-risk-title">Four unresolved launch cases</h2>
      <p className="mt-3 max-w-4xl text-base leading-7 text-stone-700">
        Option A is the only rendered candidate: retain the bounded mechanism contrast. Option B, no common throughline, requires Semantic IR revision. Option C, no overarching synthesis, requires conclusion-plan revision. Options B and C are non-authoritative review alternatives.
      </p>
      <div className="mt-6 divide-y divide-stone-200 border-y border-stone-200">
        {risks.map((risk) => (
          <details className="py-5" key={risk.risk_id}>
            <summary className="cursor-pointer font-semibold text-stone-950">{risk.question}</summary>
            <p className="mt-3 max-w-4xl text-base leading-7 text-stone-700"><strong>Current treatment:</strong> {risk.current_treatment}</p>
            <p className="mt-2 max-w-4xl text-base leading-7 text-stone-700"><strong>Decision needed:</strong> {risk.user_decision_required}</p>
          </details>
        ))}
      </div>
    </section>
  );
}

function toEvidenceRow(record) {
  const voteSources = record.official_vote_source || [];
  const meaningSources = record.official_action_meaning_sources || [];
  return {
    canonical_action_id: record.canonical_action_id,
    chamber: "house",
    congress: 119,
    rollcall_number: record.roll_call,
    vote_date: record.date,
    vote_type: record.legislative_stage,
    description: `House roll ${record.roll_call}`,
    position: record.member_action,
    interpretation_status: record.non_proposition_state || "interpreted",
    plain_english_summary: record.governed_action_meaning || "No safe public analytical meaning is available for this action.",
    question: record.governed_action_meaning || "The exact final-package policy question remains unresolved.",
    episode_relationship: record.episode_id || "No safe primary episode assignment.",
    uncertainty_note: record.limitations.join(" "),
    source_url: voteSources[0]?.url,
    source_basis: meaningSources.map((source) => ({ label: source.source_id, url: source.url })),
    provenance_refs: [record.canonical_action_id, ...record.proposition_ids],
  };
}
