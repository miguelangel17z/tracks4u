import uuid

from django.db import models
from django.utils import timezone


class TelemetryEvent(models.Model):
    DEVICE_CHOICES = [
        ("web_desktop", "Web Desktop"),
        ("web_mobile", "Web Mobile"),
        ("web_tablet", "Web Tablet"),
        ("unknown", "Unknown"),
    ]
    ENTRYPOINT_CHOICES = [
        ("home", "Home"),
        ("search", "Search"),
        ("artist_profile", "Artist Profile"),
        ("playlist", "Playlist"),
        ("track_page", "Track Page"),
        ("library", "Library"),
        ("external_link", "External Link"),
        ("unknown", "Unknown"),
    ]

    id = models.BigAutoField(primary_key=True)
    event_id = models.UUIDField(unique=True, default=uuid.uuid4)
    event_type = models.CharField(max_length=40)
    ts = models.DateTimeField(default=timezone.now)
    session_id = models.CharField(max_length=64)
    user = models.ForeignKey(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column="user_id",
        related_name="telemetry_events",
    )
    device = models.CharField(max_length=20, default="unknown", choices=DEVICE_CHOICES)
    geo = models.JSONField(null=True, blank=True)
    entrypoint = models.CharField(
        max_length=20,
        default="unknown",
        choices=ENTRYPOINT_CHOICES,
    )
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    acked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "telemetry_event"

    def __str__(self):
        return f"{self.event_type} ({self.event_id})"
