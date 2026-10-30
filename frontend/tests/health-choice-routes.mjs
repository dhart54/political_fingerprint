import fs from "node:fs";
import { installPassARoutes, foushee, positions } from "./pass-a-fixtures.mjs";

export const transport = JSON.parse(fs.readFileSync(new URL("./fixtures/health-choice-api.json", import.meta.url), "utf8"));
export function responseFor(member, scope) {
  return transport.responses.find((r) => r.member_bioguide_id === member && r.scope === scope);
}
export async function installHealthRoutes(page, member) {
  const profile = member === "F000477" ? foushee : { ...foushee, id: "leg_thomas_massie", bioguide_id: member, name_display: "Thomas Massie", state: "KY", district: "04", party: "R" };
  await installPassARoutes(page, { positionsOverride: (scope) => ({ ...positions,
    scope_metadata: { congresses: scope === "all" ? [118,119] : [Number(scope)], requested_congresses: scope === "all" ? [118,119] : [Number(scope)] },
    positions: [...positions.positions, { domain: "HEALTH_SOCIAL", yea_count: member === "F000477" ? 1 : 0, nay_count: 0, other_count: member === "M001184" ? 1 : 0, total_votes: 1, recorded_votes: 1, interpreted_support_count: 0, interpreted_oppose_count: 0, interpreted_other_count: 0, interpreted_total: 0 }],
  }), evidenceOverrides: { HEALTH_SOCIAL: (scope) => scope === "118" ? [] : [{
    canonical_action_id: "house:119:2:180", roll_call_id: "house:119:2:180", rollcall_number: 180,
    congress: 119, chamber: "house", vote_date: "2026-05-20", bill_number: "S.2393",
    bill_title: "Fiscal Year 2025 Veterans Affairs Major Medical Facility Authorization Act",
    description: "On Motion to Suspend the Rules and Pass", question: "On Motion to Suspend the Rules and Pass",
    position: member === "F000477" ? "yea" : "not_voting", issue_domain: "HEALTH_SOCIAL",
    source_url: "https://clerk.house.gov/evs/2026/roll180.xml", vote_type: "final_passage",
  }] } });
  // Last route wins. Deliver exact Python API bytes: no frontend fixture
  // completion, requested_scope repair, tier replacement or field synthesis.
  await page.route("**/editorial-presentations?*", async (route) => {
    const scope = new URL(route.request().url()).searchParams.get("scope") || "all";
    await route.fulfill({ json: responseFor(member, scope) });
  });
  await page.route(`**/legislators/${profile.id}/profile`, (route) => route.fulfill({ json: profile }));
  return profile;
}
