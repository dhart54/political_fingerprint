import { recordCardUrl } from "../lib/recordCard.mjs";

export function followRecordLink(event, state = {}) {
  if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
  event.preventDefault();
  window.history.pushState(state, "", event.currentTarget.href);
  window.dispatchEvent(new PopStateEvent("popstate"));
}

export default function RecordCardFinding({ entry, legislatorId, scope, receiptsVisible, routePath = "/" }) {
  const finding = entry.sourceFinding;
  const link = (options) => recordCardUrl(routePath, { legislatorId, scope, ...options });
  return <section className="scroll-mt-28 py-6" id="finding-detail" aria-labelledby="finding-detail-heading" data-testid="card-finding-detail">
    <a className="inline-flex min-h-11 items-center text-sm font-semibold text-teal-900 underline underline-offset-4" href={link({ hash: "record-at-a-glance" })} onClick={(e) => followRecordLink(e, { returnCardEntry: entry.id })}>← Return to record at a glance</a>
    <p className="eyebrow mt-3">Reviewed finding · {entry.reviewedScope}</p>
    <h3 id="finding-detail-heading" tabIndex={-1} className="mt-2 max-w-4xl font-serif text-3xl leading-tight text-stone-950">{finding.public_title || finding.title || finding.heading}</h3>
    {entry.detail_paragraphs ? <div className="mt-4 max-w-4xl space-y-3 text-base leading-7 text-stone-800" data-testid="card-finding-explanation">{entry.detail_paragraphs.map((text) => <p key={text}>{text}</p>)}</div> : <>
      <p className="mt-4 max-w-4xl text-base leading-7 text-stone-800">{finding.primary_sentence || finding.body}</p>
      {finding.secondary_clarification ? <p className="mt-3 max-w-4xl text-base leading-7 text-stone-700">{finding.secondary_clarification}</p> : null}
      {finding.limitations?.length ? <ul className="mt-4 max-w-4xl list-disc space-y-2 pl-5 text-sm leading-6 text-stone-600">{finding.limitations.map((limit) => <li key={limit}>{limit}</li>)}</ul> : null}
    </>}
    <p className="mt-3 text-sm text-stone-600">{entry.evidence_label}</p>
    <div className="mt-4 flex flex-wrap gap-4">
      {!receiptsVisible ? <a className="primary-button inline-flex items-center" href={link({ issue: entry.issue_id, findingId: entry.finding_id, sourceHash: entry.sourcePresentationHash, view: "receipts", hash: "vote-record" })} onClick={followRecordLink} aria-label={`See ${entry.action_ids.length} House votes: ${entry.headline}`}>See {entry.action_ids.length} House votes</a> : null}
      <a className="secondary-button inline-flex items-center" href={link({ issue: entry.issue_id, hash: "vote-record" })} onClick={followRecordLink}>Complete issue record / all votes</a>
    </div>
  </section>;
}
