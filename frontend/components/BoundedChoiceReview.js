export default function BoundedChoiceReview({ presentation }) {
  if (presentation?.presentation_branch !== "bounded_choice_review") return null;
  const records = presentation.records;
  const supporting = presentation.display_role === "supporting_notable_choice";
  const accounting = presentation.display_role === "non_directional_accounting";
  if (!supporting && !accounting) return null;

  return (
    <section
      className="rounded-2xl border border-stone-200 bg-white p-5 shadow-sm sm:p-8"
      data-testid="bounded-choice-review"
      data-display-role={presentation.display_role}
      data-member-id={presentation.member_id}
      data-presentation-sha256={presentation.presentation_subject_sha256}
    >
      <div className="flex flex-wrap items-center gap-3 text-sm">
        <span className="rounded-full bg-teal-50 px-3 py-1 font-semibold text-teal-950">
          {presentation.official_member_action}
        </span>
        <span className="text-stone-600">House · May 20, 2026 · S.2393</span>
      </div>
      <p className="mt-5 max-w-3xl text-sm leading-6 text-stone-600" data-testid="choice-scope">
        {records.scope_label.text}
      </p>
      <h2 className="mt-4 max-w-3xl font-serif text-2xl leading-snug text-stone-950 sm:text-3xl">
        {supporting ? records.finding_title.text : "Recorded Not Voting"}
      </h2>
      <p className="mt-4 max-w-3xl whitespace-pre-line text-base leading-7 text-stone-800" data-testid={supporting ? "supporting-choice" : "not-voting-accounting"}>
        {supporting ? records.finding.text : records.accounting.text}
      </p>
      <div className="mt-6 max-w-3xl border-l-2 border-stone-200 pl-4">
        <h3 className="text-sm font-semibold text-stone-900">Details and qualifications</h3>
        <p className="mt-2 whitespace-pre-line text-sm leading-6 text-stone-700" data-testid="choice-qualifications">
          {records.qualifications.text}
        </p>
      </div>
      <details className="mt-7 border-t border-stone-200 pt-5" data-testid="choice-receipts">
        <summary className="cursor-pointer font-semibold text-teal-900 underline decoration-teal-800/30 underline-offset-4">
          Inspect this vote and its sources
        </summary>
        <dl className="mt-4 grid gap-x-6 gap-y-3 text-sm sm:grid-cols-[8rem_1fr]">
          <dt className="font-semibold text-stone-700">House question</dt>
          <dd className="text-stone-700">{presentation.receipt.question}</dd>
          <dt className="font-semibold text-stone-700">Recorded action</dt>
          <dd className="text-stone-700">{presentation.official_member_action} · Roll {presentation.receipt.roll_number}</dd>
        </dl>
        <ul className="mt-4 flex flex-wrap gap-x-6 gap-y-3 text-sm">
          {presentation.sources.map((source) => (
            <li key={source.source_id}>
              <a className="font-medium text-teal-900 underline underline-offset-4" href={source.url} target="_blank" rel="noreferrer">
                {source.source_id.startsWith("clerk:") ? "Official House vote" : "Exact Senate-engrossed bill text"}
              </a>
            </li>
          ))}
        </ul>
      </details>
    </section>
  );
}
