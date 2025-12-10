// frontend/app/places/page.tsx
import { fetchPlaces, type Place } from '@/lib/api';

export const revalidate = 0; // always fetch fresh in dev

export default async function PlacesPage() {
  let places: Place[] = [];
  let error: string | null = null;

  try {
    places = await fetchPlaces();
  } catch (err) {
    error =
      err instanceof Error
        ? err.message
        : 'Something went wrong while fetching places.';
  }

  return (
    <div>
      <h1 className="text-3xl font-bold mb-4">Places in Bozeman</h1>
      {error && (
        <div className="mb-4 rounded bg-red-50 text-red-700 px-4 py-3">
          Unable to load places from the API. {error}
        </div>
      )}
      {!error && places.length === 0 ? (
        <p className="text-gray-600">No places found. Check if your backend seed command ran.</p>
      ) : (
        <div className="grid gap-4 grid-cols-1 md:grid-cols-2">
          {places.map((place) => (
            <a
              key={place.id}
              href={`/places/${place.id}`}
              className="block bg-white rounded-lg shadow hover:shadow-lg transition p-4"
            >
              <h2 className="text-xl font-semibold">{place.name}</h2>
              {place.address && (
                <p className="text-sm text-gray-500 mt-1">{place.address}</p>
              )}
              <div className="mt-2 flex items-center justify-between text-sm text-gray-600">
                {place.rating != null && (
                  <span>⭐ {place.rating.toFixed(1)}</span>
                )}
                {place.review_count != null && (
                  <span>{place.review_count} reviews</span>
                )}
              </div>
              {place.recommendations && place.recommendations.length > 0 && (
                <div className="mt-3 text-xs text-green-700">
                  {place.recommendations.length} recommendation
                  {place.recommendations.length !== 1 && 's'} available
                </div>
              )}
            </a>
          ))}
        </div>
      )}
    </div>
  );
}
