from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'reviews', views.ReviewViewSet, basename='internal-review')
# Keep only admin/internal endpoints that make sense for debugging raw data.
# Mentions and per-menu-item summaries are removed in the new project direction.

urlpatterns = [
    # Admin-only internal endpoints for debugging and maintenance
    # Access protected by `IsAdminUser` on the viewsets
    path('', include(router.urls)),
]
