"use client";

import { useId, useState } from "react";

import {
  buildImportantContext,
  fousheeEconomyIssueRead,
  groupOfficialSources,
} from "../lib/editorialGoldPresentation.mjs";


export default function ApprovedEditorialSlice({ editorialSlice }) {
  const [openItem, setOpenItem] = useState(null);

  if (!editorialSlice) {
    return null;
  }

  const counts = editorialSlice.slice_counts;

  function toggleItem(itemKey) {
    setOpenItem((current) => (current === itemKey ? null : itemKey));
  }

  return (
    <section
      aria-label="Focused Economy and Taxes explanations"
      className="rounded-xl border border-cyan-900/20 bg-cyan-50/60 px-3 py-3 sm:px-4"
      data-testid="approved-editorial-slice"
    >
      <div>
        <p className="text-xs uppercase tracking-[0.18em] text-cyan-900">Issue summary</p>
        <h5 className="mt-1 font-serif text-[1.35rem] leading-tight text-stone-950 sm:text-[1.55rem]">
          Valerie P. Foushee — Economy &amp; Taxes
        </h5>
        <p className="mt-2 max-w-4xl text-base leading-7 text-stone-800">
          {fousheeEconomyIssueRead.primarySummary}
        </p>
      </div>

      <RecordIndicators counts={counts} />

      <div className="mt-4 grid items-start gap-3 lg:grid-cols-3">
        <section className="rounded-xl border border-cyan-900/15 bg-white px-3 py-3 sm:px-4">
          <p className="text-xs uppercase tracking-[0.16em] text-cyan-900">Patterns in this sample</p>
          <ul className="mt-2 grid gap-1.5 pl-5 text-sm leading-6 text-stone-800">
            {fousheeEconomyIssueRead.patterns.map((pattern) => (
              <li className="list-disc" key={pattern}>{pattern}</li>
            ))}
          </ul>
        </section>

        <section className="rounded-xl border border-stone-200 bg-white px-3 py-3 sm:px-4">
          <p className="text-xs uppercase tracking-[0.16em] text-cyan-900">Voting context</p>
          <p className="mt-2 text-sm leading-6 text-stone-800">{fousheeEconomyIssueRead.votingContext}</p>
          <p className="mt-2 border-t border-stone-200 pt-2 text-xs leading-5 text-stone-600">
            {fousheeEconomyIssueRead.votingContextBoundary}
          </p>
        </section>
        <section className="rounded-xl border border-stone-200 bg-stone-50 px-3 py-3 sm:px-4">
          <p className="text-xs uppercase tracking-[0.16em] text-cyan-900">How to read this record</p>
          <p className="mt-2 text-sm leading-6 text-stone-700">{fousheeEconomyIssueRead.howToRead}</p>
        </section>
      </div>

      <div className="mt-4 flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-cyan-900">Reviewed record</p>
          <h6 className="mt-1 font-serif text-xl leading-tight text-stone-950">
            Vote explanations and context records
          </h6>
        </div>
        <p className="text-xs leading-5 text-stone-600">Open one record at a time for the first explanation layer.</p>
      </div>

      <div className="mt-3 grid gap-2.5">
        {editorialSlice.interpretations.map((entry) => {
          const itemKey = `vote-${entry.roll}`;
          return (
            <ApprovedInterpretationCard
              entry={entry}
              isOpen={openItem === itemKey}
              key={`approved-${entry.roll}`}
              onToggle={() => toggleItem(itemKey)}
            />
          );
        })}
        {editorialSlice.controls.map((entry) => {
          const itemKey = `control-${entry.roll}`;
          return (
            <ApprovedControlCard
              entry={entry}
              isOpen={openItem === itemKey}
              key={itemKey}
              onToggle={() => toggleItem(itemKey)}
            />
          );
        })}
      </div>
    </section>
  );
}


