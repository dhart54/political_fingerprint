import { notFound } from "next/navigation";
import RecordCardReviewJourney from "../../../components/RecordCardReviewJourney";
import { loadRecordCardReview, recordCardReviewEnabled, REVIEW_PROFILES } from "../../../lib/recordCardReviewServer.mjs";

export const dynamic = "force-dynamic";
export default async function RecordCardReviewPage({ searchParams }) {
  if (!recordCardReviewEnabled()) notFound();
  const query = await searchParams;
  if (query.policy === "shared") return <RecordCardReviewJourney candidate={{ sharedPolicy: true }} profiles={REVIEW_PROFILES} dataSource={query.data === "live" ? "live" : "snapshot"} />;
  return <RecordCardReviewJourney candidate={loadRecordCardReview().candidate} profiles={REVIEW_PROFILES} />;
}
