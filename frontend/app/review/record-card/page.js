import { notFound } from "next/navigation";
import RecordCardReviewJourney from "../../../components/RecordCardReviewJourney";
import { loadRecordCardReview, recordCardReviewEnabled, REVIEW_PROFILES } from "../../../lib/recordCardReviewServer.mjs";

export const dynamic = "force-dynamic";
export default function RecordCardReviewPage() {
  if (!recordCardReviewEnabled()) notFound();
  return <RecordCardReviewJourney candidate={loadRecordCardReview().candidate} profiles={REVIEW_PROFILES} />;
}
