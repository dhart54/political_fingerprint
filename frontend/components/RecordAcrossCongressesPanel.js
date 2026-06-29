"use client";

import { useEffect, useState } from "react";

import { fetchPositionEvidence, fetchRecordAcrossCongresses } from "../lib/api";
import { formatDomainLabel } from "../lib/issueDomains";
import {
  RECORD_ACROSS_COPY,
  RECORD_ACROSS_COUNT_FIELDS,
  RECORD_ACROSS_PRODUCT_FRAMING,
  buildFamilyRollCallDrilldown,
  getApprovedFamilyEvidenceSummary,
  getCountBucketLabel,
  getDisplayFamilies,
  getFamilyMatchLabel,
  getSparseStateCopy,
} from "../lib/recordAcrossCongresses.mjs";

export default function RecordAcrossCongressesPanel({ legislator, onInspectDomain }) {
  const [state, setState] = useState({
    status: "idle",
    response: null,
  });

  const isHouse = String(legislator?.chamber || "").toLowerCase() === "house";

  useEffect(() => {
    let active = true;

    async function loadRecordAcrossCongresses() {
      if (!isHouse || !legislator?.id) {
        setState({ status: "idle", response: null });
        return;
      }

      setState({ status: "loading", response: null });

      try {
        const response = await fetchRecordAcrossCongresses({ legislatorId: legislator.id });
        if (active) {
          setState({ status: "ready", response });
        }
      } catch (_error) {
        if (active) {
          setState({ status: "idle", response: null });
        }
      }
    }

    loadRecordAcrossCongresses();

    return () => {
      active = false;
    };
  }, [isHouse, legislator?.id]);

  if (!isHouse || state.status !== "ready") {
    return null;
  }

  return (
    <RecordAcrossCongressesContent
      onInspectDomain={onInspectDomain}
      response={state.response}
    />
  );
}

export function RecordAcrossCongressesContent({ response, onInspectDomain }) {
  if (!response || response.product_framing !== RECORD_ACROSS_PRODUCT_FRAMING) {
    return null;
  }

  const displayFamilies = getDisplayFamilies(response);
  const sparseStateCopy = getSparseStateCopy(response);

  return (
    <details className="mt-5 rounded-2xl border border-stone-200 bg-white px-4 py-4 shadow-[0_10px_28px_rgba(15,23,42,0.06)] lg:px-5" data-testid="record-across-congresses-panel">
      <summary className="cursor-pointer text-sm font-semibold uppercase tracking-[0.18em] text-stone-700 marker:text-cyan-900">
        {RECORD_ACROSS_COPY.panelTitle}
      </summary>
      <div className="mt-4 border-t border-stone-200 pt-4">
        <p className="max-w-3xl text-sm leading-6 text-stone-700">
          {RECORD_ACROSS_COPY.oneSentenceExplanation}
        </p>
        <AvailabilitySummary summary={response.summary} />
        {displayFamilies.length > 0 ? (
          <div className="mt-4 grid gap-3">
            {displayFamilies.map((family) => (
              <FamilyEvidenceCard
                family={family}
                key={family.family_id}
                legislatorId={response.legislator_identifier || response.legislator?.legislator_identifier}
              />
            ))}
          </div>
        ) : (
          <div className="mt-4 rounded-xl border border-stone-200 bg-stone-50 px-4 py-4">
            <p className="text-sm font-medium leading-6 text-stone-900">{sparseStateCopy}</p>
            <p className="mt-2 text-sm leading-6 text-stone-600">
              {RECORD_ACROSS_COPY.missingNoRecordCaveat}
            </p>
          </div>
        )}
        <div className="mt-4 grid gap-2 border-t border-stone-200 pt-4 text-sm leading-6 text-stone-600 md:grid-cols-3">
          <p>{RECORD_ACROSS_COPY.notVotingCaveat}</p>
          <p>{RECORD_ACROSS_COPY.relatedUnavailableNote}</p>
          <p>{RECORD_ACROSS_COPY.whyNotInferenceExplanation}</p>
        </div>
      </div>
    </details>
  );
}

