"use client";

import { useState } from "react";

import ZipLookupPanel from "./ZipLookupPanel";

export default function ZipLookupStateFixture() {
  const [selectedLegislator, setSelectedLegislator] = useState(null);
  const [selectCount, setSelectCount] = useState(0);

  function handleSelectLegislator(legislator) {
    setSelectedLegislator(legislator);
    setSelectCount((value) => value + 1);
  }

  return (
    <main className="min-h-screen bg-stone-100 p-6 text-stone-900">
      <div className="mx-auto max-w-4xl">
        <h1 className="font-serif text-3xl text-stone-950">ZIP lookup state fixture</h1>
        <p className="mt-2 text-sm leading-6 text-stone-700" data-testid="zip-lookup-selected">
          Selected: {selectedLegislator ? selectedLegislator.name_display : "none"}; count: {selectCount}
        </p>
        <ZipLookupPanel
          onSelectLegislator={handleSelectLegislator}
          showElectionContext={false}
          variant="standard"
        />
        <section id="manual-representative-search" className="mt-6 rounded-xl border border-stone-200 bg-white p-4">
          <h2 className="text-sm font-semibold uppercase tracking-[0.18em] text-stone-700">
            Manual representative search
          </h2>
          <p className="mt-2 text-sm leading-6 text-stone-600">
            Search fallback fixture target.
          </p>
        </section>
      </div>
    </main>
  );
}
