from django.contrib import admin
from .models import Place, Review, PlaceRecommendation


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
	list_display = ('name', 'city', 'rating', 'user_ratings_total')
	search_fields = ('name', 'address')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
	list_display = ('place', 'author_name', 'rating', 'created_at')
	list_filter = ('rating',)
	search_fields = ('text', 'author_name')


@admin.register(PlaceRecommendation)
class PlaceRecommendationAdmin(admin.ModelAdmin):
	list_display = ('place', 'rank', 'text', 'confidence', 'source')
	list_filter = ('source',)
	search_fields = ('text',)
