"use client";

import { useState } from "react";

import HealthStatus from "../components/HealthStatus";
import DriftIndicator from "../components/DriftIndicator";
import FingerprintRadar from "../components/FingerprintRadar";
import ComparisonPanel from "../components/ComparisonPanel";
import LegislatorPicker from "../components/LegislatorPicker";
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

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_#f4eee1,_#e6dbc1_50%,_#d5c3a2)] text-stone-900">
      <section className="mx-auto flex min-h-screen max-w-[1180px] flex-col justify-center px-5 py-16 sm:px-6 lg:py-20">
        <p className="mb-4 text-sm uppercase tracking-[0.35em] text-stone-600">
          Political Fingerprint
        </p>
        <h1 className="max-w-[980px] font-serif text-5xl leading-[0.95] sm:text-7xl">
          See what issues your representative actually spends votes on.
        </h1>
        <p className="mt-6 max-w-[740px] text-xl leading-8 text-stone-700">
          A fast behavioral profile built from categorized policy votes, precomputed
          issue emphasis, and change-over-time metrics.
        </p>
        <div className="mt-10 grid gap-4 lg:grid-cols-3">
          <article className="rounded-3xl border border-stone-300/70 bg-white/65 p-5 shadow-[0_18px_60px_rgba(72,52,24,0.08)] backdrop-blur">
            <p className="text-xs uppercase tracking-[0.3em] text-stone-500">
              Issue Focus
            </p>
            <p className="mt-3 text-base leading-7 text-stone-700">
              See which policy domains dominate this legislator's recent voting record, with chamber comparison built in.
            </p>
          </article>
          <article className="rounded-3xl border border-stone-300/70 bg-white/65 p-5 shadow-[0_18px_60px_rgba(72,52,24,0.08)] backdrop-blur">
            <p className="text-xs uppercase tracking-[0.3em] text-stone-500">
              Change Over Time
            </p>
            <p className="mt-3 text-base leading-7 text-stone-700">
              Measure whether their recent issue mix looks stable or has shifted meaningfully across the last two years.
            </p>
          </article>
          <article className="rounded-3xl border border-stone-300/70 bg-white/65 p-5 shadow-[0_18px_60px_rgba(72,52,24,0.08)] backdrop-blur">
            <p className="text-xs uppercase tracking-[0.3em] text-stone-500">
              Who Represents Me
            </p>
            <p className="mt-3 text-base leading-7 text-stone-700">
              Start with your ZIP code, then inspect the voting behavior of your House member and senators side by side.
            </p>
          </article>
        </div>
        <LegislatorPicker
          onSelect={setSelectedLegislator}
          selectedLegislator={selectedLegislator}
        />
        <FingerprintRadar
          legislatorId={selectedLegislator.id}
          title={selectedLegislator.name_display}
        />
        <DriftIndicator legislatorId={selectedLegislator.id} />
        <SummaryPanel legislatorId={selectedLegislator.id} />
        <ComparisonPanel
          defaultLeftLegislator={selectedLegislator}
          defaultRightLegislator={DEFAULT_COMPARE_RIGHT}
        />
        <ZipLookupPanel />
        <HealthStatus />
      </section>
    </main>
  );
}
