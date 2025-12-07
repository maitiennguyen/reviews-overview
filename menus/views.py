from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAdminUser
from .models import Place, Review
from .serializers import (
    PlaceSerializer,
    ReviewSerializer,
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
    
