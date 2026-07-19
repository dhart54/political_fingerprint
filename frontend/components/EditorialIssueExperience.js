"use client";

import { useId, useState } from "react";

import { buildImportantContext, groupOfficialSources } from "../lib/editorialIssuePresentation.mjs";

export default function EditorialIssueExperience({ experience }) {
  const [openRecordId, setOpenRecordId] = useState(null);
  if (!experience) return null;

  return (
    <section
      aria-label={`${experience.identity.issueDisplayName} editorial issue experience`}
      className="rounded-xl border border-cyan-900/20 bg-cyan-50/60 px-3 py-3 sm:px-4"
      data-testid="editorial-issue-experience"
    >
      {experience.publication.isReview ? (
        <p className="mb-3 rounded-lg border border-amber-300 bg-amber-50 px-3 py-2 text-xs font-semibold uppercase tracking-[0.14em] text-amber-900" data-testid="editorial-review-label">
          {experience.publication.reviewLabel || "Editorial review preview \u2014 not published"}
        </p>
      ) : null}

      <header>
        <p className="text-xs uppercase tracking-[0.18em] text-cyan-900">Issue summary</p>
        <h5 className="mt-1 font-serif text-[1.35rem] leading-tight text-stone-950 sm:text-[1.55rem]">
          {experience.identity.memberDisplayName} {"\u2014"} {experience.identity.issueDisplayName}
        </h5>
        {experience.identity.reviewedPeriod ? (
          <p className="mt-1 text-xs uppercase tracking-[0.12em] text-stone-500">{experience.identity.reviewedPeriod}</p>
        ) : null}
        {experience.synthesis.primary ? (
          <p className="mt-2 max-w-3xl text-base leading-7 text-stone-800">{experience.synthesis.primary}</p>
        ) : null}
        {experience.synthesis.evidenceBreadth ? (
          <p className="mt-2 text-xs font-medium uppercase tracking-[0.12em] text-cyan-950">
            {experience.synthesis.evidenceBreadth}
          </p>
        ) : null}
      </header>

      <RecordIndicators indicators={experience.indicators} />
      <SummaryPanels synthesis={experience.synthesis} />

      <div className="mt-4 flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-cyan-900">Reviewed record</p>
          <h6 className="mt-1 font-serif text-xl leading-tight text-stone-950">Vote explanations and context records</h6>
        </div>
        <p className="text-xs leading-5 text-stone-600">Open one record at a time for the first explanation layer.</p>
      </div>

      <div className="mt-3 grid gap-2.5">
        {experience.records.map((record) => (
          <EditorialRecordCard
            isOpen={openRecordId === record.id}
            key={record.id}
            onToggle={() => setOpenRecordId((current) => current === record.id ? null : record.id)}
            record={record}
          />
        ))}
      </div>
    </section>
  );
}

function RecordIndicators({ indicators = [] }) {
  if (!indicators.length) return null;
  return (
    <div aria-label="Reviewed record indicators" className="mt-3 flex flex-wrap gap-2">
      {indicators.map((indicator) => (
        <span className="rounded-full border border-cyan-900/15 bg-white px-3 py-1.5 text-xs tracking-[0.04em] text-cyan-950" key={indicator.key}>
          {indicator.label}
        </span>
      ))}
    </div>
  );
}

