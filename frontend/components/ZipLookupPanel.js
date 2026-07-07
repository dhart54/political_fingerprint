"use client";

import { useEffect, useState } from "react";

import { fetchCandidateEvidence, fetchSupportedZips, fetchZipLookup, fetchZipRaces } from "../lib/api";
import { formatDomainLabel } from "../lib/issueDomains";
import { ZIP_LOOKUP_STATES, classifyZipLookupState } from "../lib/zipLookupState.mjs";

const DEFAULT_ZIP = "27701";

export default function ZipLookupPanel({
  onComparePair,
  onRaceStateChange,
  onSelectLegislator,
  showElectionContext = true,
  variant = "standard",
}) {
  const [zipCode, setZipCode] = useState(DEFAULT_ZIP);
  const [state, setState] = useState({
    status: "idle",
    payload: null,
    lookupState: null,
    error: null,
  });
  const [supportedZips, setSupportedZips] = useState({
    status: "loading",
    dataSource: null,
    zips: [],
  });
  const [raceState, setRaceState] = useState({
    status: "idle",
    payload: null,
    error: null,
  });
  const [selectedComparisonPreset, setSelectedComparisonPreset] = useState("house_first_senator");

  async function runLookup(nextZipCode) {
    if (nextZipCode.length !== 5) {
      setState({
        status: "error",
        payload: null,
        lookupState: null,
        error: "Enter a valid 5-digit ZIP code.",
      });
      return;
    }

    try {
      setState({
        status: "loading",
        payload: null,
        lookupState: null,
        error: null,
      });

      const payload = await fetchZipLookup({ zipCode: nextZipCode });
      const lookupState = classifyZipLookupState(payload);
      if (lookupState.canAutoSelectHouse) {
        loadZipRaces(nextZipCode);
      } else {
        resetRaceState();
      }
      setSelectedComparisonPreset("house_first_senator");
      setState({
        status: "ready",
        payload,
        lookupState,
        error: null,
      });
      if (lookupState.canAutoSelectHouse && payload.house_rep) {
        onSelectLegislator?.(payload.house_rep);
      }
      if (lookupState.canAutoSelectHouse && lookupState.canAutoSelectSenate && payload.house_rep && payload.senators?.[0]) {
        onComparePair?.({
          left: payload.house_rep,
          right: payload.senators[0],
        });
      }
    } catch (error) {
      const unsupportedPayload = {
        zip: nextZipCode,
        status: ZIP_LOOKUP_STATES.UNSUPPORTED_ZIP,
        data_source: "none",
        house_rep: null,
        senators: [],
        district_mappings: [],
      };
      const lookupState = classifyZipLookupState(unsupportedPayload);
      setState({
        status: "ready",
        payload: unsupportedPayload,
        lookupState,
        error: null,
      });
      resetRaceState();
    }
  }

  function resetRaceState() {
    const idleState = {
      status: "idle",
      payload: null,
      error: null,
    };
    setRaceState(idleState);
    onRaceStateChange?.(idleState);
  }

  async function loadZipRaces(nextZipCode) {
    try {
      const loadingState = {
        status: "loading",
        payload: null,
        error: null,
      };
      setRaceState(loadingState);
      onRaceStateChange?.(loadingState);
      const payload = await fetchZipRaces({ zipCode: nextZipCode });
      const readyState = {
        status: "ready",
        payload,
        error: null,
      };
      setRaceState(readyState);
      onRaceStateChange?.(readyState);
    } catch (error) {
      const errorState = {
        status: "error",
        payload: null,
        error: "Upcoming race data is not loaded for this ZIP yet.",
      };
      setRaceState(errorState);
      onRaceStateChange?.(errorState);
    }
  }

  useEffect(() => {
    runLookup(DEFAULT_ZIP);
  }, []);

  useEffect(() => {
    let active = true;

    async function loadSupportedZips() {
      try {
        const payload = await fetchSupportedZips();
        if (!active) {
          return;
        }
        setSupportedZips({
          status: "ready",
          dataSource: payload.data_source,
          zips: payload.zips || [],
        });
      } catch (error) {
        if (!active) {
          return;
        }
        setSupportedZips({
          status: "error",
          dataSource: null,
          zips: [],
        });
      }
    }

    loadSupportedZips();

    return () => {
      active = false;
    };
  }, []);

  function handleLookup(event) {
    event.preventDefault();
    runLookup(zipCode);
  }

  function selectComparisonPreset(preset, pair, selectedLegislator = pair.left) {
    setSelectedComparisonPreset(preset);
    onSelectLegislator?.(selectedLegislator);
    onComparePair?.(pair);
  }

  const isHero = variant === "hero";
  const sectionClassName = isHero
    ? "rounded-2xl border border-cyan-900/15 bg-white p-3 shadow-[0_10px_28px_rgba(15,23,42,0.09)] lg:p-4"
    : "mt-8 rounded-[2rem] border border-stone-200 bg-white p-5 shadow-[0_16px_40px_rgba(15,23,42,0.08)] lg:p-6";
  const hasResult = state.status === "ready";
  const lookupState = state.lookupState;
  const payload = state.payload;
  const showHouseCard =
    hasResult &&
    payload?.house_rep &&
    lookupState?.state !== ZIP_LOOKUP_STATES.AMBIGUOUS_ZIP &&
    lookupState?.state !== ZIP_LOOKUP_STATES.MULTI_STATE_ZIP &&
    lookupState?.state !== ZIP_LOOKUP_STATES.UNSUPPORTED_ZIP;
  const showSenateCards =
    hasResult &&
    payload?.senators?.length > 0 &&
    lookupState?.state !== ZIP_LOOKUP_STATES.MULTI_STATE_ZIP &&
    lookupState?.state !== ZIP_LOOKUP_STATES.UNSUPPORTED_ZIP;
  const canAutoSelectHouse = Boolean(lookupState?.canAutoSelectHouse);

  return (
    <section className={sectionClassName}>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.22em] text-stone-500">
            Start Here
          </p>
          <h3 className="mt-1 font-serif text-[1.45rem] leading-[1] text-stone-950 sm:text-[1.85rem]">
            {hasResult && canAutoSelectHouse ? "Your officials" : "Start with your ZIP."}
          </h3>
          <p className={`mt-2 max-w-2xl text-sm leading-5 text-stone-700 ${hasResult && isHero ? "sr-only" : ""}`}>
            Check whether the loaded ZIP map can safely identify a House district, then inspect voting records.
          </p>
        </div>
        <p className="text-xs uppercase tracking-[0.18em] text-stone-500">
          {supportedZips.status === "ready" && supportedZips.zips.length
            ? `Try ${buildZipSuggestion(supportedZips.zips)}`
            : "Loaded ZIPs appear here"}
        </p>
      </div>

      <form className="mt-3 flex flex-col gap-2 sm:flex-row" onSubmit={handleLookup}>
        <label className="sr-only" htmlFor="zip-code-input">
          ZIP code
        </label>
        <input
          id="zip-code-input"
          className="h-11 flex-1 rounded-full border border-stone-300 bg-stone-50 px-4 text-sm text-stone-900 outline-none ring-0 placeholder:text-stone-500"
          inputMode="numeric"
          maxLength={5}
          onChange={(event) => setZipCode(event.target.value.replace(/\D/g, "").slice(0, 5))}
          placeholder="Enter ZIP code"
          value={zipCode}
        />
        <button
          className="h-11 rounded-full bg-cyan-900 px-5 text-sm uppercase tracking-[0.18em] text-white shadow-[0_10px_24px_rgba(22,78,99,0.22)]"
          type="submit"
        >
          Show My Reps
        </button>
      </form>

      <div className="mt-3 flex flex-col gap-1.5 rounded-xl bg-stone-950 px-3 py-2.5 text-stone-100 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-[11px] uppercase tracking-[0.18em] text-stone-400">
            Result
          </p>
          <p className="mt-1 text-sm text-stone-50">
            {state.status === "idle" ? "Ready to lookup" : null}
            {state.status === "loading" ? "Looking up legislators..." : null}
            {state.status === "error" ? "Lookup unavailable" : null}
            {state.status === "ready"
              ? lookupState?.title || "Lookup result"
              : null}
          </p>
        </div>
        <p className="text-sm leading-5 text-stone-300">
          {state.status === "idle" ? "Run a ZIP lookup to load representatives." : null}
          {state.status === "loading" ? "Loading House and Senate results." : null}
          {state.status === "error" ? state.error : null}
          {state.status === "ready"
            ? lookupState?.message
            : null}
        </p>
      </div>

      {state.status === "ready" && lookupState ? (
        <div className={`mt-3 rounded-xl border px-3 py-3 ${getLookupNoticeClass(lookupState.severity)}`}>
          <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.18em]">
                Lookup state: {formatLookupState(lookupState.state)}
              </p>
              {lookupState.caveats.length ? (
                <div className="mt-2 grid gap-1.5">
                  {lookupState.caveats.map((caveat) => (
                    <p className="text-sm leading-5" key={caveat}>
                      {caveat}
                    </p>
                  ))}
                </div>
              ) : null}
            </div>
            <a
              className="w-fit rounded-full border border-current px-3 py-2 text-xs uppercase tracking-[0.14em]"
              href="#manual-representative-search"
            >
              Search by name
            </a>
          </div>
          {lookupState.nextActions.length ? (
            <ul className="mt-2 grid gap-1 text-sm leading-5">
              {lookupState.nextActions.map((action) => (
                <li key={action}>{action}</li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}

      {state.status === "ready" ? (
        <div className="mt-2">
          {isHero ? (
            <div className="grid gap-2 sm:grid-cols-3">
              {showHouseCard ? (
                <CompactOfficialButton
                  heading={canAutoSelectHouse ? "House" : "Loaded House"}
                  legislator={state.payload.house_rep}
                  onSelectLegislator={onSelectLegislator}
                />
              ) : null}
              {showSenateCards ? state.payload.senators.map((senator) => (
                <CompactOfficialButton
                  heading="Senate"
                  key={senator.id}
                  legislator={senator}
                  onSelectLegislator={onSelectLegislator}
                />
              )) : null}
            </div>
          ) : (
            <>
              <div className="mb-3 flex flex-wrap gap-2 rounded-xl border border-cyan-900/10 bg-cyan-50 px-3 py-3">
                <p className="w-full text-sm leading-5 text-stone-700">
                  {canAutoSelectHouse
                    ? "Your House profile opened below. Use these buttons to change the comparison pair."
                    : "ZIP lookup did not auto-open a House profile. Use manual search or inspect clearly labeled loaded records."}
                </p>
                {canAutoSelectHouse && state.payload.house_rep && state.payload.senators[0] ? (
                  <button
                    className={getComparePresetClass(selectedComparisonPreset === "house_first_senator")}
                    aria-label={`Compare ${state.payload.house_rep.name_display} with ${state.payload.senators[0].name_display}`}
                    aria-pressed={selectedComparisonPreset === "house_first_senator"}
                    onClick={() =>
                      selectComparisonPreset("house_first_senator", {
                        left: state.payload.house_rep,
                        right: state.payload.senators[0],
                      })
                    }
                    type="button"
                  >
                    House vs Senator
                  </button>
                ) : null}
                {canAutoSelectHouse && state.payload.house_rep && state.payload.senators[1] ? (
                  <button
                    className={getComparePresetClass(selectedComparisonPreset === "house_second_senator")}
                    aria-label={`Compare ${state.payload.house_rep.name_display} with ${state.payload.senators[1].name_display}`}
                    aria-pressed={selectedComparisonPreset === "house_second_senator"}
                    onClick={() =>
                      selectComparisonPreset("house_second_senator", {
                        left: state.payload.house_rep,
                        right: state.payload.senators[1],
                      })
                    }
                    type="button"
                  >
                    House vs Other Senator
                  </button>
                ) : null}
                {lookupState.canAutoSelectSenate && state.payload.senators[0] && state.payload.senators[1] ? (
                  <button
                    className={getComparePresetClass(selectedComparisonPreset === "senators")}
                    aria-label={`Compare ${state.payload.senators[0].name_display} with ${state.payload.senators[1].name_display}`}
                    aria-pressed={selectedComparisonPreset === "senators"}
                    onClick={() =>
                      selectComparisonPreset(
                        "senators",
                        {
                          left: state.payload.senators[0],
                          right: state.payload.senators[1],
                        },
                        state.payload.senators[0],
                      )
                    }
                    type="button"
                  >
                    Compare Senators
                  </button>
                ) : null}
              </div>

              <div className="grid gap-4 lg:grid-cols-[0.95fr_1.05fr]">
                {showHouseCard ? (
                  <LegislatorCard
                    accent="bg-cyan-100 text-cyan-900"
                    heading={canAutoSelectHouse ? "House Representative" : "Loaded House Record"}
                    legislator={state.payload.house_rep}
                    onSelectLegislator={onSelectLegislator}
                  />
                ) : null}
                {showSenateCards ? (
                  <div className="grid gap-4">
                    {state.payload.senators.map((senator) => (
                    <LegislatorCard
                      accent="bg-emerald-100 text-emerald-900"
                      key={senator.id}
                      heading="Senator"
                      legislator={senator}
                      onSelectLegislator={onSelectLegislator}
                    />
                    ))}
                  </div>
                ) : null}
              </div>

              {showElectionContext ? (
                <UpcomingRacePanel
                  onSelectLegislator={onSelectLegislator}
                  raceState={raceState}
                />
              ) : null}
            </>
          )}
        </div>
      ) : null}

      {!isHero && supportedZips.status === "ready" && supportedZips.zips.length > 0 ? (
        <div className="mt-5 rounded-[1.25rem] border border-stone-200 bg-stone-50 px-4 py-4">
          <p className="text-xs uppercase tracking-[0.24em] text-stone-500">
            Loaded ZIP Map
          </p>
          <p className="mt-2 text-sm leading-6 text-stone-700">
            Showing {supportedZips.zips.length} loaded ZIP {supportedZips.zips.length === 1 ? "mapping" : "mappings"}
            {supportedZips.dataSource ? ` from ${supportedZips.dataSource}.` : "."}{" "}
            {supportedZips.dataSource === "fixtures"
              ? "This is sample coverage, not national coverage yet."
              : "ZIPs are not always precise; ambiguous results stay gated."}
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            {supportedZips.zips.slice(0, 8).map((row) => (
              <button
                className="rounded-full border border-stone-300 bg-white px-3 py-2 text-xs uppercase tracking-[0.18em] text-stone-700"
                aria-label={`Lookup ZIP ${row.zip}, ${row.state}-${row.district}`}
                key={row.zip}
                onClick={() => {
                  setZipCode(row.zip);
                  runLookup(row.zip);
                }}
                type="button"
              >
                {row.zip} {row.state}-{row.district}
              </button>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  );
}

function CompactOfficialButton({ heading, legislator, onSelectLegislator }) {
  if (!legislator) {
    return null;
  }

  return (
    <button
      className="rounded-xl border border-stone-200 bg-stone-50 px-3 py-3 text-left transition hover:border-cyan-800 hover:bg-cyan-50 focus:outline-none focus:ring-2 focus:ring-cyan-800 focus:ring-offset-2"
      onClick={() => onSelectLegislator?.(legislator)}
      type="button"
    >
      <p className="text-[11px] uppercase tracking-[0.16em] text-stone-500">{heading}</p>
      <p className="mt-1 text-sm font-semibold leading-5 text-stone-950">{legislator.name_display}</p>
      <p className="mt-1 text-xs leading-4 text-stone-600">
        {legislator.party} - {legislator.state}
        {legislator.district ? `-${legislator.district}` : " statewide"}
      </p>
    </button>
  );
}

export function UpcomingRacePanel({ onSelectLegislator, preferences = {}, raceState }) {
  if (raceState.status === "idle") {
    return null;
  }

  const races = raceState.payload?.races || [];

  return (
    <details className="mt-5 rounded-[1.5rem] border border-stone-200 bg-stone-50 px-4 py-4">
      <summary className="cursor-pointer list-none">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.26em] text-stone-500">
              Secondary Election Context
            </p>
            <h4 className="mt-2 font-serif text-[1.65rem] leading-none text-stone-950">
              Upcoming federal races
            </h4>
          </div>
          <span className="w-fit rounded-full border border-stone-300 bg-white px-3 py-2 text-[11px] uppercase tracking-[0.16em] text-stone-700">
            Open election context
          </span>
        </div>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-stone-600">
          Current representatives and voting evidence are the primary read. Open this when you want the upcoming race context loaded for the ZIP.
        </p>
      </summary>

      <div className="mt-5 border-t border-stone-200 pt-4">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.26em] text-stone-500">
              Election / Challenger Layer
            </p>
            <h5 className="mt-2 font-serif text-[1.55rem] leading-none text-stone-950">
              Race context after the voting record
            </h5>
          </div>
          <p className="max-w-xl text-sm leading-6 text-stone-600">
            Candidate rows stay separated by evidence type: recorded votes for linked incumbents, sourced stated-position or institutional records when reviewed, and insufficient evidence when nothing issue-specific is loaded.
          </p>
        </div>

        {raceState.status === "loading" ? (
          <p className="mt-4 text-sm leading-6 text-stone-700">
            Checking upcoming federal race coverage...
          </p>
        ) : null}
        {raceState.status === "error" ? (
          <p className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm leading-6 text-amber-900">
            {raceState.error}
          </p>
        ) : null}
        {raceState.status === "ready" && races.length === 0 ? (
          <p className="mt-4 rounded-2xl border border-stone-200 bg-white px-4 py-3 text-sm leading-6 text-stone-700">
            No upcoming federal race rows are loaded for this ZIP yet.
          </p>
        ) : null}
        {raceState.status === "ready" && races.length > 0 ? (
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            {races.map((race) => (
              <article className="rounded-[1.25rem] border border-stone-200 bg-white px-4 py-4" key={race.id}>
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-xs uppercase tracking-[0.22em] text-stone-500">
                      {formatRaceOffice(race)}
                    </p>
                    <h5 className="mt-2 text-[1.35rem] leading-7 text-stone-950">
                      {race.office_name}
                    </h5>
                  </div>
                  <span className="rounded-full bg-cyan-50 px-3 py-1 text-[11px] uppercase tracking-[0.16em] text-cyan-900">
                    {formatRaceStatus(race.status)}
                  </span>
                </div>
                <p className="mt-3 text-sm leading-6 text-stone-700">
                  {race.election_label} - {formatDate(race.election_date)}
                </p>
                <div className="mt-4 grid gap-2">
                  {(race.candidates || []).length ? (
                    <>
                      <RaceCandidateLimitNote candidates={race.candidates} />
                      {getVisibleRaceCandidates(race.candidates).map((candidate) => (
                        <RaceCandidateCard
                          candidate={candidate}
                          key={candidate.id}
                          onSelectLegislator={onSelectLegislator}
                          preferences={preferences}
                        />
                      ))}
                    </>
                  ) : (
                    <p className="rounded-2xl border border-stone-200 bg-stone-50 px-3 py-3 text-sm leading-6 text-stone-700">
                      Candidate roster is not loaded for this race yet. This row is election structure only, not a candidate comparison.
                    </p>
                  )}
                </div>
              </article>
            ))}
          </div>
        ) : null}
      </div>
    </details>
  );
}

function RaceCandidateLimitNote({ candidates }) {
  const hiddenCount = Math.max(0, candidates.length - VISIBLE_RACE_CANDIDATE_LIMIT);

  if (!hiddenCount) {
    return null;
  }

  return (
    <p className="rounded-2xl border border-stone-200 bg-stone-50 px-3 py-3 text-sm leading-6 text-stone-700">
      Showing the strongest {VISIBLE_RACE_CANDIDATE_LIMIT} candidate evidence rows first. {hiddenCount} additional lower-signal candidate {hiddenCount === 1 ? "row is" : "rows are"} hidden here to keep election context secondary to the current voting record.
    </p>
  );
}

const VISIBLE_RACE_CANDIDATE_LIMIT = 6;

function getVisibleRaceCandidates(candidates) {
  return [...candidates]
    .sort((left, right) => candidateEvidencePriority(right) - candidateEvidencePriority(left))
    .slice(0, VISIBLE_RACE_CANDIDATE_LIMIT);
}

function candidateEvidencePriority(candidate) {
  if (candidate.voting_summary) {
    return 4;
  }
  if ((candidate.candidate_evidence_summary?.total_count || 0) > 0) {
    return 3;
  }
  if (candidate.evidence_tier && candidate.evidence_tier !== "insufficient_evidence") {
    return 2;
  }
  return 1;
}

function RaceCandidateCard({ candidate, onSelectLegislator, preferences = {} }) {
  const linkedLegislator = candidate.linked_legislator;
  const votingSummary = candidate.voting_summary;
  const candidateEvidenceSummary = candidate.candidate_evidence_summary;
  const selectedIssueReads = buildSelectedIssueCandidateReads({
    candidateEvidenceSummary,
    hasVotingSummary: Boolean(votingSummary),
    preferences,
  });
  const [evidenceState, setEvidenceState] = useState({
    status: "idle",
    payload: null,
    error: null,
  });

  async function toggleCandidateEvidence() {
    if (evidenceState.status === "ready") {
      setEvidenceState({
        status: "idle",
        payload: null,
        error: null,
      });
      return;
    }

    try {
      setEvidenceState({
        status: "loading",
        payload: null,
        error: null,
      });
      const payload = await fetchCandidateEvidence({ candidateId: candidate.id });
      setEvidenceState({
        status: "ready",
        payload,
        error: null,
      });
    } catch (error) {
      setEvidenceState({
        status: "error",
        payload: null,
        error: "Candidate evidence could not be loaded.",
      });
    }
  }

  return (
    <div className="rounded-2xl border border-stone-200 bg-stone-50 px-3 py-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm font-medium text-stone-950">{candidate.name}</p>
        <span className="rounded-full bg-white px-3 py-1 text-[11px] uppercase tracking-[0.16em] text-stone-700">
          {formatEvidenceTier(candidate.evidence_tier)}
        </span>
      </div>
      <p className="mt-2 text-sm leading-6 text-stone-700">
        {candidate.evidence_note || "Evidence details are not loaded yet."}
      </p>
      {candidate.source_url ? (
        <a
          className="mt-2 inline-flex text-xs uppercase tracking-[0.16em] text-cyan-900 underline-offset-4 hover:underline"
          href={candidate.source_url}
          rel="noreferrer"
          target="_blank"
        >
          Open Candidate Source
        </a>
      ) : null}
      {votingSummary ? (
        <div className="mt-3 rounded-2xl border border-cyan-900/10 bg-white px-3 py-3">
          <p className="text-[11px] uppercase tracking-[0.18em] text-cyan-900">
            Recorded Votes
          </p>
          <div className="mt-3 grid gap-2 sm:grid-cols-2">
            <MiniMetric
              label="Eligible votes"
              value={formatNumber(votingSummary.eligible_vote_count)}
            />
            <MiniMetric
              label="Interpreted"
              value={formatNumber(votingSummary.interpreted_vote_count)}
            />
          </div>
          {votingSummary.top_domains?.length ? (
            <div className="mt-3 flex flex-wrap gap-2">
              {votingSummary.top_domains.map((domain) => (
                <span
                  className="rounded-full bg-cyan-50 px-3 py-1 text-[11px] uppercase tracking-[0.14em] text-cyan-950"
                  key={domain.domain}
                >
                  {formatDomainLabel(domain.domain)} - {domain.vote_count}
                </span>
              ))}
            </div>
          ) : null}
          <p className="mt-3 text-xs leading-5 text-stone-500">
            Window {formatDate(votingSummary.window_start)} to {formatDate(votingSummary.window_end)}
          </p>
        </div>
      ) : null}
      {selectedIssueReads.length ? (
        <div className="mt-3 rounded-2xl border border-stone-200 bg-white px-3 py-3">
          <p className="text-[11px] uppercase tracking-[0.18em] text-stone-500">
            Selected Issue Evidence
          </p>
          <div className="mt-2 grid gap-2">
            {selectedIssueReads.map((read) => (
              <p className="text-sm leading-6 text-stone-700" key={read.domain}>
                <span className="font-medium text-stone-950">{formatDomainLabel(read.domain)}:</span>{" "}
                {read.text}
              </p>
            ))}
          </div>
        </div>
      ) : null}
      {!votingSummary ? (
        <div className="mt-3 rounded-2xl border border-stone-200 bg-white px-3 py-3">
          <p className="text-[11px] uppercase tracking-[0.18em] text-stone-500">
            Candidate Evidence Type
          </p>
          {candidateEvidenceSummary?.total_count > 0 ? (
            <>
              <p className="mt-2 text-sm leading-6 text-stone-700">
                {formatNumber(candidateEvidenceSummary.total_count)} reviewed sourced record{candidateEvidenceSummary.total_count === 1 ? "" : "s"} loaded across {formatNumber(candidateEvidenceSummary.issue_domain_count)} issue area{candidateEvidenceSummary.issue_domain_count === 1 ? "" : "s"}. These stay separate from recorded-vote evidence.
              </p>
              <button
                className="mt-3 rounded-full border border-stone-300 bg-stone-50 px-3 py-2 text-xs uppercase tracking-[0.16em] text-stone-800 transition hover:border-cyan-800 hover:bg-cyan-50 hover:text-cyan-950 focus:outline-none focus:ring-2 focus:ring-cyan-800 focus:ring-offset-2"
                onClick={toggleCandidateEvidence}
                type="button"
              >
                {evidenceState.status === "ready" ? "Hide Evidence" : "View Evidence"}
              </button>
              <CandidateEvidenceDetails evidenceState={evidenceState} />
            </>
          ) : (
            <p className="mt-2 text-sm leading-6 text-stone-700">
              Insufficient evidence: no recorded governing behavior, reviewed stated position, or reviewed institutional record is loaded for this candidate yet.
            </p>
          )}
        </div>
      ) : null}
      {linkedLegislator ? (
        <button
          className="mt-3 rounded-full border border-cyan-800 bg-white px-3 py-2 text-xs uppercase tracking-[0.16em] text-cyan-900 transition hover:bg-cyan-900 hover:text-white focus:outline-none focus:ring-2 focus:ring-cyan-800 focus:ring-offset-2"
          onClick={() => onSelectLegislator?.(linkedLegislator)}
          type="button"
        >
          Open Voting Record
        </button>
      ) : null}
    </div>
  );
}

function buildSelectedIssueCandidateReads({ candidateEvidenceSummary, hasVotingSummary, preferences }) {
  const selectedDomains = Object.keys(preferences || {});
  if (!selectedDomains.length) {
    return [];
  }

  const issueDomainMap = new Map(
    (candidateEvidenceSummary?.issue_domains || []).map((row) => [row.domain, row]),
  );

  return selectedDomains.map((domain) => {
    if (hasVotingSummary) {
      return {
        domain,
        text: "Recorded-vote evidence is available through this candidate's linked voting record.",
      };
    }

    const row = issueDomainMap.get(domain);
    if (!row || !row.total_count) {
      return {
        domain,
        text: "insufficient evidence loaded for this candidate.",
      };
    }

    const statedCount = row.tier_counts?.sourced_stated_position || 0;
    const institutionalCount = row.tier_counts?.institutional_record || 0;
    const parts = [];
    if (institutionalCount) {
      parts.push(`${formatNumber(institutionalCount)} institutional record${institutionalCount === 1 ? "" : "s"}`);
    }
    if (statedCount) {
      parts.push(`${formatNumber(statedCount)} stated-position record${statedCount === 1 ? "" : "s"}`);
    }

    return {
      domain,
      text: parts.length ? `${parts.join(" and ")} loaded.` : "reviewed evidence loaded.",
    };
  });
}

function CandidateEvidenceDetails({ evidenceState }) {
  if (evidenceState.status === "idle") {
    return null;
  }
  if (evidenceState.status === "loading") {
    return (
      <p className="mt-3 text-sm leading-6 text-stone-600">
        Loading sourced evidence...
      </p>
    );
  }
  if (evidenceState.status === "error") {
    return (
      <p className="mt-3 rounded-2xl border border-amber-200 bg-amber-50 px-3 py-3 text-sm leading-6 text-amber-900">
        {evidenceState.error}
      </p>
    );
  }

  const evidenceRows = evidenceState.payload?.evidence || [];
  if (!evidenceRows.length) {
    return (
      <p className="mt-3 rounded-2xl border border-stone-200 bg-stone-50 px-3 py-3 text-sm leading-6 text-stone-700">
        No candidate evidence rows are loaded for this candidate yet.
      </p>
    );
  }

  return (
    <div className="mt-3 grid gap-2">
      {evidenceRows.map((row) => (
        <article className="rounded-2xl border border-stone-200 bg-stone-50 px-3 py-3" key={row.id}>
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full bg-white px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] text-stone-700">
              {formatEvidenceTypeLabel(row.evidence_tier)}
            </span>
            {row.issue_domain ? (
              <span className="rounded-full bg-cyan-50 px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] text-cyan-950">
                {formatDomainLabel(row.issue_domain)}
              </span>
            ) : null}
            <span className="rounded-full bg-white px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] text-stone-600">
              {row.confidence} confidence
            </span>
          </div>
          <p className="mt-2 text-sm leading-6 text-stone-800">
            {row.neutral_summary}
          </p>
          <a
            className="mt-2 inline-flex text-xs uppercase tracking-[0.16em] text-cyan-900 underline-offset-4 hover:underline"
            href={row.source_url}
            rel="noreferrer"
            target="_blank"
          >
            Open Source
          </a>
        </article>
      ))}
    </div>
  );
}

function MiniMetric({ label, value }) {
  return (
    <div>
      <p className="font-serif text-[1.45rem] leading-none text-stone-950">{value}</p>
      <p className="mt-1 text-[11px] uppercase tracking-[0.16em] text-stone-500">{label}</p>
    </div>
  );
}

function LegislatorCard({ accent, heading, legislator, onSelectLegislator }) {
  return (
    <article className="rounded-[1.5rem] border border-stone-200 bg-white px-5 py-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.7)]">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-xs uppercase tracking-[0.25em] text-stone-500">{heading}</p>
        <span className={`rounded-full px-3 py-1 text-[11px] uppercase tracking-[0.22em] ${accent}`}>
          {formatParty(legislator.party)}
        </span>
      </div>
      <h4 className="mt-3 font-serif text-[1.75rem] leading-[1] text-stone-950 sm:text-[2.1rem] sm:leading-[0.98]">
        {legislator.name_display}
      </h4>
      <p className="mt-2 text-sm text-stone-600">
        {formatChamber(legislator.chamber)} - {legislator.state}
      </p>
      <dl className="mt-4 grid gap-4 sm:grid-cols-2">
        <Meta label="Bioguide" value={legislator.bioguide_id} />
        <Meta label="Party" value={formatParty(legislator.party)} />
        <Meta label="Chamber" value={legislator.chamber} />
        <Meta
          label="District"
          value={legislator.district ? `${legislator.state}-${legislator.district}` : "Statewide"}
        />
      </dl>
      {onSelectLegislator ? (
        <div className="mt-4">
          <button
            className="rounded-full bg-stone-900 px-4 py-2 text-xs uppercase tracking-[0.22em] text-stone-100"
            aria-label={`Open profile for ${legislator.name_display}`}
            onClick={() => onSelectLegislator(legislator)}
            type="button"
          >
            Open Profile
          </button>
        </div>
      ) : null}
    </article>
  );
}

function Meta({ label, value }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-[0.2em] text-stone-500">{label}</dt>
      <dd className="mt-1 text-sm text-stone-700">{value}</dd>
    </div>
  );
}

function getComparePresetClass(isSelected) {
  const base =
    "rounded-full border px-4 py-2 text-xs uppercase tracking-[0.22em] transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cyan-900";
  if (isSelected) {
    return `${base} border-cyan-900 bg-cyan-900 text-white shadow-[0_10px_24px_rgba(22,78,99,0.22)]`;
  }

  return `${base} border-white bg-white text-cyan-900 hover:border-cyan-800/30 hover:bg-cyan-100 hover:text-cyan-950`;
}

function getLookupNoticeClass(severity) {
  if (severity === "warning") {
    return "border-amber-200 bg-amber-50 text-amber-950";
  }
  if (severity === "info") {
    return "border-cyan-900/15 bg-cyan-50 text-cyan-950";
  }
  return "border-stone-200 bg-stone-50 text-stone-800";
}

function formatLookupState(value) {
  return String(value || "unknown")
    .split("_")
    .map((segment) => segment[0].toUpperCase() + segment.slice(1))
    .join(" ");
}

function formatChamber(chamber) {
  return chamber ? chamber[0].toUpperCase() + chamber.slice(1) : "";
}

function formatParty(party) {
  return party === "D" ? "Democrat" : party === "R" ? "Republican" : party;
}

function formatRaceOffice(race) {
  if (race.chamber === "house" && race.district) {
    return `${race.state}-${race.district}`;
  }
  if (race.chamber === "senate") {
    return `${race.state} statewide`;
  }
  return race.state || "Federal";
}

function formatRaceStatus(status) {
  return String(status || "upcoming")
    .split("_")
    .map((segment) => segment[0].toUpperCase() + segment.slice(1))
    .join(" ");
}

function formatEvidenceTier(tier) {
  if (tier === "recorded_governing_behavior") {
    return "Recorded behavior";
  }
  if (tier === "institutional_record") {
    return "Institutional record";
  }
  if (tier === "sourced_stated_position") {
    return "Stated position";
  }
  return "Insufficient evidence";
}

function formatEvidenceTypeLabel(tier) {
  if (tier === "recorded_governing_behavior") {
    return "Recorded votes";
  }
  if (tier === "institutional_record") {
    return "Institutional record";
  }
  if (tier === "sourced_stated_position") {
    return "Stated position";
  }
  return "Insufficient evidence";
}

function formatNumber(value) {
  if (typeof value !== "number") {
    return "0";
  }
  return new Intl.NumberFormat("en-US").format(value);
}

function formatDate(value) {
  if (!value) {
    return "date not loaded";
  }
  return String(value).slice(0, 10);
}

function buildZipSuggestion(zips) {
  const values = zips
    .map((row) => row.zip)
    .filter(Boolean)
    .slice(0, 3);

  if (!values.length) {
    return "";
  }

  return values.join(", ");
}
