import fs from "node:fs/promises";
import path from "node:path";
import { notFound } from "next/navigation";
import BoundedChoiceReview from "../../../components/BoundedChoiceReview";

export const dynamic = "force-dynamic";

export default async function HealthChoiceReview({ searchParams }) {
  // This candidate route is local development only, even if a deployment
  // accidentally receives the fixture flag. Public activation uses the normal
  // publication selector and shared component, never this route.
  if (process.env.NODE_ENV === "production" || process.env.ENABLE_HEALTH_CHOICE_REVIEW !== "1") notFound();
  const params = await searchParams;
  const member = params.member || "F000477";
  const names = { F000477: "Valerie Foushee", M001184: "Thomas Massie" };
  if (!Object.hasOwn(names, member)) notFound();
  const source = path.resolve(process.cwd(), "../docs/editorial/review_packages/health_bounded_choice_v1", `${member.toLowerCase()}-presentation.json`);
  let presentation;
  try {
    presentation = JSON.parse(await fs.readFile(source, "utf8"));
  } catch {
    notFound();
  }
  if (presentation.member_id !== member || presentation.presentation_branch !== "bounded_choice_review") notFound();
  return (
    <main className="mx-auto max-w-5xl px-4 py-8 sm:px-8 sm:py-12">
      <aside className="mb-7 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm leading-6 text-amber-950">
        Private preview · Content and rendering acceptance pending. This candidate is not published.
      </aside>
      <header className="mb-7">
        <p className="text-sm font-semibold uppercase tracking-wider text-stone-500">Health · One reviewed choice</p>
        <h1 className="mt-2 font-serif text-3xl text-stone-950 sm:text-4xl">{names[member]}</h1>
        <nav className="mt-4 flex flex-wrap gap-5 text-sm" aria-label="Review member">
          {Object.entries(names).map(([id, name]) => <a key={id} className="text-teal-900 underline underline-offset-4" aria-current={id === member ? "page" : undefined} href={`/review/health-choice?member=${id}`}>{name}</a>)}
        </nav>
      </header>
      <BoundedChoiceReview presentation={presentation} />
    </main>
  );
}
