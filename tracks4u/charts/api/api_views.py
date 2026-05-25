from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from charts import services
from .serializers import (
    SalesByPeriodSerializer,
    RevenueSerializer,
    TopTracksSerializer,
    TopGenresSerializer,
    SummarySerializer,
)


class SalesByPeriodView(APIView):
    """
    GET /internal/charts/sales/?period=30d
    Períodos válidos: 7d | 30d | 90d | 1y
    Uso interno — consumido por flask_charts.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        period = request.query_params.get("period", "30d")
        data = services.get_sales_by_period(period)
        return Response(SalesByPeriodSerializer(data).data)


class RevenueView(APIView):
    """
    GET /internal/charts/revenue/?period=30d
    Ingresos totales y por tipo de licencia.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        period = request.query_params.get("period", "30d")
        data = services.get_revenue(period)
        return Response(RevenueSerializer(data).data)


class TopTracksView(APIView):
    """
    GET /internal/charts/top-tracks/?limit=10
    Tracks más vendidos.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        limit = int(request.query_params.get("limit", 10))
        data = services.get_top_tracks(limit)
        return Response(TopTracksSerializer(data).data)


class TopGenresView(APIView):
    """
    GET /internal/charts/top-genres/?period=30d
    Géneros más vendidos en el período.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        period = request.query_params.get("period", "30d")
        data = services.get_top_genres(period)
        return Response(TopGenresSerializer(data).data)


class SummaryView(APIView):
    """
    GET /internal/charts/summary/?period=30d
    KPIs rápidos para las cards del dashboard.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        period = request.query_params.get("period", "30d")
        data = services.get_summary(period)
        return Response(SummarySerializer(data).data)


class DashboardDataView(APIView):
    """
    GET /internal/charts/dashboard/?period=30d
    Toda la información consolidada del dashboard.
    """

    permission_classes = [AllowAny]

    def get(self, request):

        period = request.query_params.get("period", "30d")

        data = services.get_dashboard_data(period)

        return Response(data)