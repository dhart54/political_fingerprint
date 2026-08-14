import SemanticIcon from "./SemanticIcon";
import {
  buildFindingIndex,
  buildPatternIndex,
} from "../lib/selectedIssueExperience.mjs";

export default function ReviewedAnalysisSection({
  onSeeActions,
  presentation,
  rows = [],
}) {
  if (!presentation?.review_state || presentation.tier === "receipts_only") {
    return null;
  }
  const overview = presentation.overview || null;
  const syntheses = buildFindingIndex(presentation, rows, "syntheses");
  const patterns = overview
    ? buildFindingIndex(presentation, rows, "repeated_patterns")
    : buildPatternIndex(presentation, rows);
  const trajectories = overview
    ? buildFindingIndex(presentation, rows, "policy_trajectories")
    : [];
  const notableChoices = buildFindingIndex(presentation, rows, "notable_choices");
  const takeaway = overview?.primary_sentence
    || presentation.teaser
    || presentation.conclusion?.body
    || "";
  const overviewClarification = overview?.secondary_clarification || "";
  const legacyAdditionalConclusion = overview
    ? ""
    : additionalConclusionText(takeaway, presentation.conclusion?.body);

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
        {overviewClarification ? (
          <p className="mt-4 text-base leading-7 text-stone-700">
            {overviewClarification}
          </p>
        ) : null}
        {legacyAdditionalConclusion ? (
          <details className="mt-4 text-base leading-7 text-stone-700">
            <summary className="cursor-pointer font-semibold text-teal-900 underline decoration-teal-800/30 underline-offset-4">
              Read the complete conclusion
            </summary>
            <p className="mt-3 max-w-4xl">{legacyAdditionalConclusion}</p>
          </details>
        ) : null}
        {overview ? (
          <div className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-2 text-sm">
            <span className="font-medium text-stone-600">
              {overview.evidence_count_label}
            </span>
            <SupportingVotesButton
              item={{
                actionCount: overview.action_ids.length,
                actionIds: overview.action_ids,
                heading: overview.public_title || overview.title,
                wording_item_id: overview.wording_item_id,
              }}
              onSeeActions={onSeeActions}
            />
          </div>
        ) : null}
      </div>

      {syntheses.length ? (
        <FindingSection
          heading="What the record shows across choices"
          items={syntheses}
          onSeeActions={onSeeActions}
          tone="featured"
        />
      ) : null}

      {patterns.length ? (
        <FindingSection
          heading="Patterns in this issue record"
          items={patterns}
          onSeeActions={onSeeActions}
        />
      ) : null}

      {trajectories.length ? (
        <FindingSection
          heading="A limiting trajectory"
          items={trajectories}
          onSeeActions={onSeeActions}
        />
      ) : null}

      {notableChoices.length ? (
        <details className="mt-8 border-y border-stone-200 py-4">
          <summary className="cursor-pointer text-base font-semibold text-stone-950">
            Other notable choices · {notableChoices.length}
          </summary>
          <div className="mt-4 divide-y divide-stone-200 border-t border-stone-200">
            {notableChoices.map((item) => (
              <FindingRow
                item={item}
                key={item.wording_item_id || item.proposition_id}
                onSeeActions={onSeeActions}
              />
            ))}
          </div>
        </details>
      ) : null}

      <p className="mt-6 max-w-4xl text-sm leading-6 text-stone-600">
        Based on reviewed recorded actions; this does not infer motive, ideology, character, future behavior, or voting advice.
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

function FindingSection({ heading, items, onSeeActions, tone = "plain" }) {
  return (
    <div className="mt-8">
      <h3 className="font-serif text-2xl leading-tight text-stone-950 sm:text-[1.65rem]">
        {heading}
      </h3>
      <div className={`mt-4 divide-y divide-stone-200 border-y border-stone-200 ${tone === "featured" ? "bg-white/45 px-4 sm:px-5" : ""}`}>
        {items.map((item) => (
          <FindingRow
            item={item}
            key={item.wording_item_id || item.proposition_id}
            onSeeActions={onSeeActions}
          />
        ))}
      </div>
    </div>
  );
}

function FindingRow({ item, onSeeActions }) {
  const heading = item.title || item.heading;
  const body = item.primary_sentence || item.body;
  const accounting = item.evidence_count_label || fallbackAccounting(item);
  const showDirection = item.showDirection !== false && Boolean(item.direction);
  const limitations = item.limitations || [];
  return (
    <article className={`grid gap-3 py-4 sm:items-start sm:gap-5 ${
      showDirection
        ? "sm:grid-cols-[8.5rem_minmax(0,1fr)_auto]"
        : "sm:grid-cols-[minmax(0,1fr)_auto]"
    }`}>
      {showDirection ? (
        <div className={`flex min-h-8 items-center gap-3 pattern-${item.direction}`}>
          <SemanticIcon kind={item.direction} />
          <span className="semantic-label text-sm font-semibold">
            {item.statusLabel}
          </span>
        </div>
      ) : null}
      <div className="min-w-0">
        <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
          <h4 className="text-base font-semibold leading-6 text-stone-950">
            {heading}
          </h4>
          <span className="text-sm leading-6 text-stone-600">{accounting}</span>
        </div>
        <p className="mt-1 max-w-4xl text-sm leading-6 text-stone-700">
          {body}
        </p>
        {item.secondary_clarification ? (
          <p className="mt-2 max-w-4xl text-sm leading-6 text-stone-600">
            {item.secondary_clarification}
          </p>
        ) : null}
        {limitations.length ? (
          <details className="mt-2 text-sm leading-6 text-stone-600">
            <summary className="cursor-pointer font-medium text-stone-700">
              Boundaries and limitations
            </summary>
            <ul className="mt-2 list-disc space-y-1 pl-5">
              {limitations.map((limitation) => (
                <li key={limitation}>{limitation}</li>
              ))}
            </ul>
          </details>
        ) : null}
      </div>
      <SupportingVotesButton item={{ ...item, heading }} onSeeActions={onSeeActions} />
    </article>
  );
}

function SupportingVotesButton({ item, onSeeActions }) {
  const governedWordingItem = Boolean(item.wording_item_id);
  const voteLabel = `${item.actionCount} ${item.actionCount === 1 ? "vote" : "votes"}`;
  return (
    <button
      aria-label={governedWordingItem
        ? `View supporting votes for ${item.heading}`
        : `View ${voteLabel} for ${item.heading}`}
      className="justify-self-start font-semibold text-teal-900 underline decoration-teal-800/30 underline-offset-4 sm:justify-self-end"
      onClick={() => onSeeActions(item.actionIds, item.heading, {
        direction: item.direction,
        episodeCount: item.episodeCount,
        showDirection: item.showDirection,
        statusLabel: item.statusLabel,
      })}
      type="button"
    >
      {governedWordingItem
        ? `View supporting ${item.actionCount === 1 ? "vote" : "votes"}`
        : `View ${voteLabel}`}
    </button>
  );
}

function fallbackAccounting(pattern) {
  const voteText = `${pattern.actionCount} ${pattern.actionCount === 1 ? "vote" : "votes"}`;
  const episodeText = pattern.episodeCount
    ? `${pattern.episodeCount} ${pattern.episodeCount === 1 ? "episode" : "episodes"}`
    : "episode count unavailable";
  return pattern.direction === "mixed"
    ? `${voteText} within ${episodeText}`
    : `${voteText} · ${episodeText}`;
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
