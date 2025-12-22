from difflib import SequenceMatcher

from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAdminUser, AllowAny
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


class ReviewSearchViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public search over reviews by keyword. Supports optional place scoping by name or id.
    Includes a lightweight fuzzy fallback for minor misspellings.
    """
    serializer_class = ReviewSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['text', 'author_name']
    ordering_fields = ['created_at', 'rating']
    ordering = ['-created_at']

    def get_queryset(self):
        base = Review.objects.select_related('place')
        query = self.request.query_params.get('q')
        if not query:
            return base.none()

        place_ids = self._parse_multi_param('place')
        place_names = self._parse_multi_param('place_name')

        target_place_ids = set(place_ids)
        for name in place_names:
            target_place_ids.update(self._match_place_ids(name))

        if place_names and not target_place_ids:
            return base.none()

        if target_place_ids:
            base = base.filter(place_id__in=target_place_ids)

        qs = base.filter(text__icontains=query)
        if qs.exists() or len(query) < 3:
            return qs

        # Fuzzy fallback for minor misspellings (small data sets only)
        fuzzy_ids = self._fuzzy_review_ids(base, query, limit=500)
        if not fuzzy_ids:
            return qs
        return base.filter(id__in=fuzzy_ids)

    @staticmethod
    def _normalize_text(text: str) -> str:
        return "".join(ch.lower() for ch in text if ch.isalnum() or ch.isspace())

    def _fuzzy_review_ids(self, qs, term: str, limit: int = 500):
        norm_term = self._normalize_text(term)
        if len(norm_term) < 4:
            return []
        ids = []
        for row in qs.values("id", "text")[:limit]:
            norm_text = self._normalize_text(row["text"] or "")
            for token in norm_text.split():
                if len(token) < 3:
                    continue
                if abs(len(token) - len(norm_term)) > 1:
                    continue
                if SequenceMatcher(None, norm_term, token).ratio() >= 0.9:
                    ids.append(row["id"])
                    break
        return ids

    def _match_place_ids(self, term: str):
        direct = list(Place.objects.filter(name__icontains=term).values_list("id", flat=True))
        if direct:
            return direct

        norm_term = term.lower().strip()
        scored = []
        for place in Place.objects.all().values("id", "name"):
            score = SequenceMatcher(None, norm_term, place["name"].lower()).ratio()
            if score >= 0.6:
                scored.append((score, place["id"]))
        scored.sort(key=lambda tup: tup[0], reverse=True)
        return [pid for _, pid in scored[:5]]

    def _parse_multi_param(self, key: str):
        values = self.request.query_params.getlist(key) or []
        expanded = []
        for val in values:
            expanded.extend([v.strip() for v in val.split(",") if v.strip()])
        if key == 'place':
            cleaned = []
            for v in expanded:
                try:
                    cleaned.append(int(v))
                except (TypeError, ValueError):
                    continue
            return cleaned
        return expanded
    
