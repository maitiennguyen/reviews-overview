from rest_framework.test import APITestCase
from django.urls import reverse
from menus.models import Place, PlaceRecommendation


class PlaceAPITests(APITestCase):
    def setUp(self):
        self.place = Place.objects.create(
            name="API Place",
            google_place_id="api-123",
            address="100 API Ave",
        )
        PlaceRecommendation.objects.create(place=self.place, text="Top pick", rank=1, confidence=0.9)
        PlaceRecommendation.objects.create(place=self.place, text="Second pick", rank=2, confidence=0.7)

    def test_list_places_includes_recommendations(self):
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
        self.assertIn('recommendations', found)
        self.assertEqual(len(found['recommendations']), 2)
        self.assertEqual(found['review_count'], 0)

    def test_retrieve_place_detail(self):
        url = reverse('menus:place-detail', args=[self.place.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['id'], self.place.id)
        self.assertIn('recommendations', data)
