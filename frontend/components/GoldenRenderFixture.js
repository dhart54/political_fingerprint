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
import {
  editorialGoldIssueFixtureData,
  editorialGoldLegislator,
} from "../lib/editorialGoldRenderFixture.mjs";
import { justiceEditorialIssueFixtureData } from "../lib/justiceEditorialRenderFixture.mjs";
import { justiceCrossMemberRenderProfiles } from "../lib/justiceCrossMemberReviewSlices.mjs";
import { EDITORIAL_EXPERIENCE_MODE } from "../lib/editorialIssueExperience.mjs";
import { reviewEditorialIssueSlices } from "../lib/editorialIssueReviewSlices.mjs";
import {
  mixedAvailabilityIssueFixtureData,
  proceduralOnlyIssueFixtureData,
  syntheticDevelopingEditorialCandidate,
  syntheticEditorialCandidate,
  syntheticEditorialIssueFixtureData,
  syntheticEditorialLegislator,
  syntheticLimitedEditorialCandidate,
  syntheticLimitedEditorialIssueFixtureData,
} from "../lib/editorialIssueTestFixtures.mjs";

export default function GoldenRenderFixture() {
  const [evidenceRequest, setEvidenceRequest] = useState({
    domain: "NATIONAL_SECURITY_FOREIGN",
    requestedAt: 1,
  });
  const [limitedEvidenceRequest, setLimitedEvidenceRequest] = useState({
    domain: "NATIONAL_SECURITY_FOREIGN",
    requestedAt: 1,
  });
  const [editorialGoldRequest] = useState({
    domain: "ECONOMY_TAXES",
    requestedAt: 1,
  });
  const [justiceEditorialRequest] = useState({ domain: "JUSTICE_PUBLIC_SAFETY", requestedAt: 1 });
  const [syntheticEditorialRequest] = useState({
    domain: "ENVIRONMENT_ENERGY",
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

        <section
          className="mt-5 scroll-mt-4"
          data-review-harness="pending-editorial"
          data-testid="foushee-economy-editorial-gold"
          id="foushee-economy-editorial-gold"
        >
          <div className="rounded-2xl border border-cyan-900/20 bg-white px-4 py-3 shadow-[0_8px_24px_rgba(15,23,42,0.06)]" data-review-harness-chrome="true">
            <p className="text-xs uppercase tracking-[0.2em] text-cyan-800">Unpublished review — internal harness</p>
            <h2 className="mt-1 font-serif text-[1.8rem] leading-tight text-stone-950">
              Valerie P. Foushee — Economy &amp; Taxes
            </h2>
            <p className="mt-1 text-sm leading-6 text-stone-600">
              Episode-aware issue synthesis and a focused record review.
            </p>
          </div>
          <PositionByIssue
            editorialCandidates={reviewEditorialIssueSlices}
            editorialMode={EDITORIAL_EXPERIENCE_MODE.review}
            evidenceRequest={editorialGoldRequest}
            fixtureData={editorialGoldIssueFixtureData}
            legislator={editorialGoldLegislator}
            legislatorId={editorialGoldLegislator.id}
            scope="all"
            title="Valerie P. Foushee's Economy & Taxes evidence"
          />
        </section>

        <section className="mt-5 scroll-mt-4" data-review-harness="pending-editorial" data-testid="foushee-justice-editorial-gold" id="foushee-justice-editorial-gold">
          <div className="rounded-2xl border border-cyan-900/20 bg-white px-4 py-3 shadow-[0_8px_24px_rgba(15,23,42,0.06)]" data-review-harness-chrome="true">
            <p className="text-xs uppercase tracking-[0.2em] text-cyan-800">Unpublished review — internal harness</p>
            <h2 className="mt-1 font-serif text-[1.8rem] leading-tight text-stone-950">Valerie P. Foushee {"—"} Justice &amp; Public Safety</h2>
            <p className="mt-1 text-sm leading-6 text-stone-600">Pending, episode-aware editorial review through the generic issue renderer.</p>
          </div>
          <PositionByIssue editorialCandidates={reviewEditorialIssueSlices} editorialMode={EDITORIAL_EXPERIENCE_MODE.review} evidenceRequest={justiceEditorialRequest} fixtureData={justiceEditorialIssueFixtureData} legislator={editorialGoldLegislator} legislatorId={editorialGoldLegislator.id} scope="all" title="Valerie P. Foushee's Justice & Public Safety evidence" />
        </section>

        {justiceCrossMemberRenderProfiles.map((profile) => (
          <section
            className="mt-5 scroll-mt-4"
            data-review-harness="cross-member-pending"
            data-testid={`justice-cross-member-${profile.memberId}`}
            id={`justice-cross-member-${profile.memberId}`}
            key={profile.memberId}
          >
            <div className="rounded-2xl border border-indigo-900/20 bg-white px-4 py-3 shadow-[0_8px_24px_rgba(15,23,42,0.06)]" data-review-harness-chrome="true">
              <p className="text-xs uppercase tracking-[0.2em] text-indigo-800">Cross-member validation — review only</p>
              <h2 className="mt-1 font-serif text-[1.8rem] leading-tight text-stone-950">
                {profile.legislator.name_display} — Justice &amp; Public Safety
              </h2>
              <p className="mt-1 text-sm leading-6 text-stone-600">
                Shared PR #95 episode research with a member-specific recorded-action overlay.
              </p>
            </div>
            <PositionByIssue
              editorialCandidates={[profile.candidate]}
              editorialMode={EDITORIAL_EXPERIENCE_MODE.review}
              evidenceRequest={justiceEditorialRequest}
              fixtureData={profile.fixtureData}
              legislator={profile.legislator}
              legislatorId={profile.legislator.id}
              scope="all"
              title={`${profile.legislator.name_display}'s Justice & Public Safety evidence`}
            />
          </section>
        ))}

        <section className="mt-5 scroll-mt-4" data-review-harness="production-fallback" data-testid="foushee-justice-production-gate-fixture" id="foushee-justice-production-gate-fixture">
          <div className="rounded-2xl border border-stone-300 bg-white px-4 py-3" data-review-harness-chrome="true"><p className="text-xs uppercase tracking-[0.2em] text-stone-600">Production-gate fallback proof</p><h2 className="mt-1 font-serif text-[1.8rem]">Pending Justice content stays unpublished</h2></div>
          <PositionByIssue evidenceRequest={justiceEditorialRequest} fixtureData={justiceEditorialIssueFixtureData} legislator={editorialGoldLegislator} legislatorId={editorialGoldLegislator.id} scope="all" title="Production-mode Justice evidence" />
        </section>

        <section className="mt-5 scroll-mt-4" data-review-harness="simulated-production" data-testid="synthetic-editorial-fixture" id="synthetic-editorial-fixture">
          <div className="rounded-2xl border border-violet-300 bg-white px-4 py-3 shadow-[0_8px_24px_rgba(15,23,42,0.06)]" data-review-harness-chrome="true">
            <p className="text-xs uppercase tracking-[0.2em] text-violet-800">Synthetic fixture — simulated production eligibility</p>
            <h2 className="mt-1 font-serif text-[1.8rem] leading-tight text-stone-950">Jordan Example {"\u2014"} public presentation proof</h2>
            <p className="mt-1 text-sm leading-6 text-stone-600">Internal test-only frame. The nested surface is the exact public adapter and renderer.</p>
          </div>
          <PositionByIssue
            editorialCandidates={[syntheticEditorialCandidate]}
            evidenceRequest={syntheticEditorialRequest}
            fixtureData={syntheticEditorialIssueFixtureData}
            legislator={syntheticEditorialLegislator}
            legislatorId={syntheticEditorialLegislator.id}
            scope="all"
            title="Jordan Example's issue evidence"
          />
        </section>

        <section className="mt-5 scroll-mt-4" data-review-harness="developing-record" data-testid="public-developing-record" id="public-developing-record">
          <div className="rounded-2xl border border-amber-300 bg-white px-4 py-3" data-review-harness-chrome="true"><p className="text-xs uppercase tracking-[0.2em] text-amber-800">Synthetic fixture — developing public state</p><h2 className="mt-1 font-serif text-[1.8rem]">Developing record</h2></div>
          <PositionByIssue editorialCandidates={[syntheticDevelopingEditorialCandidate]} evidenceRequest={syntheticEditorialRequest} fixtureData={syntheticEditorialIssueFixtureData} legislator={syntheticEditorialLegislator} legislatorId={syntheticEditorialLegislator.id} scope="all" title="Jordan Example's developing issue record" />
        </section>

        <section className="mt-5 scroll-mt-4" data-review-harness="limited-evidence" data-testid="public-limited-evidence" id="public-limited-evidence">
          <div className="rounded-2xl border border-amber-300 bg-white px-4 py-3" data-review-harness-chrome="true"><p className="text-xs uppercase tracking-[0.2em] text-amber-800">Synthetic fixture — limited public state</p><h2 className="mt-1 font-serif text-[1.8rem]">Limited evidence</h2></div>
          <PositionByIssue editorialCandidates={[syntheticLimitedEditorialCandidate]} evidenceRequest={syntheticEditorialRequest} fixtureData={syntheticLimitedEditorialIssueFixtureData} legislator={syntheticEditorialLegislator} legislatorId={syntheticEditorialLegislator.id} scope="all" title="Jordan Example's limited issue record" />
        </section>

        <section className="mt-5 scroll-mt-4" data-review-harness="procedural-only" data-testid="public-procedural-only" id="public-procedural-only">
          <div className="rounded-2xl border border-stone-300 bg-white px-4 py-3" data-review-harness-chrome="true"><p className="text-xs uppercase tracking-[0.2em] text-stone-600">Synthetic fixture — fallback proof</p><h2 className="mt-1 font-serif text-[1.8rem]">Procedural context only</h2></div>
          <PositionByIssue evidenceRequest={syntheticEditorialRequest} fixtureData={proceduralOnlyIssueFixtureData} legislator={syntheticEditorialLegislator} legislatorId={syntheticEditorialLegislator.id} scope="all" title="Jordan Example's procedural record" />
        </section>

        <section className="mt-5 scroll-mt-4" data-review-harness="mixed-availability" data-testid="public-mixed-availability" id="public-mixed-availability">
          <div className="rounded-2xl border border-stone-300 bg-white px-4 py-3" data-review-harness-chrome="true"><p className="text-xs uppercase tracking-[0.2em] text-stone-600">Synthetic fixture — navigation proof</p><h2 className="mt-1 font-serif text-[1.8rem]">Mixed issue availability</h2></div>
          <PositionByIssue editorialCandidates={[syntheticEditorialCandidate]} evidenceRequest={syntheticEditorialRequest} fixtureData={mixedAvailabilityIssueFixtureData} legislator={syntheticEditorialLegislator} legislatorId={syntheticEditorialLegislator.id} scope="all" title="Jordan Example's issue evidence" />
        </section>

        <section className="mt-5 scroll-mt-4" data-review-harness="production-fallback" data-testid="foushee-production-gate-fixture" id="foushee-production-gate-fixture">
          <div className="rounded-2xl border border-stone-300 bg-white px-4 py-3 shadow-[0_8px_24px_rgba(15,23,42,0.06)]" data-review-harness-chrome="true">
            <p className="text-xs uppercase tracking-[0.2em] text-stone-600">Production-gate fallback proof</p>
            <h2 className="mt-1 font-serif text-[1.8rem] leading-tight text-stone-950">Pending editorial content stays unpublished</h2>
            <p className="mt-1 text-sm leading-6 text-stone-600">The same pending source data runs in default production mode and keeps the basic evidence experience.</p>
          </div>
          <PositionByIssue
            evidenceRequest={editorialGoldRequest}
            fixtureData={editorialGoldIssueFixtureData}
            legislator={editorialGoldLegislator}
            legislatorId={editorialGoldLegislator.id}
            scope="all"
            title="Production-mode representative issue evidence"
          />
        </section>

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
