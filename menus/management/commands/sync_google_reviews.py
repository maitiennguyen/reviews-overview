import os
import requests
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from menus.models import Place, Review
from django.db import transaction
from datetime import datetime


GOOGLE_PLACE_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"


class Command(BaseCommand):
    help = "Sync Google Place details and reviews into the local database."

    def add_arguments(self, parser):
        parser.add_argument(
            '--place-id',
            dest='place_id',
            help='Optional Google Place ID to sync a single place (google_place_id).',
        )
        parser.add_argument(
            '--pk',
            dest='pk',
            type=int,
            help='Optional local Place PK to sync a single place by primary key.',
        )
        parser.add_argument(
            '--limit',
            dest='limit',
            type=int,
            default=None,
            help='Optional limit number of places to sync when running for all places.',
        )

    def handle(self, *args, **options):
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise CommandError('Environment variable GOOGLE_API_KEY is required')

        place_id = options.get('place_id')
        pk = options.get('pk')
        limit = options.get('limit')

        if place_id and pk:
            raise CommandError('Use either --place-id or --pk, not both')

        if place_id:
            qs = Place.objects.filter(google_place_id=place_id)
        elif pk:
            qs = Place.objects.filter(pk=pk)
        else:
            qs = Place.objects.all().order_by('id')
            if limit:
                qs = qs[:limit]

        total = qs.count()
        self.stdout.write(f"Syncing {total} place(s) from Google Places...")

        for place in qs:
            try:
                self.stdout.write(f"Fetching details for {place.name} ({place.google_place_id})")
                params = {
                    'place_id': place.google_place_id,
                    'fields': 'name,rating,user_ratings_total,geometry,formatted_address,reviews',
                    'key': api_key,
                }
                resp = requests.get(GOOGLE_PLACE_DETAILS_URL, params=params, timeout=10)
                resp.raise_for_status()
                payload = resp.json()

                status = payload.get('status')
                if status != 'OK':
                    self.stderr.write(f"Google Places API returned status={status} for {place.google_place_id}")
                    continue

                result = payload.get('result', {})

                # Update place metadata
                updated = False
                rating = result.get('rating')
                if rating is not None and rating != place.rating:
                    place.rating = rating
                    updated = True

                user_ratings_total = result.get('user_ratings_total')
                if user_ratings_total is not None and user_ratings_total != place.user_ratings_total:
                    place.user_ratings_total = user_ratings_total
                    updated = True

                address = result.get('formatted_address')
                if address and address != place.address:
                    place.address = address
                    updated = True

                geometry = result.get('geometry', {}).get('location')
                if geometry:
                    lat = geometry.get('lat')
                    lng = geometry.get('lng')
                    if lat is not None and lat != place.latitude:
                        place.latitude = lat
                        updated = True
                    if lng is not None and lng != place.longitude:
                        place.longitude = lng
                        updated = True

                place.last_synced = timezone.now()
                updated = True

                if updated:
                    place.save()
                    self.stdout.write(self.style.SUCCESS(f"Updated place {place.name}"))

                # Process reviews (if any)
                reviews = result.get('reviews', [])
                if not reviews:
                    self.stdout.write("  No reviews returned by Google for this place.")
                    continue

                with transaction.atomic():
                    for rv in reviews:
                        # Google review id may be absent; fall back to author_name+time
                        google_review_id = rv.get('author_url') or rv.get('author_name') or None
                        # Google Places reviews contain 'time' as epoch seconds
                        created_at = None
                        if 'time' in rv:
                            try:
                                created_at = datetime.fromtimestamp(rv.get('time'), tz=timezone.utc)
                            except Exception:
                                created_at = timezone.now()

                        defaults = {
                            'author_name': rv.get('author_name', '')[:255],
                            'rating': rv.get('rating', 0),
                            'text': rv.get('text', '') or '',
                            'language': rv.get('language', 'en'),
                        }

                        # Attempt to find existing review by google_review_id (author_url) or fallback
                        review_obj = None
                        if google_review_id:
                            review_obj = Review.objects.filter(google_review_id=google_review_id, place=place).first()

                        if not review_obj:
                            # Try to find by text + rating + created_at
                            qs_similar = Review.objects.filter(place=place, rating=defaults['rating'])
                            if created_at:
                                qs_similar = qs_similar.filter(created_at=created_at)
                            if defaults['text']:
                                qs_similar = qs_similar.filter(text__icontains=defaults['text'][:50])
                            review_obj = qs_similar.first()

                        if review_obj:
                            # Update fields if changed
                            changed = False
                            for k, v in defaults.items():
                                if getattr(review_obj, k) != v:
                                    setattr(review_obj, k, v)
                                    changed = True
                            if created_at and review_obj.created_at != created_at:
                                review_obj.created_at = created_at
                                changed = True
                            if changed:
                                review_obj.save()
                                self.stdout.write(self.style.NOTICE(f"  Updated review {review_obj.id}"))
                        else:
                            # Create new review
                            new_google_id = google_review_id or f"{place.id}-{rv.get('time') or timezone.now().timestamp()}"
                            review = Review(
                                place=place,
                                google_review_id=new_google_id,
                                author_name=defaults['author_name'],
                                rating=defaults['rating'],
                                text=defaults['text'],
                                language=defaults['language'],
                                created_at=created_at or timezone.now(),
                            )
                            review.save()
                            self.stdout.write(self.style.SUCCESS(f"  Created review {review.id}"))

            except requests.RequestException as e:
                self.stderr.write(f"Network error while fetching {place.google_place_id}: {e}")
            except Exception as e:
                self.stderr.write(f"Unexpected error while syncing {place.google_place_id}: {e}")

        self.stdout.write(self.style.SUCCESS("Google Places sync completed."))
