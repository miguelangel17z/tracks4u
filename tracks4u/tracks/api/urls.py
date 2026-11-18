from django.urls import path

from .api_views import TrackDetailAPIView, TrackListCreateAPIView

urlpatterns = [
    path("", TrackListCreateAPIView.as_view(), name="api-track-list"),
    path("crear/", TrackListCreateAPIView.as_view(), name="api-track-create"),
    path("<int:pk>/", TrackDetailAPIView.as_view(), name="api-track-detail"),
]
