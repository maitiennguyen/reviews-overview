// frontend/src/app/search/page.tsx
"use client";

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { fetchPlaces, searchPlacesByName, searchReviews, type Place, type Review } from '@/lib/api';

function levenshtein(a: string, b: string): number {
  const m = a.length;
  const n = b.length;
  const dp = Array.from({ length: m + 1 }, (_, i) => i);

  for (let j = 1; j <= n; j++) {
    let prev = dp[0];
    dp[0] = j;
    for (let i = 1; i <= m; i++) {
      const temp = dp[i];
      if (a[i - 1] === b[j - 1]) {
        dp[i] = prev;
      } else {
        dp[i] = Math.min(prev, dp[i - 1], dp[i]) + 1;
      }
      prev = temp;
    }
  }
  return dp[m];
}

function similarity(a: string, b: string): number {
  const maxLen = Math.max(a.length, b.length);
  if (maxLen === 0) return 1;
  return 1 - levenshtein(a.toLowerCase(), b.toLowerCase()) / maxLen;
}

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Review[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);
  const [placeQuery, setPlaceQuery] = useState('');
  const [placeSuggestions, setPlaceSuggestions] = useState<Place[]>([]);
  const [allPlaces, setAllPlaces] = useState<Place[]>([]);
  const [selectedPlaces, setSelectedPlaces] = useState<Place[]>([]);
  const [placeLoading, setPlaceLoading] = useState(false);
  const pageNote = useMemo(() => {
    if (!hasSearched) return '';
    if (results.length >= 20) {
      return 'Showing first 20 results (API paginated). Narrow your keyword for deeper matches.';
    }
    return `Showing ${results.length} result${results.length === 1 ? '' : 's'}.`;
  }, [results.length, hasSearched]);

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

  useEffect(() => {
    fetchPlaces()
      .then(setAllPlaces)
      .catch(() => {});
  }, []);

  useEffect(() => {
    const term = placeQuery.trim();
    if (!term) {
      setPlaceSuggestions([]);
      return;
    }

    const timer = setTimeout(async () => {
      setPlaceLoading(true);
      try {
        const apiResults = await searchPlacesByName(term);
        if (apiResults.length > 0) {
          setPlaceSuggestions(apiResults);
          return;
        }
        const fuzzy = allPlaces
          .map((p) => ({ place: p, score: similarity(term, p.name) }))
          .filter((p) => p.score >= 0.55)
          .sort((a, b) => b.score - a.score)
          .slice(0, 5)
          .map((p) => p.place);
        setPlaceSuggestions(fuzzy);
      } finally {
        setPlaceLoading(false);
      }
    }, 200);

    return () => clearTimeout(timer);
  }, [placeQuery, allPlaces]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = query.trim();
    const placeNameParam = placeQuery.trim();
    setHasSearched(true);
    if (!trimmed) {
      setResults([]);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const names = selectedPlaces.map((p) => p.name);
      if (!names.length && placeNameParam) {
        names.push(placeNameParam);
      }
      const data = await searchReviews(trimmed, undefined, undefined, names);
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
    <div className="space-y-4">
      <div className="card p-6 space-y-3">
        <p className="text-sm uppercase tracking-[0.18em] text-cyan-200">Search</p>
        <h1 className="text-3xl font-semibold text-white">Find item mentions in real reviews</h1>
        <p className="text-slate-200 max-w-2xl">
          Type an item or keyword (e.g., &quot;latte&quot;, &quot;burger&quot;) and optionally pick a place
          by name.
        </p>
      </div>

      <form onSubmit={onSubmit} className="card p-5 flex flex-col gap-4">
        <div className="flex flex-col gap-2">
          <label className="text-sm text-slate-300">Item keyword</label>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search for an item..."
            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-white shadow-sm focus:outline-none focus:ring-2 focus:ring-cyan-300/60"
          />
        </div>
        <div className="flex flex-col gap-2">
          <label className="text-sm text-slate-300">Place (optional)</label>
          <input
            type="text"
            value={placeQuery}
            onChange={(e) => setPlaceQuery(e.target.value)}
            placeholder="Start typing a place name…"
            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-white shadow-sm focus:outline-none focus:ring-2 focus:ring-cyan-300/60"
          />
          {placeLoading && <div className="text-xs text-slate-400">Searching places…</div>}
          {placeSuggestions.length > 0 && (
            <div className="mt-2 border border-white/10 rounded-lg bg-white/5 shadow-sm max-h-56 overflow-y-auto">
              {placeSuggestions.map((p) => (
                <button
                  key={p.id}
                  type="button"
                  className="w-full text-left px-3 py-2 hover:bg-cyan-400/10"
                  onClick={() => {
                    setSelectedPlaces((prev) =>
                      prev.find((sp) => sp.id === p.id) ? prev : [...prev, p]
                    );
                    setPlaceQuery('');
                    setPlaceSuggestions([]);
                  }}
                >
                  <div className="text-white">{p.name}</div>
                  {p.address && <div className="text-xs text-slate-300">{p.address}</div>}
                </button>
              ))}
            </div>
          )}
          {selectedPlaces.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-2">
              {selectedPlaces.map((p) => (
                <span key={p.id} className="pill bg-white/5 border border-white/10 text-cyan-100 flex items-center gap-2">
                  {p.name}
                  <button
                    type="button"
                    className="text-xs text-white/80 hover:text-white"
                    onClick={() =>
                      setSelectedPlaces((prev) => prev.filter((sp) => sp.id !== p.id))
                    }
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <button
            type="submit"
            className="inline-flex items-center justify-center px-4 py-2 rounded-lg bg-cyan-400 text-slate-900 font-semibold hover:bg-cyan-300 transition disabled:opacity-60"
            disabled={loading}
          >
            {loading ? 'Searching…' : 'Search'}
          </button>
        </div>
      </form>

      {error && (
        <div className="rounded border border-red-400/40 bg-red-500/10 text-red-100 px-4 py-3">
          {error}
        </div>
      )}

      {hasSearched && !loading && results.length === 0 && !error && (
        <p className="text-slate-400">No reviews found for that keyword.</p>
      )}

      {pageNote && (
        <div className="text-xs text-slate-300">{pageNote}</div>
      )}

      <div className="space-y-3">
        {results.map((review) => (
          <article
            key={review.id}
            className="rounded-lg border border-white/10 bg-white/5 p-4 space-y-3"
          >
            <div className="flex items-center justify-between gap-3 text-sm text-slate-300">
              <div className="space-y-1">
                <Link href={`/places/${review.place}`} className="text-white font-medium hover:text-cyan-200">
                  {review.place_name}
                </Link>
                <div className="text-xs text-slate-400">{new Date(review.created_at).toLocaleDateString()}</div>
              </div>
              <div className="pill bg-white/5 border border-white/10 text-slate-100">⭐ {review.rating}</div>
            </div>
            <p className="text-slate-100 leading-relaxed">{highlight(review.text, query)}</p>
          </article>
        ))}
      </div>
    </div>
  );
}
