from django.contrib import admin

from .models import TelemetryEvent


@admin.register(TelemetryEvent)
class TelemetryEventAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "event_id",
        "event_type",
        "session_id",
        "user",
        "device",
        "entrypoint",
        "ts",
        "created_at",
        "acked_at",
    )
    list_filter = ("event_type", "device", "entrypoint")
    search_fields = ("event_id", "session_id")
    readonly_fields = (
        "id",
        "event_id",
        "event_type",
        "ts",
        "session_id",
        "user",
        "device",
        "geo",
        "entrypoint",
        "payload",
        "created_at",
        "acked_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
