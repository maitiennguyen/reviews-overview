from rest_framework import serializers
from .models import Place, MenuItem, Review, MenuItemReviewMention, MenuItemReviewSummary


class MenuItemReviewMentionSerializer(serializers.ModelSerializer):
    review_text = serializers.CharField(source='review.text', read_only=True)
    review_rating = serializers.IntegerField(source='review.rating', read_only=True)
    review_author = serializers.CharField(source='review.author_name', read_only=True)

    class Meta:
        model = MenuItemReviewMention
        fields = ('id', 'review', 'relevance_score', 'review_text', 'review_rating', 'review_author')
        read_only_fields = ('id', 'review_text', 'review_rating', 'review_author')


class MenuItemReviewSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItemReviewSummary
        fields = ('id', 'summary_text', 'sentiment_score', 'tags', 'last_updated')
        read_only_fields = ('id', 'last_updated')


class MenuItemSerializer(serializers.ModelSerializer):
    place_name = serializers.CharField(source='place.name', read_only=True)
    ai_summary = MenuItemReviewSummarySerializer(read_only=True)

    class Meta:
        model = MenuItem
        fields = ('id', 'place', 'place_name', 'name', 'description', 'category', 'is_active', 'ai_summary')
        read_only_fields = ('id', 'place_name', 'ai_summary')


class ReviewSerializer(serializers.ModelSerializer):
    place_name = serializers.CharField(source='place.name', read_only=True)
    menu_item_mentions = MenuItemReviewMentionSerializer(source='menu_item_mentions', many=True, read_only=True)

    class Meta:
        model = Review
        fields = ('id', 'place', 'place_name', 'google_review_id', 'author_name', 'rating', 'text', 'language', 'created_at', 'fetched_at', 'menu_item_mentions')
        read_only_fields = ('id', 'place_name', 'menu_item_mentions', 'fetched_at')


class PlaceSerializer(serializers.ModelSerializer):
    menu_items = MenuItemSerializer(many=True, read_only=True)
    review_count = serializers.SerializerMethodField()

    class Meta:
        model = Place
        fields = ('id', 'name', 'google_place_id', 'address', 'city', 'latitude', 'longitude', 'rating', 'user_ratings_total', 'last_synced', 'menu_items', 'review_count')
        read_only_fields = ('id', 'menu_items', 'review_count', 'last_synced')

    def get_review_count(self, obj):
        return obj.reviews.count()
