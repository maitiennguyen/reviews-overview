from rest_framework.test import APITestCase
from django.urls import reverse
from django.utils import timezone
from menus.models import Place, PlaceRecommendation, Review


class PlaceAPITests(APITestCase):
    def setUp(self):
        self.place = Place.objects.create(
            name="API Place",
            google_place_id="api-123",
            address="100 API Ave",
        )
        PlaceRecommendation.objects.create(place=self.place, text="Top pick", rank=1, confidence=0.9)
        PlaceRecommendation.objects.create(place=self.place, text="Second pick", rank=2, confidence=0.7)

    def test_list_places_excludes_recommendations(self):
        url = reverse('menus:place-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        # Expect results array and our place to be present
        self.assertIn('results', data)
        found = None
        for item in data['results']:
            if item['google_place_id'] == 'api-123':
                found = item
                break

        self.assertIsNotNone(found, 'Seeded place not found in list')
        self.assertNotIn('recommendations', found)
        self.assertEqual(found['review_count'], 0)

    def test_retrieve_place_detail(self):
        url = reverse('menus:place-detail', args=[self.place.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['id'], self.place.id)
        self.assertNotIn('recommendations', data)

    def test_search_reviews_returns_matches(self):
        other_place = Place.objects.create(
            name="Other Place",
            google_place_id="other-123",
            address="200 API Ave",
        )
        Review.objects.create(
            place=self.place,
            google_review_id="rev-1",
            author_name="Alice",
            rating=5,
            text="Loved the latte here!",
            language="en",
            created_at=timezone.now(),
        )
        Review.objects.create(
            place=other_place,
            google_review_id="rev-2",
            author_name="Bob",
            rating=4,
            text="Great burger spot.",
            language="en",
            created_at=timezone.now(),
        )

        url = reverse('menus:review-search-list')
        resp = self.client.get(url, {"q": "latte"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('results', data)
        self.assertEqual(len(data['results']), 1)
        hit = data['results'][0]
        self.assertEqual(hit['text'], "Loved the latte here!")
        self.assertEqual(hit['place'], self.place.id)
        self.assertEqual(hit['place_name'], self.place.name)

    def test_search_reviews_can_filter_by_places_multiple(self):
        other_place = Place.objects.create(
            name="Other Place",
            google_place_id="other-123",
            address="200 API Ave",
        )
        another_place = Place.objects.create(
            name="Third Place",
            google_place_id="third-123",
            address="300 API Ave",
        )
        Review.objects.create(
            place=self.place,
            google_review_id="rev-3",
            author_name="Alice",
            rating=5,
            text="Loved the latte here!",
            language="en",
            created_at=timezone.now(),
        )
        Review.objects.create(
            place=other_place,
            google_review_id="rev-4",
            author_name="Bob",
            rating=4,
            text="Loved the latte here too",
            language="en",
            created_at=timezone.now(),
        )
        Review.objects.create(
            place=another_place,
            google_review_id="rev-4b",
            author_name="Sam",
            rating=3,
            text="No latte mention here",
            language="en",
            created_at=timezone.now(),
        )
        url = reverse('menus:review-search-list')
        resp = self.client.get(url, {"q": "latte", "place": [self.place.id, other_place.id]})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data['results']), 2)
        place_ids = {r['place'] for r in data['results']}
        self.assertEqual(place_ids, {self.place.id, other_place.id})

    def test_search_reviews_by_place_name(self):
        other_place = Place.objects.create(
            name="Canyon Coffee",
            google_place_id="other-456",
            address="300 API Ave",
        )
        Review.objects.create(
            place=self.place,
            google_review_id="rev-5",
            author_name="Alice",
            rating=5,
            text="Latte and pancakes!",
            language="en",
            created_at=timezone.now(),
        )
        Review.objects.create(
            place=other_place,
            google_review_id="rev-6",
            author_name="Bob",
            rating=4,
            text="Latte over here too",
            language="en",
            created_at=timezone.now(),
        )

        url = reverse('menus:review-search-list')
        resp = self.client.get(url, {"q": "latte", "place_name": "API Place"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['place'], self.place.id)

    def test_search_reviews_fuzzy_keyword(self):
        Review.objects.create(
            place=self.place,
            google_review_id="rev-7",
            author_name="Alice",
            rating=5,
            text="Amazing latte here.",
            language="en",
            created_at=timezone.now(),
        )
        url = reverse('menus:review-search-list')
        resp = self.client.get(url, {"q": "lattle"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data['results']), 1)

    def test_search_reviews_fuzzy_keyword_rejects_far_match(self):
        Review.objects.create(
            place=self.place,
            google_review_id="rev-7b",
            author_name="Alice",
            rating=5,
            text="Great croissant here.",
            language="en",
            created_at=timezone.now(),
        )
        url = reverse('menus:review-search-list')
        resp = self.client.get(url, {"q": "latte"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        # No latte mention, should return nothing with tightened fuzzy rules.
        self.assertEqual(len(data['results']), 0)

    def test_search_reviews_fuzzy_place_name(self):
        Review.objects.create(
            place=self.place,
            google_review_id="rev-8",
            author_name="Alice",
            rating=5,
            text="Great brunch.",
            language="en",
            created_at=timezone.now(),
        )
        url = reverse('menus:review-search-list')
        resp = self.client.get(url, {"q": "brunch", "place_name": "Api Plaec"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['place'], self.place.id)

    def test_search_reviews_blank_query_returns_empty(self):
        Review.objects.create(
            place=self.place,
            google_review_id="rev-3",
            author_name="Alice",
            rating=5,
            text="Some text",
            language="en",
            created_at=timezone.now(),
        )
        url = reverse('menus:review-search-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('results', data)
        self.assertEqual(data['results'], [])
