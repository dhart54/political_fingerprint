export default function HomePage() {
  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_#f3efe4,_#e7dcc5_52%,_#d8c7aa)] text-stone-900">
      <section className="mx-auto flex min-h-screen max-w-5xl flex-col justify-center px-6 py-20">
        <p className="mb-4 text-sm uppercase tracking-[0.35em] text-stone-600">
          Political Fingerprint
        </p>
        <h1 className="max-w-3xl font-serif text-5xl leading-tight sm:text-7xl">
          In 60 seconds, understand how this politician actually behaves.
        </h1>
        <p className="mt-6 max-w-2xl text-lg leading-8 text-stone-700">
          Deterministic civic analytics built from categorized policy votes,
          precomputed metrics, and neutral summaries.
        </p>
        <div className="mt-12 grid gap-4 sm:grid-cols-3">
          <article className="rounded-3xl border border-stone-300/70 bg-white/65 p-5 shadow-[0_18px_60px_rgba(72,52,24,0.08)] backdrop-blur">
            <p className="text-xs uppercase tracking-[0.3em] text-stone-500">
              Fingerprint
            </p>
            <p className="mt-3 text-sm leading-6 text-stone-700">
              Eight-domain vote emphasis with explicit zeroes and chamber median comparison.
            </p>
          </article>
          <article className="rounded-3xl border border-stone-300/70 bg-white/65 p-5 shadow-[0_18px_60px_rgba(72,52,24,0.08)] backdrop-blur">
            <p className="text-xs uppercase tracking-[0.3em] text-stone-500">
              Drift
            </p>
            <p className="mt-3 text-sm leading-6 text-stone-700">
              Deterministic stability measurement across early and recent voting windows.
            </p>
          </article>
          <article className="rounded-3xl border border-stone-300/70 bg-white/65 p-5 shadow-[0_18px_60px_rgba(72,52,24,0.08)] backdrop-blur">
            <p className="text-xs uppercase tracking-[0.3em] text-stone-500">
              Lookup
            </p>
            <p className="mt-3 text-sm leading-6 text-stone-700">
              ZIP-based representative and senator lookup backed by deterministic fixture data.
            </p>
          </article>
        </div>
      </section>
    </main>
  );
}