function AvailabilitySummary({ summary = {} }) {
  const items = [
    {
      label: "Families with evidence in both Congresses",
      value: summary.display_eligible_family_count || 0,
    },
    {
      label: RECORD_ACROSS_COPY.directComparableFamilyLabel,
      value: summary.directly_comparable_display_eligible_family_count || 0,
    },
    {
      label: RECORD_ACROSS_COPY.conditionalComparableFamilyLabel,
      value: summary.conditionally_comparable_display_eligible_family_count || 0,
    },
  ];

  return (
    <div className="mt-4 grid gap-2 md:grid-cols-3">
      {items.map((item) => (
        <div className="rounded-xl border border-stone-200 bg-stone-50 px-3 py-3" key={item.label}>
          <p className="font-serif text-[1.6rem] leading-none text-cyan-900">{item.value}</p>
          <p className="mt-1 text-[11px] uppercase tracking-[0.14em] text-stone-600">{item.label}</p>
        </div>
      ))}
    </div>
  );
}

function FamilyEvidenceCard({ family, legislatorId }) {
  const matchLabel = getFamilyMatchLabel(family.comparability_status);
  const [drilldownState, setDrilldownState] = useState({
    status: "closed",
    drilldown: null,
  });

  async function toggleDrilldown() {
    if (drilldownState.status === "ready") {
      setDrilldownState({ status: "closed", drilldown: null });
      return;
    }

    setDrilldownState({ status: "loading", drilldown: null });
    try {
      const payload = await fetchPositionEvidence({
        legislatorId,
        domain: family.issue_domain,
        scope: "all",
      });
      setDrilldownState({
        status: "ready",
        drilldown: buildFamilyRollCallDrilldown({
          family,
          evidenceRows: payload?.evidence || [],
        }),
      });
    } catch (_error) {
      setDrilldownState({
        status: "error",
        drilldown: null,
      });
    }
  }

  return (
    <article className="rounded-xl border border-stone-200 bg-stone-50 px-4 py-4" data-testid={`record-family-card-${family.family_id}`}>
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full border border-cyan-900/20 bg-cyan-50 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-cyan-900">
              {matchLabel}
            </span>
            <span className="rounded-full border border-stone-200 bg-white px-3 py-1 text-[11px] uppercase tracking-[0.14em] text-stone-600">
              {formatDomainLabel(family.issue_domain)}
            </span>
          </div>
          <h3 className="mt-3 font-serif text-[1.35rem] leading-tight text-stone-950">
            {family.family_name}
          </h3>
          <p className="mt-2 text-sm leading-6 text-stone-700">{family.governing_question}</p>
          <p className="mt-2 rounded-lg border border-stone-200 bg-white px-3 py-2 text-sm leading-6 text-stone-700">
            {family.comparability_caveat}
          </p>
        </div>
        <button
          aria-expanded={drilldownState.status === "ready"}
          className="w-fit rounded-full border border-cyan-900/20 bg-white px-4 py-2 text-xs font-semibold uppercase tracking-[0.14em] text-cyan-900 transition hover:bg-cyan-50 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={!legislatorId || drilldownState.status === "loading"}
          onClick={toggleDrilldown}
          type="button"
        >
          {drilldownState.status === "ready" ? "Close roll-call evidence." : RECORD_ACROSS_COPY.sourceEvidenceDrilldownPrompt}
        </button>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <CongressCounts
          counts={family.family_evidence_counts_by_congress?.["118"]}
          label="118th"
        />
        <CongressCounts
          counts={family.family_evidence_counts_by_congress?.["119"]}
          label="119th"
        />
      </div>
      <FamilyRollCallDrilldown state={drilldownState} />
    </article>
  );
}

function FamilyRollCallDrilldown({ state }) {
  if (state.status === "closed") {
    return null;
  }

  if (state.status === "loading") {
    return (
      <div className="mt-4 rounded-xl border border-stone-200 bg-white px-4 py-4 text-sm leading-6 text-stone-600">
        Loading roll-call evidence.
      </div>
    );
  }

  if (state.status === "error" || !state.drilldown) {
    return (
      <div className="mt-4 rounded-xl border border-stone-200 bg-white px-4 py-4 text-sm leading-6 text-stone-600">
        Roll-call evidence is unavailable right now.
      </div>
    );
  }

  return (
    <section className="mt-4 rounded-xl border border-cyan-900/15 bg-white px-4 py-4" data-testid="record-family-roll-call-drilldown">
      <div className="flex flex-wrap items-center gap-2">
        <span className="rounded-full border border-cyan-900/20 bg-cyan-50 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-cyan-900">
          {state.drilldown.match_label}
        </span>
        <span className="rounded-full border border-stone-200 bg-white px-3 py-1 text-[11px] uppercase tracking-[0.14em] text-stone-600">
          {formatDomainLabel(state.drilldown.issue_domain)}
        </span>
      </div>
      <h4 className="mt-3 font-serif text-[1.25rem] leading-tight text-stone-950">
        {state.drilldown.family_name}
      </h4>
      <p className="mt-2 text-sm leading-6 text-stone-700">{state.drilldown.governing_question}</p>
      <p className="mt-2 rounded-lg border border-stone-200 bg-stone-50 px-3 py-2 text-sm leading-6 text-stone-700">
        {state.drilldown.comparability_caveat}
      </p>
      <div className="mt-4 grid gap-4 xl:grid-cols-2">
        <RollCallCongressSection label="118th" rows={state.drilldown.congresses["118"]} />
        <RollCallCongressSection label="119th" rows={state.drilldown.congresses["119"]} />
      </div>
      <div className="mt-4 grid gap-2 border-t border-stone-200 pt-4 text-xs leading-5 text-stone-600 md:grid-cols-3">
        <p>{RECORD_ACROSS_COPY.notVotingCaveat}</p>
        <p>{RECORD_ACROSS_COPY.missingNoRecordCaveat}</p>
        <p>{RECORD_ACROSS_COPY.whyNotInferenceExplanation}</p>
      </div>
    </section>
  );
}

