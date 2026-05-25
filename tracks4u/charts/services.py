from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from payment.models import License
from tracks.models import Track

LICENSE_PRICES_USD = {
    "basic": 9.99,
    "premium": 29.99,
    "exclusive": 99.99,
}


def _date_filter(period: str):
    """Retorna el datetime de inicio según el período solicitado."""
    now = timezone.now()
    periods = {
        "7d":  now - timedelta(days=7),
        "30d": now - timedelta(days=30),
        "90d": now - timedelta(days=90),
        "1y":  now - timedelta(days=365),
    }
    return periods.get(period)

def get_dashboard_data(period="30d"):

    return {
        "summary": get_summary(period),
        "sales": get_sales_by_period(period),
        "revenue": get_revenue(period),
        "top_tracks": get_top_tracks(10),
        "top_genres": get_top_genres(period),
    }


#  Ventas totales por período 

def get_sales_by_period(period: str = "30d") -> dict:
    """
    Retorna la cantidad de licencias vendidas agrupadas por día
    dentro del período solicitado.
    """
    since = _date_filter(period)
    qs = License.objects.filter(created_at__gte=since) if since else License.objects.all()

    # Agrupar por fecha (día)
    from django.db.models.functions import TruncDay
    data = (
        qs
        .annotate(day=TruncDay("created_at"))
        .values("day")
        .annotate(total=Count("id"))
        .order_by("day")
    )

    return {
        "period": period,
        "labels": [entry["day"].strftime("%Y-%m-%d") for entry in data],
        "values": [entry["total"] for entry in data],
        "total_sales": qs.count(),
    }


#  Ingresos totales y por tipo de licencia 

def get_revenue(period: str = "30d") -> dict:
    """
    Calcula ingresos totales y desglosados por tipo de licencia
    usando los precios fijos definidos en LICENSE_PRICES_USD.
    """
    since = _date_filter(period)
    qs = License.objects.filter(created_at__gte=since) if since else License.objects.all()

    breakdown = (
        qs
        .values("license_type")
        .annotate(count=Count("id"))
        .order_by("license_type")
    )

    result = {}
    total_revenue = 0.0

    for entry in breakdown:
        lt = entry["license_type"]
        price = LICENSE_PRICES_USD.get(lt, 0)
        revenue = round(entry["count"] * price, 2)
        result[lt] = {
            "count": entry["count"],
            "unit_price_usd": price,
            "revenue_usd": revenue,
        }
        total_revenue += revenue

    return {
        "period": period,
        "total_revenue_usd": round(total_revenue, 2),
        "breakdown": result,
        # Para chart de dona
        "labels": list(result.keys()),
        "values": [v["revenue_usd"] for v in result.values()],
    }


#  Tracks más vendidos 

def get_top_tracks(limit: int = 10) -> dict:
    """
    Retorna los tracks con más licencias vendidas,
    usando sales_count del modelo Track.
    """
    tracks = (
        Track.objects
        .filter(sales_count__gt=0)
        .order_by("-sales_count")[:limit]
    )

    return {
        "labels": [t.title for t in tracks],
        "values": [t.sales_count for t in tracks],
        "tracks": [
            {
                "id": t.id,
                "title": t.title,
                "genre": t.genre or "N/A",
                "sales_count": t.sales_count,
                "is_sold": t.is_sold,
            }
            for t in tracks
        ],
    }


#  Géneros más vendidos 

def get_top_genres(period: str = "30d") -> dict:
    """
    Agrupa las licencias vendidas por género del track asociado.
    """
    since = _date_filter(period)
    qs = License.objects.filter(created_at__gte=since) if since else License.objects.all()

    data = (
        qs
        .values("track__genre")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    labels = [entry["track__genre"] or "Sin género" for entry in data]
    values = [entry["total"] for entry in data]

    return {
        "period": period,
        "labels": labels,
        "values": values,
    }


#   Resumen general (KPI cards) 

def get_summary(period: str = "30d") -> dict:
    """
    KPIs rápidos para las cards del dashboard.
    """
    since = _date_filter(period)
    qs = License.objects.filter(created_at__gte=since) if since else License.objects.all()

    total_sales = qs.count()
    total_revenue = sum(
        LICENSE_PRICES_USD.get(lt, 0) * count
        for lt, count in qs.values_list("license_type", flat=False)
        .values("license_type")
        .annotate(count=Count("id"))
        .values_list("license_type", "count")
    )

    top_track = Track.objects.order_by("-sales_count").first()

    return {
        "period": period,
        "total_sales": total_sales,
        "total_revenue_usd": round(total_revenue, 2),
        "total_tracks": Track.objects.count(),
        "top_track": top_track.title if top_track else "—",
    }
