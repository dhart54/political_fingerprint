"use client";

import { useState } from "react";
import { groupOfficialSources } from "../lib/editorialIssuePresentation.mjs";

export default function EditorialIssueExperience({ experience }) {
  if (!experience) return null;
  const presentation = experience.publicPresentation;

  return (
    <section
      aria-label={`${experience.identity.memberDisplayName} ${experience.identity.issueDisplayName} reviewed issue record`}
      className="rounded-xl border border-cyan-900/20 bg-cyan-50/60 px-3 py-3 sm:px-4"
      data-coverage-state={presentation.coverage?.state}
      data-public-surface="editorial-issue"
      data-testid="editorial-issue-experience"
    >
      <header>
        <p className="text-xs uppercase tracking-[0.18em] text-cyan-900">Reviewed issue record</p>
        <h4 className="mt-1 font-serif text-[1.55rem] leading-tight text-stone-950 sm:text-[1.85rem]">
          {experience.identity.memberDisplayName} {"—"} {experience.identity.issueDisplayName}
        </h4>
        {presentation.conclusion ? <p className="mt-3 max-w-[78ch] text-[1.08rem] leading-7 text-stone-900">{presentation.conclusion}</p> : null}
        {presentation.strengthLabel ? <p className="mt-3 w-fit rounded-full border border-cyan-900/15 bg-white px-3 py-1.5 text-xs font-medium text-cyan-950">{presentation.strengthLabel}</p> : null}
        {presentation.coverageLine ? <p className="mt-3 text-sm font-medium leading-6 text-stone-700" data-testid="editorial-coverage-line">{presentation.coverageLine}</p> : null}
        {presentation.proceduralContextLine ? <p className="mt-1 text-xs leading-5 text-stone-500">{presentation.proceduralContextLine}</p> : null}
        {presentation.coverageNote ? <p className="mt-2 text-xs leading-5 text-stone-600"><span className="font-semibold text-stone-700">Coverage note:</span> {presentation.coverageNote}</p> : null}
        {presentation.methodNote ? <p className="mt-1 text-xs leading-5 text-stone-600"><span className="font-semibold text-stone-700">Method note:</span> {presentation.methodNote}</p> : null}
      </header>

      <AnalyticalFindings sections={presentation.analyticalSections} />

      {experience.featuredEpisodes.length ? <section className="mt-5" aria-labelledby="featured-episodes-title">
        <p className="text-xs uppercase tracking-[0.18em] text-cyan-900">Evidence behind the conclusion</p>
        <h5 className="mt-1 font-serif text-xl leading-tight text-stone-950" id="featured-episodes-title">Featured policy episodes</h5>
        <div className="mt-3 grid gap-3">
          {experience.featuredEpisodes.map((episode) => <EpisodeCard episode={episode} key={episode.id} />)}
        </div>
      </section> : null}

      <CompleteRecord experience={experience} />

      {presentation.votingContext ? (
        <details className="mt-4 rounded-xl border border-stone-200 bg-white px-3 py-2.5">
          <summary className="cursor-pointer text-xs uppercase tracking-[0.14em] text-cyan-900 marker:text-cyan-900">Secondary voting context</summary>
          <p className="mt-2 text-sm leading-6 text-stone-700">{presentation.votingContext}</p>
        </details>
      ) : null}
    </section>
  );
}

function AnalyticalFindings({ sections = [] }) {
  if (!sections.length) return null;
  return (
    <div className="mt-4 grid items-start gap-3 md:grid-cols-2" data-testid="editorial-analytical-findings">
      {sections.map((section) => (
        <section className="rounded-xl border border-cyan-900/15 bg-white px-3 py-3 sm:px-4" key={section.key}>
          <h5 className="text-xs uppercase tracking-[0.16em] text-cyan-900">{section.title}</h5>
          <ul className="mt-2 grid gap-1.5 pl-5 text-sm leading-6 text-stone-800">
            {section.items.map((item, index) => <li className="list-disc" key={`${item.episodeId || "finding"}-${index}`}>{item.text}</li>)}
          </ul>
        </section>
      ))}
    </div>
  );
}

