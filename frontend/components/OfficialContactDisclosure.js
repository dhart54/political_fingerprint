"use client";

import { useEffect, useId, useRef, useState } from "react";
import { fetchLegislatorContact } from "../lib/api";
import { buildContactDetails } from "../lib/officialContact.mjs";

export default function OfficialContactDisclosure({ legislatorId, representativeName }) {
  const [open, setOpen] = useState(false);
  const [state, setState] = useState({ status: "idle", details: null });
  const requestSequence = useRef(0);
  const trigger = useRef(null);
  const panelId = useId();
  useEffect(() => () => { requestSequence.current += 1; }, []);

  function close() {
    requestSequence.current += 1;
    setOpen(false);
    setState({ status: "idle", details: null });
    trigger.current?.focus({ preventScroll: true });
  }

  async function show() {
    const request = ++requestSequence.current;
    setOpen(true);
    setState({ status: "loading", details: null });
    try {
      // This existing GET receives member identity only, never vote/route context.
      const payload = await fetchLegislatorContact({ legislatorId });
      if (request !== requestSequence.current) return;
      setState({ status: "ready", details: buildContactDetails(payload, legislatorId) });
    } catch {
      if (request !== requestSequence.current) return;
      setState({ status: "error", details: null });
    }
  }

  return <div className="mt-4 border-t border-stone-200 pt-3" data-testid="official-contact">
    <button aria-controls={panelId} aria-expanded={open} className="source-link min-h-11 text-sm" onClick={open ? close : show} ref={trigger} type="button">
      Official contact information
    </button>
    {open ? <div aria-label="Official contact information" className="mt-2 rounded-lg border border-stone-200 bg-white px-3 py-3 text-sm leading-6 text-stone-700" id={panelId} role="region">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="font-semibold text-stone-950">Contact details for {representativeName || "this record"}</p>
        <button className="secondary-button text-sm" onClick={close} type="button">Close contact information</button>
      </div>
      {state.status === "loading" ? <p className="mt-2" role="status">Loading contact information.</p> : null}
      {state.status === "error" ? <p className="mt-2" role="alert">Contact information is unavailable right now.</p> : null}
      {state.status === "ready" ? <ContactDetails details={state.details} /> : null}
    </div> : null}
  </div>;
}

function ContactDetails({ details }) {
  if (details.status === "missing") return <p className="mt-2" role="status">Contact details are not loaded for this record.</p>;
  const hasContact = details.phone || details.websiteUrl || details.formUrl;
  return <>
    <p className="mt-2">{ORIGINS[details.origin]}</p>
    {!hasContact ? <p className="mt-2" role="status">Contact details are not available in this response.</p> : null}
    <div className="mt-2 flex flex-wrap items-center gap-x-5 gap-y-1">
      {details.phone ? <ContactLink href={details.phone.href}>Phone: {details.phone.text}</ContactLink> : null}
      {details.websiteUrl ? <ContactLink href={details.websiteUrl}>Official website</ContactLink> : null}
      {details.formUrl ? <ContactLink href={details.formUrl}>Contact form</ContactLink> : null}
    </div>
    {details.withheld ? <p className="mt-2">Some supplied contact details could not be displayed.</p> : null}
    <p className="mt-2 text-xs leading-5 text-stone-600">
      {details.sourceType || "Source type unavailable"}. {details.retrievedAt
        ? <span className="whitespace-nowrap">Retrieved: <time dateTime={details.retrievedAt}>{details.retrievedAt}</time>.</span>
        : "Retrieval date not supplied."}
    </p>
    {details.sourceUrl ? <ContactLink href={details.sourceUrl}>Source for contact details</ContactLink> : <p className="mt-1 text-xs text-stone-600">Source link not supplied.</p>}
  </>;
}

function ContactLink({ href, children }) {
  return <a className="source-link inline-flex min-h-11 items-center text-sm" href={href} referrerPolicy="no-referrer" rel="noopener noreferrer" target={href.startsWith("tel:") ? undefined : "_blank"}>{children}</a>;
}

const ORIGINS = {
  database: "Stored contact details.",
  curated_fallback: "Curated fallback contact details.",
  not_supplied: "Contact details supplied; data origin not specified.",
};
