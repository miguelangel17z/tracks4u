from django.views.generic import CreateView, ListView
from django.urls import reverse_lazy
from .models import Track
from .services import TrackService


class TrackCreateView(CreateView):
    model = Track
    fields = ['title', 'audio_file', 'price', 'bpm']
    template_name = 'tracks/track_form.html'
    success_url = reverse_lazy('track-list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        TrackService._notificar_track_subido(self.object)
        return response


class TrackListView(ListView):
    model = Track
    template_name = 'tracks/track_list.html'
    context_object_name = 'tracks'
    ordering = ['-created_at']