function EpisodeCard({ episode, compact = false }) {
  const [expanded, setExpanded] = useState(false);
  const actionLabel = episode.actionCount === 1 ? "View episode" : `View episode and ${episode.actionCount} related actions`;
  const showTrajectoryDetail = episode.actionCount > 1
    && episode.memberTrajectoryDetail
    && normalizeText(episode.memberTrajectoryDetail) !== normalizeText(episode.memberTrajectory);
  return (
    <details
      className="group rounded-xl border border-cyan-900/15 bg-white shadow-[0_7px_20px_rgba(15,23,42,0.04)]"
      data-episode-id={episode.id}
      onToggle={(event) => setExpanded(event.currentTarget.open)}
    >
      <summary aria-expanded={expanded} className="cursor-pointer list-none px-3 py-3 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-cyan-800 sm:px-4">
        <span className="flex items-start justify-between gap-3">
          <span>
            <span className="block text-[11px] uppercase tracking-[0.14em] text-stone-500">{episode.periodLabel}{episode.dateSpan ? ` · ${episode.dateSpan}` : ""}</span>
            <span className="mt-1 block text-[1.02rem] font-semibold leading-6 text-stone-950">{episode.title}</span>
          </span>
          <span className="shrink-0 rounded-full bg-cyan-50 px-2.5 py-1 text-[11px] text-cyan-950">{episode.actionCount} {episode.actionCount === 1 ? "action" : "related actions"}</span>
        </span>
        <span className="mt-2 block text-sm leading-6 text-stone-800">{episode.memberTrajectory}</span>
        <span className="mt-2 flex flex-wrap gap-1.5" aria-label="Action timeline">
          {episode.actions.map((action) => <ActionChip action={action} key={action.id} />)}
        </span>
        {episode.conclusionRelevance && !compact ? <span className="mt-2 block text-xs font-medium leading-5 text-cyan-900">{episode.conclusionRelevance}</span> : null}
        <span className="mt-3 flex items-center gap-2 text-xs font-semibold text-cyan-950">
          <span>{actionLabel}</span>
          <span aria-hidden="true" className="text-base leading-none transition-transform group-open:rotate-90">›</span>
        </span>
      </summary>
      <div className="border-t border-stone-200 px-3 pb-3 pt-3 sm:px-4 sm:pb-4">
        <EpisodeFact title="What this episode was about" text={episode.sharedQuestion} />
        {episode.materialDifferences ? <EpisodeFact title="How the proposals changed" text={episode.materialDifferences} /> : null}
        {showTrajectoryDetail ? <EpisodeFact title="The member's record across the episode" text={episode.memberTrajectoryDetail} /> : null}
        <div className="mt-3 grid gap-2.5">
          {episode.actions.map((action) => <ActionReceipt record={action} key={action.id} />)}
        </div>
      </div>
    </details>
  );
}

function ActionChip({ action }) {
  return <span className="rounded-full border border-stone-200 bg-stone-50 px-2.5 py-1 text-xs text-stone-700">{action.memberAction} · roll {action.roll}</span>;
}

