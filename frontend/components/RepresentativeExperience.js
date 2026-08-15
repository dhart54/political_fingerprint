"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import IssueDetail from "./IssueDetail";
import IssueDiscoveryControls from "./IssueDiscoveryControls";
import IssueOverviewGrid from "./IssueOverviewGrid";
import {
  fetchEditorialPresentations,
  fetchPositions,
} from "../lib/api";
import { hasAvailableIssueEvidence } from "../lib/basicEvidencePresentation.mjs";
import {
  getEditorialPresentation,
  indexEditorialPresentations,
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
}) {
  const [mode, setMode] = useState("recommended");
  const initialLandingHandled = useRef(false);
  const movedBeforeInitialLanding = useRef(false);
  const [state, setState] = useState({
    status: "loading",
    positions: null,
    presentations: null,
    error: null,
  });

  useEffect(() => {
    let active = true;
    setState({
      status: "loading",
      positions: null,
      presentations: null,
      error: null,
    });
    async function load() {
      try {
        const [positions, presentations] = fixtureData
          ? [fixtureData.positions, fixtureData.presentations]
          : await Promise.all([
              fetchPositions({ legislatorId: legislator.id, scope }),
              fetchEditorialPresentations({
                legislatorId: legislator.id,
                scope,
              }).catch(() => ({
                legislator_id: legislator.id,
                member_bioguide_id: legislator.bioguide_id,
                presentations: [],
              })),
            ]);
        if (active) {
          setState({
            status: "ready",
            positions,
            presentations,
            error: null,
          });
        }
      } catch {
        if (active) {
          setState({
            status: "error",
            positions: null,
            presentations: null,
            error: "This representative’s issue records are unavailable right now.",
          });
        }
      }
    }
    load();
    return () => {
      active = false;
    };
  }, [fixtureData, legislator.bioguide_id, legislator.id, scope]);

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
  const selectedRow = overviewRows.find((row) => row.domain === selectedIssue);
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
      "ArrowDown", "ArrowUp", "End", "Home", "PageDown", "PageUp", " ",
    ]);
    const markKeyboardMove = (event) => {
      if (movementKeys.has(event.key)) {
        markMoved();
      }
    };
    window.addEventListener("wheel", markMoved, { passive: true });
    window.addEventListener("touchmove", markMoved, { passive: true });
    window.addEventListener("pointerdown", markMoved, { passive: true });
    window.addEventListener("keydown", markKeyboardMove);
    return () => {
      window.removeEventListener("wheel", markMoved);
      window.removeEventListener("touchmove", markMoved);
      window.removeEventListener("pointerdown", markMoved);
      window.removeEventListener("keydown", markKeyboardMove);
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
    window.requestAnimationFrame(() => {
      document.getElementById("issue-summary")?.scrollIntoView({
        behavior: window.matchMedia?.("(prefers-reduced-motion: reduce)").matches
          ? "auto"
          : "smooth",
        block: "start",
      });
      window.requestAnimationFrame(() => {
        document.getElementById("selected-issue-heading")?.focus({
          preventScroll: true,
        });
      });
    });
  }, [directIssueLanding, selectedRow, state.status]);

  function selectIssue(issue) {
    onSelectIssue(issue);
    window.requestAnimationFrame(() => {
      document.getElementById("issue-detail")?.scrollIntoView({
        behavior: window.matchMedia?.("(prefers-reduced-motion: reduce)").matches
          ? "auto"
          : "smooth",
        block: "start",
      });
      window.requestAnimationFrame(() => {
        document.getElementById("selected-issue-heading")?.focus({
          preventScroll: true,
        });
      });
    });
  }

  return (
    <>
      <section className="scroll-mt-24 border-t border-stone-200 py-8" id="issues">
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
          <IssueOverviewGrid
            mode={mode}
            onSelect={selectIssue}
            rows={displayedRows}
            selectedIssue={selectedIssue}
          />
        ) : null}
      </section>

      {selectedRow ? (
        <IssueDetail
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
