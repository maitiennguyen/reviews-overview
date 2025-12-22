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
export type Place = {
  id: number;
  name: string;
  address: string | null;
  city: string;
  rating: number | null;
  user_ratings_total: number | null;
  review_count: number;
};

export type Review = {
  id: number;
  place: number;
  place_name: string;
  google_review_id: string;
  author_name: string;
  rating: number;
  text: string;
  language: string;
  created_at: string;
  fetched_at: string;
};

// Generic paginated shape
type Paginated<T> = { results: T[]; next?: string | null; previous?: string | null; count?: number };

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

export function fetchPlacesPage(page = 1): Promise<Paginated<Place>> {
  const params = new URLSearchParams({ page: String(page) });
  return fetchJSON(`/places/?${params.toString()}`);
}

export function fetchPlace(id: string | number): Promise<Place> {
  return fetchJSON(`/places/${id}/`);
}

export function searchPlacesByName(query: string): Promise<Place[]> {
  const params = new URLSearchParams({ search: query });
  return fetchList<Place>(`/places/?${params.toString()}`);
}

export function searchReviews(
  query: string,
  placeId?: number | string,
  placeName?: string,
  placeNames?: string[]
): Promise<Review[]> {
  const params = new URLSearchParams({ q: query });
  if (placeId) {
    params.set('place', String(placeId));
  }
  if (placeName) {
    params.append('place_name', placeName);
  }
  if (placeNames && placeNames.length > 0) {
    placeNames.forEach((name) => {
      if (name.trim()) params.append('place_name', name.trim());
    });
  }
  return fetchList<Review>(`/search/reviews/?${params.toString()}`);
}