function ActionReceipt({ record }) {
  return (
    <details className="rounded-lg border border-stone-200 bg-stone-50" data-action-status={record.actionStatus} data-testid={`editorial-record-${record.id}`}>
      <summary className="cursor-pointer px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-cyan-800">
        <span className="block text-[11px] uppercase tracking-[0.13em] text-stone-500">{record.legislativeStage} · House roll {record.roll}</span>
        <span className="mt-1 block text-sm font-semibold leading-6 text-stone-950">{record.headline}</span>
        <span className="mt-1 block text-sm leading-6 text-stone-700">{record.actionAndResult}</span>
      </summary>
      <div className="border-t border-stone-200 px-3 pb-3 pt-3">
        {record.practicalChoice ? <Fact label={record.presentationLabels?.practicalChoice || "The choice before the House"} text={record.practicalChoice} /> : null}
        <div className="mt-3 grid gap-3 md:grid-cols-2">
          <FactGroup title="What changed">
            <Fact label={record.presentationLabels?.priorBaseline || "Prior baseline"} text={record.whatChanged?.before} />
            <Fact label="Change at stake" text={record.whatChanged?.changeAtStake} />
          </FactGroup>
          <FactGroup title="Impact and outcome">
            <Fact label={record.presentationLabels?.affected || "Who or what was affected"} text={record.impactAndOutcome?.affected} />
            <Fact label="Scale and timing" text={record.impactAndOutcome?.scaleAndTiming} />
            <Fact label="Outcome" text={record.impactAndOutcome?.outcome} />
          </FactGroup>
        </div>
        <ActionDepth record={record} />
      </div>
    </details>
  );
}

function ActionDepth({ record }) {
  const hasArguments = record.arguments?.supporters || record.arguments?.opponents;
  const context = [...(record.importantContext || []), record.additionalDetail?.laterHistory].filter(Boolean);
  const hasDepth = hasArguments || record.additionalDetail?.detail || context.length || record.sources?.length;
  if (!hasDepth) return null;
  return (
    <details className="mt-3 rounded-lg border border-stone-200 bg-white px-3 py-2.5">
      <summary className="cursor-pointer text-xs uppercase tracking-[0.14em] text-cyan-900 marker:text-cyan-900">Arguments, context, and official sources</summary>
      <div className="mt-3 border-t border-stone-200 pt-3">
        {hasArguments ? (
          <div className={`grid items-start gap-3 ${record.arguments.supporters && record.arguments.opponents ? "md:grid-cols-2" : "max-w-3xl"}`}>
            <ArgumentField argument={record.arguments.supporters} label="Supporters argued" />
            <ArgumentField argument={record.arguments.opponents} label="Opponents argued" />
          </div>
        ) : null}
        {hasArguments ? <p className="mt-2 text-xs leading-5 text-stone-600">{record.argumentBoundary}</p> : null}
        {record.oneSidedArgumentNote ? <p className="mt-2 text-xs leading-5 text-stone-600">{record.oneSidedArgumentNote}</p> : null}
        {record.additionalDetail?.detail ? <section className="mt-3"><p className="text-[11px] uppercase tracking-[0.14em] text-cyan-900">More detail</p><p className="mt-1 text-sm leading-6 text-stone-800">{record.additionalDetail.detail}</p></section> : null}
        {context.length ? <section className="mt-3"><p className="text-[11px] uppercase tracking-[0.14em] text-cyan-900">{record.presentationLabels?.context || "Important context"}</p><ul className="mt-1 grid gap-1.5 pl-5 text-sm leading-6 text-stone-800">{context.map((item) => <li className="list-disc" key={item}>{item}</li>)}</ul></section> : null}
        <OfficialSources sources={record.sources} />
      </div>
    </details>
  );
}

function CompleteRecord({ experience }) {
  const auxiliary = experience.ungroupedRecords || [];
  return (
    <details className="mt-5 rounded-xl border border-cyan-900/15 bg-white px-3 py-3 sm:px-4" data-testid="complete-reviewed-record">
      <summary className="cursor-pointer font-semibold text-cyan-950 marker:text-cyan-900">Explore the complete reviewed record</summary>
      <div className="mt-3 grid gap-4 border-t border-stone-200 pt-3">
        {experience.completeRecord.map((family) => (
          <section key={family.id}>
            <p className="text-xs uppercase tracking-[0.14em] text-stone-500">Policy family · {humanize(family.id)}</p>
            {family.congresses.map((group) => (
              <div className="mt-2 grid gap-2" key={group.congress}>
                <p className="text-sm font-semibold text-stone-800">{group.congress}th Congress</p>
                {group.episodes.map((episode) => <EpisodeCard compact episode={episode} key={episode.id} />)}
              </div>
            ))}
          </section>
        ))}
        <AuxiliaryRecords records={auxiliary} />
        <ProceduralContext records={experience.proceduralRecords} />
      </div>
    </details>
  );
}

