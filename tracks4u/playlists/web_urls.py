from django.urls import path

from playlists.views import PlaylistDetailView, PlaylistListView

urlpatterns = [
    path("", PlaylistListView.as_view(), name="playlist-list"),
    path("<int:pk>/", PlaylistDetailView.as_view(), name="playlist-detail"),
]
