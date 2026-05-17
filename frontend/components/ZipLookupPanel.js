"use client";

import { useEffect, useState } from "react";

import { fetchSupportedZips, fetchZipLookup, fetchZipRaces } from "../lib/api";

const DEFAULT_ZIP = "27701";

export default function ZipLookupPanel({
  onComparePair,
  onSelectLegislator,
  variant = "standard",
}) {
  const [zipCode, setZipCode] = useState(DEFAULT_ZIP);
  const [state, setState] = useState({
    status: "idle",
    payload: null,
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
        error: "Enter a valid 5-digit ZIP code.",
      });
      return;
    }

    try {
      setState({
        status: "loading",
        payload: null,
        error: null,
      });

      const payload = await fetchZipLookup({ zipCode: nextZipCode });
      loadZipRaces(nextZipCode);
      setSelectedComparisonPreset("house_first_senator");
      setState({
        status: "ready",
        payload,
        error: null,
      });
      if (payload.house_rep) {
        onSelectLegislator?.(payload.house_rep);
      }
      if (payload.house_rep && payload.senators?.[0]) {
        onComparePair?.({
          left: payload.house_rep,
          right: payload.senators[0],
        });
      }
    } catch (error) {
      const suggestions = buildZipSuggestion(supportedZips.zips);
      setState({
        status: "error",
        payload: null,
        error: suggestions
          ? `That ZIP code is not in the loaded map yet. Try ${suggestions}.`
          : "That ZIP code is not in the loaded map yet.",
      });
      setRaceState({
        status: "idle",
        payload: null,
        error: null,
      });
    }
  }

  async function loadZipRaces(nextZipCode) {
    try {
      setRaceState({
        status: "loading",
        payload: null,
        error: null,
      });
      const payload = await fetchZipRaces({ zipCode: nextZipCode });
      setRaceState({
        status: "ready",
        payload,
        error: null,
      });
    } catch (error) {
      setRaceState({
        status: "error",
        payload: null,
        error: "Upcoming race data is not loaded for this ZIP yet.",
      });
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
    ? "rounded-[2rem] border border-cyan-900/15 bg-white p-5 shadow-[0_24px_70px_rgba(15,23,42,0.16)] lg:p-6"
    : "mt-8 rounded-[2rem] border border-stone-200 bg-white p-5 shadow-[0_16px_40px_rgba(15,23,42,0.08)] lg:p-6";

  return (
    <section className={sectionClassName}>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-stone-500">
            Start Here
          </p>
          <h3 className="mt-2 font-serif text-[2.05rem] leading-[0.98] text-stone-950 sm:text-[2.65rem] sm:leading-[0.95]">
            Start with your ZIP.
          </h3>
          <p className="mt-3 max-w-2xl text-[15px] leading-7 text-stone-700">
            Load your House member and senators, then compare their records against the same issues.
          </p>
        </div>
        <p className="text-xs uppercase tracking-[0.25em] text-stone-500">
          {supportedZips.status === "ready" && supportedZips.zips.length
            ? `Try ${buildZipSuggestion(supportedZips.zips)}`
            : "Loaded ZIPs appear here"}
        </p>
      </div>

      <form className="mt-5 flex flex-col gap-3 sm:flex-row" onSubmit={handleLookup}>
        <label className="sr-only" htmlFor="zip-code-input">
          ZIP code
        </label>
        <input
          id="zip-code-input"
          className="h-12 flex-1 rounded-full border border-stone-300 bg-stone-50 px-5 text-sm text-stone-900 outline-none ring-0 placeholder:text-stone-500"
          inputMode="numeric"
          maxLength={5}
          onChange={(event) => setZipCode(event.target.value.replace(/\D/g, "").slice(0, 5))}
          placeholder="Enter ZIP code"
          value={zipCode}
        />
        <button
          className="h-12 rounded-full bg-cyan-900 px-6 text-sm uppercase tracking-[0.25em] text-white shadow-[0_10px_24px_rgba(22,78,99,0.22)]"
          type="submit"
        >
          Show My Reps
        </button>
      </form>

      <div className="mt-5 flex flex-col gap-3 rounded-[1.5rem] bg-stone-950 px-5 py-5 text-stone-100 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-stone-400">
            Result
          </p>
          <p className="mt-3 text-lg text-stone-50">
            {state.status === "idle" ? "Ready to lookup" : null}
            {state.status === "loading" ? "Looking up legislators..." : null}
            {state.status === "error" ? "Lookup unavailable" : null}
            {state.status === "ready"
              ? `ZIP ${state.payload.zip} maps to ${state.payload.state}-${state.payload.district}.`
              : null}
          </p>
        </div>
        <p className="text-sm leading-7 text-stone-300">
          {state.status === "idle" ? "Run a ZIP lookup to load representatives." : null}
          {state.status === "loading" ? "Loading House and Senate results." : null}
          {state.status === "error" ? state.error : null}
          {state.status === "ready"
            ? `${state.payload.senators.length + (state.payload.house_rep ? 1 : 0)} officials ready to inspect.`
            : null}
        </p>
      </div>

      {state.status === "ready" ? (
        <div className="mt-5">
          <div className="mb-4 flex flex-wrap gap-3 rounded-[1.25rem] border border-cyan-900/10 bg-cyan-50 px-4 py-4">
            <p className="w-full text-sm leading-6 text-stone-700">
              Your House profile opened below. Use these buttons to change the comparison pair.
            </p>
            {state.payload.house_rep && state.payload.senators[0] ? (
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
            {state.payload.house_rep && state.payload.senators[1] ? (
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
            {state.payload.senators[0] && state.payload.senators[1] ? (
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
            <LegislatorCard
              accent="bg-cyan-100 text-cyan-900"
              heading="House Representative"
              legislator={state.payload.house_rep}
              onSelectLegislator={onSelectLegislator}
            />
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
          </div>

          <UpcomingRacePanel
            onSelectLegislator={onSelectLegislator}
            raceState={raceState}
          />
        </div>
      ) : null}

      {supportedZips.status === "ready" && supportedZips.zips.length > 0 ? (
        <div className="mt-5 rounded-[1.25rem] border border-stone-200 bg-stone-50 px-4 py-4">
          <p className="text-xs uppercase tracking-[0.24em] text-stone-500">
            Loaded ZIP Coverage
          </p>
          <p className="mt-2 text-sm leading-6 text-stone-700">
            Showing {supportedZips.zips.length} loaded ZIP {supportedZips.zips.length === 1 ? "mapping" : "mappings"}
            {supportedZips.dataSource ? ` from ${supportedZips.dataSource}.` : "."}
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

function UpcomingRacePanel({ onSelectLegislator, raceState }) {
  if (raceState.status === "idle") {
    return null;
  }

  const races = raceState.payload?.races || [];

  return (
    <div className="mt-5 rounded-[1.5rem] border border-stone-200 bg-stone-50 px-4 py-4">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.26em] text-stone-500">
            Upcoming Federal Races
          </p>
          <h4 className="mt-2 font-serif text-[1.85rem] leading-none text-stone-950">
            Ballot preview
          </h4>
        </div>
        <p className="max-w-xl text-sm leading-6 text-stone-600">
          This first slice shows office context before live candidate filings are loaded. Current officeholders link back to recorded-vote evidence.
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
                  race.candidates.map((candidate) => (
                    <RaceCandidateCard
                      candidate={candidate}
                      key={candidate.id}
                      onSelectLegislator={onSelectLegislator}
                    />
                  ))
                ) : (
                  <p className="rounded-2xl border border-stone-200 bg-stone-50 px-3 py-3 text-sm leading-6 text-stone-700">
                    Candidate roster is not loaded yet. The race row is shown as ballot structure only.
                  </p>
                )}
              </div>
            </article>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function RaceCandidateCard({ candidate, onSelectLegislator }) {
  const linkedLegislator = candidate.linked_legislator;
  const votingSummary = candidate.voting_summary;
  const candidateEvidenceSummary = candidate.candidate_evidence_summary;

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
      {!votingSummary ? (
        <div className="mt-3 rounded-2xl border border-stone-200 bg-white px-3 py-3">
          <p className="text-[11px] uppercase tracking-[0.18em] text-stone-500">
            Candidate Evidence
          </p>
          {candidateEvidenceSummary?.total_count > 0 ? (
            <p className="mt-2 text-sm leading-6 text-stone-700">
              {formatNumber(candidateEvidenceSummary.total_count)} sourced evidence record{candidateEvidenceSummary.total_count === 1 ? "" : "s"} loaded across {formatNumber(candidateEvidenceSummary.issue_domain_count)} issue area{candidateEvidenceSummary.issue_domain_count === 1 ? "" : "s"}.
            </p>
          ) : (
            <p className="mt-2 text-sm leading-6 text-stone-700">
              No recorded governing behavior or sourced issue-position evidence is loaded yet.
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

function formatDomainLabel(domain) {
  return String(domain || "")
    .toLowerCase()
    .split("_")
    .map((segment) => segment[0]?.toUpperCase() + segment.slice(1))
    .join(" ");
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
