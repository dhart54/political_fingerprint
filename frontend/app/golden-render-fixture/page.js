import { notFound } from "next/navigation";

import GoldenRenderFixture from "../../components/GoldenRenderFixture";

export const dynamic = "force-dynamic";

export default function GoldenRenderFixturePage() {
  if (process.env.ENABLE_GOLDEN_RENDER_FIXTURE !== "1") {
    notFound();
  }

  return <GoldenRenderFixture />;
}
