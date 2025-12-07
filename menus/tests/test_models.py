from django.test import TestCase
from menus.models import Place, PlaceRecommendation


class PlaceRecommendationModelTests(TestCase):
    def test_create_and_order_recommendations(self):
        place = Place.objects.create(
            name="Test Place",
            google_place_id="test-123",
            address="1 Test St",
        )

        r1 = PlaceRecommendation.objects.create(
            place=place, text="Try the burger", rank=1, confidence=0.92
        )
        r2 = PlaceRecommendation.objects.create(
            place=place, text="Add fries as a side", rank=2, confidence=0.75
        )

        qs = list(place.recommendations.all())
        self.assertEqual(len(qs), 2)
        self.assertEqual(qs[0].rank, 1)
        self.assertEqual(qs[0].text, r1.text)
        self.assertEqual(qs[1].rank, 2)
        self.assertEqual(qs[1].text, r2.text)
