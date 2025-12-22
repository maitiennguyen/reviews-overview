// frontend/src/app/places/[id]/SearchWithinPlace.tsx
"use client";

import { useMemo, useState } from 'react';
import Link from 'next/link';
import { searchReviews, type Review } from '@/lib/api';

type Props = {
  placeId: number;
  placeName: string;
};

export function SearchWithinPlace({ placeId, placeName }: Props) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Review[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  const highlight = (text: string, term: string) => {
    if (!term) return text;
    const escaped = term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const regex = new RegExp(`(${escaped})`, 'gi');
    return text.split(regex).map((part, idx) => {
      const isMatch = regex.test(part);
      regex.lastIndex = 0;
      if (isMatch) {
        return (
          <mark key={idx} className="bg-cyan-400/30 text-white px-1 rounded">
            {part}
          </mark>
        );
      }
      return <span key={idx}>{part}</span>;
    });
  };

  const limitMessage = useMemo(() => {
    if (!hasSearched) return null;
    if (results.length >= 20) {
      return 'Showing 20 results';
    }
    return `Showing ${results.length} result${results.length === 1 ? '' : 's'}.`;
  }, [hasSearched, results.length]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = query.trim();
    setHasSearched(true);
    if (!trimmed) {
      setResults([]);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await searchReviews(trimmed, placeId);
      setResults(data);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Something went wrong searching reviews.';
      setError(message);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="space-y-4 card p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-2xl font-semibold text-white">Search reviews at {placeName}</h2>
          <p className="text-slate-300 text-sm">
            Find mentions of an item within this place’s reviews.
          </p>
        </div>
        <Link
          href="/search"
          className="text-xs text-cyan-200 hover:text-cyan-100 underline-offset-4 hover:underline"
        >
          Global search
        </Link>
      </div>
      <form onSubmit={onSubmit} className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g., latte, burger, gluten"
          className="w-full sm:w-72 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-white shadow-sm focus:outline-none focus:ring-2 focus:ring-cyan-300/60"
        />
        <button
          type="submit"
          className="inline-flex items-center justify-center px-4 py-2 rounded-lg bg-cyan-400 text-slate-900 font-semibold hover:bg-cyan-300 transition disabled:opacity-60"
          disabled={loading}
        >
          {loading ? 'Searching…' : 'Search'}
        </button>
      </form>

      {error && (
        <div className="rounded border border-red-400/40 bg-red-500/10 text-red-100 px-4 py-3">
          {error}
        </div>
      )}

      {hasSearched && !loading && results.length === 0 && !error && (
        <p className="text-slate-400 text-sm">No reviews mention that keyword here.</p>
      )}

      {limitMessage && (
        <div className="text-xs text-slate-300">{limitMessage}</div>
      )}

      <div className="space-y-3">
        {results.map((review) => (
          <article key={review.id} className="rounded-lg border border-white/10 bg-white/5 p-4 space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-300">
              <span>{new Date(review.created_at).toLocaleDateString()}</span>
              <span className="pill bg-white/5 border border-white/10 text-slate-100">⭐ {review.rating}</span>
            </div>
            <p className="text-slate-100 leading-relaxed">{highlight(review.text, query)}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
