"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import RepresentativeExperience from "../components/RepresentativeExperience";
import RepresentativeFinder from "../components/RepresentativeFinder";
import RepresentativeHeader from "../components/RepresentativeHeader";
import ScopeControl from "../components/ScopeControl";
import { fetchLegislatorProfile } from "../lib/api";
import {
  buildPassAUrl,
  parsePassARouteState,
} from "../lib/frontendPassA.mjs";

const EMPTY_ROUTE = {
  legislatorId: null,
  issue: null,
  scope: "all",
};

export default function HomePage() {
  const [routeReady, setRouteReady] = useState(false);
  const [route, setRoute] = useState(EMPTY_ROUTE);
  const [legislatorState, setLegislatorState] = useState({
    status: "idle",
    legislator: null,
    error: null,
  });
  const [finderOpen, setFinderOpen] = useState(false);

  useEffect(() => {
    function syncFromLocation() {
      setRoute(parsePassARouteState(window.location.search));
      setFinderOpen(false);
      setRouteReady(true);
    }
    syncFromLocation();
    window.addEventListener("popstate", syncFromLocation);
    return () => window.removeEventListener("popstate", syncFromLocation);
  }, []);

  useEffect(() => {
    let active = true;
    if (!routeReady || !route.legislatorId) {
      setLegislatorState({
        status: "idle",
        legislator: null,
        error: null,
      });
      return () => {
        active = false;
      };
    }
    setLegislatorState((current) => (
      current.legislator?.id === route.legislatorId
        ? current
        : { status: "loading", legislator: null, error: null }
    ));
    async function loadProfile() {
      try {
        const legislator = await fetchLegislatorProfile({
          legislatorId: route.legislatorId,
        });
        if (active) {
          setLegislatorState({
            status: "ready",
            legislator,
            error: null,
          });
        }
      } catch {
        if (active) {
          setLegislatorState({
            status: "error",
            legislator: null,
            error: "That representative record is unavailable. Search again to continue.",
          });
        }
      }
    }
    loadProfile();
    return () => {
      active = false;
    };
  }, [route.legislatorId, routeReady]);

  function navigate(next, { replace = false } = {}) {
    const resolved = { ...route, ...next };
    const url = buildPassAUrl(window.location.href, resolved);
    window.history[replace ? "replaceState" : "pushState"]({}, "", url);
    setRoute(resolved);
  }

  function selectRepresentative(legislator) {
    setLegislatorState({
      status: "ready",
      legislator,
      error: null,
    });
    setFinderOpen(false);
    navigate({
      legislatorId: legislator.id,
      issue: null,
    });
    window.requestAnimationFrame(() => {
      document.getElementById("representative-name")?.focus?.();
      window.scrollTo({
        top: 0,
        behavior: window.matchMedia?.("(prefers-reduced-motion: reduce)").matches
          ? "auto"
          : "smooth",
      });
    });
  }

  const legislator = legislatorState.legislator;

  return (
    <main className="min-h-screen bg-[#f7f3e9] text-stone-900">
      <header className="border-b border-stone-200/90 bg-[#fbf8f1]">
        <div className="mx-auto flex max-w-[90rem] items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-10">
          <Link className="font-serif text-xl font-semibold text-stone-950" href="/">
            Political Fingerprint
          </Link>
          <p className="hidden text-sm text-stone-600 sm:block">
            Voting records, explained with receipts.
          </p>
        </div>
      </header>

      <div className="mx-auto max-w-[90rem] px-4 py-8 sm:px-6 lg:px-10 lg:py-10">
        {!routeReady || legislatorState.status === "loading" ? (
          <p className="py-20 text-center text-base text-stone-700" role="status">
            Loading representative journey…
          </p>
        ) : null}

        {routeReady && !route.legislatorId ? (
          <div className="mx-auto max-w-5xl py-4 sm:py-10">
            <p className="eyebrow">Understand the record in one intentional scroll</p>
            <h1 className="mt-3 max-w-4xl font-serif text-5xl leading-[1.05] text-stone-950 sm:text-6xl">
              Who represents you, and what have they done?
            </h1>
            <p className="mt-5 max-w-3xl text-lg leading-8 text-stone-700">
              Find a federal representative, choose an issue, and inspect bounded plain-language summaries alongside chronological exact vote receipts.
            </p>
            <div className="mt-9">
              <RepresentativeFinder onSelect={selectRepresentative} />
            </div>
          </div>
        ) : null}

        {routeReady && route.legislatorId && legislatorState.status === "error" ? (
          <div className="mx-auto max-w-4xl">
            <p className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-base text-rose-800" role="alert">
              {legislatorState.error}
            </p>
            <div className="mt-5">
              <RepresentativeFinder onSelect={selectRepresentative} />
            </div>
          </div>
        ) : null}

        {legislator ? (
          <>
            <RepresentativeHeader
              legislator={legislator}
              onSwitch={() => setFinderOpen(true)}
              scope={route.scope}
            />
            {finderOpen ? (
              <div className="my-5" role="region" aria-label="Switch representative">
                <RepresentativeFinder
                  compact
                  onCancel={() => setFinderOpen(false)}
                  onSelect={selectRepresentative}
                />
              </div>
            ) : null}
            <ScopeControl
              onChange={(scope) => navigate({ scope })}
              scope={route.scope}
            />
            <RepresentativeExperience
              legislator={legislator}
              onSelectIssue={(issue) => navigate({ issue })}
              scope={route.scope}
              selectedIssue={route.issue}
            />
            <MethodFooter />
          </>
        ) : null}
      </div>
    </main>
  );
}

function MethodFooter() {
  return (
    <footer className="mt-12 border-t border-stone-300 py-8">
      <div className="grid gap-5 md:grid-cols-3">
        <FooterNote
          heading="Recorded behavior"
          text="The page maps supplied legislative actions. It does not infer motive, character, ideology, or how anyone should vote."
        />
        <FooterNote
          heading="Evidence boundaries"
          text="Present, Not Voting, procedural, limited-context, and unresolved records remain distinct and do not become support or opposition."
        />
        <FooterNote
          heading="Issue summaries"
          text="Issue summaries stay bounded to the stated actions and Congress. Vote receipts remain available for direct inspection."
        />
      </div>
    </footer>
  );
}

function FooterNote({ heading, text }) {
  return (
    <div>
      <h2 className="text-sm font-semibold uppercase tracking-[0.12em] text-teal-900">
        {heading}
      </h2>
      <p className="mt-2 text-base leading-7 text-stone-700">{text}</p>
    </div>
  );
}
