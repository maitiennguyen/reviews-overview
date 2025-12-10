// frontend/lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000/api';

async function fetchJSON(path: string, init?: RequestInit) {
  const res = await fetch(`${API_BASE}${path}`, {
    // You can tweak this later (e.g., add headers)
    ...init,
  });

  if (!res.ok) {
    // Simple error; you can make this nicer later
    const text = await res.text();
    throw new Error(`API ${res.status} ${res.statusText}: ${text}`);
  }

  return res.json();
}

// Types that roughly match your DRF serializers
export type PlaceRecommendation = {
  id: number;
  text: string;
  rank: number;
  confidence: number | null;
  source: string;
};

export type Place = {
  id: number;
  name: string;
  address: string | null;
  city: string;
  rating: number | null;
  user_ratings_total: number | null;
  review_count: number;
  recommendations: PlaceRecommendation[];
};

// Generic paginated shape
type Paginated<T> = { results: T[] };

// Shared fetch + unwrap
async function fetchList<T>(path: string): Promise<T[]> {
  const data = await fetchJSON(path);
  if (Array.isArray(data)) return data;
  if (data && Array.isArray((data as Paginated<T>).results)) {
    return (data as Paginated<T>).results;
  }
  throw new Error(`Unexpected list response for ${path}`);
}

// Public API helpers
export function fetchPlaces(): Promise<Place[]> {
  return fetchList<Place>('/places/');
}

export function fetchPlace(id: string | number): Promise<Place> {
  return fetchJSON(`/places/${id}/`);
}
