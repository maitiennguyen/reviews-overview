# Copilot Instructions for revove

**revove** analyzes Google Reviews for Bozeman restaurants and generates AI-powered place-level "what to order" recommendations derived from reviews and place metadata.

## Project Architecture

revove is a Django REST Framework application with a PostgreSQL backend:

- **Frontend**: Future React/Next.js app (calls DRF API)
- **Backend**: Django 6.0 with DRF (Port 8000) + PostgreSQL
- **Data Flow**: Google API → Reviews → Database → Mention Detection → AI Summarization

### Core Data Models (`menus/models.py`)

Current models (after the recent pivot) focus on place-level insights:

1. **Place**: Restaurants/cafés (fields: `name`, `google_place_id`, `address`, `city`, `latitude`, `longitude`, `rating`, `user_ratings_total`, `last_synced`).
2. **Review**: Google reviews linked to a `Place` (`place`, `google_review_id`, `author_name`, `rating`, `text`, `language`, `created_at`, `fetched_at`). Raw review records are for internal/admin use.
3. **PlaceRecommendation**: AI-generated, place-level recommendations (1–3 per `Place`). Fields: `place` (FK), `text`, `rank` (1 = top), `confidence`, `source`, timestamps. Unique constraint: `(place, rank)`.

Pattern: Models use `__str__()` for admin display; FKs use `on_delete=models.CASCADE`; timestamps use `auto_now_add`/`auto_now` where appropriate.

## Development Workflow

# Setting up the environment

```bash
# Install dependencies
python -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt  # if exists, or install Django, DRF, psycopg2, python-dotenv

# Configure .env
cp .env.example .env  # Add DATABASE_URL, GOOGLE_API_KEY (future), etc.

# Migrate database
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run server
python manage.py runserver

# Run tests (lightweight)
DJANGO_SETTINGS_MODULE=revove.test_settings python manage.py test menus.tests.test_models menus.tests.test_api
```

### Key Commands

- `python manage.py makemigrations` → Generate migration files after model changes
- `python manage.py migrate` → Apply migrations to database
- `python manage.py shell` → Django shell for testing queries
- `python manage.py admin` → Admin interface (http://localhost:8000/admin/)

### Common Tasks

**Add a new model field**:
1. Edit `menus/models.py`
2. Run `python manage.py makemigrations menus`
3. Run `python manage.py migrate`
4. Register in `menus/admin.py` if needed

**Test a database query**:
```bash
python manage.py shell
>>> from menus.models import Place
>>> Place.objects.all()
```

## API Development Guidelines

**Current State**: Public API exposes `Place` endpoints with nested `recommendations`. Raw `Review` data and admin-processing endpoints live under the `internal/` router and are protected with `IsAdminUser`.

**Next Steps / Priorities**:

1. Keep the public surface small: `Place` read-only endpoints only (list & detail). Include nested `PlaceRecommendation` and a `review_count` field in the `PlaceSerializer`.
2. Maintain admin-only `Review` viewset under `menus/internal_urls.py` for raw data inspection and manual fixes.
3. Implement the recommendation-generation pipeline (management command or scheduled job) that aggregates reviews per `Place` and calls an LLM to upsert `PlaceRecommendation` records (1–3 per place).

**Current Routes**:
- `GET /api/places/` – List places (paginated) with nested `recommendations` and `review_count`.
- `GET /api/places/<id>/` – Place detail with `recommendations`.
- `GET /internal/reviews/` – Admin-only list of reviews (requires admin permission).

## Code Patterns & Conventions

### Model Design

- Use `max_length` constraints (e.g., 255 for names, 500 for addresses)
- Default values: `city = "Bozeman"` (hardcoded for this MVP)
- Nullable fields use `null=True, blank=True`
- Unique constraints via `unique=True` or `unique_together`
- Timestamps: `auto_now` for updates, `auto_now_add` for creation

### Django Admin Registration (`menus/admin.py`)

Register `Place`, `Review`, and `PlaceRecommendation` for admin access. Keep list displays focused; examples:
```python
@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
   list_display = ('name', 'city', 'rating', 'user_ratings_total')
   search_fields = ('name', 'address')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
   list_display = ('place', 'author_name', 'rating', 'created_at')
   list_filter = ('rating', 'language')

@admin.register(PlaceRecommendation)
class PlaceRecommendationAdmin(admin.ModelAdmin):
   list_display = ('place', 'rank', 'text', 'confidence', 'last_updated')
   list_filter = ('source',)
```

### Database

- **Type**: PostgreSQL (configured in settings.py)
- **Connection**: Loaded via `.env` file using `python-dotenv`
- **Migrations**: Located in `menus/migrations/`

## Upcoming Integrations (Future Phases)

### Phase 2: Google Reviews Sync

The project already includes `menus/management/commands/sync_google_reviews.py` which calls the Google Places API (v1) to update `Place` metadata and save available reviews into `Review` records. This command reads `GOOGLE_API_KEY` from the environment/settings.

### Phase 3: Recommendation Generation (AI)

Goal: generate 1–3 short, actionable "what to order" recommendations per `Place` from aggregated reviews and place metadata.

Approach:
1. Aggregate up to N recent/high-quality reviews per place.
2. Build a structured prompt containing place metadata and the selected reviews.
3. Call an LLM (configurable client) to return 1–3 recommendation texts with optional confidence scores.
4. Upsert `PlaceRecommendation` records with `rank` ordering.

Implementation options: a management command (`menus/management/commands/generate_recommendations.py`), a scheduled job (Celery beat), or a GitHub Action for on-demand runs.

### Phase 4: Automation

- **Scheduler Options**: Celery + Redis, Cron job, GitHub Action, Railway scheduled job
- **Weekly Tasks**: Refresh reviews, regenerate recommendations, and optionally re-run confidence calibration

## Important Notes

- **Settings**: `DEBUG = True` in development settings — turn OFF and secure secrets before production.
- **CORS**: corsheaders enabled for development; restrict origins in production.
- **Branch**: Current working branch: `feature/place-menuitem-setup`.
- **Seed Data**: `menus/management/commands/seed_data.py` seeds three Bozeman places (Jam!, Backcountry Burger Bar, Treeline Coffee Roasters).
- **Sync**: `menus/management/commands/sync_google_reviews.py` exists and requires a valid `GOOGLE_API_KEY` with Places access.
- **Tests**: Lightweight unit tests were added for `PlaceRecommendation` and `Place` API. For local runs without Postgres privileges, use the test settings:

```bash
DJANGO_SETTINGS_MODULE=revove.test_settings python manage.py test menus.tests.test_models menus.tests.test_api
```

- **Security**: Public API surface intentionally minimal (places + recommendations). Raw review data remains behind admin-only endpoints (`/internal/`).

## Useful Resources

- Django Docs: https://docs.djangoproject.com/en/6.0/
- DRF Docs: https://www.django-rest-framework.org/
- Google Places API: https://developers.google.com/maps/documentation/places

