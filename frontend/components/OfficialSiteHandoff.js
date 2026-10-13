// Static navigation only. Never accept location, member or vote context here.
const HOUSE_FINDER = "https://www.house.gov/representatives/find-your-representative";
const HOUSE_DIRECTORY = "https://www.house.gov/representatives";
const SENATE_DIRECTORY = "https://www.senate.gov/senators/index.htm";

export default function OfficialSiteHandoff({ purpose }) {
  if (!["verify-representation", "find-member"].includes(purpose)) return null;
  const verify = purpose === "verify-representation";
  return (
    <div
      aria-label={verify ? "Verify representation on official sites" : "Find this member in official directories"}
      className="mt-3 rounded-xl border border-stone-200 bg-stone-50 p-3 text-sm leading-6 text-stone-700"
      role="group"
    >
      <p className="font-semibold text-stone-950">
        {verify ? "Verify who represents you on official sites." : "Find this member in an official directory."}
      </p>
      <p className="mt-1">
        {verify
          ? "Enter any location details there yourself."
          : "Look for this member by name to find their website and contact options. Current directories may not include former members."}
      </p>
      <div className="mt-2 flex flex-wrap gap-x-5 gap-y-1">
        <OfficialLink href={verify ? HOUSE_FINDER : HOUSE_DIRECTORY}>
          {verify ? "Open official House finder" : "Open official House directory"}
        </OfficialLink>
        <OfficialLink href={SENATE_DIRECTORY}>Open official Senate directory</OfficialLink>
      </div>
      <p className="mt-1 text-xs text-stone-600">Links open in a new tab.</p>
    </div>
  );
}

function OfficialLink({ href, children }) {
  return <a className="source-link inline-flex min-h-11 items-center" href={href} referrerPolicy="no-referrer" rel="noopener noreferrer" target="_blank">{children}</a>;
}
