from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path

from tracks.api.api_views import ArtistDetailAPIView, GenreListAPIView

urlpatterns = [
    path("", lambda request: redirect("users/")),
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    path("tracks/", include("tracks.urls")),
    path("playlists/", include("playlists.web_urls")),
    path("api/tracks/", include("tracks.api.urls")),
    path("api/genres/", GenreListAPIView.as_view(), name="api-genre-list"),
    path("api/artists/<int:pk>/", ArtistDetailAPIView.as_view(), name="api-artist-detail"),
    path("api/playlists/", include("playlists.urls")),
    path("api/events/", include("telemetry.urls")),
    path("users/", include("users.urls")),
    path("payment/", include("payment.urls")),
    path("internal/charts/", include("charts.urls")),
    path("api/sistema/", include("sistema_client.urls")),
]
