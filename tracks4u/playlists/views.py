from django.views.generic import DetailView, ListView

from playlists.models import Playlist


class PlaylistListView(ListView):
    model = Playlist
    template_name = "playlists/playlist_list.html"
    context_object_name = "playlists"

    def get_queryset(self):
        return (
            Playlist.objects.filter(is_public=True)
            .select_related("owner")
            .prefetch_related("playlist_tracks__track")
            .order_by("-created_at")
        )


class PlaylistDetailView(DetailView):
    model = Playlist
    template_name = "playlists/playlist_detail.html"
    context_object_name = "playlist"

    def get_queryset(self):
        return Playlist.objects.select_related("owner").prefetch_related(
            "playlist_tracks__track__artist",
            "playlist_tracks__track__genres",
        )
