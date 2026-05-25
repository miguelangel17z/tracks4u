from django.urls import path
from charts.api.api_views import (
    SalesByPeriodView,
    RevenueView,
    TopTracksView,
    TopGenresView,
    SummaryView,
)

# Estos endpoints son INTERNOS — solo accesibles dentro de la red Docker.
# No exponer al exterior via nginx.

urlpatterns = [
    path("sales/",      SalesByPeriodView.as_view(), name="charts-sales"),
    path("revenue/",    RevenueView.as_view(),        name="charts-revenue"),
    path("top-tracks/", TopTracksView.as_view(),      name="charts-top-tracks"),
    path("top-genres/", TopGenresView.as_view(),      name="charts-top-genres"),
    path("summary/",    SummaryView.as_view(),         name="charts-summary"),
]
