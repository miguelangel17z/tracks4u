from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView

from .models import Artist, Genre, Track
from .services import TrackCreatorService


def home(request):
    return HttpResponse("Home page")


class TrackCreateView(CreateView):
    model = Track
    fields = [
        "title",
        "audio_file",
        "cover_image",
        "subgenre",
        "language",
        "bpm",
        "track_type",
        "price",
    ]
    template_name = "tracks/track_form.html"
    success_url = reverse_lazy("track-list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["genres"] = Genre.objects.all().order_by("name")
        return ctx

    def form_valid(self, form):
        track = form.save()
        TrackCreatorService.crear_track(track)
        return HttpResponseRedirect(self.success_url)


class TrackListView(ListView):
    model = Track
    template_name = "tracks/track_list.html"
    context_object_name = "tracks"

    def get_queryset(self):
        return (
            Track.objects.select_related("artist")
            .prefetch_related("genres")
            .order_by("-created_at", "-id")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["genres"] = Genre.objects.all().order_by("name")
        ctx["selected_genre"] = self.request.GET.get("genre", "")
        return ctx


class TrackDetailView(DetailView):
    model = Track
    template_name = "tracks/Track_detail.html"
    context_object_name = "track"

    def get_queryset(self):
        return Track.objects.select_related("artist").prefetch_related("genres")


class ArtistDetailView(DetailView):
    model = Artist
    template_name = "tracks/artist_detail.html"
    context_object_name = "artist"

    def get_queryset(self):
        return Artist.objects.prefetch_related("genres", "tracks__genres")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["tracks"] = (
            self.object.tracks.select_related("artist")
            .prefetch_related("genres")
            .order_by("-created_at", "-id")
        )
        return ctx
