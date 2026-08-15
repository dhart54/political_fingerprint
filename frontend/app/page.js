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
  const [routeNavigation, setRouteNavigation] = useState("initial");
  const [legislatorState, setLegislatorState] = useState({
    status: "idle",
    legislator: null,
    error: null,
  });
  const [finderOpen, setFinderOpen] = useState(false);

  useEffect(() => {
    function syncFromLocation(navigation = "history") {
      setRoute(parsePassARouteState(window.location.search));
      setRouteNavigation(navigation);
      setFinderOpen(false);
      setRouteReady(true);
    }
    syncFromLocation("initial");
    const handlePopState = () => syncFromLocation("history");
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
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
    setRouteNavigation("user");
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
      <SiteHeader
        representativeName={legislator?.name_display}
        selectedIssue={route.issue}
      />

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
              directIssueLanding={routeNavigation === "initial" && Boolean(route.issue)}
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

function SiteHeader({ representativeName, selectedIssue }) {
  const showSelectedIssueNavigation = Boolean(representativeName && selectedIssue);
  return (
    <header className="sticky top-0 z-30 border-b border-stone-200/90 bg-[#fbf8f1]/95 backdrop-blur">
      <div className="mx-auto grid max-w-[90rem] grid-cols-[1fr_auto] items-center gap-x-4 gap-y-2 px-4 py-3 sm:px-6 lg:grid-cols-[1fr_auto_1fr] lg:px-10">
        <Link className="font-serif text-xl font-semibold leading-none text-stone-950" href="/">
          Political Fingerprint
        </Link>
        {showSelectedIssueNavigation ? (
          <nav
            aria-label="Selected issue sections"
            className="order-3 col-span-2 flex items-center justify-center gap-1 overflow-x-auto lg:order-none lg:col-span-1"
          >
            {[
              ["issues", "Issues"],
              ["issue-summary", "Issue summary"],
              ["vote-record", "Vote record"],
            ].map(([id, label]) => (
              <a
                className="min-h-11 shrink-0 border-b-2 border-transparent px-3 py-3 text-sm font-semibold text-stone-700 hover:border-teal-700 hover:text-teal-900 focus-visible:border-teal-700"
                href={`#${id}`}
                key={id}
              >
                {label}
              </a>
            ))}
          </nav>
        ) : (
          <p className="hidden text-sm text-stone-600 lg:block">
            Voting records, explained with receipts.
          </p>
        )}
        {showSelectedIssueNavigation ? (
          <a
            className="justify-self-end text-sm font-semibold text-stone-900 hover:text-teal-900"
            href="#representative-name"
          >
            {representativeName}
          </a>
        ) : null}
      </div>
    </header>
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
