from django.contrib import admin

from .models import Playlist, PlaylistTrack


class PlaylistTrackInline(admin.TabularInline):
    model = PlaylistTrack
    extra = 1


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "owner", "is_public", "created_at")
    list_filter = ("is_public",)
    search_fields = ("name", "owner__username")
    readonly_fields = ("created_at", "updated_at")
    inlines = [PlaylistTrackInline]


@admin.register(PlaylistTrack)
class PlaylistTrackAdmin(admin.ModelAdmin):
    list_display = ("id", "playlist", "track", "position", "added_at")
    readonly_fields = ("added_at", "updated_at")
