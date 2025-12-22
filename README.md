# revove

Revove ingests Google reviews for Bozeman food and drink spots and surfaces them via a Django REST API and a Next.js frontend. AI-generated “what to order” recommendations exist but are paused while we pivot to search-by-item mentions in reviews.

## Contents
- High-level design: `architecture.md`
- Backend (Django + DRF): models, API, data-ingestion commands in `menus/`
- Frontend (Next.js): proof-of-concept UI in `frontend/`

## Requirements
- Python 3.11+ with `pip`
- PostgreSQL running locally (default DB: `revove_db`, user: `mainguyen`)
- Node.js 20+ and npm
- Google Places API (New) key with access to reviews
- Optional for AI pipeline: `sentence-transformers`, `numpy`, compiled `llama.cpp` binary, and local GGUF models

## Environment
Create a `.env` in the repo root:
```
GOOGLE_API_KEY=your_api_key
DB_PASSWORD=your_db_password
```
You can adjust DB name/user/host/port in `revove/settings.py` if needed. The frontend reads `NEXT_PUBLIC_API_BASE` (defaults to `http://localhost:8000/api`).

## Backend (Django + DRF)
Install dependencies and run the server:
```bash
python -m venv .venv
source .venv/bin/activate
pip install django djangorestframework django-filter django-cors-headers requests python-dotenv
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

### Data ingestion
- Seed sample places (optional): `python manage.py seed_data`
- Fetch Bozeman places via Places API: `python manage.py fetch_bozeman_places --keyword restaurant --radius 8000`
- Sync details + reviews for all places: `python manage.py sync_google_reviews`

### Recommendation pipeline (paused)
The experimental LLM pipeline is available but currently on hold. If you want to exercise it locally:
```bash
python manage.py generate_recommendations \
  --llama-bin ./llama.cpp/main \
  --extractor-model /path/to/qwen2-1_5b-instruct.gguf \
  --reasoning-model /path/to/qwen2_5-7b-instruct.gguf \
  --dry-run
```
This populates `PlaceRecommendation` rows; quality is under review.

### API surface
- Public: `/api/places/` (list/detail; includes nested recommendations and `review_count`)
- Internal/admin: `/internal/reviews/` (read-only, `IsAdminUser` protected)

## Frontend (Next.js)
The UI is a small proof of concept that lists places and shows stored recommendations.
```bash
cd frontend
npm install
NEXT_PUBLIC_API_BASE=http://localhost:8000/api npm run dev
```
Open `http://localhost:3000` to view. Pages live under `frontend/src/app/`.

## Current focus and future work
- Now: build item search that returns reviews mentioning a query term across places.
- Next: re-enable reliable mention extraction and AI recommendation generation; add item-level summaries per place.
