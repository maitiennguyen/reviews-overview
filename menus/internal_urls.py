from django.urls import path
from .views import ReviewViewSet

# Admin-only internal endpoints for debugging and maintenance
# Access protected by `IsAdminUser` on the viewsets
review_list = ReviewViewSet.as_view({'get': 'list'})
review_detail = ReviewViewSet.as_view({'get': 'retrieve'})

urlpatterns = [
    path('reviews/', review_list, name='internal-review-list'),
    path('reviews/<int:pk>/', review_detail, name='internal-review-detail'),
]
