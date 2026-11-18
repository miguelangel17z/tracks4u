from django.urls import path

from .views import EventAckView, EventDrainView, EventIngestView

urlpatterns = [
    path("", EventIngestView.as_view(), name="telemetry-ingest"),
    path("drain/", EventDrainView.as_view(), name="telemetry-drain"),
    path("ack/", EventAckView.as_view(), name="telemetry-ack"),
]
