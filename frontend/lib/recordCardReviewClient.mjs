async function request(resource, { legislatorId, scope = "all", domain } = {}) {
  const query = new URLSearchParams({ resource, member: legislatorId, scope });
  if (domain) query.set("domain", domain);
  const response = await fetch(`/api/review/record-card?${query}`, { cache: "no-store" });
  if (!response.ok) throw Error("Review input unavailable");
  return response.json();
}
export const recordCardReviewClient = {
  fetchLegislatorProfile: (args) => request("profile", args),
  fetchPositions: (args) => request("positions", args),
  fetchEditorialPresentations: (args) => request("editorial", args),
  fetchPositionEvidence: (args) => request("evidence", args),
};
