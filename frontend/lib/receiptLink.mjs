import { actionReceiptId, buildPassAUrl, canonicalActionId } from "./frontendPassA.mjs";

// A receipt link owns exact vote identity, not a finding or local filter state.
export function buildReceiptLink(context, row) {
  const actionId = canonicalActionId(row);
  if (!context?.legislatorId || !context.issue || !actionId
      || !/^[a-zA-Z0-9_:-]+$/.test(actionId) || actionId.endsWith(":")) return "";
  const pathname = new URL(context.routePath || "/", "http://localhost").pathname;
  const url = new URL(buildPassAUrl(pathname, context), "http://localhost");
  url.hash = actionReceiptId(row);
  return `${url.pathname}${url.search}${url.hash}`;
}
