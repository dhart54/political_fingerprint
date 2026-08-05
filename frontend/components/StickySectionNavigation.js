export default function StickySectionNavigation({ hasAnalysis, hasEpisodes }) {
  const links = [
    ["issues", "Issues"],
    ...(hasAnalysis ? [["reviewed-analysis", "Issue summary"]] : []),
    ...(hasEpisodes ? [["policy-episodes", "Policy episodes"]] : []),
    ["vote-record", "Vote record"],
  ];
  return (
    <nav
      aria-label="Selected issue sections"
      className="sticky top-0 z-20 -mx-4 border-y border-stone-200 bg-[#f7f3e9]/95 px-4 py-2 backdrop-blur sm:mx-0 sm:rounded-xl sm:border sm:px-3"
    >
      <div className="flex gap-1 overflow-x-auto">
        {links.map(([id, label]) => (
          <a
            className="min-h-11 shrink-0 rounded-lg px-3 py-3 text-sm font-semibold text-stone-700 hover:bg-white hover:text-teal-900 focus-visible:bg-white"
            href={`#${id}`}
            key={id}
          >
            {label}
          </a>
        ))}
      </div>
    </nav>
  );
}
