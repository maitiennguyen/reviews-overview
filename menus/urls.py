from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'menus'

router = DefaultRouter()
router.register(r'places', views.PlaceViewSet, basename='place')
router.register(r'search/reviews', views.ReviewSearchViewSet, basename='review-search')
# Public API surface exposes places and keyword-based review search.
# Raw review listings remain internal/admin-only.

urlpatterns = [
    path('', include(router.urls)),
]
