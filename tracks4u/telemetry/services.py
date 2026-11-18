from datetime import datetime, timedelta, timezone as dt_timezone
from decimal import Decimal
import uuid
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .models import TelemetryEvent
from .schemas import DEVICES, ENTRYPOINTS, SCHEMA_VERSION, validate_payload


def _clean_payload_types(payload: dict) -> dict:
    """Convierte Decimal/UUID dentro del payload a tipos serializables por JSONField."""
    cleaned = {}
    for k, v in payload.items():
        if isinstance(v, Decimal):
            cleaned[k] = float(v)
        elif isinstance(v, uuid.UUID):
            cleaned[k] = str(v)
        else:
            cleaned[k] = v
    return cleaned


def _format_iso_utc(dt: datetime) -> str:
    if dt is None:
        return None
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, dt_timezone.utc)
    dt_utc = dt.astimezone(dt_timezone.utc)
    return dt_utc.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _parse_event_ts(raw_ts: Any) -> datetime:
    if raw_ts is None or raw_ts == "":
        return timezone.now()
    if isinstance(raw_ts, datetime):
        dt = raw_ts
    elif isinstance(raw_ts, str):
        dt = parse_datetime(raw_ts)
        if dt is None:
            raise ValueError("Invalid ISO 8601 timestamp in ts")
    else:
        raise ValueError("Invalid timestamp type in ts")

    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, dt_timezone.utc)

    if dt > timezone.now() + timedelta(minutes=5):
        raise ValueError("ts cannot be more than 5 minutes in the future")
    return dt


def serialize_event(event: TelemetryEvent) -> dict:
    """Serializa una fila de TelemetryEvent al envelope oficial para el drenaje."""
    return {
        "id": event.id,
        "event_id": str(event.event_id),
        "schema_version": SCHEMA_VERSION,
        "event_type": event.event_type,
        "ts": _format_iso_utc(event.ts),
        "received_at": _format_iso_utc(event.created_at),
        "session_id": event.session_id,
        "user_id": event.user_id,
        "device": event.device,
        "geo": event.geo,
        "entrypoint": event.entrypoint,
        "payload": event.payload,
    }


def emit_event(
    event_type: str,
    *,
    user=None,
    session_id: str,
    payload: dict,
    device: str = "unknown",
    geo: Optional[dict] = None,
    entrypoint: str = "unknown",
    ts: Any = None,
    event_id: Any = None,
) -> Optional[TelemetryEvent]:
    """
    Emite un evento al outbox (telemetry_event).
    Puede invocarse dentro de un transaction.atomic() de negocio.
    Devuelve la instancia creada o None si el event_id ya existía.
    """
    if not session_id or not isinstance(session_id, str) or len(session_id) > 64:
        raise ValueError("session_id must be a non-empty string up to 64 chars")

    device = device if device in DEVICES else "unknown"
    entrypoint = entrypoint if entrypoint in ENTRYPOINTS else "unknown"

    payload_errors = validate_payload(event_type, payload)
    if payload_errors:
        raise ValueError("; ".join(payload_errors))

    parsed_ts = _parse_event_ts(ts)

    if event_id is not None:
        try:
            ev_uuid = uuid.UUID(str(event_id))
        except ValueError as exc:
            raise ValueError("Invalid event_id UUID") from exc
    else:
        ev_uuid = uuid.uuid4()

    auth_user = user if (user is not None and getattr(user, "is_authenticated", True)) else None
    resolved_geo = geo
    if resolved_geo is None and auth_user is not None and getattr(auth_user, "country", None):
        resolved_geo = {"country": auth_user.country}

    if TelemetryEvent.objects.filter(event_id=ev_uuid).exists():
        return None

    obj = TelemetryEvent(
        event_id=ev_uuid,
        event_type=event_type,
        ts=parsed_ts,
        session_id=session_id,
        user=auth_user,
        device=device,
        geo=resolved_geo,
        entrypoint=entrypoint,
        payload=_clean_payload_types(payload),
    )
    TelemetryEvent.objects.bulk_create([obj], ignore_conflicts=True)
    return TelemetryEvent.objects.filter(event_id=ev_uuid).first()


