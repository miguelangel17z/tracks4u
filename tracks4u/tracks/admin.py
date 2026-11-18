from django.contrib import admin

from .models import Artist, ArtistGenre, Genre, Track, TrackGenre


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at", "updated_at")
    search_fields = ("name",)
    readonly_fields = ("created_at", "updated_at")


class ArtistGenreInline(admin.TabularInline):
    model = ArtistGenre
    extra = 1


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ("id", "stage_name", "user", "country", "created_at")
    search_fields = ("stage_name", "user__username")
    readonly_fields = ("created_at", "updated_at")
    inlines = [ArtistGenreInline]


class TrackGenreInline(admin.TabularInline):
    model = TrackGenre
    extra = 1


@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "artist", "price", "bpm", "track_type", "created_at")
    list_filter = ("track_type", "language")
    search_fields = ("title", "artist__stage_name")
    readonly_fields = ("created_at", "updated_at")
    inlines = [TrackGenreInline]
