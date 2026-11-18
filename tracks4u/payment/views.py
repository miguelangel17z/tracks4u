from django.views.generic import TemplateView

from tracks.models import Track


class CheckoutView(TemplateView):
    template_name = "payment/checkout.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        track_id = self.request.GET.get("track_id")
        if track_id and str(track_id).isdigit():
            ctx["track"] = (
                Track.objects.filter(id=int(track_id))
                .select_related("artist")
                .prefetch_related("genres")
                .first()
            )
        return ctx