function SummaryPanels({ synthesis }) {
  const panels = [
    synthesis.patterns?.length ? { title: "Patterns in this sample", kind: "patterns", value: synthesis.patterns } : null,
    synthesis.votingContext ? { title: "Voting context", kind: "context", value: synthesis.votingContext, boundary: synthesis.votingContextBoundary } : null,
    synthesis.howToRead ? { title: "How to read this record", kind: "guidance", value: synthesis.howToRead } : null,
  ].filter(Boolean);
  if (!panels.length) return null;

  return (
    <div className={`mt-4 grid items-start gap-3 ${panels.length === 3 ? "lg:grid-cols-3" : panels.length === 2 ? "md:grid-cols-2" : "max-w-3xl"}`}>
      {panels.map((panel) => (
        <section className={`rounded-xl border px-3 py-3 sm:px-4 ${panel.kind === "patterns" ? "border-cyan-900/15 bg-white" : "border-stone-200 bg-stone-50"}`} key={panel.title}>
          <p className="text-xs uppercase tracking-[0.16em] text-cyan-900">{panel.title}</p>
          {panel.kind === "patterns" ? (
            <ul className="mt-2 grid gap-1.5 pl-5 text-sm leading-6 text-stone-800">
              {panel.value.map((pattern) => <li className="list-disc" key={pattern}>{pattern}</li>)}
            </ul>
          ) : (
            <p className="mt-2 text-sm leading-6 text-stone-800">{panel.value}</p>
          )}
          {panel.boundary ? <p className="mt-2 border-t border-stone-200 pt-2 text-xs leading-5 text-stone-600">{panel.boundary}</p> : null}
        </section>
      ))}
    </div>
  );
}

function EditorialRecordCard({ isOpen, onToggle, record }) {
  const generatedId = useId();
  const panelId = `${generatedId}-panel`;
  const context = buildImportantContext(record);
  const isContextOnly = record.inclusionClass === "context_only";

  return (
    <article
      className={`rounded-xl border ${isContextOnly ? "border-stone-200 bg-stone-50" : "border-cyan-900/15 bg-white shadow-[0_7px_20px_rgba(15,23,42,0.05)]"}`}
      data-inclusion-class={record.inclusionClass}
      data-testid={`editorial-record-${record.id}`}
    >
      <h6>
        <button
          aria-controls={panelId}
          aria-expanded={isOpen}
          className="w-full cursor-pointer px-3 py-3 text-left focus:outline-none focus:ring-2 focus:ring-inset focus:ring-cyan-800 sm:px-4"
          onClick={onToggle}
          type="button"
        >
          {isContextOnly ? <span className="block text-[11px] uppercase tracking-[0.16em] text-stone-500">Context-only record {"\u2014"} not included in substantive votes</span> : null}
          <span className="mt-1 flex items-start gap-2">
            <span aria-hidden="true" className="mt-0.5 text-cyan-900">{isOpen ? "\u25be" : "\u25b8"}</span>
            <span className={`${isContextOnly ? "text-sm font-normal" : "text-[1.02rem] font-semibold sm:text-[1.08rem]"} leading-6 text-stone-950`}>{record.headline}</span>
          </span>
          {!isContextOnly && record.practicalChoice ? <span className="mt-1 block pl-5 text-sm font-normal leading-6 text-stone-700">{record.practicalChoice}</span> : null}
          {!isContextOnly && record.actionAndResult ? <span className="mt-2 block rounded-lg bg-stone-50 px-3 py-2 text-sm font-normal leading-6 text-stone-800">{record.actionAndResult}</span> : null}
        </button>
      </h6>

      {isOpen ? (
        <div className="border-t border-stone-200 px-3 pb-3 pt-3 sm:px-4 sm:pb-4" id={panelId}>
          {isContextOnly ? (
            <>
              {record.practicalChoice ? <dl><Fact label="Why it is not counted" text={record.practicalChoice} /></dl> : null}
              <OfficialSources sources={record.sources} />
            </>
          ) : (
            <>
              <FirstExpansion record={record} />
              <DeeperDisclosure context={context} record={record} />
            </>
          )}
        </div>
      ) : null}
    </article>
  );
}

function FirstExpansion({ record }) {
  const changed = [record.whatChanged?.before, record.whatChanged?.changeAtStake].some(Boolean);
  const impact = [record.impactAndOutcome?.affected, record.impactAndOutcome?.scaleAndTiming, record.impactAndOutcome?.outcome].some(Boolean);
  if (!changed && !impact) return null;
  return (
    <div className={`grid gap-3 ${changed && impact ? "md:grid-cols-2" : ""}`}>
      {changed ? <FactGroup title="What changed"><Fact label="Before this vote" text={record.whatChanged.before} /><Fact label="Change at stake" text={record.whatChanged.changeAtStake} /></FactGroup> : null}
      {impact ? <FactGroup title="Impact and outcome"><Fact label="Who it affected" text={record.impactAndOutcome.affected} /><Fact label="Scale and timing" text={record.impactAndOutcome.scaleAndTiming} /><Fact label="Outcome" text={record.impactAndOutcome.outcome} /></FactGroup> : null}
    </div>
  );
}

