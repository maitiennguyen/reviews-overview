import os
import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from menus.models import Place, Review
from django.utils import timezone


class Command(BaseCommand):
    help = "Sync Google Places API (New) details + reviews for all Places."

    BASE_URL = "https://places.googleapis.com/v1/places"

    def handle(self, *args, **options):
        # Prefer a Django settings value, fall back to environment variable
        api_key = os.getenv('GOOGLE_API_KEY')

        if not api_key:
            self.stdout.write(self.style.ERROR("❌ Missing GOOGLE_API_KEY in settings or environment"))
            return

        places = Place.objects.all()
        if not places.exists():
            self.stdout.write(self.style.WARNING("⚠ No Place records found."))
            return

        self.stdout.write(self.style.NOTICE("🔄 Starting Google Places sync…"))

        for place in places:
            self.sync_place(place, api_key)

        self.stdout.write(self.style.SUCCESS("✨ Sync complete!"))

    def sync_place(self, place, api_key):
        """Fetch Place details + reviews using the new Places API."""

        fields = ",".join([
            "displayName",
            "rating",
            "userRatingCount",
            "formattedAddress",
            "location",
            "reviews"  # Only returned for Advanced tier
        ])

        url = f"{self.BASE_URL}/{place.google_place_id}"
        params = {
            "fields": fields,
            "key": api_key,
        }

        response = requests.get(url, params=params)
        data = response.json()

        # Handle API errors
        if "error" in data:
            err = data["error"]
            self.stdout.write(self.style.ERROR(
                f"❌ Error for {place.name}: {err.get('message')} ({err.get('status')})"
            ))
            return

        # --- Update Place metadata ---
        display_name = data.get("displayName", {})
        place.name = display_name.get("text", place.name)

        place.rating = data.get("rating")
        place.user_ratings_total = data.get("userRatingCount")
        place.address = data.get("formattedAddress", place.address)

        # location.latitude / location.longitude
        location = data.get("location", {})
        place.latitude = location.get("latitude")
        place.longitude = location.get("longitude")

        place.last_synced = timezone.now()
        place.save()

        # --- Save reviews (if available) ---
        reviews = data.get("reviews", [])
        saved_count = 0

        for r in reviews:
            # Each review has a unique 'name' field like: places/PLACE_ID/reviews/XXXX
            google_review_id = r.get("name")

            if not google_review_id:
                continue

            if Review.objects.filter(google_review_id=google_review_id).exists():
                continue

            text_obj = r.get("text") or {}
            text_val = text_obj.get("text")
            if not text_val:
                # Skip reviews with no text to avoid violating NOT NULL constraint
                continue

            publish_time = r.get("publishTime")
            try:
                created_dt = timezone.datetime.fromisoformat(publish_time.replace("Z", "+00:00")) if publish_time else timezone.now()
            except Exception:
                created_dt = timezone.now()

            Review.objects.create(
                place=place,
                google_review_id=google_review_id,
                author_name=r.get("authorAttribution", {}).get("displayName"),
                rating=r.get("rating"),
                text=text_val,
                language="en",  # New API doesn’t always return language
                created_at=created_dt,
            )

            saved_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"✓ Synced {saved_count} new reviews for {place.name}"
        ))
