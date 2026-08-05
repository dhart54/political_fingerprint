import { buildPatternIndex } from "../lib/selectedIssueExperience.mjs";

export default function ReviewedAnalysisSection({
  onSeeActions,
  presentation,
  rows = [],
}) {
  if (!presentation?.review_state || presentation.tier === "receipts_only") {
    return null;
  }
  const patterns = buildPatternIndex(presentation, rows);
  const reviewState = presentation.review_state;
  const conclusionBody = presentation.conclusion?.body || presentation.teaser;
  const hasLongConclusion = Boolean(
    presentation.conclusion?.body
    && presentation.conclusion.body !== presentation.teaser,
  );

  return (
    <section
      className="scroll-mt-24 border-t border-stone-200 py-10 sm:py-12"
      data-testid="reviewed-analysis"
      id="reviewed-analysis"
    >
      <div className="flex flex-wrap items-center gap-x-3 gap-y-2 text-sm text-stone-600">
        <span className="rounded-full bg-teal-950 px-3 py-1 font-semibold text-white">
          {reviewTypeLabel(reviewState.review_scope)}
        </span>
        <span>{reviewState.total_recorded_actions} reviewed actions</span>
        <span aria-hidden="true">·</span>
        <span>{reviewState.complete_episode_count} policy episodes</span>
        <span aria-hidden="true">·</span>
        <span>{formatCongressScope(reviewState.congress_scope)}</span>
      </div>

      <div className="mt-7 max-w-5xl border-l-4 border-teal-800 pl-5 sm:pl-7">
        <p className="eyebrow text-teal-800">Main takeaway</p>
        <h3 className="mt-2 font-serif text-3xl leading-tight text-stone-950 sm:text-4xl">
          {presentation.conclusion?.headline || "What this issue record shows"}
        </h3>
        <p className="mt-4 max-w-4xl text-lg leading-8 text-stone-800">
          {presentation.teaser || conclusionBody}
        </p>
        {hasLongConclusion ? (
          <details className="mt-4 max-w-4xl text-base leading-7 text-stone-700">
            <summary className="cursor-pointer font-semibold text-teal-900 underline decoration-teal-800/30 underline-offset-4">
              Read the full reviewed conclusion
            </summary>
            <p className="mt-3">{conclusionBody}</p>
          </details>
        ) : null}
      </div>

      {patterns.length ? (
        <div className="mt-12">
          <div className="max-w-3xl">
            <p className="eyebrow">Pattern index</p>
            <h3 className="mt-2 font-serif text-3xl leading-tight text-stone-950">
              The strongest repeated patterns, in proportion
            </h3>
            <p className="mt-3 text-base leading-7 text-stone-700">
              Bar length reflects the number of exact actions attached to each reviewed pattern. It is not a score.
            </p>
          </div>
          <div className="mt-6 divide-y divide-stone-200 border-y border-stone-200">
            {patterns.map((pattern) => (
              <PatternRow
                key={pattern.proposition_id}
                onSeeActions={onSeeActions}
                pattern={pattern}
              />
            ))}
          </div>
        </div>
      ) : null}

      <p className="mt-10 max-w-4xl border-l-2 border-stone-300 pl-4 text-sm leading-6 text-stone-600">
        Based on reviewed recorded actions; this does not infer motive, ideology, character, future behavior, or voting advice.
      </p>

      {presentation.limitations?.length ? (
        <details className="mt-8 border-y border-stone-200 py-5">
          <summary className="cursor-pointer text-base font-semibold text-stone-950">
            Limitations and unresolved actions · {presentation.limitations.length}
          </summary>
          <div className="mt-5 grid gap-6 md:grid-cols-2">
            {presentation.limitations.map((limitation, index) => (
              <article key={`${limitation.heading}-${index}`}>
                <h4 className="text-base font-semibold text-stone-950">
                  {limitation.heading}
                </h4>
                <p className="mt-2 text-base leading-7 text-stone-700">
                  {limitation.body}
                </p>
              </article>
            ))}
          </div>
        </details>
      ) : null}

      {presentation.scope_boundary ? (
        <details className="mt-4 max-w-4xl text-sm leading-6 text-stone-600">
          <summary className="cursor-pointer font-semibold text-stone-800">
            Scope boundary
          </summary>
          <p className="mt-3 border-l-2 border-stone-300 pl-4">
            {presentation.scope_boundary}
          </p>
        </details>
      ) : null}
    </section>
  );
}

function PatternRow({ onSeeActions, pattern }) {
  const episodeText = pattern.episodeCount
    ? `${pattern.episodeCount} ${pattern.episodeCount === 1 ? "episode" : "episodes"}`
    : "episode count not supplied";
  return (
    <article className="grid gap-4 py-6 md:grid-cols-[minmax(0,1fr)_12rem] md:items-center">
      <div>
        <div className="flex flex-wrap items-center gap-2 text-xs font-semibold uppercase tracking-[0.1em]">
          <span className={pattern.direction === "mixed" ? "text-amber-800" : "text-teal-800"}>
            {pattern.statusLabel}
          </span>
          <span className="text-stone-500">
            {pattern.actionCount} exact {pattern.actionCount === 1 ? "action" : "actions"} · {episodeText}
          </span>
        </div>
        <h4 className="mt-2 text-lg font-semibold leading-7 text-stone-950">
          {pattern.heading}
        </h4>
        {pattern.shortExplanation ? (
          <p className="mt-1 text-sm leading-6 text-stone-600">{pattern.shortExplanation}.</p>
        ) : null}
        <details className="mt-3 text-sm leading-6 text-stone-700">
          <summary className="cursor-pointer font-semibold text-stone-800">Read pattern explanation</summary>
          <p className="mt-2 max-w-3xl">{pattern.body}</p>
        </details>
        <button
          aria-label={`Show ${pattern.actionCount} exact ${pattern.actionCount === 1 ? "action" : "actions"} for ${pattern.heading}`}
          className="mt-4 font-semibold text-teal-900 underline decoration-teal-800/30 underline-offset-4"
          onClick={() => onSeeActions(pattern.actionIds, pattern.heading, {
            direction: pattern.direction,
            episodeCount: pattern.episodeCount,
          })}
          type="button"
        >
          Show exact actions
        </button>
      </div>
      <div aria-label={`${pattern.actionCount} exact actions relative to the largest pattern`}>
        <div className="h-2 overflow-hidden rounded-full bg-stone-200">
          <div
            className={`h-full rounded-full ${pattern.direction === "mixed" ? "bg-amber-500" : "bg-teal-700"}`}
            style={{ width: `${pattern.relativeWeight}%` }}
          />
        </div>
        <p className="mt-2 text-right text-xs text-stone-500">{pattern.actionCount} actions</p>
      </div>
    </article>
  );
}

function formatCongressScope(scope) {
  return (scope || []).map((congress) => `${congress}th Congress`).join(", ");
}

function reviewTypeLabel(value) {
  if (value === "full_defined_issue_record") {
    return "Full reviewed record";
  }
  if (value === "benchmark_sample") {
    return "Reviewed record sample";
  }
  return "Bounded reviewed record";
}
