import { formatDomainLabel } from "../lib/issueDomains";
import { recordCardUrl, SECTION_ORDER } from "../lib/recordCard.mjs";
import { scopeLabel } from "../lib/frontendPassA.mjs";

const LABELS = { support: "Supported", opposition: "Opposed", mixed: "Different choices, kept together" };
const STATES = {
  loading: "Loading reviewed findings…",
  error: "Reviewed findings are unavailable right now. You can still explore the issue records below.",
  incomplete: "The reviewed finding inputs are incomplete. Explore the available issue records below.",
  identity_mismatch: "The returned findings do not match this representative and scope. Explore the issue records below.",
  source_mismatch: "The reviewed source has changed. This selection needs a fresh review; issue records remain available below.",
  empty: "No reviewed findings are available for this representative and scope. Start with an issue’s vote record below.",
  not_selected: "Reviewed issue findings are available below; a selection for this overview has not been prepared.",
};

export default function RecordAtAGlance({ model, legislatorId, scope, onNavigate }) {
  if (model.status !== "ready") return (
    <section className="border-y border-stone-300 py-5" aria-label="Reviewed findings status">
      <p role="status" className="text-base leading-7 text-stone-700">{STATES[model.status] || STATES.incomplete}</p>
      {model.status !== "loading" ? <a className="inline-flex min-h-11 items-center font-semibold text-teal-900 underline underline-offset-4" href="#issues">Explore all issues →</a> : null}
    </section>
  );
  return (
    <section className="scroll-mt-24 rounded-2xl border border-stone-300 bg-white/70 px-5 py-5 sm:px-7 sm:py-6" id="record-at-a-glance" aria-labelledby="record-card-heading" data-testid="record-card">
      <h2 className="font-serif text-3xl leading-tight text-stone-950 sm:text-4xl" id="record-card-heading" tabIndex={-1}>Record at a glance</h2>
      <p className="mt-2 text-base leading-6 text-stone-700">Selected findings from the reviewed voting record.</p>
      <p className="mt-2 text-sm leading-6 text-stone-600">Findings below: <strong className="font-semibold text-stone-800">119th Congress</strong> · Recorded-vote scope: {scopeLabel(scope)}</p>
      <div className="mt-5 grid gap-x-8 gap-y-5 md:grid-cols-2">
        {SECTION_ORDER.map((section) => {
          const entries = model.entries.filter((e) => e.section === section);
          return entries.length ? (
            <div key={section} className={section === "mixed" ? "md:col-span-2" : ""}>
              <h3 className="border-b border-stone-300 pb-2 text-sm font-bold uppercase tracking-widest text-stone-800">{LABELS[section]}</h3>
              <div className={section === "mixed" ? "grid gap-x-8 md:grid-cols-2" : ""}>
                {entries.map((entry) => (
                  <article className="min-w-0 border-b border-stone-200 py-4 last:border-b-0" key={entry.id} data-testid="record-card-entry">
                    <p className="text-xs font-semibold leading-5 text-teal-900">{formatDomainLabel(entry.issue_id)}</p>
                    <h4 className="mt-1 font-serif text-xl font-semibold leading-7 text-stone-950">{entry.headline}</h4>
                    {entry.explanation ? <p className="mt-2 text-sm leading-6 text-stone-700">{entry.explanation}</p> : null}
                    <p className="mt-2 text-xs leading-5 text-stone-600">{entry.evidence_label}</p>
                    <a className="inline-flex min-h-11 items-center text-sm font-semibold text-teal-900 underline decoration-teal-800/40 underline-offset-4" href={recordCardUrl("/review/record-card", { legislatorId, scope, issue: entry.issue_id, findingId: entry.finding_id, sourceHash: entry.sourcePresentationHash, hash: "finding-detail" })} onClick={(event) => onNavigate(event, entry)} aria-label={`Explore finding: ${entry.headline}`} id={entry.id}>Finding & supporting votes →</a>
                  </article>
                ))}
              </div>
            </div>
          ) : null;
        })}
      </div>
      <div className="mt-4 border-t border-stone-300 pt-4 text-sm leading-6 text-stone-600">
        <p>Reviewed findings available in {model.reviewedDomains.length} of 8 issues: {model.reviewedDomains.map(formatDomainLabel).join("; ")}.</p>
        <p className="mt-1">A selection of specific choices, not a complete statement of priorities. <a className="inline-flex min-h-11 items-center font-semibold text-teal-900 underline underline-offset-4" href="#issues">Explore all issues →</a></p>
        <details><summary className="min-h-11 cursor-pointer py-2 font-semibold text-stone-700">Coverage and review details</summary>
          <p>A precise review cutoff is not supplied. Findings cover their stated 119th-Congress reviewed records, even when all available Congresses are selected.</p>
          <p className="mt-2">This selection and shorter wording are candidates for product review. Card generated {model.generationTime}; this is not an evidence cutoff.</p>
        </details>
      </div>
    </section>
  );
}
