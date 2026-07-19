import { notFound } from "next/navigation";

import GoldenRenderFixture from "../../components/GoldenRenderFixture";

export const dynamic = "force-dynamic";

export default function GoldenRenderFixturePage() {
  const isFixtureEnabled =
    process.env.ENABLE_GOLDEN_RENDER_FIXTURE === "1" || process.env.VERCEL_ENV === "preview";

  if (!isFixtureEnabled) {
    notFound();
  }

  return <GoldenRenderFixture />;
}
