import { notFound } from "next/navigation";

import M6ReviewPage from "../../../components/M6ReviewPage";
import fixture from "../../../fixtures/foushee_justice_m6_review.json";

export default function FousheeJusticeM6Review() {
  if (process.env.ENABLE_M6_REVIEW_FIXTURE !== "1") {
    notFound();
  }
  return <M6ReviewPage fixture={fixture} />;
}
