"use client";

import { useEffect, useState } from "react";

import AlignmentPanel from "../components/AlignmentPanel";
import IssuePreferencePanel from "../components/IssuePreferencePanel";
import ComparisonPanel from "../components/ComparisonPanel";
import LegislatorPicker from "../components/LegislatorPicker";
import PositionByIssue from "../components/PositionByIssue";
import ProfileQuickRead from "../components/ProfileQuickRead";
import ZipLookupPanel from "../components/ZipLookupPanel";
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
  const [evidenceRequest, setEvidenceRequest] = useState(null);
  const [comparisonSeed, setComparisonSeed] = useState({
    left: DEFAULT_LEGISLATOR,
    right: DEFAULT_COMPARE_RIGHT,
  });
  const [coverageMetadata, setCoverageMetadata] = useState(null);

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

  return (
    <main className="min-h-screen bg-[#f7f4ec] text-stone-900">
      <section className="mx-auto max-w-[1440px] px-5 py-6 sm:px-6 lg:py-8">
        <div className="grid min-h-[calc(100vh-4rem)] gap-7 lg:grid-cols-[0.88fr_1.12fr] lg:items-center">
          <div className="max-w-[720px]">
            <p className="mb-4 text-sm uppercase tracking-[0.35em] text-cyan-800">
              Political Fingerprint
            </p>
            <h1 className="font-serif text-5xl leading-[0.95] text-stone-950 sm:text-[4.4rem] lg:text-[5.45rem]">
              In 60 seconds, see how your politicians vote.
            </h1>
            <p className="mt-5 max-w-[640px] text-[17px] leading-8 text-stone-700 sm:text-lg">
              Enter a ZIP code, open a representative or senator, and see their recent voting record by issue. The read is deterministic, neutral, and built from categorized policy votes.
            </p>
            <p className="mt-4 max-w-[640px] text-[14px] leading-7 text-stone-600">
              {buildCoverageRead(coverageMetadata)}
            </p>
            <div className="mt-7 grid gap-3 sm:grid-cols-3">
              <HeroStat value={formatNumber(coverageMetadata?.legislator_count, "548")} label="legislators loaded" />
              <HeroStat value={formatNumber(coverageMetadata?.eligible_roll_call_count, "8")} label="eligible roll calls" />
              <HeroStat value={formatPercent(coverageMetadata?.source_url_share)} label="source links" />
            </div>
          </div>
          <ZipLookupPanel
            onComparePair={setComparisonSeed}
            onSelectLegislator={setSelectedLegislator}
            variant="hero"
          />
        </div>

        <section className="mt-8 rounded-[2rem] border border-stone-200 bg-white px-5 py-5 shadow-[0_16px_40px_rgba(15,23,42,0.08)] lg:px-6">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-stone-500">
                Current Profile
              </p>
              <h2 className="mt-2 font-serif text-[2.75rem] leading-none text-stone-950">
                {selectedLegislator.name_display}
              </h2>
              <p className="mt-2 text-[15px] leading-6 text-stone-600">
                {formatChamber(selectedLegislator.chamber)} - {selectedLegislator.party} - {selectedLegislator.state}
                {selectedLegislator.district ? `-${selectedLegislator.district}` : " statewide"}
              </p>
            </div>
            <div className="grid gap-2 sm:grid-cols-3 lg:min-w-[520px]">
              <MiniStep label="1" value="Pick issues" />
              <MiniStep label="2" value="Compare records" />
              <MiniStep label="3" value="Inspect evidence" />
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
        />

        <IssuePreferencePanel
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

        <PositionByIssue
          evidenceRequest={evidenceRequest}
          legislatorId={selectedLegislator.id}
          title={`${selectedLegislator.name_display}'s voting pattern by issue`}
        />
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

        <LegislatorPicker
          onSelect={setSelectedLegislator}
          selectedLegislator={selectedLegislator}
        />

        <footer className="mt-8 border-t border-stone-300/80 py-6 text-sm leading-6 text-stone-600">
          <div className="grid gap-4 md:grid-cols-[1.2fr_0.8fr] md:items-start">
            <p>
              Political Fingerprint uses categorized policy votes, excludes procedural votes, and keeps issue alignment tied to interpreted roll-call evidence when available.
            </p>
            <p className="md:text-right">
              Data window: {formatDate(coverageMetadata?.window_start)} to {formatDate(coverageMetadata?.window_end)}.
            </p>
          </div>
        </footer>
      </section>
    </main>
  );
}

function HeroStat({ value, label }) {
  return (
    <div className="border-l border-cyan-700/30 pl-4">
      <p className="font-serif text-[2.4rem] leading-none text-cyan-900">{value}</p>
      <p className="mt-2 text-xs uppercase tracking-[0.2em] text-stone-600">{label}</p>
    </div>
  );
}

function buildCoverageRead(metadata) {
  if (!metadata) {
    return "Coverage context loads from the backend when available; local fallback data remains deterministic for development.";
  }

  return `Coverage window ${formatDate(metadata.window_start)} to ${formatDate(metadata.window_end)}. Procedural votes are excluded, and source links are tracked for evidence drilldowns.`;
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

function MiniStep({ label, value }) {
  return (
    <div className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3">
      <p className="text-xs uppercase tracking-[0.24em] text-cyan-800">Step {label}</p>
      <p className="mt-2 text-sm leading-5 text-stone-800">{value}</p>
    </div>
  );
}

function formatChamber(chamber) {
  return chamber ? chamber[0].toUpperCase() + chamber.slice(1) : "";
}
