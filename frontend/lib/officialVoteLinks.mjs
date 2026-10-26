// Official HTML pages link back to these exact XML routes. Verification examples
// and access limitations are recorded in docs/plans/frontend_loading_anchors_vote_links.md.
// Do not infer a vote from a bill, date, member, or other parent-measure context.
export function readableOfficialVoteUrl(sourceUrl) {
  let url;
  try { url = new URL(sourceUrl); } catch { return null; }
  if (!["https:", "http:"].includes(url.protocol) || url.username || url.password || url.port || url.search || url.hash) return null;

  if (url.hostname === "clerk.house.gov") {
    const match = /^\/evs\/(\d{4})\/roll(\d{3,4})\.xml$/.exec(url.pathname);
    if (match && Number(match[1]) >= 1990 && Number(match[1]) <= new Date().getUTCFullYear() && Number(match[2]) > 0) {
      return `https://clerk.house.gov/Votes/${match[1]}${Number(match[2])}`;
    }
  }
  // Other chambers/formats retain the supplied URL until the readable page's
  // exact source identity is verified; an apparent extension convention is insufficient.
  return null;
}
