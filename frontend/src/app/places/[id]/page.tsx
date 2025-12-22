// frontend/src/app/places/[id]/page.tsx
import Link from 'next/link';
import { fetchPlace } from '@/lib/api';
import { SearchWithinPlace } from './SearchWithinPlace';

export default async function PlaceDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const place = await fetchPlace(id);

  return (
    <div className="space-y-6">
      <Link href="/places" className="text-cyan-200 hover:text-cyan-100 underline-offset-4 hover:underline text-sm">
        &larr; Back to places
      </Link>

      <section className="card p-6 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="space-y-2">
            <p className="text-sm uppercase tracking-[0.18em] text-cyan-200">Place</p>
            <h1 className="text-3xl font-semibold text-white">{place.name}</h1>
            {place.address && <p className="text-slate-300">{place.address}</p>}
          </div>
          <div className="flex items-center gap-3">
            {place.rating != null && (
              <span className="pill bg-white/5 border border-white/10 text-slate-100 text-sm">
                ⭐ {place.rating.toFixed(1)}
              </span>
            )}
            {place.review_count != null && (
              <span className="pill bg-white/5 border border-white/10 text-slate-100 text-sm">
                {place.review_count} reviews
              </span>
            )}
          </div>
        </div>
      </section>

      <SearchWithinPlace placeId={place.id} placeName={place.name} />
    </div>
  );
}
