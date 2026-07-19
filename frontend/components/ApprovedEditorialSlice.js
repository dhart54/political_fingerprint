export default function ApprovedEditorialSlice({ editorialSlice }) {
  if (!editorialSlice) {
    return null;
  }

  const counts = editorialSlice.slice_counts;

  return (
    <section
      aria-label="Focused Economy and Taxes explanations"
      className="rounded-xl border border-cyan-900/20 bg-cyan-50/60 px-3 py-3 sm:px-4"
    >
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-cyan-900">
            Focused explanations
          </p>
          <h5 className="mt-1 font-serif text-[1.35rem] leading-tight text-stone-950 sm:text-[1.55rem]">
            Key Economy &amp; Taxes votes, explained in layers
          </h5>
          <p className="mt-1 max-w-3xl text-sm leading-6 text-stone-700">
            Six substantive votes cover four policy episodes. One Not Voting record and two context-only votes stay visible without being counted as support or opposition.
          </p>
        </div>
        <span className="w-fit rounded-full bg-white px-3 py-1 text-xs uppercase tracking-[0.14em] text-cyan-950">
          {counts.substantive_rolls + counts.not_voting_records + counts.context_controls} records
        </span>
      </div>

      <div className="mt-3 grid gap-2.5">
        {editorialSlice.interpretations.map((entry) => (
          <ApprovedInterpretationCard entry={entry} key={`approved-${entry.roll}`} />
        ))}
        {editorialSlice.controls.map((entry) => (
          <ApprovedControlCard entry={entry} key={`control-${entry.roll}`} />
        ))}
      </div>
    </section>
  );
}


function ApprovedInterpretationCard({ entry }) {
  return (
    <details
      className="group rounded-xl border border-cyan-900/15 bg-white shadow-[0_7px_20px_rgba(15,23,42,0.05)]"
      data-testid={`approved-editorial-roll-${entry.roll}`}
    >
      <summary className="cursor-pointer px-3 py-3 marker:text-cyan-900 sm:px-4">
        <span className="pr-4 text-[1.02rem] font-semibold leading-6 text-stone-950 sm:text-[1.08rem]">
          {entry.ten_second.headline}
        </span>
        <span className="mt-1 block pr-4 text-sm leading-6 text-stone-700">
          {entry.ten_second.practical_choice}
        </span>
        <span className="mt-2 block rounded-lg bg-stone-50 px-3 py-2 text-sm leading-6 text-stone-800">
          {entry.ten_second.member_action_and_result}
        </span>
      </summary>

      <div className="border-t border-stone-200 px-3 pb-3 pt-3 sm:px-4 sm:pb-4">
        <div className="grid gap-2 md:grid-cols-2">
          <PublicField label="Before this vote" text={entry.thirty_second.prior_baseline} />
          <PublicField label="How it worked" text={entry.thirty_second.mechanism} />
          <PublicField label="Who or what it affected" text={entry.thirty_second.affected} />
          <PublicField label="Scale or timing" text={entry.thirty_second.scale_or_timing} />
          <PublicField
            className="md:col-span-2"
            label="What happened next"
            text={entry.thirty_second.what_happened_next}
          />
        </div>

        <details className="mt-3 rounded-xl border border-stone-200 bg-stone-50 px-3 py-2.5">
          <summary className="cursor-pointer text-xs uppercase tracking-[0.16em] text-cyan-900 marker:text-cyan-900">
            Arguments, history, caveats, and sources
          </summary>
          <div className="mt-3 grid gap-2 border-t border-stone-200 pt-3">
            <PublicField label="More detail" text={entry.two_minute.detail} />
            <ArgumentField argument={entry.two_minute.supporter_argument} label="Supporters argued" />
            <ArgumentField argument={entry.two_minute.opponent_argument} label="Opponents argued" />
            <PublicField label="Evidence boundary" text={entry.two_minute.argument_boundary} />
            <PublicField label="Later history" text={entry.two_minute.later_history} />
            <CaveatList caveats={entry.two_minute.caveats} />
            <SourceList sources={entry.two_minute.sources} />
          </div>
        </details>
      </div>
    </details>
  );
}


function ApprovedControlCard({ entry }) {
  return (
    <details
      className="group rounded-xl border border-stone-200 bg-stone-50"
      data-testid={`approved-editorial-control-${entry.roll}`}
    >
      <summary className="cursor-pointer list-none px-3 py-3 marker:hidden sm:px-4 [&::-webkit-details-marker]:hidden">
        <span className="block text-[11px] uppercase tracking-[0.16em] text-stone-500">
          Context record — not included in the six substantive votes
        </span>
        <span className="mt-1 block text-sm leading-6 text-stone-800">
          {entry.context_summary}
        </span>
        <span className="mt-2 block text-[11px] uppercase tracking-[0.14em] text-cyan-800 group-open:hidden">
          Why it stays separate
        </span>
      </summary>
      <div className="border-t border-stone-200 px-3 pb-3 pt-3 sm:px-4">
        <PublicField label="Why it is not counted" text={entry.why_not_counted} />
        <SourceList sources={entry.sources} />
      </div>
    </details>
  );
}


function PublicField({ className = "", label, text }) {
  return (
    <div className={`rounded-lg border border-stone-200 bg-white px-3 py-2.5 ${className}`}>
      <p className="text-[11px] uppercase tracking-[0.14em] text-cyan-900">{label}</p>
      <p className="mt-1 text-sm leading-6 text-stone-800">{text}</p>
    </div>
  );
}


function ArgumentField({ argument, label }) {
  return (
    <div className="rounded-lg border border-stone-200 bg-white px-3 py-2.5">
      <p className="text-[11px] uppercase tracking-[0.14em] text-cyan-900">{label}</p>
      <p className="mt-1 text-xs leading-5 text-stone-500">{argument.attribution}</p>
      <p className="mt-1 text-sm leading-6 text-stone-800">{argument.argument}</p>
    </div>
  );
}


function CaveatList({ caveats }) {
  return (
    <div className="rounded-lg border border-stone-200 bg-white px-3 py-2.5">
      <p className="text-[11px] uppercase tracking-[0.14em] text-cyan-900">Keep in mind</p>
      <ul className="mt-1 grid gap-1 pl-4 text-sm leading-6 text-stone-800">
        {caveats.map((caveat) => (
          <li className="list-disc" key={caveat}>{caveat}</li>
        ))}
      </ul>
    </div>
  );
}


function SourceList({ sources }) {
  return (
    <div className="rounded-lg border border-stone-200 bg-white px-3 py-2.5">
      <p className="text-[11px] uppercase tracking-[0.14em] text-cyan-900">Official sources</p>
      <ul className="mt-2 grid gap-2 text-sm leading-5">
        {sources.map((source) => (
          <li key={source.url}>
            <a
              className="break-words text-cyan-900 underline decoration-cyan-900/30 underline-offset-4 hover:decoration-cyan-900"
              href={source.url}
              rel="noreferrer"
              target="_blank"
            >
              {source.label}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}
