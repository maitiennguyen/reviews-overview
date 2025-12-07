from rest_framework import serializers
from .models import Place, Review, PlaceRecommendation


class PlaceRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlaceRecommendation
        fields = ('id', 'text', 'rank', 'confidence', 'source', 'last_updated')
        read_only_fields = ('id', 'last_updated')


class ReviewSerializer(serializers.ModelSerializer):
    place_name = serializers.CharField(source='place.name', read_only=True)

    class Meta:
        model = Review
        fields = ('id', 'place', 'place_name', 'google_review_id', 'author_name', 'rating', 'text', 'language', 'created_at', 'fetched_at')
        read_only_fields = ('id', 'place_name', 'fetched_at')


class PlaceSerializer(serializers.ModelSerializer):
    recommendations = PlaceRecommendationSerializer(many=True, read_only=True)
    review_count = serializers.SerializerMethodField()

    class Meta:
        model = Place
        fields = ('id', 'name', 'google_place_id', 'address', 'city', 'latitude', 'longitude', 'rating', 'user_ratings_total', 'last_synced', 'recommendations', 'review_count')
        read_only_fields = ('id', 'recommendations', 'review_count', 'last_synced')

    def get_review_count(self, obj):
        return obj.reviews.count()