def ingest_events(events: List[dict], user=None) -> dict:
    """
    Valida e inserta un lote de hasta 100 eventos provenientes del front.
    Ignora cualquier user_id enviado en el cuerpo; el user proviene solo del JWT.
    """
    auth_user = (
        user if (user is not None and getattr(user, "is_authenticated", False)) else None
    )

    rejected = []
    candidates = []
    candidate_uuids = []

    for index, raw in enumerate(events):
        if not isinstance(raw, dict):
            rejected.append({"index": index, "error": "Event item must be a JSON object"})
            continue

        raw_event_id = raw.get("event_id")
        if not raw_event_id:
            rejected.append({"index": index, "error": "event_id is required"})
            continue
        try:
            ev_uuid = uuid.UUID(str(raw_event_id))
        except ValueError:
            rejected.append({"index": index, "error": "event_id must be a valid UUID"})
            continue

        event_type = raw.get("event_type")
        session_id = raw.get("session_id")
        if not session_id or not isinstance(session_id, str) or len(session_id) > 64:
            rejected.append(
                {"index": index, "error": "session_id is required (max 64 chars)"}
            )
            continue

        device = raw.get("device") or "unknown"
        if device not in DEVICES:
            rejected.append(
                {"index": index, "error": f"Invalid device: {device}"}
            )
            continue

        entrypoint = raw.get("entrypoint") or "unknown"
        if entrypoint not in ENTRYPOINTS:
            rejected.append(
                {"index": index, "error": f"Invalid entrypoint: {entrypoint}"}
            )
            continue

        geo = raw.get("geo")
        if geo is not None and not isinstance(geo, dict):
            rejected.append({"index": index, "error": "geo must be a JSON object or null"})
            continue
        if geo is None and auth_user is not None and getattr(auth_user, "country", None):
            geo = {"country": auth_user.country}

        try:
            parsed_ts = _parse_event_ts(raw.get("ts"))
        except ValueError as exc:
            rejected.append({"index": index, "error": str(exc)})
            continue

        payload = raw.get("payload")
        payload_errors = validate_payload(event_type, payload)
        if payload_errors:
            rejected.append({"index": index, "error": "; ".join(payload_errors)})
            continue

        candidates.append(
            (
                ev_uuid,
                TelemetryEvent(
                    event_id=ev_uuid,
                    event_type=event_type,
                    ts=parsed_ts,
                    session_id=session_id,
                    user=auth_user,
                    device=device,
                    geo=geo,
                    entrypoint=entrypoint,
                    payload=_clean_payload_types(payload),
                ),
            )
        )
        candidate_uuids.append(ev_uuid)

    if not candidates:
        return {"accepted": 0, "duplicates": 0, "rejected": rejected}

    existing_in_db = set(
        TelemetryEvent.objects.filter(event_id__in=candidate_uuids).values_list(
            "event_id", flat=True
        )
    )

    to_insert = []
    seen_in_batch = set()
    duplicates = 0

    for ev_uuid, model_instance in candidates:
        if ev_uuid in existing_in_db or ev_uuid in seen_in_batch:
            duplicates += 1
        else:
            seen_in_batch.add(ev_uuid)
            to_insert.append(model_instance)

    if to_insert:
        TelemetryEvent.objects.bulk_create(to_insert, ignore_conflicts=True)

    return {
        "accepted": len(to_insert),
        "duplicates": duplicates,
        "rejected": rejected,
    }


def drain(since: int = 0, limit: int = 500) -> dict:
    """
    Lee hasta `limit` eventos pendientes con ventana de asentamiento
    (created_at <= now() - TELEMETRY_SETTLE_SECONDS).
    """
    max_limit = int(getattr(settings, "TELEMETRY_DRAIN_MAX_LIMIT", 1000))
    settle_sec = int(getattr(settings, "TELEMETRY_SETTLE_SECONDS", 5))
    effective_limit = min(max(1, limit), max_limit)
    cutoff = timezone.now() - timedelta(seconds=settle_sec)

    rows = list(
        TelemetryEvent.objects.filter(
            id__gt=since,
            acked_at__isnull=True,
            created_at__lte=cutoff,
        ).order_by("id")[: effective_limit + 1]
    )

    has_more = len(rows) > effective_limit
    batch = rows[:effective_limit]
    next_cursor = batch[-1].id if batch else since

    return {
        "events": [serialize_event(ev) for ev in batch],
        "next_cursor": next_cursor,
        "has_more": has_more,
    }


def ack(last_id: int) -> int:
    """Marca como confirmados todos los eventos pendientes con id <= last_id."""
    return TelemetryEvent.objects.filter(
        id__lte=last_id,
        acked_at__isnull=True,
    ).update(acked_at=timezone.now())
