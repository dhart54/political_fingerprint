// Receipt/finding/card hashes retain their existing component owners. No-hash
// entries retain browser restoration; this does not set history.scrollRestoration.
const SECTION_IDS = new Set(["representative-name", "issues", "issue-summary", "issue-detail"]);
const MOVEMENT_KEYS = new Set(["ArrowDown", "ArrowUp", "End", "Home", "PageDown", "PageUp", " ", "Tab"]);

export function sectionRouteKey(route) {
  return `${route.legislatorId || ""}:${route.scope}:${route.issue || ""}:${route.findingId || ""}`;
}

export function createSectionNavigation(journey) {
  let generation = 0;
  let observer;
  let frame;
  let latestRoute;

  function invalidate() {
    generation += 1;
    observer?.disconnect();
    observer = undefined;
    if (frame !== undefined) cancelAnimationFrame(frame);
    frame = undefined;
  }

  function begin(route, restore = false) {
    invalidate();
    latestRoute = route;
    const current = generation;
    const href = window.location.href;
    const isCurrent = () => generation === current && window.location.href === href;
    const id = window.location.hash.slice(1);
    if (!restore || !SECTION_IDS.has(id)) return isCurrent;
    const routeKey = sectionRouteKey(route);

    function schedule() {
      if (!isCurrent() || frame !== undefined) return;
      // Wait for the matching React commit and browser history restoration, not
      // a fixed delay. Missing targets are retried only on relevant DOM changes.
      frame = requestAnimationFrame(() => {
        frame = requestAnimationFrame(() => {
          frame = undefined;
          if (!isCurrent() || journey.dataset.routeKey !== routeKey) return;
          // Profile arrival can still replace the short loading layout and wrap
          // the sticky navigation. Restore after the issue layout has settled
          // (including its error state), before handing control back to readers.
          if (journey.querySelector("#issues")?.dataset.sectionReady !== "true") return;
          const target = document.getElementById(id);
          if (!target || !journey.contains(target)) return;
          observer?.disconnect();
          observer = undefined;
          // History restoration is immediate, also cancelling a superseded
          // smooth issue-selection scroll. Explicit issue clicks retain motion.
          target.scrollIntoView({ behavior: "instant", block: "start" });
          const focusTarget = id === "issue-summary" || id === "issue-detail"
            ? document.getElementById("selected-issue-heading") : target;
          focusTarget?.focus({ preventScroll: true });
        });
      });
    }

    observer = new MutationObserver(schedule);
    observer.observe(journey, { childList: true, subtree: true, attributes: true, attributeFilter: ["data-route-key", "data-section-ready"] });
    schedule();
    return isCurrent;
  }

  const keyboardMovement = event => {
    if (MOVEMENT_KEYS.has(event.key)) invalidate();
  };
  const reassertSection = event => {
    if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const link = event.target instanceof Element ? event.target.closest("a[href]") : null;
    // Same-hash activation need not dispatch hashchange. The preceding pointer
    // or keyboard movement cancelled the old intent; this click is a new one.
    if (latestRoute && link?.href === window.location.href && SECTION_IDS.has(window.location.hash.slice(1))) {
      begin(latestRoute, true);
    }
  };
  journey.addEventListener("click", reassertSection);
  window.addEventListener("wheel", invalidate, { passive: true });
  window.addEventListener("touchstart", invalidate, { passive: true });
  window.addEventListener("pointerdown", invalidate, { passive: true });
  window.addEventListener("keydown", keyboardMovement);

  return {
    begin,
    dispose() {
      invalidate();
      window.removeEventListener("wheel", invalidate);
      window.removeEventListener("touchstart", invalidate);
      window.removeEventListener("pointerdown", invalidate);
      window.removeEventListener("keydown", keyboardMovement);
      journey.removeEventListener("click", reassertSection);
    },
  };
}
