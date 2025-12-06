from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAdminUser
from .models import Place, MenuItem, Review, MenuItemReviewMention, MenuItemReviewSummary
from .serializers import (
    PlaceSerializer,
    MenuItemSerializer,
    ReviewSerializer,
    MenuItemReviewMentionSerializer,
    MenuItemReviewSummarySerializer,
)


class PlaceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Place model.
    Provides list and detail endpoints for restaurant places.
    """
    queryset = Place.objects.all()
    serializer_class = PlaceSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['city']
    search_fields = ['name', 'address']
    ordering_fields = ['name', 'rating', 'user_ratings_total']
    ordering = ['name']


class MenuItemViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for MenuItem model.
    Provides list and detail endpoints for menu items.
    Supports filtering by place and searching by name.
    """
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['place', 'category', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'category']
    ordering = ['name']

    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """
        Get AI summary for a specific menu item.
        Returns the MenuItemReviewSummary if it exists.
        """
        menu_item = self.get_object()
        try:
            summary = menu_item.ai_summary
            serializer = MenuItemReviewSummarySerializer(summary)
            return Response(serializer.data)
        except MenuItemReviewSummary.DoesNotExist:
            return Response({'detail': 'No AI summary available for this menu item.'}, status=404)


class ReviewViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Review model.
    Provides list and detail endpoints for reviews.
    Supports filtering by place and rating.
    """
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['place', 'rating', 'language']
    search_fields = ['text', 'author_name']
    ordering_fields = ['rating', 'created_at']
    ordering = ['-created_at']


class MenuItemReviewMentionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for MenuItemReviewMention model.
    Provides list and detail endpoints for menu item review mentions.
    """
    queryset = MenuItemReviewMention.objects.all()
    serializer_class = MenuItemReviewMentionSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['menu_item', 'review']
    ordering_fields = ['relevance_score']
    ordering = ['-relevance_score']


class MenuItemReviewSummaryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for MenuItemReviewSummary model.
    Provides list and detail endpoints for AI-generated summaries.
    """
    queryset = MenuItemReviewSummary.objects.all()
    serializer_class = MenuItemReviewSummarySerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['last_updated', 'sentiment_score']
    ordering = ['-last_updated']
