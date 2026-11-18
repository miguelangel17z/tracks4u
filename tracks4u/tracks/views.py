from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView

from .models import Track
from .services import TrackCreatorService, TrackQueryService


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

    def form_valid(self, form):
        track = form.save()
        TrackCreatorService.crear_track(track)
        return HttpResponseRedirect(self.success_url)


class TrackListView(ListView):
    model = Track
    template_name = "tracks/track_list.html"
    context_object_name = "tracks"

    def get_queryset(self):
        return Track.objects.select_related("artist").prefetch_related("genres").order_by("-created_at")


class TrackDetailView(DetailView):
    model = Track
    template_name = "tracks/Track_detail.html"
    context_object_name = "track"

    def get_queryset(self):
        return Track.objects.select_related("artist").prefetch_related("genres")