function DeeperDisclosure({ context, record }) {
  const hasArguments = record.arguments?.supporters || record.arguments?.opponents;
  const hasBothArguments = record.arguments?.supporters && record.arguments?.opponents;
  const hasDetails = record.additionalDetail?.detail;
  const hasSources = record.sources?.length;
  if (!hasArguments && !hasDetails && !context.length && !hasSources) return null;
  return (
    <details className="mt-3 rounded-lg border border-stone-200 bg-stone-50 px-3 py-2.5">
      <summary className="cursor-pointer text-xs uppercase tracking-[0.14em] text-cyan-900 marker:text-cyan-900">Arguments, context, and sources</summary>
      <div className="mt-3 border-t border-stone-200 pt-3">
        {hasArguments ? (
          <div className={`grid items-start gap-3 ${hasBothArguments ? "md:grid-cols-2" : "max-w-3xl"}`}>
            <ArgumentField argument={record.arguments.supporters} label="Supporters argued" />
            <ArgumentField argument={record.arguments.opponents} label="Opponents argued" />
          </div>
        ) : null}
        {hasDetails ? <section className="mt-3"><p className="text-[11px] uppercase tracking-[0.14em] text-cyan-900">More detail</p><p className="mt-1 text-sm leading-6 text-stone-800">{record.additionalDetail.detail}</p></section> : null}
        {context.length ? <section className="mt-3"><p className="text-[11px] uppercase tracking-[0.14em] text-cyan-900">Important context</p><ul className="mt-1 grid gap-1.5 pl-5 text-sm leading-6 text-stone-800">{context.map((item) => <li className="list-disc" key={item}>{item}</li>)}</ul></section> : null}
        <OfficialSources sources={record.sources} />
      </div>
    </details>
  );
}

function FactGroup({ children, title }) {
  return <section className="border-l-2 border-cyan-900/25 pl-3"><p className="text-xs uppercase tracking-[0.14em] text-cyan-900">{title}</p><dl className="mt-2 grid gap-2">{children}</dl></section>;
}

function Fact({ label, text }) {
  if (!text) return null;
  return <div><dt className="text-[11px] font-medium uppercase tracking-[0.1em] text-stone-500">{label}</dt><dd className="mt-0.5 text-sm leading-5 text-stone-800">{text}</dd></div>;
}

function ArgumentField({ argument, label }) {
  if (!argument?.argument) return null;
  return <section className="rounded-lg border border-cyan-900/15 bg-white px-3 py-2.5"><p className="text-[11px] uppercase tracking-[0.14em] text-cyan-900">{label}</p><p className="mt-1 text-sm leading-6 text-stone-900">{argument.argument}</p>{argument.attribution ? <p className="mt-1 text-xs leading-5 text-stone-500">{"\u2014"} {argument.attribution}</p> : null}</section>;
}

function OfficialSources({ sources = [] }) {
  const groups = groupOfficialSources(sources);
  const count = groups.reduce((total, group) => total + group.items.length, 0);
  if (!count) return null;
  return (
    <details className="mt-3 border-t border-stone-200 pt-2">
      <summary className="cursor-pointer text-[11px] uppercase tracking-[0.14em] text-cyan-900 marker:text-cyan-900">Official sources ({count})</summary>
      <div className="mt-2 grid gap-2">
        {groups.map((group) => <section key={group.name}><p className="text-xs font-semibold text-stone-700">{group.name}</p><ul className="mt-1 grid gap-1 pl-4 text-xs leading-5 text-stone-600">{group.items.map((source) => <li className="list-disc" key={source.url}><a className="text-cyan-900 underline decoration-cyan-900/35 underline-offset-2 hover:decoration-cyan-900" href={source.url} rel="noreferrer" target="_blank">{source.name}</a>{source.locator ? <span className="block text-stone-500">{source.locator}</span> : null}</li>)}</ul></section>)}
      </div>
    </details>
  );
}
