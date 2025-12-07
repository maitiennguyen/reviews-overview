from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'menus'

router = DefaultRouter()
router.register(r'places', views.PlaceViewSet, basename='place')
# Public API surface exposes only places (with nested recommendations) and keeps raw reviews internal.
# Intentionally do not register review or internal-processing viewsets here.

urlpatterns = [
    path('', include(router.urls)),
]
