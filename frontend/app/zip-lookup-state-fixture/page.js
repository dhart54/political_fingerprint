import { notFound } from "next/navigation";

import ZipLookupStateFixture from "../../components/ZipLookupStateFixture";

export const dynamic = "force-dynamic";

export default function ZipLookupStateFixturePage() {
  if (process.env.ENABLE_ZIP_LOOKUP_STATE_FIXTURE !== "1") {
    notFound();
  }

  return <ZipLookupStateFixture />;
}
