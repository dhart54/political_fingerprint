"use client";

import { useEffect, useRef, useState } from "react";

import {
  fetchLegislatorSearch,
  fetchZipLookup,
} from "../lib/api";
import { classifyZipLookupState } from "../lib/zipLookupState.mjs";
import OfficialSiteHandoff from "./OfficialSiteHandoff";

const SLOW_SEARCH_DELAY_MS = 8_000;

export default function RepresentativeFinder({
  compact = false,
  onCancel = null,
  onSelect,
}) {
  const [zip, setZip] = useState("");
  const [name, setName] = useState("");
  // Cancellation stops transport; the shared sequence also rejects late callbacks.
  const requestSequence = useRef(0);
  const pendingRequest = useRef(null);
  const zipInput = useRef(null);
  const nameInput = useRef(null);
  useEffect(() => () => {
    requestSequence.current += 1;
    const pending = pendingRequest.current;
    pendingRequest.current = null;
    clearTimeout(pending?.timer);
    pending?.controller.abort();
  }, []);
  const [state, setState] = useState({
    status: "idle",
    mode: null,
    results: [],
    message: "Search by ZIP code or representative name.",
  });

  function invalidateRequest() {
    const sequence = ++requestSequence.current;
    const pending = pendingRequest.current;
    pendingRequest.current = null;
    clearTimeout(pending?.timer);
    pending?.controller.abort();
    return sequence;
  }

  function beginRequest(mode, query) {
    const pending = pendingRequest.current;
    // Set the identity synchronously: repeated submits before rerender are inert.
    if (pending?.mode === mode && pending.query === query) return null;
    const sequence = invalidateRequest();
    const request = { sequence, mode, query, controller: new AbortController() };
    pendingRequest.current = request;
    setState({
      status: "loading",
      mode,
      results: [],
      message: mode === "zip" ? "Looking up representatives…" : "Searching representative records…",
    });
    request.timer = setTimeout(() => {
      if (sequence !== requestSequence.current) return;
      setState((current) => sequence === requestSequence.current && current.status === "loading"
        ? { ...current, slow: true }
        : current);
    }, SLOW_SEARCH_DELAY_MS);
    return request;
  }

  function finishRequest(request) {
    clearTimeout(request.timer);
    if (pendingRequest.current === request) pendingRequest.current = null;
  }

  async function searchZip(event) {
    event.preventDefault();
    if (!/^\d{5}$/.test(zip)) {
      invalidateRequest();
      setState({
        status: "error",
        mode: "zip",
        results: [],
        message: "Enter a valid 5-digit ZIP code.",
      });
      return;
    }
    const request = beginRequest("zip", zip);
    if (!request) return;
    try {
      const payload = await fetchZipLookup({ zipCode: zip, signal: request.controller.signal });
      if (request.sequence !== requestSequence.current) return;
      const lookup = classifyZipLookupState(payload);
      const results = [
        ...(payload?.house_rep ? [payload.house_rep] : []),
        ...(payload?.senators || []),
      ].filter(Boolean);
      setState({
        status: "ready",
        mode: "zip",
        results,
        lookup,
        message: `ZIP ${zip}: ${lookup.title}`,
      });
    } catch (error) {
      if (request.sequence !== requestSequence.current) return;
      if (error.message.includes("status 404")) {
        const lookup = classifyZipLookupState(null);
        setState({
          status: "ready",
          mode: "zip",
          results: [],
          lookup,
          message: `ZIP ${zip}: ${lookup.title}`,
        });
        return;
      }
      setState({
        status: "error",
        mode: "zip",
        results: [],
        message: "ZIP lookup is unavailable right now. Try a name search.",
      });
    } finally {
      finishRequest(request);
    }
  }

  async function searchName(event) {
    event.preventDefault();
    const query = name.trim();
    if (query.length < 2) {
      invalidateRequest();
      setState({
        status: "error",
        mode: "name",
        results: [],
        message: "Enter at least two letters of a representative’s name.",
      });
      return;
    }
    const request = beginRequest("name", query);
    if (!request) return;
    try {
      const payload = await fetchLegislatorSearch({ query, signal: request.controller.signal });
      if (request.sequence !== requestSequence.current) return;
      const results = (payload?.results || []).slice(0, 12);
      setState({
        status: "ready",
        mode: "name",
        results,
        message: results.length
          ? `Found ${results.length} ${results.length === 1 ? "match" : "matches"}.`
          : `No representatives matched “${query}.”`,
      });
    } catch {
      if (request.sequence !== requestSequence.current) return;
      setState({
        status: "error",
        mode: "name",
        results: [],
        message: "Name search is unavailable right now. Please try again.",
      });
    } finally {
      finishRequest(request);
    }
  }

  function cancelSearch() {
    const pending = pendingRequest.current;
    if (!pending) return;
    invalidateRequest();
    setState({
      status: "idle",
      mode: null,
      results: [],
      message: "Search cancelled. Submit a search when you're ready to try again.",
    });
    (pending.mode === "zip" ? zipInput : nameInput).current?.focus();
  }

  function dismiss() {
    invalidateRequest();
    onCancel?.();
  }

  function select(representative) {
    invalidateRequest();
    onSelect(representative);
  }

  return (
    <section
      aria-labelledby="representative-finder-heading"
      className={`border border-stone-200 bg-white ${
        compact
          ? "rounded-2xl p-4 sm:p-5"
          : "rounded-[1.75rem] p-5 shadow-[0_18px_48px_rgba(31,41,55,0.06)] sm:p-7 lg:p-8"
      }`}
      data-testid="representative-finder"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="eyebrow">Find your representative</p>
          <h2
            className="mt-2 font-serif text-3xl leading-tight text-stone-950 sm:text-4xl"
            id="representative-finder-heading"
          >
            Start with a person, not a score.
          </h2>
          <p className="mt-3 max-w-2xl text-base leading-7 text-stone-700">
            Search a ZIP code or name, then explore recorded actions issue by issue.
          </p>
        </div>
        {onCancel ? (
          <button className="secondary-button shrink-0" onClick={dismiss} type="button">
            Close
          </button>
        ) : null}
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <form className="rounded-2xl border border-stone-200 bg-stone-50 p-4" onSubmit={searchZip}>
          <label className="text-sm font-semibold text-stone-900" htmlFor="pass-a-zip">
            Search by ZIP
          </label>
          <div className="mt-2 flex flex-col gap-2 sm:flex-row">
            <input
              autoComplete="postal-code"
              className="field"
              id="pass-a-zip"
              inputMode="numeric"
              maxLength={5}
              onChange={(event) => setZip(event.target.value.replace(/\D/g, "").slice(0, 5))}
              placeholder="e.g. 27701"
              ref={zipInput}
              value={zip}
            />
            <button className="primary-button" type="submit">
              Find by ZIP
            </button>
          </div>
        </form>

        <form className="rounded-2xl border border-stone-200 bg-stone-50 p-4" onSubmit={searchName}>
          <label className="text-sm font-semibold text-stone-900" htmlFor="pass-a-name">
            Search by name
          </label>
          <div className="mt-2 flex flex-col gap-2 sm:flex-row">
            <input
              autoComplete="off"
              className="field"
              id="pass-a-name"
              onChange={(event) => setName(event.target.value)}
              placeholder="Representative name"
              ref={nameInput}
              value={name}
            />
            <button className="primary-button" type="submit">
              Search names
            </button>
          </div>
        </form>
      </div>

      <div
        aria-live="polite"
        aria-atomic="true"
        className={`mt-4 text-sm leading-6 ${
          state.status === "error" ? "text-rose-800" : "text-stone-600"
        }`}
        role={state.status === "error" ? "alert" : "status"}
        data-lookup-state={state.lookup?.state}
      >
        <p className={state.lookup ? "font-semibold text-stone-900" : ""}>{state.message}</p>
        {state.status === "loading" && state.slow ? (
          <p className="mt-2">This search is taking longer than expected. You can keep waiting, cancel it, or try a different search.</p>
        ) : null}
        {state.lookup ? (
          <div className={`mt-2 rounded-xl border p-3 ${
            state.lookup.severity === "warning"
              ? "border-amber-200 bg-amber-50 text-amber-950"
              : "border-stone-200 bg-stone-50 text-stone-700"
          }`}>
            <p>{state.lookup.message}</p>
            {state.lookup.caveats.map((caveat) => <p className="mt-2" key={caveat}>{caveat}</p>)}
          </div>
        ) : null}
      </div>

      {state.status === "loading" ? (
        <button className="secondary-button mt-3" onClick={cancelSearch} type="button">
          Cancel search
        </button>
      ) : null}

      {state.lookup ? (
        <button
          className="mt-2 min-h-11 text-sm font-semibold text-teal-900 underline"
          onClick={() => nameInput.current?.focus()}
          type="button"
        >
          Search by representative name
        </button>
      ) : null}

      {state.status === "ready" && state.mode === "zip" && state.lookup ? (
        <OfficialSiteHandoff purpose="verify-representation" />
      ) : null}

      {state.results.length ? (
        <>
          {state.mode === "zip" ? (
            <p className="mt-3 text-sm leading-6 text-stone-700" id="zip-record-inspection">
              Choose a loaded record to inspect. This ZIP result is not a confirmed address match.
            </p>
          ) : null}
          <div
            aria-label="Representative search results"
            className="mt-3 grid max-h-[22rem] gap-2 overflow-y-auto pr-1 sm:grid-cols-2"
            role="list"
          >
            {state.results.map((representative) => (
              <div key={representative.id} role="listitem">
                <button
                  aria-label={`Select ${representative.name_display}, ${formatOffice(representative)}`}
                  aria-describedby={state.mode === "zip" ? "zip-record-inspection" : undefined}
                  className="group min-h-20 w-full rounded-xl border border-stone-200 bg-white p-3 text-left transition hover:border-teal-700 focus-visible:border-teal-800"
                  onClick={() => select(representative)}
                  type="button"
                >
                  <span className="block text-base font-semibold text-stone-950 group-hover:text-teal-900">
                    {representative.name_display}
                  </span>
                  <span className="mt-1 block text-sm leading-5 text-stone-600">
                    {formatOffice(representative)}
                  </span>
                  {state.mode === "zip" ? <span className="mt-2 block text-xs font-semibold text-teal-900">Inspect loaded record</span> : null}
                </button>
              </div>
            ))}
          </div>
        </>
      ) : null}
    </section>
  );
}

function formatOffice(representative) {
  const chamber = representative.chamber === "senate" ? "U.S. Senate" : "U.S. House";
  const place = representative.chamber !== "senate" && representative.district
    ? `${representative.state} district ${String(representative.district).replace(/^0/, "")}`
    : `${representative.state}, statewide`;
  return `${chamber} · ${place} · ${formatParty(representative.party)}`;
}

function formatParty(party) {
  return { D: "Democratic", R: "Republican", I: "Independent" }[party]
    || String(party || "Party not listed");
}
