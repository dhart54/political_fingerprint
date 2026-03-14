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
  id: "leg_alex_morgan",
  bioguide_id: "H000001",
  name_display: "Alex Morgan",
  chamber: "house",
  state: "NC",
  district: "04",
  party: "D",
};

const DEFAULT_COMPARE_RIGHT = {
  id: "leg_jordan_lee",
  bioguide_id: "S000001",
  name_display: "Jordan Lee",
  chamber: "senate",
  state: "NC",
  district: null,
  party: "R",
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
          In 60 seconds, understand how this politician actually behaves.
        </h1>
        <p className="mt-6 max-w-[740px] text-lg leading-8 text-stone-700">
          Deterministic civic analytics built from categorized policy votes,
          precomputed metrics, and neutral summaries.
        </p>
        <div className="mt-10 grid gap-4 lg:grid-cols-3">
          <article className="rounded-3xl border border-stone-300/70 bg-white/65 p-5 shadow-[0_18px_60px_rgba(72,52,24,0.08)] backdrop-blur">
            <p className="text-xs uppercase tracking-[0.3em] text-stone-500">
              Fingerprint
            </p>
            <p className="mt-3 text-base leading-7 text-stone-700">
              Eight-domain vote emphasis with explicit zeroes and chamber median comparison.
            </p>
          </article>
          <article className="rounded-3xl border border-stone-300/70 bg-white/65 p-5 shadow-[0_18px_60px_rgba(72,52,24,0.08)] backdrop-blur">
            <p className="text-xs uppercase tracking-[0.3em] text-stone-500">
              Drift
            </p>
            <p className="mt-3 text-base leading-7 text-stone-700">
              Deterministic stability measurement across early and recent voting windows.
            </p>
          </article>
          <article className="rounded-3xl border border-stone-300/70 bg-white/65 p-5 shadow-[0_18px_60px_rgba(72,52,24,0.08)] backdrop-blur">
            <p className="text-xs uppercase tracking-[0.3em] text-stone-500">
              Lookup
            </p>
            <p className="mt-3 text-base leading-7 text-stone-700">
              ZIP-based representative and senator lookup backed by deterministic fixture data.
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
