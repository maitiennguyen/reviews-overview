from django.db import models
from django.utils import timezone

class Place(models.Model):
    name = models.CharField(max_length=255)
    google_place_id = models.CharField(max_length=255, unique=True)
    address = models.CharField(max_length=500, blank=True)
    city = models.CharField(max_length=100, default="Bozeman")
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    rating = models.FloatField(null=True, blank=True)
    user_ratings_total = models.IntegerField(null=True, blank=True)
    last_synced = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name


class Review(models.Model):
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='reviews')
    google_review_id = models.CharField(max_length=255, unique=True)
    author_name = models.CharField(max_length=255, blank=True)
    rating = models.IntegerField()
    text = models.TextField(blank=True)
    language = models.CharField(max_length=10, default="en")
    created_at = models.DateTimeField()
    fetched_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for {self.place.name} ({self.rating}★)"


class PlaceRecommendation(models.Model):
    """AI-generated place-level recommendation (1-3 per Place).

    Stores a short recommendation text and an optional confidence score.
    """
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='recommendations')
    text = models.CharField(max_length=255)
    rank = models.PositiveSmallIntegerField(default=1)  # 1 = top recommendation
    confidence = models.FloatField(null=True, blank=True)
    source = models.CharField(max_length=50, default='ai')
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('place', 'rank')
        ordering = ['place', 'rank']

    def __str__(self):
        return f"{self.place.name} - #{self.rank}: {self.text}"
