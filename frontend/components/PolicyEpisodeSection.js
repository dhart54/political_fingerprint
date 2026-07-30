"use client";

import { useMemo, useState } from "react";

export default function PolicyEpisodeSection({ episodes = [] }) {
  const [expandedId, setExpandedId] = useState(null);
  const ordered = useMemo(
    () => [...episodes].sort((left, right) => (
      String(right.latest_action_date || "").localeCompare(
        String(left.latest_action_date || ""),
      )
      || Number(left.presentation_order ?? 0) - Number(right.presentation_order ?? 0)
    )),
    [episodes],
  );

  if (!ordered.length) {
    return null;
  }

  return (
    <section className="scroll-mt-24 border-t border-stone-200 py-10" id="policy-episodes">
      <p className="eyebrow">Reviewed episode presentation</p>
      <h3 className="mt-2 font-serif text-3xl leading-tight text-stone-950">
        Policy episodes
      </h3>
      <div className="mt-5 divide-y divide-stone-200 border-y border-stone-200">
        {ordered.map((episode) => {
          const expanded = expandedId === episode.episode_id;
          return (
            <article key={episode.episode_id}>
              <button
                aria-expanded={expanded}
                className="flex min-h-16 w-full items-start justify-between gap-4 py-5 text-left"
                onClick={() => setExpandedId(expanded ? null : episode.episode_id)}
                type="button"
              >
                <span>
                  <span className="block text-lg font-semibold text-stone-950">
                    {episode.title}
                  </span>
                  <span className="mt-1 block text-sm text-stone-600">
                    {episode.latest_action_date}
                  </span>
                </span>
                <span aria-hidden="true" className="text-xl text-teal-900">
                  {expanded ? "−" : "+"}
                </span>
              </button>
              {expanded ? <EpisodeDetail episode={episode} /> : null}
            </article>
          );
        })}
      </div>
    </section>
  );
}

function EpisodeDetail({ episode }) {
  const actions = [...(episode.exact_actions || [])].sort((left, right) => (
    String(left.action_date || "").localeCompare(String(right.action_date || ""))
  ));
  return (
    <div className="grid gap-5 pb-6 text-base leading-7 text-stone-700 md:grid-cols-2">
      <EpisodeField label="Practical policy question" value={episode.practical_policy_question} />
      <EpisodeField label="Member record" value={episode.member_record} />
      <EpisodeField label="Outcome" value={episode.outcome} />
      <EpisodeField label="What would change" value={episode.what_would_change} />
      <EpisodeField label="Affected people or institutions" value={episode.affected_people_or_institutions} />
      <EpisodeField label="Current status" value={episode.current_status} />
      <EpisodeField label="Supporter argument" value={episode.supporter_argument_summary} />
      <EpisodeField label="Opponent argument" value={episode.opponent_argument_summary} />
      <EpisodeField label="Source limitation" value={episode.one_sided_source_limitation} />
      <EpisodeField label="Context and caveats" value={episode.context_and_caveats} />
      <EpisodeSources sources={episode.official_sources} />
      {actions.length ? (
        <div className="md:col-span-2">
          <h4 className="font-semibold text-stone-950">Exact actions, oldest first</h4>
          <ol className="mt-2 list-decimal space-y-1 pl-5">
            {actions.map((action) => (
              <li key={action.action_id}>
                {action.action_date}: {action.label}
              </li>
            ))}
          </ol>
        </div>
      ) : null}
    </div>
  );
}

function EpisodeSources({ sources }) {
  const normalized = (Array.isArray(sources) ? sources : [])
    .map((source) => {
      if (typeof source === "string" && /^https?:\/\//.test(source)) {
        return { label: "Official episode source", url: source };
      }
      if (source && typeof source === "object") {
        const url = source.url || source.source_url;
        if (typeof url === "string" && /^https?:\/\//.test(url)) {
          return {
            label: source.label || source.title || "Official episode source",
            url,
          };
        }
      }
      return null;
    })
    .filter(Boolean);
  if (!normalized.length) {
    return null;
  }
  return (
    <div>
      <h4 className="font-semibold text-stone-950">Official sources</h4>
      <ul className="mt-1 space-y-1">
        {normalized.map((source) => (
          <li key={source.url}>
            <a className="source-link" href={source.url} rel="noreferrer" target="_blank">
              {source.label}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}

function EpisodeField({ label, value }) {
  if (!value) {
    return null;
  }
  return (
    <div>
      <h4 className="font-semibold text-stone-950">{label}</h4>
      <p className="mt-1">{value}</p>
    </div>
  );
}
