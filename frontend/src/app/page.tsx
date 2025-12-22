// frontend/app/page.tsx
export default function HomePage() {
  return (
    <div className="space-y-10">
      <section className="card p-8 md:p-10">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-8">
          <div className="space-y-4 max-w-2xl">
            <p className="text-sm uppercase tracking-[0.2em] text-cyan-200">
              Bozeman Restautants and Cafes Reviews
            </p>
            <h1 className="text-4xl md:text-5xl font-semibold leading-tight text-white">
              Search real reviews for what to order.
            </h1>
            <p className="text-slate-200 text-lg max-w-2xl">
              revove pulls Google reviews for Bozeman spots so you can find item mentions fast.
            </p>
            <div className="flex flex-col sm:flex-row gap-3">
              <a
                href="/search"
                className="px-5 py-3 rounded-lg bg-cyan-400 text-slate-900 font-semibold shadow-lg shadow-cyan-500/30 hover:bg-cyan-300 transition"
              >
                Search reviews
              </a>
              <a
                href="/places"
                className="px-5 py-3 rounded-lg border border-white/15 text-white hover:border-cyan-300/60 hover:text-cyan-100 transition"
              >
                Browse places
              </a>
            </div>
          </div>
        </div>
      </section>

      <section className="grid md:grid-cols-2 gap-4">
        {[
          {
            title: 'Search by item',
            copy: 'Find every mention of “latte” or “burger” across Bozeman in one go.',
          },
          {
            title: 'Filter by place',
            copy: 'Zero in on a spot by name and get every mention of your item there.',
          },
        ].map((card) => (
          <div key={card.title} className="card p-4">
            <div className="text-sm uppercase tracking-[0.18em] text-cyan-200 mb-2">
              {card.title}
            </div>
            <p className="text-slate-200">{card.copy}</p>
          </div>
        ))}
      </section>
    </div>
  );
}
