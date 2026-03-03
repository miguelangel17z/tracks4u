from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import CreateView, ListView
from django.urls import reverse_lazy

from .models import Track
from .services import TrackCreatorService, TrackQueryService


def home(request):
    return HttpResponse("Home page")


class TrackCreateView(CreateView):
    model = Track
    fields = ["title", "audio_file", "cover_image", "price", "bpm", "genre", "stock"]
    template_name = "tracks/track_form.html"
    success_url = reverse_lazy("track-list")

    def form_valid(self, form):
        track = form.save()                        # View sabe de Forms → hace el save()
        TrackCreatorService.crear_track(track)     # Service recibe Track puro
        return HttpResponseRedirect(self.success_url)


class TrackListView(ListView):
    model = Track
    template_name = "tracks/track_list.html"
    context_object_name = "tracks"
    ordering = ["-created_at"]