function RollCallCongressSection({ label, rows = [] }) {
  return (
    <div className="min-w-0 rounded-xl border border-stone-200 bg-stone-50 px-3 py-3">
      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-stone-600">{label}</p>
      <div className="mt-3 grid gap-3">
        {rows.length > 0 ? (
          rows.map((row) => <RollCallEvidenceRow key={`${label}-${row.roll_call_id}`} row={row} />)
        ) : (
          <p className="rounded-lg border border-stone-200 bg-white px-3 py-3 text-sm leading-6 text-stone-600">
            No family roll-call IDs are listed for this Congress.
          </p>
        )}
      </div>
    </div>
  );
}

function RollCallEvidenceRow({ row }) {
  const bucketLabel = getCountBucketLabel(row.count_bucket);
  const countedLabel = row.counted_substantive_evidence
    ? "Counted substantive evidence"
    : "Not counted substantive evidence";

  return (
    <article className="min-w-0 rounded-lg border border-stone-200 bg-white px-3 py-3">
      <div className="grid gap-2 md:grid-cols-[minmax(0,1fr)_auto] md:items-start">
        <div className="min-w-0">
          <p className="break-words text-[11px] uppercase tracking-[0.16em] text-stone-500">
            Roll {row.rollcall_number || row.roll_call_id}
            {row.vote_date ? ` - ${formatDate(row.vote_date)}` : ""}
          </p>
          <p className="mt-1 break-words text-sm font-medium leading-5 text-stone-950">
            {row.question || row.description || "Vote question unavailable"}
          </p>
        </div>
        <div className="flex flex-wrap gap-2 md:justify-end">
          <span className="w-fit rounded-full border border-stone-200 bg-stone-50 px-3 py-1 text-xs uppercase tracking-[0.16em] text-stone-700">
            {formatVotePosition(row.position)}
          </span>
          <span className="w-fit rounded-full border border-cyan-900/20 bg-cyan-50 px-3 py-1 text-[11px] uppercase tracking-[0.14em] text-cyan-900">
            {bucketLabel}
          </span>
        </div>
      </div>
      <p className="mt-2 text-sm leading-6 text-stone-700">
        {getApprovedFamilyEvidenceSummary(row)}
      </p>
      <div className="mt-3 flex flex-col gap-2 border-t border-stone-200 pt-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-xs uppercase tracking-[0.16em] text-stone-500">{countedLabel}</p>
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
    </article>
  );
}

function CongressCounts({ counts = {}, label }) {
  return (
    <div className="rounded-xl border border-stone-200 bg-white px-3 py-3">
      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-stone-600">
        {label}
      </p>
      <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-5 md:grid-cols-2 xl:grid-cols-5">
        {RECORD_ACROSS_COUNT_FIELDS.map((field) => (
          <div className="min-h-[72px] rounded-lg border border-stone-100 bg-stone-50 px-2 py-2" key={field.key}>
            <p className="font-serif text-[1.35rem] leading-none text-stone-950">
              {counts[field.key] || 0}
            </p>
            <p className="mt-1 text-[11px] leading-4 text-stone-600">{field.label}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function formatDate(value) {
  if (!value) {
    return "";
  }
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(date);
}

function formatVotePosition(position) {
  if (!position) {
    return "Missing/no-record";
  }
  if (position === "not_voting") {
    return "Not voting";
  }
  return String(position)
    .split("_")
    .map((segment) => (segment ? segment[0].toUpperCase() + segment.slice(1) : segment))
    .join(" ");
}