function RecordIndicators({ counts }) {
  const indicators = [
    `${counts.substantive_rolls} substantive votes`,
    `${counts.policy_episodes} policy episodes`,
    `${counts.not_voting_records} Not Voting`,
    `${counts.context_controls} context-only records`,
  ];

  return (
    <div aria-label="Reviewed record indicators" className="mt-3 flex flex-wrap gap-2">
      {indicators.map((indicator) => (
        <span
          className="rounded-full border border-cyan-900/15 bg-white px-3 py-1.5 text-xs tracking-[0.04em] text-cyan-950"
          key={indicator}
        >
          {indicator}
        </span>
      ))}
    </div>
  );
}


function ApprovedInterpretationCard({ entry, isOpen, onToggle }) {
  const id = useId();
  const panelId = `${id}-panel`;
  const importantContext = buildImportantContext(entry);

  return (
    <article
      className="rounded-xl border border-cyan-900/15 bg-white shadow-[0_7px_20px_rgba(15,23,42,0.05)]"
      data-testid={`approved-editorial-roll-${entry.roll}`}
    >
      <h6>
        <button
          aria-controls={panelId}
          aria-expanded={isOpen}
          className="w-full cursor-pointer px-3 py-3 text-left focus:outline-none focus:ring-2 focus:ring-inset focus:ring-cyan-800 sm:px-4"
          onClick={onToggle}
          type="button"
        >
          <span className="flex items-start gap-2">
            <span aria-hidden="true" className="mt-0.5 text-cyan-900">{isOpen ? "▾" : "▸"}</span>
            <span className="text-[1.02rem] font-semibold leading-6 text-stone-950 sm:text-[1.08rem]">
              {entry.ten_second.headline}
            </span>
          </span>
          <span className="mt-1 block pl-5 text-sm font-normal leading-6 text-stone-700">
            {entry.ten_second.practical_choice}
          </span>
          <span className="mt-2 block rounded-lg bg-stone-50 px-3 py-2 text-sm font-normal leading-6 text-stone-800">
            {entry.ten_second.member_action_and_result}
          </span>
        </button>
      </h6>

      {isOpen ? (
        <div className="border-t border-stone-200 px-3 pb-3 pt-3 sm:px-4 sm:pb-4" id={panelId}>
          <div className="grid gap-3 md:grid-cols-2">
            <CompactGroup title="What changed">
              <CompactFact label="Before this vote" text={entry.thirty_second.prior_baseline} />
              <CompactFact label="Change at stake" text={entry.thirty_second.mechanism} />
            </CompactGroup>
            <CompactGroup title="Impact and outcome">
              <CompactFact label="Who it affected" text={entry.thirty_second.affected} />
              <CompactFact label="Scale and timing" text={entry.thirty_second.scale_or_timing} />
              <CompactFact label="Outcome" text={entry.thirty_second.what_happened_next} />
            </CompactGroup>
          </div>

          <details className="mt-3 rounded-lg border border-stone-200 bg-stone-50 px-3 py-2.5">
            <summary className="cursor-pointer text-xs uppercase tracking-[0.14em] text-cyan-900 marker:text-cyan-900">
              Arguments, context, and sources
            </summary>
            <div className="mt-3 border-t border-stone-200 pt-3">
              <div className="grid gap-3 md:grid-cols-2">
                <ArgumentField argument={entry.two_minute.supporter_argument} label="Supporters argued" />
                <ArgumentField argument={entry.two_minute.opponent_argument} label="Opponents argued" />
              </div>
              <section className="mt-3">
                <p className="text-[11px] uppercase tracking-[0.14em] text-cyan-900">More detail</p>
                <p className="mt-1 text-sm leading-6 text-stone-800">{entry.two_minute.detail}</p>
              </section>
              <ImportantContext items={importantContext} />
              <OfficialSources sources={entry.two_minute.sources} />
            </div>
          </details>
        </div>
      ) : null}
    </article>
  );
}


