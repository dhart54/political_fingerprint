export default function ReviewedAnalysisSection({
  onSeeActions,
  presentation,
}) {
  if (!presentation?.review_state || presentation.tier === "receipts_only") {
    return null;
  }
  const support = (presentation.repeated_patterns || []).filter(
    (item) => item.direction === "support",
  );
  const opposition = (presentation.repeated_patterns || []).filter(
    (item) => item.direction === "opposition",
  );
  const mixed = [
    ...(presentation.repeated_patterns || []).filter(
      (item) => item.direction === "mixed",
    ),
    ...(presentation.policy_trajectories || []).filter(
      (item) => item.direction === "mixed",
    ),
  ];
  const copy = reviewCopy(presentation.review_state);

  return (
    <section
      className="scroll-mt-24 border-t border-stone-200 py-10"
      data-testid="reviewed-analysis"
      id="reviewed-analysis"
    >
      <div className="rounded-2xl border border-teal-900/15 bg-teal-50/60 p-5 sm:p-7">
        <span className="status-pill status-reviewed">
          {presentation.public_status_label}
        </span>
        <p className="mt-4 text-sm font-semibold text-teal-950">
          Reviewed scope: {formatCongressScope(presentation.review_state.congress_scope)}
          {" · "}
          {presentation.review_state.total_recorded_actions} actions in {copy.scopeNoun}
          {" · "}
          {presentation.review_state.complete_episode_count} policy episodes
        </p>
        <h3 className="mt-6 font-serif text-3xl leading-tight text-stone-950">
          {copy.conclusionTitle}
        </h3>
        <p className="mt-3 max-w-4xl text-lg leading-8 text-stone-800">
          {presentation.conclusion?.body || presentation.teaser}
        </p>
      </div>

      <FindingGroup
        items={support}
        onSeeActions={onSeeActions}
        title={`Where ${copy.subject} shows support`}
      />
      <FindingGroup
        items={opposition}
        onSeeActions={onSeeActions}
        title={`Where ${copy.subject} shows opposition`}
      />
      <FindingGroup
        items={mixed}
        onSeeActions={onSeeActions}
        tone="mixed"
        title="Where the record is mixed"
      />

      {presentation.limitations?.length ? (
        <div className="mt-10 border-t border-stone-200 pt-8">
          <h3 className="font-serif text-3xl leading-tight text-stone-950">
            {copy.limitationTitle}
          </h3>
          <div className="mt-5 grid gap-5 md:grid-cols-2">
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
          {presentation.scope_boundary ? (
            <p className="mt-6 max-w-4xl border-l-2 border-stone-300 pl-4 text-base leading-7 text-stone-700">
              {presentation.scope_boundary}
            </p>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

function FindingGroup({ items, onSeeActions, title, tone = "standard" }) {
  if (!items.length) {
    return null;
  }
  return (
    <div className="mt-10">
      <h3 className="font-serif text-3xl leading-tight text-stone-950">{title}</h3>
      <div className="mt-5 divide-y divide-stone-200 border-y border-stone-200">
        {items.map((item) => (
          <article
            className={tone === "mixed" ? "bg-amber-50/60 px-4 py-6" : "py-6"}
            key={item.proposition_id}
          >
            <h4 className="text-lg font-semibold leading-7 text-stone-950">
              {item.heading}
            </h4>
            <p className="mt-2 max-w-4xl text-base leading-7 text-stone-700">
              {item.body}
            </p>
            {item.action_ids?.length ? (
              <button
                aria-label={`Show ${item.action_ids.length} exact ${item.action_ids.length === 1 ? "action" : "actions"} for ${item.heading}`}
                className="secondary-button mt-4"
                onClick={() => onSeeActions(item.action_ids, item.heading)}
                type="button"
              >
                Show {item.action_ids.length} exact {item.action_ids.length === 1 ? "action" : "actions"}
              </button>
            ) : null}
          </article>
        ))}
      </div>
    </div>
  );
}

function formatCongressScope(scope) {
  return (scope || []).map((congress) => `${congress}th Congress`).join(", ");
}

function reviewCopy(reviewState) {
  const sample = reviewState.review_scope !== "full_defined_issue_record";
  return sample
    ? {
        conclusionTitle: "What this reviewed sample found",
        limitationTitle: "What this sample does not establish",
        scopeNoun: "the declared benchmark sample",
        subject: "the reviewed sample",
      }
    : {
        conclusionTitle: "What this full review found",
        limitationTitle: "What this review does not establish",
        scopeNoun: "the full defined issue record",
        subject: "the reviewed record",
      };
}
