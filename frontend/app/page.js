"use client";

import { useState } from "react";

import HealthStatus from "../components/HealthStatus";
import AlignmentPanel from "../components/AlignmentPanel";
import DriftIndicator from "../components/DriftIndicator";
import FingerprintRadar from "../components/FingerprintRadar";
import IssuePreferencePanel from "../components/IssuePreferencePanel";
import ComparisonPanel from "../components/ComparisonPanel";
import LegislatorPicker from "../components/LegislatorPicker";
import PositionByIssue from "../components/PositionByIssue";
import ProfileQuickRead from "../components/ProfileQuickRead";
import SummaryPanel from "../components/SummaryPanel";
import ZipLookupPanel from "../components/ZipLookupPanel";

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
  const [comparisonSeed, setComparisonSeed] = useState({
    left: DEFAULT_LEGISLATOR,
    right: DEFAULT_COMPARE_RIGHT,
  });

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
            <div className="mt-7 grid gap-3 sm:grid-cols-3">
              <HeroStat value="548" label="legislators loaded" />
              <HeroStat value="8" label="issue domains" />
              <HeroStat value="730" label="day window" />
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
              <MiniStep label="1" value="Position by issue" />
              <MiniStep label="2" value="Compare records" />
              <MiniStep label="3" value="Check context" />
            </div>
          </div>
        </section>

        <IssuePreferencePanel
          preferences={issuePreferences}
          onChange={setIssuePreferences}
        />

        <AlignmentPanel
          legislator={selectedLegislator}
          preferences={issuePreferences}
        />

        <ProfileQuickRead legislator={selectedLegislator} />

        <LegislatorPicker
          onSelect={setSelectedLegislator}
          selectedLegislator={selectedLegislator}
        />
        <PositionByIssue
          legislatorId={selectedLegislator.id}
          title={`${selectedLegislator.name_display}'s voting pattern by issue`}
        />
        <ComparisonPanel
          defaultLeftLegislator={selectedLegislator}
          defaultRightLegislator={DEFAULT_COMPARE_RIGHT}
          seedPair={comparisonSeed}
        />
        <FingerprintRadar
          legislatorId={selectedLegislator.id}
          title={selectedLegislator.name_display}
        />
        <DriftIndicator legislatorId={selectedLegislator.id} />
        <SummaryPanel legislatorId={selectedLegislator.id} />
        <HealthStatus />
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