function ApprovedControlCard({ entry, isOpen, onToggle }) {
  const id = useId();
  const panelId = `${id}-panel`;

  return (
    <article
      className="rounded-xl border border-stone-200 bg-stone-50"
      data-testid={`approved-editorial-control-${entry.roll}`}
    >
      <h6>
        <button
          aria-controls={panelId}
          aria-expanded={isOpen}
          className="w-full cursor-pointer px-3 py-3 text-left focus:outline-none focus:ring-2 focus:ring-inset focus:ring-cyan-800 sm:px-4"
          onClick={onToggle}
          type="button"
        >
          <span className="block text-[11px] uppercase tracking-[0.16em] text-stone-500">
            Context-only record — not included in the six substantive votes
          </span>
          <span className="mt-1 flex items-start gap-2 text-sm leading-6 text-stone-800">
            <span aria-hidden="true" className="text-cyan-900">{isOpen ? "▾" : "▸"}</span>
            <span>{entry.context_summary}</span>
          </span>
        </button>
      </h6>
      {isOpen ? (
        <div className="border-t border-stone-200 px-3 pb-3 pt-3 sm:px-4" id={panelId}>
          <p className="text-[11px] uppercase tracking-[0.14em] text-cyan-900">Why it is not counted</p>
          <p className="mt-1 text-sm leading-6 text-stone-800">{entry.why_not_counted}</p>
          <OfficialSources sources={entry.sources} />
        </div>
      ) : null}
    </article>
  );
}


function CompactGroup({ children, title }) {
  return (
    <section className="border-l-2 border-cyan-900/25 pl-3">
      <p className="text-xs uppercase tracking-[0.14em] text-cyan-900">{title}</p>
      <dl className="mt-2 grid gap-2">{children}</dl>
    </section>
  );
}


function CompactFact({ label, text }) {
  return (
    <div>
      <dt className="text-[11px] font-medium uppercase tracking-[0.1em] text-stone-500">{label}</dt>
      <dd className="mt-0.5 text-sm leading-5 text-stone-800">{text}</dd>
    </div>
  );
}


function ArgumentField({ argument, label }) {
  return (
    <section className="rounded-lg border border-cyan-900/15 bg-white px-3 py-2.5">
      <p className="text-[11px] uppercase tracking-[0.14em] text-cyan-900">{label}</p>
      <p className="mt-1 text-sm leading-6 text-stone-900">{argument.argument}</p>
      <p className="mt-1 text-xs leading-5 text-stone-500">— {argument.attribution}</p>
    </section>
  );
}


function ImportantContext({ items }) {
  return (
    <section className="mt-3 border-t border-stone-200 pt-3">
      <p className="text-[11px] uppercase tracking-[0.14em] text-cyan-900">Important context</p>
      <ul className="mt-1 grid gap-1 pl-4 text-sm leading-5 text-stone-700">
        {items.map((item) => (
          <li className="list-disc" key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}


function OfficialSources({ sources }) {
  const groups = groupOfficialSources(sources);
  const count = groups.reduce((total, group) => total + group.items.length, 0);

  return (
    <details className="mt-3 border-t border-stone-200 pt-3">
      <summary className="cursor-pointer text-xs uppercase tracking-[0.14em] text-cyan-900 marker:text-cyan-900">
        Official sources ({count})
      </summary>
      <div className="mt-2 grid gap-3 md:grid-cols-2">
        {groups.map((group) => (
          <section key={group.name}>
            <p className="text-[11px] uppercase tracking-[0.12em] text-stone-500">{group.name}</p>
            <ul className="mt-1 grid gap-2 text-sm leading-5">
              {group.items.map((source) => (
                <li key={source.url}>
                  <a
                    className="text-cyan-900 underline decoration-cyan-900/30 underline-offset-4 hover:decoration-cyan-900"
                    href={source.url}
                    rel="noreferrer"
                    target="_blank"
                  >
                    {source.name}
                  </a>
                  <span className="mt-0.5 block text-xs leading-5 text-stone-500">{source.locator}</span>
                </li>
              ))}
            </ul>
          </section>
        ))}
      </div>
    </details>
  );
}
