"use client";

import { useState } from "react";

import PositionByIssue from "./PositionByIssue";
import ProfileQuickRead from "./ProfileQuickRead";
import RecordAcrossCongressesPanel from "./RecordAcrossCongressesPanel";
import {
  goldenFixtureData,
  goldenIssueFixtureData,
  goldenLegislator,
  goldenRecordAcrossResponse,
  limitedEvidenceFixtureData,
  limitedEvidenceIssueFixtureData,
  limitedEvidenceLegislator,
} from "../lib/goldenRenderFixture.mjs";

export default function GoldenRenderFixture() {
  const [evidenceRequest, setEvidenceRequest] = useState({
    domain: "NATIONAL_SECURITY_FOREIGN",
    requestedAt: 1,
  });
  const [limitedEvidenceRequest, setLimitedEvidenceRequest] = useState({
    domain: "NATIONAL_SECURITY_FOREIGN",
    requestedAt: 1,
  });

  return (
    <main className="min-h-screen bg-[#f7f4ec] px-4 py-5 text-stone-900 sm:px-6">
      <section className="mx-auto max-w-[1440px]">
        <div className="rounded-2xl border border-cyan-900/20 bg-white px-4 py-4 shadow-[0_10px_28px_rgba(15,23,42,0.06)]">
          <p className="text-xs uppercase tracking-[0.24em] text-cyan-800">Golden render fixture</p>
          <h1 className="mt-2 font-serif text-[2rem] leading-tight text-stone-950">
            Golden public reads validation
          </h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-stone-700">
            This route is enabled only for local or CI validation. It renders deterministic fixture data through the same profile, issue, receipt, and Record Across surfaces used by the product.
          </p>
        </div>

        <section data-testid="golden-valerie-profile">
          <div className="mt-4 rounded-2xl border border-stone-200 bg-white px-4 py-3 shadow-[0_8px_24px_rgba(15,23,42,0.06)]">
            <p className="text-xs uppercase tracking-[0.2em] text-stone-500">Current Profile</p>
            <h2 className="mt-1 font-serif text-[2rem] leading-tight text-stone-950">{goldenLegislator.name_display}</h2>
            <p className="mt-1 text-sm leading-6 text-stone-600">
              Fixture profile for deterministic profile summary, issue card, expanded read, and receipt validation.
            </p>
          </div>
          <ProfileQuickRead
            fixtureData={goldenFixtureData}
            legislator={goldenLegislator}
            onInspectDomain={(domain) => setEvidenceRequest({ domain, requestedAt: Date.now() })}
            scope="all"
          />
          <PositionByIssue
            evidenceRequest={evidenceRequest}
            fixtureData={goldenIssueFixtureData}
            legislator={goldenLegislator}
            legislatorId={goldenLegislator.id}
            scope="all"
            title={`${goldenLegislator.name_display}'s golden issue evidence`}
          />
          <RecordAcrossCongressesPanel
            fixtureResponse={goldenRecordAcrossResponse}
            legislator={goldenLegislator}
            onInspectDomain={(domain) => setEvidenceRequest({ domain, requestedAt: Date.now() })}
          />
        </section>

        <section className="mt-5" data-testid="golden-limited-profile">
          <div className="rounded-2xl border border-amber-200 bg-white px-4 py-3 shadow-[0_8px_24px_rgba(15,23,42,0.06)]">
            <p className="text-xs uppercase tracking-[0.2em] text-amber-700">Limited evidence guard</p>
            <h2 className="mt-1 font-serif text-[1.8rem] leading-tight text-stone-950">
              One-sided limited evidence remains cautious
            </h2>
          </div>
          <ProfileQuickRead
            fixtureData={limitedEvidenceFixtureData}
            legislator={limitedEvidenceLegislator}
            onInspectDomain={(domain) => setLimitedEvidenceRequest({ domain, requestedAt: Date.now() })}
            scope="all"
          />
          <PositionByIssue
            evidenceRequest={limitedEvidenceRequest}
            fixtureData={limitedEvidenceIssueFixtureData}
            legislator={limitedEvidenceLegislator}
            legislatorId={limitedEvidenceLegislator.id}
            scope="all"
            title={`${limitedEvidenceLegislator.name_display}'s limited issue evidence`}
          />
        </section>
      </section>
    </main>
  );
}
