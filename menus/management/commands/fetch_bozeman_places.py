"""
Fetch Bozeman places from Google Places API and insert any missing ones.

Usage:
  python manage.py fetch_bozeman_places --keyword restaurant --radius 8000
  python manage.py fetch_bozeman_places --dry-run
"""

import os
from typing import List, Optional

import requests
from django.core.management.base import BaseCommand, CommandError

from menus.models import Place

# Google Places API (New) endpoint
PLACES_NEARBY_URL = "https://places.googleapis.com/v1/places:searchNearby"
BOZEMAN_COORDS = (45.6770, -111.0429)  # downtown Bozeman
DEFAULT_RADIUS_METERS = 8000


class Command(BaseCommand):
    help = "Fetch Bozeman places from Google Places API and add any missing ones."

    def add_arguments(self, parser):
        parser.add_argument(
            "--radius",
            type=int,
            default=DEFAULT_RADIUS_METERS,
            help="Search radius in meters (default: 8000).",
        )
        parser.add_argument(
            "--keyword",
            default="restaurant",
            help="Keyword to filter places (e.g., restaurant, cafe).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show results without writing to DB.",
        )

    def handle(self, *args, **options):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise CommandError("GOOGLE_API_KEY is not set")

        params = {
            "includedTypes": self._parse_types(options["keyword"]),
            "maxResultCount": 20,
            "rankPreference": "POPULARITY",
            "locationRestriction": {
                "circle": {
                    "center": {
                        "latitude": BOZEMAN_COORDS[0],
                        "longitude": BOZEMAN_COORDS[1],
                    },
                    "radius": options["radius"],
                }
            },
        }

        added = 0
        seen = set(Place.objects.values_list("google_place_id", flat=True))
        next_page: Optional[str] = None

        while True:
            body = params.copy()
            if next_page:
                body["pageToken"] = next_page

            headers = {
                "X-Goog-Api-Key": api_key,
                "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location,places.rating,places.userRatingCount",
            }

            resp = requests.post(PLACES_NEARBY_URL, headers=headers, json=body, timeout=15)
            if resp.status_code != 200:
                raise CommandError(f"Google Places error {resp.status_code}: {resp.text}")

            data = resp.json()
            results = data.get("places", [])

            for r in results:
                place_id = r.get("id")
                if not place_id or place_id in seen:
                    continue

                geom = r.get("location", {})
                fields = {
                    "name": r.get("displayName", {}).get("text"),
                    "google_place_id": place_id,
                    "address": r.get("formattedAddress"),
                    "city": "Bozeman",
                    "latitude": geom.get("latitude"),
                    "longitude": geom.get("longitude"),
                    "rating": r.get("rating"),
                    "user_ratings_total": r.get("userRatingCount"),
                }

                if options["dry_run"]:
                    self.stdout.write(f"[dry-run] Would add: {fields}")
                else:
                    Place.objects.create(**fields)
                    added += 1
                    seen.add(place_id)

            next_page = data.get("nextPageToken")
            if not next_page:
                break

        self.stdout.write(self.style.SUCCESS(f"Added {added} new places."))

    @staticmethod
    def _parse_types(keyword: str) -> List[str]:
        # Accept comma-separated keywords; strip and lower-case
        parts = [p.strip().lower() for p in keyword.split(",") if p.strip()]
        return parts or ["restaurant"]
