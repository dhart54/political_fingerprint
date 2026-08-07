import SemanticIcon from "./SemanticIcon";
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
  const takeaway = presentation.teaser || presentation.conclusion?.body || "";
  const additionalConclusion = additionalConclusionText(
    takeaway,
    presentation.conclusion?.body,
  );

  return (
    <section
      className="scroll-mt-24 border-t border-stone-200 pb-10 pt-8 sm:pb-12 sm:pt-10"
      data-testid="reviewed-analysis"
      id="reviewed-analysis"
    >
      <div className="max-w-[58rem]">
        <p className="eyebrow">Main takeaway</p>
        <p className="mt-3 font-serif text-2xl leading-[1.38] text-stone-950 sm:text-[1.7rem]">
          {takeaway}
        </p>
        {additionalConclusion ? (
          <details className="mt-4 text-base leading-7 text-stone-700">
            <summary className="cursor-pointer font-semibold text-teal-900 underline decoration-teal-800/30 underline-offset-4">
              Read the complete conclusion
            </summary>
            <p className="mt-3 max-w-4xl">{additionalConclusion}</p>
          </details>
        ) : null}
      </div>

      {patterns.length ? (
        <div className="mt-8">
          <h3 className="font-serif text-2xl leading-tight text-stone-950 sm:text-[1.65rem]">
            Patterns in this issue record
          </h3>
          <div className="mt-4 divide-y divide-stone-200 border-y border-stone-200">
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

      <p className="mt-6 max-w-4xl text-sm leading-6 text-stone-600">
        This issue summary describes the reviewed record; it does not infer motive, character, future behavior, or voting advice.
      </p>

      {presentation.limitations?.length ? (
        <details className="mt-6 border-y border-stone-200 py-4">
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
        <details className="mt-3 border-b border-stone-200 pb-4 text-sm leading-6 text-stone-600">
          <summary className="cursor-pointer font-semibold text-stone-800">
            Scope boundary
          </summary>
          <p className="mt-3 max-w-4xl border-l-2 border-stone-300 pl-4">
            {presentation.scope_boundary}
          </p>
        </details>
      ) : null}
    </section>
  );
}

function PatternRow({ onSeeActions, pattern }) {
  const voteText = `${pattern.actionCount} ${pattern.actionCount === 1 ? "vote" : "votes"}`;
  const episodeText = pattern.episodeCount
    ? `${pattern.episodeCount} ${pattern.episodeCount === 1 ? "episode" : "episodes"}`
    : "episode count unavailable";
  const accounting = pattern.direction === "mixed"
    ? `${voteText} within ${episodeText}`
    : `${voteText} · ${episodeText}`;
  return (
    <article className="grid gap-3 py-4 sm:grid-cols-[8.5rem_minmax(0,1fr)_auto] sm:items-center sm:gap-5">
      <div className={`flex items-center gap-3 pattern-${pattern.direction}`}>
        <SemanticIcon kind={pattern.direction} />
        <span className="text-sm font-semibold">{pattern.statusLabel}</span>
      </div>
      <div className="min-w-0">
        <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
          <h4 className="text-base font-semibold leading-6 text-stone-950">
            {pattern.heading}
          </h4>
          <span className="text-sm leading-6 text-stone-600">{accounting}</span>
        </div>
        <p className="mt-1 max-w-4xl text-sm leading-6 text-stone-700">
          {pattern.body}
        </p>
      </div>
      <button
        aria-label={`View ${pattern.actionCount} ${pattern.actionCount === 1 ? "vote" : "votes"} for ${pattern.heading}`}
        className="justify-self-start font-semibold text-teal-900 underline decoration-teal-800/30 underline-offset-4 sm:justify-self-end"
        onClick={() => onSeeActions(pattern.actionIds, pattern.heading, {
          direction: pattern.direction,
          episodeCount: pattern.episodeCount,
          statusLabel: pattern.statusLabel,
        })}
        type="button"
      >
        View {pattern.actionCount} {pattern.actionCount === 1 ? "vote" : "votes"}
      </button>
    </article>
  );
}

function additionalConclusionText(teaser, conclusion) {
  const lead = normalize(teaser);
  const body = String(conclusion || "").replace(/\s+/g, " ").trim();
  if (!body || normalize(body) === lead) {
    return "";
  }
  const firstBoundary = body.search(/[.!?](?=\s+[A-Z]|$)/);
  if (firstBoundary < 0) {
    return body;
  }
  const firstSentence = body.slice(0, firstBoundary + 1);
  const sharedOpening = normalize(firstSentence).slice(0, 52);
  if (sharedOpening && lead.startsWith(sharedOpening)) {
    return body.slice(firstBoundary + 1).trim();
  }
  return body;
}

function normalize(value) {
  return String(value || "")
    .normalize("NFKC")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}