function AuxiliaryRecords({ records = [] }) {
  if (!records.length) return null;
  const groups = [
    ["substantive", "Substantive actions"],
    ["not_voting", "Not Voting actions"],
    ["present", "Present actions"],
    ["service_ineligible", "Actions outside the member's service"],
    ["missing_evidence", "Expected evidence unavailable"],
  ];
  return groups.map(([kind, title]) => {
    const matches = records.filter((record) => record.inclusionClass === kind);
    if (!matches.length) return null;
    return <section key={kind}><h6 className="text-sm font-semibold text-stone-900">{title}</h6><div className="mt-2 grid gap-2">{matches.map((record) => <ActionReceipt key={record.id} record={record} />)}</div></section>;
  });
}

function ProceduralContext({ records = [] }) {
  if (!records.length) return null;
  return (
    <details className="rounded-lg border border-stone-200 bg-stone-50 px-3 py-2.5">
      <summary className="cursor-pointer text-sm font-semibold text-stone-900">Procedural voting context</summary>
      <p className="mt-2 text-sm leading-6 text-stone-700">{records.length} floor-process {records.length === 1 ? "action was" : "actions were"} reviewed but not used to summarize support or opposition.</p>
      <div className="mt-2 grid gap-2">
        {records.map((record) => <ContextReceipt record={record} key={record.id} />)}
      </div>
    </details>
  );
}

function ContextReceipt({ record }) {
  return <details className="rounded-lg border border-stone-200 bg-white px-3 py-2"><summary className="cursor-pointer text-sm text-stone-800">House roll {record.roll}: {record.headline}</summary><p className="mt-2 text-sm leading-6 text-stone-700">{record.practicalChoice}</p><OfficialSources sources={record.sources} /></details>;
}

function EpisodeFact({ title, text }) {
  if (!text) return null;
  return <section className="mt-3 first:mt-0"><h6 className="text-xs uppercase tracking-[0.14em] text-cyan-900">{title}</h6><p className="mt-1 text-sm leading-6 text-stone-800">{text}</p></section>;
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
  return <section className="rounded-lg border border-cyan-900/15 bg-stone-50 px-3 py-2.5"><p className="text-[11px] uppercase tracking-[0.14em] text-cyan-900">{label}</p><p className="mt-1 text-sm leading-6 text-stone-900">{argument.argument}</p>{argument.attribution ? <p className="mt-1 text-xs leading-5 text-stone-500">— {argument.attribution}</p> : null}</section>;
}

function OfficialSources({ sources = [] }) {
  const groups = groupOfficialSources(sources);
  const count = groups.reduce((total, group) => total + group.items.length, 0);
  if (!count) return null;
  return (
    <details className="mt-3 border-t border-stone-200 pt-2">
      <summary className="cursor-pointer text-[11px] uppercase tracking-[0.14em] text-cyan-900 marker:text-cyan-900">Official sources ({count})</summary>
      <div className="mt-2 grid gap-2">{groups.map((group) => <section key={group.name}><p className="text-xs font-semibold text-stone-700">{group.name}</p><ul className="mt-1 grid gap-1 pl-4 text-xs leading-5 text-stone-600">{group.items.map((source) => <li className="list-disc" key={source.url}><a className="text-cyan-900 underline decoration-cyan-900/35 underline-offset-2" href={source.url} rel="noreferrer" target="_blank">{source.name}</a>{source.locator ? <span className="block text-stone-500">{source.locator}</span> : null}</li>)}</ul></section>)}</div>
    </details>
  );
}

function humanize(value) {
  return String(value || "").replace(/[-_]+/g, " ");
}

function normalizeText(value) {
  return String(value || "").toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
}
