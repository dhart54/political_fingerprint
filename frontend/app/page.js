"use client";

import { useEffect, useState } from "react";

import AlignmentPanel from "../components/AlignmentPanel";
import IssuePreferencePanel from "../components/IssuePreferencePanel";
import ComparisonPanel from "../components/ComparisonPanel";
import LegislatorPicker from "../components/LegislatorPicker";
import PositionByIssue from "../components/PositionByIssue";
import ProfileQuickRead from "../components/ProfileQuickRead";
import ZipLookupPanel, { UpcomingRacePanel } from "../components/ZipLookupPanel";
import { fetchCoverageMetadata } from "../lib/api";

const DEFAULT_LEGISLATOR = {
  id: "leg_aaron_bean",
  bioguide_id: "B001317",
  name_display: "Aaron Bean",
  chamber: "house",
  state: "FL",
  district: "04",
  party: "R",
};

const DEFAULT_COMPARE_RIGHT = {
  id: "leg_adam_smith",
  bioguide_id: "S000510",
  name_display: "Adam Smith",
  chamber: "house",
  state: "WA",
  district: "09",
  party: "D",
};

export default function HomePage() {
  const [selectedLegislator, setSelectedLegislator] = useState(DEFAULT_LEGISLATOR);
  const [issuePreferences, setIssuePreferences] = useState({});
  const [profileRead, setProfileRead] = useState(null);
  const [evidenceRequest, setEvidenceRequest] = useState(null);
  const [comparisonSeed, setComparisonSeed] = useState({
    left: DEFAULT_LEGISLATOR,
    right: DEFAULT_COMPARE_RIGHT,
  });
  const [coverageMetadata, setCoverageMetadata] = useState(null);
  const [zipRaceState, setZipRaceState] = useState({
    status: "idle",
    payload: null,
    error: null,
  });

  useEffect(() => {
    let active = true;

    async function loadCoverageMetadata() {
      try {
        const payload = await fetchCoverageMetadata();
        if (active) {
          setCoverageMetadata(payload);
        }
      } catch (error) {
        if (active) {
          setCoverageMetadata(null);
        }
      }
    }

    loadCoverageMetadata();

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    setProfileRead(null);
  }, [selectedLegislator.id]);

  return (
    <main className="min-h-screen bg-[#f7f4ec] text-stone-900">
      <section className="mx-auto max-w-[1440px] px-4 py-4 sm:px-6 lg:py-5">
        <div className="grid gap-3 lg:grid-cols-[minmax(0,0.55fr)_minmax(520px,1.45fr)] lg:items-start">
          <div className="rounded-2xl border border-stone-200 bg-white/75 px-4 py-2.5 shadow-[0_8px_22px_rgba(15,23,42,0.05)]">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.24em] text-cyan-800">
                  Political Fingerprint
                </p>
                <h1 className="mt-1 font-serif text-[1.65rem] leading-[1] text-stone-950 sm:text-[2rem] lg:text-[2.25rem]">
                  Voting record, explained.
                </h1>
              </div>
              <p className="max-w-[300px] text-sm leading-5 text-stone-700">
                Start with the clearest reviewed patterns, then inspect the proof.
              </p>
            </div>
            <div className="mt-2 grid gap-2 sm:grid-cols-3">
              <HeroStat value={formatNumber(coverageMetadata?.legislator_count, "548")} label="legislators" />
              <HeroStat value={formatNumber(coverageMetadata?.eligible_roll_call_count, "8")} label="roll calls" />
              <HeroStat value={formatPercent(coverageMetadata?.source_url_share)} label="source links" />
            </div>
          </div>
          <ZipLookupPanel
            onComparePair={setComparisonSeed}
            onRaceStateChange={setZipRaceState}
            onSelectLegislator={setSelectedLegislator}
            showElectionContext={false}
            variant="hero"
          />
        </div>

        <section className="mt-3 rounded-2xl border border-stone-200 bg-white px-4 py-3 shadow-[0_8px_24px_rgba(15,23,42,0.06)] lg:px-5">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div className="min-w-0">
              <p className="text-xs uppercase tracking-[0.2em] text-stone-500">
                Current Profile
              </p>
              <h2 className="mt-1 truncate font-serif text-[1.75rem] leading-none text-stone-950 sm:text-[2.15rem]">
                {selectedLegislator.name_display}
              </h2>
            </div>
            <div className="flex flex-wrap gap-2 text-xs uppercase tracking-[0.14em] text-stone-700">
              <span className="rounded-full border border-stone-200 bg-stone-50 px-3 py-1.5">
                {formatChamber(selectedLegislator.chamber)}
              </span>
              <span className="rounded-full border border-stone-200 bg-stone-50 px-3 py-1.5">
                {selectedLegislator.party} - {selectedLegislator.state}
                {selectedLegislator.district ? `-${selectedLegislator.district}` : " statewide"}
              </span>
              <a className="rounded-full border border-cyan-900/20 bg-cyan-50 px-3 py-1.5 text-cyan-900" href="#position-by-issue">
                Jump to evidence
              </a>
            </div>
          </div>
        </section>

        <ProfileQuickRead
          legislator={selectedLegislator}
          onInspectDomain={(domain) =>
            setEvidenceRequest({
              domain,
              requestedAt: Date.now(),
            })
          }
          onProfileRead={setProfileRead}
        />

        <PositionByIssue
          evidenceRequest={evidenceRequest}
          legislator={selectedLegislator}
          legislatorId={selectedLegislator.id}
          title={`${selectedLegislator.name_display}'s strongest issue evidence`}
        />

        <details className="mt-5 rounded-2xl border border-stone-200 bg-white px-4 py-4 shadow-[0_10px_28px_rgba(15,23,42,0.06)]" open={Object.keys(issuePreferences).length > 0}>
          <summary className="cursor-pointer text-sm font-semibold uppercase tracking-[0.18em] text-stone-700 marker:text-cyan-900">
            Tools: preferences, comparison, and switching officials
          </summary>
          <div className="mt-4 grid gap-4 border-t border-stone-200 pt-4">
            <IssuePreferencePanel
              positionRows={profileRead?.positions?.positions || []}
              preferences={issuePreferences}
              onChange={setIssuePreferences}
            />

            <AlignmentPanel
              legislator={selectedLegislator}
              preferences={issuePreferences}
              onInspectDomain={(domain) =>
                setEvidenceRequest({
                  domain,
                  requestedAt: Date.now(),
                })
              }
            />

            <details className="rounded-xl border border-stone-200 bg-stone-50 px-3 py-3">
              <summary className="cursor-pointer text-sm font-medium text-stone-900 marker:text-cyan-900">
                Compare with another official
              </summary>
              <div className="mt-3 border-t border-stone-200 pt-3">
                <ComparisonPanel
                  defaultLeftLegislator={selectedLegislator}
                  defaultRightLegislator={DEFAULT_COMPARE_RIGHT}
                  onInspectDomain={(legislator, domain) => {
                    setSelectedLegislator(legislator);
                    setEvidenceRequest({
                      domain,
                      requestedAt: Date.now(),
                    });
                  }}
                  preferences={issuePreferences}
                  seedPair={comparisonSeed}
                />
              </div>
            </details>

            {zipRaceState.status === "ready" && (zipRaceState.payload?.races || []).length > 0 ? (
              <UpcomingRacePanel
                onSelectLegislator={setSelectedLegislator}
                preferences={issuePreferences}
                raceState={zipRaceState}
              />
            ) : null}

            <details className="rounded-xl border border-stone-200 bg-stone-50 px-3 py-3">
              <summary className="cursor-pointer text-sm font-medium text-stone-900 marker:text-cyan-900">
                Search or switch official
              </summary>
              <div className="mt-3 border-t border-stone-200 pt-3">
                <LegislatorPicker
                  onSelect={setSelectedLegislator}
                  selectedLegislator={selectedLegislator}
                />
              </div>
            </details>
          </div>
        </details>

        <footer className="mt-8 border-t border-stone-300/80 py-6">
          <div className="grid gap-3 md:grid-cols-3">
            <TrustNote
              eyebrow="Method"
              text="Procedural votes may appear as context, but they do not count toward issue reads or alignment labels."
            />
            <TrustNote
              eyebrow="Evidence"
              text="Open Votes and Inspect Votes show the roll calls, vote position, classification reason, and source link when available."
            />
            <TrustNote
              eyebrow="Limits"
              text="Limited, ambiguous, and not-voting rows remain inspectable but do not drive support or opposition conclusions."
            />
          </div>
          <p className="mt-4 text-sm leading-6 text-stone-600 md:text-right">
            Data window: {formatDate(coverageMetadata?.window_start)} to {formatDate(coverageMetadata?.window_end)}.
          </p>
        </footer>
      </section>
    </main>
  );
}

function HeroStat({ value, label }) {
  return (
    <div className="border-l border-cyan-700/30 pl-3">
      <p className="font-serif text-[1.5rem] leading-none text-cyan-900 sm:text-[1.8rem]">{value}</p>
      <p className="mt-1 text-[11px] uppercase tracking-[0.16em] text-stone-600">{label}</p>
    </div>
  );
}

function formatNumber(value, fallback) {
  if (typeof value !== "number") {
    return fallback;
  }

  return new Intl.NumberFormat("en-US").format(value);
}

function formatPercent(value) {
  if (typeof value !== "number") {
    return "--";
  }

  return `${Math.round(value * 100)}%`;
}

function formatDate(value) {
  if (!value) {
    return "unknown";
  }

  return String(value).slice(0, 10);
}

function TrustNote({ eyebrow, text }) {
  return (
    <div className="rounded-2xl border border-stone-200 bg-white/70 px-4 py-4">
      <p className="text-xs uppercase tracking-[0.24em] text-cyan-800">{eyebrow}</p>
      <p className="mt-2 text-sm leading-6 text-stone-600">{text}</p>
    </div>
  );
}

function formatChamber(chamber) {
  return chamber ? chamber[0].toUpperCase() + chamber.slice(1) : "";
}
