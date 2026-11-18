from django.urls import path

from playlists.api.views import (
    PlaylistDetailAPIView,
    PlaylistListCreateAPIView,
    PlaylistReorderAPIView,
    PlaylistTrackAddAPIView,
    PlaylistTrackRemoveAPIView,
)

urlpatterns = [
    path("", PlaylistListCreateAPIView.as_view(), name="api-playlist-list"),
    path("<int:pk>/", PlaylistDetailAPIView.as_view(), name="api-playlist-detail"),
    path("<int:pk>/tracks/", PlaylistTrackAddAPIView.as_view(), name="api-playlist-add-track"),
    path(
        "<int:pk>/tracks/<int:track_id>/",
        PlaylistTrackRemoveAPIView.as_view(),
        name="api-playlist-remove-track",
    ),
    path("<int:pk>/order/", PlaylistReorderAPIView.as_view(), name="api-playlist-reorder"),
]
