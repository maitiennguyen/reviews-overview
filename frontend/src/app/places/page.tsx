// frontend/app/places/page.tsx
import Link from 'next/link';
import { fetchPlacesPage, type Place } from '@/lib/api';

export const revalidate = 0; // always fetch fresh in dev

type SearchParams = Promise<{ page?: string }>;

const PAGE_SIZE = 20;

export default async function PlacesPage({ searchParams }: { searchParams?: SearchParams }) {
  const params = (await searchParams) || {};
  const page = Math.max(parseInt(params.page || '1', 10) || 1, 1);

  let places: Place[] = [];
  let next: string | null | undefined;
  let previous: string | null | undefined;
  let count = 0;
  let error: string | null = null;

  try {
    const data = await fetchPlacesPage(page);
    places = data.results || [];
    next = data.next;
    previous = data.previous;
    count = data.count || places.length;
  } catch (err) {
    error =
      err instanceof Error
        ? err.message
        : 'Something went wrong while fetching places.';
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <p className="text-sm uppercase tracking-[0.18em] text-cyan-200">Places</p>
        <h1 className="text-3xl font-semibold text-white">Bozeman spots</h1>
        <p className="text-slate-300">
          Browse all places we have in the dataset. Click through to search reviews within a place.
        </p>
      </div>
      {error && (
        <div className="card border border-red-400/30 mb-4 text-red-100 px-4 py-3">
          Unable to load places from the API. {error}
        </div>
      )}
      {!error && places.length === 0 ? (
        <p className="text-slate-400">No places found.</p>
      ) : (
        <>
          <div className="grid gap-4 grid-cols-1 md:grid-cols-2">
            {places.map((place) => (
              <Link
                key={place.id}
                href={`/places/${place.id}`}
                className="card block transition p-5 hover:border-cyan-300/50 hover:shadow-2xl"
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h2 className="text-xl font-semibold text-white">{place.name}</h2>
                    {place.address && (
                      <p className="text-sm text-slate-300 mt-1">{place.address}</p>
                    )}
                  </div>
                  <span className="pill bg-cyan-400/15 text-cyan-100 border border-cyan-300/30">
                    {place.city}
                  </span>
                </div>
                <div className="mt-3 flex items-center justify-between text-sm text-slate-200">
                  {place.rating != null && (
                    <span className="pill bg-white/5 border border-white/10">⭐ {place.rating.toFixed(1)}</span>
                  )}
                  {place.review_count != null && (
                    <span className="pill bg-white/5 border border-white/10">
                      {place.review_count} reviews
                    </span>
                  )}
                </div>
              </Link>
            ))}
          </div>
          {count > PAGE_SIZE && (
            <div className="flex items-center justify-between mt-4 text-sm text-slate-300">
              <span>
                Page {page} of {Math.max(1, Math.ceil((count || 1) / PAGE_SIZE))}
              </span>
              <div className="flex gap-2">
                <Link
                  href={page > 2 ? `/places?page=${page - 1}` : page === 2 ? '/places' : '#'}
                  className={`px-3 py-2 rounded-lg border border-white/10 bg-white/5 hover:border-cyan-300/50 ${previous ? '' : 'pointer-events-none opacity-50'}`}
                >
                  Previous
                </Link>
                <Link
                  href={next ? `/places?page=${page + 1}` : '#'}
                  className={`px-3 py-2 rounded-lg border border-white/10 bg-white/5 hover:border-cyan-300/50 ${next ? '' : 'pointer-events-none opacity-50'}`}
                >
                  Next
                </Link>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
