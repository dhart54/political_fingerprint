import { recordCardReviewEnabled, reviewResponse } from "../../../../lib/recordCardReviewServer.mjs";

export const dynamic = "force-dynamic";
export async function GET(request) {
  if (!recordCardReviewEnabled()) return new Response(null, { status: 404 });
  try {
    const query = new URL(request.url).searchParams;
    const result = reviewResponse({ member: query.get("member"), scope: query.get("scope") || "all", resource: query.get("resource"), domain: query.get("domain") });
    if (!result) return new Response(null, { status: 404 });
    return Response.json(result.body, { status: result.status, headers: { "Cache-Control": "no-store", "X-Robots-Tag": "noindex, nofollow" } });
  } catch {
    return Response.json({ error: "Review inputs unavailable" }, { status: 503 });
  }
}
