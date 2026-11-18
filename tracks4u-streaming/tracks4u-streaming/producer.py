import json
import os
import random
import time
import uuid
from datetime import datetime, timezone

import requests
from confluent_kafka import Producer

BOOTSTRAP = os.getenv("BOOTSTRAP", "127.0.0.1:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "tracks4u.events")
DJANGO_URL = os.getenv("DJANGO_URL", "http://127.0.0.1:8000").rstrip("/")
TELEMETRY_DRAIN_TOKEN = os.getenv("TELEMETRY_DRAIN_TOKEN", "").strip()
DRAIN_LIMIT = int(os.getenv("DRAIN_LIMIT", "500"))
POLL_SECONDS = float(os.getenv("POLL_SECONDS", "3"))
SIMULATE = os.getenv("SIMULATE", "").lower() in ("1", "true", "yes")

EVENTS = [
    "play_start",
    "play_progress",
    "play_complete",
    "skip",
    "like",
    "follow",
    "share",
    "playlist_add",
    "search",
    "purchase_intent",
    "page_view",
]


def normalize_outbox_event(ev: dict) -> dict:
    """Transforma un evento del outbox de Django al formato esperado por Kafka y consumer.py."""
    raw_payload = ev.get("payload")
    payload_dict = raw_payload if isinstance(raw_payload, dict) else {}

    track_id = ev.get("track_id")
    if track_id is None:
        track_id = payload_dict.get("track_id")

    raw_geo = ev.get("geo")
    if isinstance(raw_geo, dict):
        geo_val = (
            raw_geo.get("country")
            if "country" in raw_geo
            else json.dumps(raw_geo, ensure_ascii=False)
        )
    else:
        geo_val = raw_geo

    if isinstance(raw_payload, dict):
        payload_str = json.dumps(raw_payload, ensure_ascii=False)
    elif raw_payload is None:
        payload_str = "{}"
    else:
        payload_str = str(raw_payload)

    record = dict(ev)
    record.update(
        {
            "event_id": str(ev.get("event_id") or ""),
            "ts": ev.get("ts") or datetime.now(timezone.utc).isoformat(),
            "session_id": ev.get("session_id") or "",
            "user_id": ev.get("user_id"),
            "event_type": ev.get("event_type") or "",
            "track_id": track_id,
            "device": ev.get("device") or "unknown",
            "geo": geo_val,
            "entrypoint": ev.get("entrypoint") or "unknown",
            "payload": payload_str,
        }
    )
    return record


def run_simulator() -> None:
    p = Producer({"bootstrap.servers": BOOTSTRAP})
    print(
        f"[SIMULATE=1] Enviando eventos simulados a {BOOTSTRAP} topic={KAFKA_TOPIC}... (Ctrl+C para parar)"
    )
    try:
        while True:
            u = f"u{random.randint(1, 100)}"
            ev = {
                "event_id": str(uuid.uuid4()),
                "ts": datetime.now(timezone.utc).isoformat(),
                "session_id": f"s{random.randint(1, 300)}",
                "user_id": u,
                "event_type": random.choice(EVENTS),
                "track_id": f"t{random.randint(1, 300)}",
                "device": random.choice(["web_desktop", "web_mobile", "web_tablet"]),
                "geo": random.choice(["Colombia", "Mexico", "Argentina", "Spain"]),
                "entrypoint": random.choice(["home", "search", "playlist"]),
                "payload": "{}",
            }
            p.produce(KAFKA_TOPIC, key=u, value=json.dumps(ev, ensure_ascii=False))
            p.poll(0)
            time.sleep(0.1)
    except KeyboardInterrupt:
        p.flush()


def run_connector() -> None:
    if not TELEMETRY_DRAIN_TOKEN:
        raise SystemExit(
            "Falta TELEMETRY_DRAIN_TOKEN para drenar el outbox de Django "
            "(ejemplo: TELEMETRY_DRAIN_TOKEN=<token> python producer.py, o SIMULATE=1 python producer.py)."
        )

    p = Producer({"bootstrap.servers": BOOTSTRAP})
    session = requests.Session()
    headers = {"Authorization": f"Bearer {TELEMETRY_DRAIN_TOKEN}"}
    cursor = int(os.getenv("INITIAL_CURSOR", "0"))

    print(
        f"Conector Outbox -> Kafka activo: DJANGO_URL={DJANGO_URL} -> "
        f"BOOTSTRAP={BOOTSTRAP} topic={KAFKA_TOPIC} (Ctrl+C para parar)"
    )

    try:
        while True:
            try:
                resp = session.get(
                    f"{DJANGO_URL}/api/events/drain/",
                    params={"since": cursor, "limit": DRAIN_LIMIT},
                    headers=headers,
                    timeout=15,
                )
                resp.raise_for_status()
                data = resp.json()
            except Exception as exc:
                print(f"[ERROR drain] No se pudo consultar {DJANGO_URL}/api/events/drain/: {exc}")
                time.sleep(POLL_SECONDS)
                continue

            events = data.get("events") or []
            if not events:
                time.sleep(POLL_SECONDS)
                continue

            next_cursor = data.get("next_cursor", cursor)
            has_more = bool(data.get("has_more", False))
            delivery_errors: list[str] = []

            def _on_delivery(err, msg):
                if err is not None:
                    delivery_errors.append(str(err))

            for ev in events:
                record = normalize_outbox_event(ev)
                key = str(ev.get("session_id") or ev.get("user_id") or "anon")
                p.produce(
                    KAFKA_TOPIC,
                    key=key,
                    value=json.dumps(record, ensure_ascii=False),
                    on_delivery=_on_delivery,
                )
                p.poll(0)

            remaining = p.flush(15.0)
            if remaining > 0 or delivery_errors:
                print(
                    f"[ERROR Kafka] No se confirmará el lote (sin entregar={remaining}, "
                    f"errores={delivery_errors}). Se reintentará en el siguiente ciclo."
                )
                time.sleep(POLL_SECONDS)
                continue

            try:
                ack_resp = session.post(
                    f"{DJANGO_URL}/api/events/ack/",
                    json={"last_id": next_cursor},
                    headers=headers,
                    timeout=15,
                )
                ack_resp.raise_for_status()
                acked_count = ack_resp.json().get("acked", len(events))
                print(
                    f"Drenados y confirmados {len(events)} eventos (acked={acked_count}, cursor={cursor} -> {next_cursor})"
                )
                cursor = next_cursor
            except Exception as exc:
                print(f"[ERROR ack] Eventos publicados en Kafka pero falló POST /api/events/ack/: {exc}")
                time.sleep(POLL_SECONDS)
                continue

            if not has_more:
                time.sleep(POLL_SECONDS)
    except KeyboardInterrupt:
        p.flush()


if __name__ == "__main__":
    if SIMULATE:
        run_simulator()
    else:
        run_connector()
