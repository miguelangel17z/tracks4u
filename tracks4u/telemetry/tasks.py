from datetime import timedelta
import logging

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from .models import TelemetryEvent

logger = logging.getLogger(__name__)


@shared_task(name="telemetry.purge_acked_events")
def purge_acked_events(batch_size: int = 5000) -> int:
    """
    Purga en lotes los eventos confirmados (acked_at IS NOT NULL) cuya antigüedad
    supere TELEMETRY_RETENTION_DAYS (default 7 días). Nunca borra eventos sin confirmar.
    """
    retention_days = int(getattr(settings, "TELEMETRY_RETENTION_DAYS", 7))
    cutoff = timezone.now() - timedelta(days=retention_days)
    total_deleted = 0

    while True:
        ids_to_delete = list(
            TelemetryEvent.objects.filter(
                acked_at__isnull=False,
                acked_at__lt=cutoff,
            )
            .order_by("id")
            .values_list("id", flat=True)[:batch_size]
        )
        if not ids_to_delete:
            break
        deleted_count, _ = TelemetryEvent.objects.filter(id__in=ids_to_delete).delete()
        total_deleted += deleted_count
        if len(ids_to_delete) < batch_size:
            break

    logger.info("Purgados %s eventos de telemetría confirmados anteriores a %s", total_deleted, cutoff)
    return total_deleted
