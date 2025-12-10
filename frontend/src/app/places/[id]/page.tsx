// frontend/src/app/places/[id]/page.tsx
import Link from 'next/link';
import { fetchPlace } from '@/lib/api';

export default async function PlaceDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const place = await fetchPlace(id);
  const recs = [...(place.recommendations ?? [])].sort((a, b) => a.rank - b.rank);

  return (
    <div className="space-y-6">
      <Link href="/places" className="text-blue-600 hover:underline text-sm">
        &larr; Back to places
      </Link>

      {/* header … */}

      <section>
        <h2 className="text-2xl font-semibold mb-2">What to order</h2>
        {recs.length === 0 ? (
          <p className="text-gray-500">No recommendations yet…</p>
        ) : (
          <ul className="space-y-2">
            {recs.map((r) => (
              <li key={r.id} className="bg-white rounded border shadow-sm p-3">
                <div className="flex justify-between items-center">
                  <span className="font-medium">{r.text}</span>
                  {r.confidence != null && (
                    <span className="text-xs text-gray-500">
                      confidence: {(r.confidence * 100).toFixed(0)}%
                    </span>
                  )}
                </div>
                <div className="text-xs text-gray-500 mt-1">source: {r.source}</div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
