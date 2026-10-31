"use client";

import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";

import IssueDetail from "./IssueDetail";
import IssueDiscoveryControls from "./IssueDiscoveryControls";
import IssueOverviewGrid from "./IssueOverviewGrid";
import RecordAtAGlance from "./RecordAtAGlance";
import { projectRecordCard, recordCardUrl, resolveCardFinding } from "../lib/recordCard.mjs";
import {
  fetchEditorialPresentations,
  fetchPositions,
} from "../lib/api";
import { hasAvailableIssueEvidence } from "../lib/basicEvidencePresentation.mjs";
import {
  getEditorialPresentation,
  indexEditorialPresentations,
  issuePresentationStatus,
  presentationIdentityMatches,
} from "../lib/editorialPresentation.mjs";
import { formatDomainLabel } from "../lib/issueDomains";
import { DOMAIN_ORDER } from "../lib/issueEvidenceCoverage.mjs";
import {
  buildIssueOverviewRows,
  sortAndFilterIssues,
} from "../lib/frontendPassA.mjs";

export default function RepresentativeExperience({
  directIssueLanding = false,
  fixtureData = null,
  legislator,
  onSelectIssue,
  scope,
  selectedIssue,
  dataClient = {},
  recordCardCandidate = null,
  findingRoute = {},
  routePath = "/",
  reviewMode = false,
}) {
  const [mode, setMode] = useState("recommended");
  const initialLandingHandled = useRef(false);
  const movedBeforeInitialLanding = useRef(false);
  const findingArrivalKey = JSON.stringify([findingRoute.findingId, findingRoute.findingSource, findingRoute.findingView]);
  const findingArrivalIntent = useRef({ key: findingArrivalKey, moved: false });
  if (findingArrivalIntent.current.key !== findingArrivalKey) {
    findingArrivalIntent.current = { key: findingArrivalKey, moved: false };
  }
  const analysisViewport = useRef(null);
  const [state, setState] = useState({
    status: "loading",
    positions: null,
    presentations: null,
    error: null,
    presentationStatus: "loading",
    card: { status: "loading", entries: [] },
  });

  useEffect(() => {
    let active = true;
    setState({
      status: "loading",
      positions: null,
      presentations: null,
      error: null,
      presentationStatus: "loading",
      card: { status: "loading", entries: [] },
    });
    async function loadPositions() {
      try {
        const positions = fixtureData
          ? fixtureData.positions
          : await (dataClient.fetchPositions || fetchPositions)({ legislatorId: legislator.id, scope });
        if (!Array.isArray(positions?.positions) || (positions.legislator_id && positions.legislator_id !== legislator.id) || (positions.scope && positions.scope !== scope)) throw new Error("Position identity or shape mismatch");
        if (active) {
          setState((current) => ({
            ...current,
            status: "ready",
            positions,
            error: null,
          }));
        }
      } catch {
        if (active) {
          setState((current) => ({
            ...current,
            status: "error",
            positions: null,
            error: "This representative’s issue records are unavailable right now.",
          }));
        }
      }
    }
    async function loadPresentations() {
      try {
        const presentations = fixtureData
          ? fixtureData.presentations
          : await (dataClient.fetchEditorialPresentations || fetchEditorialPresentations)({ legislatorId: legislator.id, scope });
        const presentationStatus = issuePresentationStatus(presentations, { legislatorId: legislator.id, memberBioguideId: legislator.bioguide_id }, scope);
        const card = recordCardCandidate ? await projectRecordCard({ candidate: recordCardCandidate, payload: presentations, legislatorId: legislator.id, memberBioguideId: legislator.bioguide_id, scope, requestStatus: presentationStatus }) : null;
        if (active) {
          analysisViewport.current = captureAnalysisViewport(initialLandingHandled.current && !movedBeforeInitialLanding.current && !window.location.hash);
          setState((current) => ({
            ...current,
            presentations: presentationStatus === "ready" ? presentations : null,
            presentationStatus,
            card,
          }));
        }
      } catch {
        if (active) {
          analysisViewport.current = captureAnalysisViewport(initialLandingHandled.current && !movedBeforeInitialLanding.current && !window.location.hash);
          setState((current) => ({
            ...current,
            presentations: null,
            presentationStatus: "error",
            card: { status: "error", entries: [] },
          }));
        }
      }
    }
    // Each validated response can settle without waiting for the other endpoint.
    // The shared lifetime still rejects both late responses after navigation.
    loadPositions();
    loadPresentations();
    return () => {
      active = false;
    };
  }, [dataClient.fetchPositions, dataClient.fetchEditorialPresentations, fixtureData, legislator.bioguide_id, legislator.id, scope, recordCardCandidate]);

  useLayoutEffect(() => {
    const anchor = analysisViewport.current;
    analysisViewport.current = null;
    if (!anchor?.element.isConnected || window.location.href !== anchor.href) return;
    // Preserve the reader's place when the card/analysis changes height above it.
    // If native scroll anchoring already compensated, the measured delta is zero.
    let cancelled = false;
    const preserve = () => {
      if (cancelled || !anchor.element.isConnected || window.location.href !== anchor.href) return;
      const delta = anchor.element.getBoundingClientRect().top - anchor.top;
      if (Math.abs(delta) > 1) window.scrollBy({ top: delta, behavior: "instant" });
    };
    preserve();
    // Reconcile the browser's settled layout once, without overriding any newer
    // reader interaction between this commit and the following frame.
    const cancel = () => { cancelled = true; };
    const events = ["wheel", "touchmove", "pointerdown", "keydown", "focusin", "resize"];
    events.forEach(event => window.addEventListener(event, cancel, { passive: true }));
    let frame = requestAnimationFrame(() => {
      frame = requestAnimationFrame(() => {
        preserve();
        events.forEach(event => window.removeEventListener(event, cancel));
      });
    });
    return () => {
      cancelAnimationFrame(frame);
      events.forEach(event => window.removeEventListener(event, cancel));
    };
  }, [state.presentationStatus]);

  useEffect(() => {
    if (!findingRoute.findingId || (state.status !== "loading" && state.presentationStatus !== "loading")) return undefined;
    // A finding may arrive after the reader has chosen another control or place
    // in the page. Keep that interaction's focus instead of replaying arrival.
    const markMoved = () => { findingArrivalIntent.current.moved = true; };
    const markKey = event => {
      if (["ArrowDown", "ArrowUp", "End", "Home", "PageDown", "PageUp", " ", "Tab"].includes(event.key)) markMoved();
    };
    const markControlFocus = event => {
      if (event.target instanceof Element && event.target.closest('a[href], button, input, select, textarea, [contenteditable="true"]')) markMoved();
    };
    window.addEventListener("wheel", markMoved, { passive: true });
    window.addEventListener("touchmove", markMoved, { passive: true });
    window.addEventListener("pointerdown", markMoved, { passive: true });
    window.addEventListener("keydown", markKey);
    window.addEventListener("focusin", markControlFocus);
    return () => {
      window.removeEventListener("wheel", markMoved);
      window.removeEventListener("touchmove", markMoved);
      window.removeEventListener("pointerdown", markMoved);
      window.removeEventListener("keydown", markKey);
      window.removeEventListener("focusin", markControlFocus);
    };
  }, [findingArrivalKey, findingRoute.findingId, state.presentationStatus, state.status]);

  const presentationIndex = useMemo(
    () => presentationIdentityMatches(state.presentations, {
      legislatorId: legislator.id,
      memberBioguideId: legislator.bioguide_id,
    })
      ? indexEditorialPresentations(state.presentations)
      : new Map(),
    [legislator.bioguide_id, legislator.id, state.presentations],
  );
  const overviewRows = useMemo(
    () => buildIssueOverviewRows({
      rows: (state.positions?.positions || [])
        .filter(hasAvailableIssueEvidence)
        .map((row) => ({ ...row, publicLabel: publicLabel(row.domain) })),
      presentations: presentationIndex,
      stableDomainOrder: DOMAIN_ORDER,
    }),
    [presentationIndex, state.positions],
  );
  const displayedRows = useMemo(
    () => sortAndFilterIssues(overviewRows, mode),
    [mode, overviewRows],
  );
  // Discovery hides empty domains; an explicitly selected supplied domain stays navigable.
  const selectedRow = state.positions?.positions?.find((row) => row.domain === selectedIssue);
  const selectedPresentation = getEditorialPresentation(
    state.presentations,
    selectedIssue,
    {
      legislatorId: legislator.id,
      memberBioguideId: legislator.bioguide_id,
    },
  );

  useEffect(() => {
    if (!directIssueLanding || initialLandingHandled.current) {
      return undefined;
    }
    const markMoved = () => {
      movedBeforeInitialLanding.current = true;
    };
    const movementKeys = new Set([
      "ArrowDown", "ArrowUp", "End", "Home", "PageDown", "PageUp", " ", "Tab",
    ]);
    const markKeyboardMove = (event) => {
      if (movementKeys.has(event.key)) {
        markMoved();
      }
    };
    const markControlFocus = (event) => {
      if (event.target instanceof Element && event.target.closest(
        'a[href], button, input, select, textarea, [contenteditable="true"], [tabindex]:not([tabindex="-1"])',
      )) markMoved();
    };
    window.addEventListener("wheel", markMoved, { passive: true });
    window.addEventListener("touchmove", markMoved, { passive: true });
    window.addEventListener("pointerdown", markMoved, { passive: true });
    window.addEventListener("keydown", markKeyboardMove);
    window.addEventListener("focusin", markControlFocus);
    return () => {
      window.removeEventListener("wheel", markMoved);
      window.removeEventListener("touchmove", markMoved);
      window.removeEventListener("pointerdown", markMoved);
      window.removeEventListener("keydown", markKeyboardMove);
      window.removeEventListener("focusin", markControlFocus);
    };
  }, [directIssueLanding]);

  useEffect(() => {
    if (
      !directIssueLanding
      || initialLandingHandled.current
      || movedBeforeInitialLanding.current
      || window.scrollY > 24
      || state.status !== "ready"
      || !selectedRow
    ) {
      return;
    }
    initialLandingHandled.current = true;
    if (window.location.hash) {
      return;
    }
    let focusFrame;
    const scrollFrame = window.requestAnimationFrame(() => {
      if (window.location.hash || movedBeforeInitialLanding.current) return;
      document.getElementById("issue-summary")?.scrollIntoView({
        behavior: window.matchMedia?.("(prefers-reduced-motion: reduce)").matches
          ? "auto"
          : "smooth",
        block: "start",
      });
      focusFrame = window.requestAnimationFrame(() => {
        if (window.location.hash || movedBeforeInitialLanding.current) return;
        document.getElementById("selected-issue-heading")?.focus({
          preventScroll: true,
        });
      });
    });
    return () => {
      window.cancelAnimationFrame(scrollFrame);
      if (focusFrame !== undefined) window.cancelAnimationFrame(focusFrame);
    };
  }, [directIssueLanding, selectedRow, state.status]);

  function selectIssue(issue) {
    const navigationIsCurrent = onSelectIssue(issue);
    const href = window.location.href;
    const isCurrent = () => window.location.href === href && (navigationIsCurrent?.() ?? true);
    window.requestAnimationFrame(() => {
      if (!isCurrent()) return;
      document.getElementById("issue-detail")?.scrollIntoView({
        behavior: window.matchMedia?.("(prefers-reduced-motion: reduce)").matches
          ? "auto"
          : "smooth",
        block: "start",
      });
      window.requestAnimationFrame(() => {
        if (!isCurrent()) return;
        document.getElementById("selected-issue-heading")?.focus({
          preventScroll: true,
        });
      });
    });
  }

  function navigateFinding(event, entry) {
    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    window.history.replaceState({ ...window.history.state, returnCardEntry: entry.id }, "", window.location.href);
    window.history.pushState({}, "", recordCardUrl(window.location.href, { legislatorId: legislator.id, scope, issue: entry.issue_id, findingId: entry.finding_id, sourceHash: entry.sourcePresentationHash, hash: "finding-detail" }));
    window.dispatchEvent(new PopStateEvent("popstate"));
  }
  const cardFinding = resolveCardFinding(state.card, selectedIssue, findingRoute.findingId, findingRoute.findingSource);

  useEffect(() => {
    if (state.card?.status !== "ready" || selectedIssue || (window.location.hash !== "#record-at-a-glance" && !window.history.state?.returnCardEntry)) return;
    const frame = requestAnimationFrame(() => {
      const target = document.getElementById(window.history.state?.returnCardEntry || "record-card-heading");
      target?.scrollIntoView({ behavior: "auto", block: "center" });
      target?.focus({ preventScroll: true });
    });
    return () => cancelAnimationFrame(frame);
  }, [selectedIssue, state.card]);

  return (
    <>
      {recordCardCandidate ? <RecordAtAGlance model={state.card || { status: "loading" }} legislatorId={legislator.id} scope={scope} onNavigate={navigateFinding} routePath={routePath} reviewMode={reviewMode} /> : null}
      <section className="scroll-mt-24 border-t border-stone-200 py-8" id="issues" tabIndex={-1} data-section-ready={state.status !== "loading"}>
        <p className="eyebrow">Issue discovery</p>
        <h2 className="mt-2 font-serif text-4xl leading-tight text-stone-950">
          Choose an issue
        </h2>
        <p className="mt-3 max-w-3xl text-base leading-7 text-stone-700">
          Each card shows recorded evidence in the selected Congress scope and whether a plain-language issue summary is available.
        </p>
        <IssueDiscoveryControls mode={mode} onChange={setMode} />
        {state.status === "loading" ? (
          <p className="mt-6 text-base text-stone-700" role="status">
            Loading issue records…
          </p>
        ) : null}
        {state.status === "error" ? (
          <p className="mt-6 rounded-xl border border-rose-200 bg-rose-50 p-4 text-base text-rose-800" role="alert">
            {state.error}
          </p>
        ) : null}
        {state.status === "ready" ? (
          <>
          {state.presentationStatus !== "ready" ? <p className="mt-5 text-sm leading-6 text-stone-700" role="status">{state.presentationStatus === "loading" ? "Issue summaries are still loading. Recorded vote evidence is available." : "Issue summaries could not be verified. Recorded vote evidence remains available."}</p> : null}
          <IssueOverviewGrid
            compact={state.card?.status === "ready"}
            presentationStatus={state.presentationStatus}
            mode={mode}
            onSelect={selectIssue}
            rows={displayedRows}
            selectedIssue={selectedIssue}
          />
          </>
        ) : null}
      </section>

      {selectedRow ? (
        <IssueDetail
          key={`${legislator.id}:${scope}:${selectedIssue}:${findingRoute.findingId || ""}`}
          fetchEvidence={dataClient.fetchPositionEvidence}
          cardFinding={cardFinding}
          cardFindingRequested={Boolean(recordCardCandidate && findingRoute.findingId)}
          cardFindingView={findingRoute.findingView}
          allowFindingArrivalFocus={!findingRoute.findingId || !findingArrivalIntent.current.moved}
          routePath={routePath}
          presentationStatus={state.presentationStatus}
          fixtureEvidence={fixtureData?.evidenceByDomain?.[selectedIssue] || null}
          issue={selectedIssue}
          legislatorId={legislator.id}
          presentation={selectedPresentation}
          representativeName={legislator.name_display}
          scope={scope}
        />
      ) : null}
    </>
  );
}

function publicLabel(domain) {
  return formatDomainLabel(domain);
}

function captureAnalysisViewport(preferIssueSummary) {
  const focused = document.activeElement;
  const ownedFocus = focused?.closest("#issues, #issue-detail");
  if (window.scrollY === 0 && !ownedFocus) return null;
  const headerBottom = document.querySelector("main > header")?.getBoundingClientRect().bottom || 0;
  // Initial landing can be clamped by the short pending layout before its
  // heading receives focus. Preserve that intended destination, not the grid
  // above it, whose own height changes when summaries arrive.
  const element = preferIssueSummary ? document.getElementById("issue-summary") : ownedFocus ? focused
    : document.elementFromPoint(window.innerWidth / 2, headerBottom + 24)?.closest("[data-canonical-action-id], #issue-summary, #issues");
  return element ? { element, top: element.getBoundingClientRect().top, href: window.location.href } : null;
}
