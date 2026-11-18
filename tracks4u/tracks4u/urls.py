from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path

urlpatterns = [
    path("", lambda request: redirect("users/")),
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    path("tracks/", include("tracks.urls")),
    path("api/tracks/", include("tracks.api.urls")),
    path("api/events/", include("telemetry.urls")),
    path("users/", include("users.urls")),
    path("payment/", include("payment.urls")),
    path("internal/charts/", include("charts.urls")),
    path("api/sistema/", include("sistema_client.urls")),
]

if settings.DEBUG and getattr(settings, "MEDIA_URL", None) and getattr(settings, "MEDIA_ROOT", None):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
