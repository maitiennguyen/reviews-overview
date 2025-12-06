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


class MenuItem(models.Model):
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='menu_items')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.place.name})"


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


class MenuItemReviewMention(models.Model):
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='mentions')
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='menu_item_mentions')
    relevance_score = models.FloatField(default=1.0)

    class Meta:
        unique_together = ('menu_item', 'review')


class MenuItemReviewSummary(models.Model):
    menu_item = models.OneToOneField(MenuItem, on_delete=models.CASCADE, related_name='ai_summary')
    summary_text = models.TextField(blank=True)
    sentiment_score = models.FloatField(null=True, blank=True)
    tags = models.JSONField(default=list, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"AI Summary for {self.menu_item.name}"
