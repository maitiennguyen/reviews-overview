# DRF API Layer Implementation Summary

## Current ViewSets

1) **PlaceViewSet** (`menus/views.py`)
   - ReadOnlyModelViewSet
   - Filters: `city`
   - Search: `name`, `address`
   - Order: `name`, `rating`, `user_ratings_total`
   - Public routes via `menus/urls.py`:
     - `/api/places/`
     - `/api/places/<id>/`

2) **ReviewSearchViewSet** (`menus/views.py`)
   - ReadOnlyModelViewSet (public)
   - Search: keyword in `text` or `author_name`
   - Optional scoping by place:
     - `place=<id>` OR `place_name=<name>` (with lightweight fuzzy matching on names)
   - Fuzzy fallback on keyword for minor typos (small dataset heuristic)
   - Order: `created_at`, `rating`
   - Public route: `/api/search/reviews/?q=keyword[&place=<id>|&place_name=<name>]`

3) **ReviewViewSet** (`menus/views.py`)
   - ReadOnlyModelViewSet
   - Permission: `IsAdminUser` (internal only)
   - Filters: `place`, `rating`, `language`
   - Search: `text`, `author_name`
   - Order: `rating`, `created_at`
   - Internal route via `menus/internal_urls.py`: `/internal/reviews/`

## Serializers

- **PlaceSerializer** (`menus/serializers.py`): fields `id, name, google_place_id, address, city, latitude, longitude, rating, user_ratings_total, last_synced, review_count`. Recommendations are intentionally omitted from the public API.
- **ReviewSerializer** (`menus/serializers.py`): exposes `place`, derived `place_name`, `google_review_id`, `author_name`, `rating`, `text`, `language`, `created_at`, `fetched_at`. Used by search and internal review endpoints.

## Routing

- **Public** (`menus/urls.py`)
  - `/api/places/`
  - `/api/search/reviews/`
- **Internal/Admin** (`menus/internal_urls.py`)
  - `/internal/reviews/` (protected by `IsAdminUser` on the viewset)

## Settings Highlights (`revove/settings.py`)

- DRF defaults:
  - Filter backends: DjangoFilterBackend, SearchFilter, OrderingFilter
  - Pagination: PageNumberPagination, `PAGE_SIZE=20`
  - Throttling: AnonRateThrottle `100/hour`, UserRateThrottle `1000/hour`
- CORS: `CORS_ALLOW_ALL_ORIGINS = True`
- DB: PostgreSQL (see `revove/settings.py`), tests can run with `revove/test_settings.py` to use SQLite in-memory.

## Notes and Status

- AI-generated recommendations (`PlaceRecommendation`) exist in the model but are hidden while we iterate on quality.
- Item-level summaries will follow once enough reviews are available; Google Places New API returns only ~5 top reviews per place and they rotate infrequently.
- Focus is on review-based keyword search with typo tolerance and optional multi-place scoping by name.
- All endpoints are read-only; no POST/PUT/DELETE implemented yet.

## Quick Usage

- List places: `GET /api/places/`
- Search reviews: `GET /api/search/reviews/?q=latte`
- Search reviews scoped to place name: `GET /api/search/reviews/?q=latte&place_name=Jam`
- Admin/internal reviews: `GET /internal/reviews/?place=1` (requires admin auth)
