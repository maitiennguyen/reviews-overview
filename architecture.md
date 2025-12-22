# Architecture

## System Overview
- **Goal**: ingest Google reviews for Bozeman food and drink spots and surface them as “what to order” guidance. AI-based menu-item recommendations are being iterated on but remain hidden; near-term focus is search-by-item mentions in raw reviews. Item-level summaries will follow once we collect enough reviews (Google Places New API only returns ~5 top reviews per place and they rarely rotate).
- **Stack**: Django + Django REST Framework over PostgreSQL; Next.js frontend; Google Places API (New) as the external data source; optional local LLM stack for recommendation generation.

## Domain Model
- `Place`: Google place metadata (name, address, geo, ratings, last_synced).
- `Review`: individual Google reviews tied to a place.
- `PlaceRecommendation`: AI-generated, ranked “what to order” statements per place (currently experimental and not exposed on the public API).

## Data Flow
1) **Place discovery** (`python manage.py fetch_bozeman_places`): calls Places API `places:searchNearby` to load Bozeman restaurants/cafes into the `Place` table.  
2) **Review sync** (`python manage.py sync_google_reviews`): for each place, calls Places API details endpoint to refresh metadata and ingest text reviews into `Review`.  
3) **Recommendation generation (paused)** (`python manage.py generate_recommendations`): local-only pipeline using sentence-transformers (embeddings) + llama.cpp GGUF models to extract menu items and synthesize 1–N `PlaceRecommendation` rows. Currently on hold until extraction quality improves.  
4) **API exposure**: DRF read-only viewsets serve data to the frontend. Public surface: `/api/places/` plus `/api/search/reviews/?q=keyword[&place=ID|&place_name=Name]` for keyword matches (optionally scoped by place id or fuzzy-matched name); lightweight fuzzy fallback handles minor typos. Recommendations are not returned. Internal/admin surface (`/internal/reviews/`) exposes raw reviews with `IsAdminUser` protection for debugging.  
5) **Frontend consumption**: Next.js app reads from the DRF API via `frontend/src/lib/api.ts`. Current UI lists places, has a global review search page with place-name suggestions/fuzzy matching, and supports per-place keyword search; recommendations are hidden while the item-search experience is built.

## Key Components & Responsibilities
- **Backend app (`menus`)**
  - Models: persistence for places, reviews, and ranked recommendations.
  - Management commands: acquisition (`fetch_bozeman_places`, `sync_google_reviews`,`remove_grocery_stores`), experimental AI pipeline (`generate_recommendations`).
  - API: read-only DRF viewsets with filtering/search/order on places and a keyword review search endpoint; raw review listings kept internal.
  - Settings: DRF pagination/throttling, CORS enabled for the frontend, Postgres connection via environment.
- **Frontend (`frontend/`)**
  - Next.js (app router) with simple pages for home, place list, and place detail.
  - Fetch helpers encapsulate API base URL (`NEXT_PUBLIC_API_BASE`).
  - Styles via Tailwind v4 (global CSS).

## Current Status and Roadmap
- **In progress**: LLM-based recommendation generation and mention extraction—kept off the public surface until quality is solid.
- **Now**: search for an item (e.g., “latte”, “burger”) and return reviews mentioning it (with typo tolerance and place scoping).
- **Near future**: item-level summaries per place once more reviews accumulate (current API limits to ~5 top reviews per place, rotating infrequently); stronger admin tooling, authentication/permissions for write operations, and OpenAPI docs.
