from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'reviews', views.ReviewViewSet, basename='internal-review')
router.register(r'mentions', views.MenuItemReviewMentionViewSet, basename='internal-mention')
router.register(r'summaries', views.MenuItemReviewSummaryViewSet, basename='internal-summary')

urlpatterns = [
    # Admin-only internal endpoints for debugging and maintenance
    # Access protected by `IsAdminUser` on the viewsets
    path('', include(router.urls)),
]
