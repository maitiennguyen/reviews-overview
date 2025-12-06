# Copilot Instructions for revove

**revove** analyzes Google Reviews for Bozeman restaurants and generates AI-powered menu item summaries.

## Project Architecture

revove is a Django REST Framework application with a PostgreSQL backend:

- **Frontend**: Future React/Next.js app (calls DRF API)
- **Backend**: Django 6.0 with DRF (Port 8000) + PostgreSQL
- **Data Flow**: Google API → Reviews → Database → Mention Detection → AI Summarization

### Core Data Models (`menus/models.py`)

Five interconnected models represent the problem space:

1. **Place**: Restaurants/cafés (google_place_id, rating, location)
2. **MenuItem**: Menu items owned by a Place
3. **Review**: Google reviews linked to a Place
4. **MenuItemReviewMention**: Maps reviews → menu items (with relevance_score)
5. **MenuItemReviewSummary**: AI-generated summary (summary_text, sentiment_score, tags) - OneToOne with MenuItem

**Pattern**: All models use `__str__()` methods for readable admin display. Foreign keys use `on_delete=models.CASCADE`. Timestamps use Django's `timezone` and `auto_now` where appropriate.

## Development Workflow

### Setting up the environment

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
>>> from menus.models import Place, MenuItem
>>> Place.objects.all()
```

## API Development Guidelines

**Current State**: No DRF endpoints yet (Phase 1 – Models only)

**Next Steps** (in priority order):

1. **Create Serializers** (`menus/serializers.py`):
   - PlaceSerializer, MenuItemSerializer, ReviewSerializer
   - Nested: MenuItemReviewMentionSerializer, MenuItemReviewSummarySerializer
   - Use `depth=1` for read-only nested relations

2. **Create ViewSets** (`menus/views.py`):
   ```python
   from rest_framework import viewsets
   from .serializers import PlaceSerializer
   from .models import Place

   class PlaceViewSet(viewsets.ModelViewSet):
       queryset = Place.objects.all()
       serializer_class = PlaceSerializer
   ```

3. **Register Routes** (`menus/urls.py`, then include in `revove/urls.py`):
   ```python
   from rest_framework.routers import DefaultRouter
   from .views import PlaceViewSet

   router = DefaultRouter()
   router.register(r'places', PlaceViewSet)
   urlpatterns = router.urls
   ```

**Expected Endpoints**:
- `GET /places/` – List all places
- `GET /places/<id>/` – Place details with menu items
- `GET /menu-items/` – All menu items (with filtering by place)
- `GET /menu-items/<id>/summary/` – AI summary for a menu item

## Code Patterns & Conventions

### Model Design

- Use `max_length` constraints (e.g., 255 for names, 500 for addresses)
- Default values: `city = "Bozeman"` (hardcoded for this MVP)
- Nullable fields use `null=True, blank=True`
- Unique constraints via `unique=True` or `unique_together`
- Timestamps: `auto_now` for updates, `auto_now_add` for creation

### Django Admin Registration (`menus/admin.py`)

Models are registered for admin access. Keep admin list_display clean:
```python
@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'place', 'category', 'is_active')
    list_filter = ('place', 'category', 'is_active')
```

### Database

- **Type**: PostgreSQL (configured in settings.py)
- **Connection**: Loaded via `.env` file using `python-dotenv`
- **Migrations**: Located in `menus/migrations/`

## Upcoming Integrations (Future Phases)

### Phase 2: Google Reviews API Integration

Build a management command (`menus/management/commands/sync_google_reviews.py`):
- Fetch place details via Google Places API
- Fetch reviews via Google Reviews API
- Store/update Review model records
- Update Place.last_synced timestamp

### Phase 3: Review Matching & AI Summarization

Algorithms to implement:

1. **Review → MenuItem Matching**: Populate MenuItemReviewMention
   - Start with keyword matching (simple)
   - Graduate to fuzzy string matching (fuzzywuzzy)
   - Future: LLM classification or embeddings

2. **AI Summarization**: Populate MenuItemReviewSummary
   - Aggregate all reviews mentioning a menu item
   - Call LLM (OpenAI/Claude) with structured prompt
   - Extract summary_text, sentiment_score, tags
   - Store in MenuItemReviewSummary

### Phase 4: Automation

- **Scheduler Options**: Celery + Redis, Cron job, GitHub Action, Railway scheduled job
- **Weekly Tasks**: Refresh reviews, re-run mention detection, regenerate summaries

## Important Notes

- **Settings**: Debug mode is ON (settings.py) – turn OFF before production
- **CORS**: Enabled via corsheaders middleware for future frontend consumption
- **Branch**: Currently on `feature/place-menuitem-setup`
- **Seed Data**: Example places (Jam!, Backcountry Burger Bar, Treeline Coffee) are in database
- **No Authentication Yet**: DRF defaults allow unauthenticated access – add TokenAuthentication or JWT later

## Useful Resources

- Django Docs: https://docs.djangoproject.com/en/6.0/
- DRF Docs: https://www.django-rest-framework.org/
- PostgreSQL with Django: https://docs.djangoproject.com/en/6.0/ref/databases/#postgresql-notes
