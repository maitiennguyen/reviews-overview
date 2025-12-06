from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'menus'

router = DefaultRouter()
router.register(r'places', views.PlaceViewSet, basename='place')
router.register(r'menu-items', views.MenuItemViewSet, basename='menuitem')
# Intentionally do not register Review, Mention, or Summary viewsets here.
# Those models are internal and used for processing (AI summaries, mention matching).
# Public API surface intentionally exposes only places and menu items (with nested AI summary).

urlpatterns = [
    path('', include(router.urls)),
]
