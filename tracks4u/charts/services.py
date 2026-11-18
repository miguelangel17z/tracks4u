from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, Sum
from django.db.models.functions import TruncDay
from django.utils import timezone

from payment.models import Order, OrderItem
from tracks.models import Track


def _date_filter(period: str):
    """Retorna el datetime de inicio según el período solicitado."""
    now = timezone.now()
    periods = {
        "7d": now - timedelta(days=7),
        "30d": now - timedelta(days=30),
        "90d": now - timedelta(days=90),
        "1y": now - timedelta(days=365),
    }
    return periods.get(period)


def _completed_items_qs(period: str = None):
    qs = OrderItem.objects.filter(order__status="COMPLETED")
    since = _date_filter(period) if period else None
    if since:
        qs = qs.filter(created_at__gte=since)
    return qs


def get_dashboard_data(period: str = "30d") -> dict:
    return {
        "summary": get_summary(period),
        "sales": get_sales_by_period(period),
        "revenue": get_revenue(period),
        "top_tracks": get_top_tracks(10),
        "top_genres": get_top_genres(period),
    }


def get_sales_by_period(period: str = "30d") -> dict:
    """Cantidad de canciones vendidas (OrderItem completados) agrupadas por día."""
    qs = _completed_items_qs(period)

    data = (
        qs.annotate(day=TruncDay("created_at"))
        .values("day")
        .annotate(total=Count("id"))
        .order_by("day")
    )

    return {
        "period": period,
        "labels": [entry["day"].strftime("%Y-%m-%d") for entry in data if entry["day"]],
        "values": [entry["total"] for entry in data if entry["day"]],
        "total_sales": qs.count(),
    }


def get_revenue(period: str = "30d") -> dict:
    """
    Calcula ingresos totales (Sum(price_paid)) y desglose por género,
    repartiendo price_paid en partes iguales entre los géneros de cada track
    para que los totales por género sumen exactamente el ingreso total.
    """
    qs = _completed_items_qs(period).select_related("track").prefetch_related("track__genres")

    total_agg = qs.aggregate(total=Sum("price_paid"))["total"] or Decimal("0.00")
    total_revenue = float(round(total_agg, 2))

    genre_revenue = defaultdict(lambda: Decimal("0.00"))
    genre_counts = defaultdict(int)

    for item in qs:
        price = Decimal(str(item.price_paid or 0))
        genres = list(item.track.genres.all()) if item.track else []
        if not genres:
            genre_revenue["Sin género"] += price
            genre_counts["Sin género"] += 1
        else:
            n = len(genres)
            share = (price / Decimal(n)).quantize(Decimal("0.01"))
            distributed = Decimal("0.00")
            for idx, genre in enumerate(genres):
                part = (price - distributed) if idx == n - 1 else share
                distributed += part
                genre_revenue[genre.name] += part
                genre_counts[genre.name] += 1

    sorted_genres = sorted(
        genre_revenue.keys(),
        key=lambda g: genre_revenue[g],
        reverse=True,
    )

    breakdown = {}
    for g_name in sorted_genres:
        rev_val = float(round(genre_revenue[g_name], 2))
        cnt = genre_counts[g_name]
        breakdown[g_name] = {
            "count": cnt,
            "unit_price_usd": round(rev_val / cnt, 2) if cnt else 0.0,
            "revenue_usd": rev_val,
        }

    return {
        "period": period,
        "total_revenue_usd": total_revenue,
        "breakdown": breakdown,
        "labels": sorted_genres,
        "values": [breakdown[g]["revenue_usd"] for g in sorted_genres],
    }


def get_top_tracks(limit: int = 10) -> dict:
    """Retorna los tracks más vendidos según el número de OrderItem completados."""
    agg = (
        OrderItem.objects.filter(order__status="COMPLETED")
        .values("track_id")
        .annotate(sold_count=Count("id"))
        .order_by("-sold_count", "track_id")[:limit]
    )

    counts_by_id = {row["track_id"]: row["sold_count"] for row in agg}
    tracks_by_id = {
        t.id: t
        for t in Track.objects.filter(id__in=counts_by_id.keys()).prefetch_related("genres")
    }

    labels = []
    values = []
    tracks_payload = []

    for row in agg:
        track = tracks_by_id.get(row["track_id"])
        if not track:
            continue
        sold_count = row["sold_count"]
        genre_str = ", ".join(g.name for g in track.genres.all()) or "Sin género"
        labels.append(track.title)
        values.append(sold_count)
        tracks_payload.append(
            {
                "id": track.id,
                "title": track.title,
                "genres": genre_str,
                "items_sold": sold_count,
                "price": float(track.price or 0),
            }
        )

    return {
        "labels": labels,
        "values": values,
        "tracks": tracks_payload,
    }


def get_top_genres(period: str = "30d") -> dict:
    """Agrupa los items vendidos por género del track (un item cuenta en cada uno de sus géneros)."""
    qs = _completed_items_qs(period).select_related("track").prefetch_related("track__genres")

    counts = defaultdict(int)
    for item in qs:
        genres = list(item.track.genres.all()) if item.track else []
        if not genres:
            counts["Sin género"] += 1
        else:
            for genre in genres:
                counts[genre.name] += 1

    sorted_items = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))

    return {
        "period": period,
        "labels": [k for k, _ in sorted_items],
        "values": [v for _, v in sorted_items],
    }


def get_summary(period: str = "30d") -> dict:
    """KPIs del dashboard: ventas, ingresos, ticket medio, catálogo y top track."""
    qs = _completed_items_qs(period)
    total_sales = qs.count()
    total_revenue_dec = qs.aggregate(total=Sum("price_paid"))["total"] or Decimal("0.00")
    total_revenue = float(round(total_revenue_dec, 2))

    since = _date_filter(period)
    orders_qs = Order.objects.filter(status="COMPLETED")
    if since:
        orders_qs = orders_qs.filter(created_at__gte=since)
    completed_orders_count = orders_qs.count()
    avg_ticket = (
        round(total_revenue / completed_orders_count, 2)
        if completed_orders_count > 0
        else 0.0
    )

    top_row = (
        OrderItem.objects.filter(order__status="COMPLETED")
        .values("track__title")
        .annotate(sold_count=Count("id"))
        .order_by("-sold_count")
        .first()
    )
    top_track_title = top_row["track__title"] if top_row else "—"

    return {
        "period": period,
        "total_sales": total_sales,
        "total_revenue_usd": total_revenue,
        "avg_ticket_usd": avg_ticket,
        "total_tracks": Track.objects.count(),
        "top_track": top_track_title,
    }
